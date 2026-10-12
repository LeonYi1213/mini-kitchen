import Foundation
import UIKit

struct ImportJob: Decodable {
    let id: String
    let status: String
    let completedStages: Int
    let recipe: Recipe?
    let message: String?
}
enum ImportFailure: LocalizedError {
    case invalidLink, unavailable, unreadable, incomplete, timeout
    var errorDescription: String? {
        switch self {
        case .invalidLink: "请粘贴有效的小红书分享链接。"
        case .unavailable: "暂时无法生成菜谱，请稍后重试。"
        case .unreadable: "暂时读不到这篇笔记，请重新复制分享链接。"
        case .incomplete: "菜谱信息不完整，请重新生成。"
        case .timeout: "生成时间较长，请稍后重试。"
        }
    }
}
struct ImportService {
    let baseURL: URL?
    init(baseURL: URL? = nil) {
        let configured = (Bundle.main.object(forInfoDictionaryKey: "ImportServiceURL") as? String).flatMap(URL.init(string:))
        self.baseURL = baseURL ?? configured
    }
    static func link(in text: String) -> URL? {
        guard let detector = try? NSDataDetector(types: NSTextCheckingResult.CheckingType.link.rawValue) else { return nil }
        let matches = detector.matches(in: text, range: NSRange(text.startIndex..., in: text))
        return matches.compactMap(\.url).first {
            $0.scheme == "https" && ["xhslink.cn", "xhslink.com", "www.xiaohongshu.com", "xiaohongshu.com"].contains($0.host ?? "")
        }
    }
    func create(_ url: URL) async throws -> ImportJob {
        guard let baseURL, Self.allowedEndpoint(baseURL) else { throw ImportFailure.unavailable }
        var request = URLRequest(url: baseURL.appendingPathComponent("imports"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(["url": url.absoluteString])
        return try await send(request)
    }
    static func allowedEndpoint(_ url: URL) -> Bool {
        if url.scheme == "https" { return true }
        #if DEBUG && targetEnvironment(simulator)
        return url.scheme == "http" && ["localhost", "127.0.0.1"].contains(url.host ?? "")
        #else
        return false
        #endif
    }
    func poll(_ id: String) async throws -> ImportJob {
        guard let baseURL else { throw ImportFailure.unavailable }
        return try await send(URLRequest(url: baseURL.appendingPathComponent("imports").appendingPathComponent(id)))
    }
    func cancel(_ id: String) async {
        guard let baseURL else { return }
        var request = URLRequest(url: baseURL.appendingPathComponent("imports").appendingPathComponent(id))
        request.httpMethod = "DELETE"
        authorize(&request)
        _ = try? await URLSession.shared.data(for: request)
    }
    func cacheImages(for recipe: Recipe) async throws {
        let references = Set(([recipe.cover] + (recipe.illustrated_steps ?? []).map(\.image)).compactMap { $0 })
        for reference in references where reference.hasPrefix("assets/") {
            _ = try await imageData(reference)
        }
    }
    func imageData(_ reference: String) async throws -> Data {
        guard let file = RecipeAssets.localURL(reference) else { throw ImportFailure.incomplete }
        if let data = try? Data(contentsOf: file), UIImage(data: data) != nil { return data }
        guard let baseURL, Self.allowedEndpoint(baseURL) else { throw ImportFailure.unavailable }
        var request = URLRequest(url: baseURL.appendingPathComponent(reference))
        request.timeoutInterval = 30
        authorize(&request)
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse, response.statusCode == 200,
              response.mimeType == "image/jpeg", data.count <= 10_000_000,
              UIImage(data: data) != nil else { throw ImportFailure.incomplete }
        try Task.checkCancellation()
        try FileManager.default.createDirectory(at: file.deletingLastPathComponent(), withIntermediateDirectories: true)
        try data.write(to: file, options: .atomic)
        return data
    }
    private func authorize(_ request: inout URLRequest) {
        if let token = Bundle.main.object(forInfoDictionaryKey: "ImportServiceToken") as? String, !token.isEmpty {
            request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization")
        }
    }
    private func send(_ request: URLRequest) async throws -> ImportJob {
        var request = request; request.timeoutInterval = 30
        authorize(&request)
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let response = response as? HTTPURLResponse, (200..<300).contains(response.statusCode) else { throw ImportFailure.unavailable }
        return try JSONDecoder().decode(ImportJob.self, from: data)
    }
}
enum RecipeAssets {
    static func localURL(_ reference: String) -> URL? {
        guard reference.range(of: #"^assets/xhs-[a-f0-9]{24}/[a-f0-9]{32}/frame-[0-9]{3}\.jpg$"#, options: .regularExpression) != nil else { return nil }
        return FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("RecipeImages").appendingPathComponent(reference)
    }
}

@MainActor final class ImportModel: ObservableObject {
    enum Phase { case input, working, review, failure }
    @Published var phase: Phase = .input
    @Published var text = ""
    @Published var stages = 0
    @Published var draft: Recipe?
    @Published var message = ""
    @Published var duplicate = false
    @Published var updating = false
    private var task: Task<Void, Never>?
    private var generation = UUID()
    private var jobID: String?
    private let service = ImportService()
    func start(existing: [Recipe]) {
        guard let url = ImportService.link(in: text) else { message = ImportFailure.invalidLink.localizedDescription; return }
        cancel()
        updating = false
        if let recipe = existing.first(where: { !$0.needsFormatUpgrade && ($0.source == url.absoluteString || ($0.id.hasPrefix("xhs-") && url.pathComponents.contains(String($0.id.dropFirst(4))))) }) {
            draft = recipe; duplicate = true; stages = 4; phase = .review; return
        }
        generation = UUID(); let run = generation
        phase = .working; stages = 0; message = ""; duplicate = false; updating = false
        task = Task {
            do {
                var job = try await service.create(url)
                guard run == generation else { await service.cancel(job.id); return }
                jobID = job.id
                let deadline = Date().addingTimeInterval(600)
                while true {
                    try Task.checkCancellation()
                    guard run == generation else { return }
                    stages = max(stages, min(3, max(0, job.completedStages)))
                    if job.status == "completed" {
                        guard let recipe = job.recipe, recipe.valid else { throw ImportFailure.incomplete }
                        let old = existing.first { $0.id == recipe.id || $0.source == recipe.source }
                        updating = old.map { recipe.upgrades($0) } ?? false
                        let selected = updating ? recipe : (old ?? recipe)
                        try await service.cacheImages(for: selected)
                        try Task.checkCancellation()
                        guard run == generation else { return }
                        draft = selected
                        duplicate = old != nil && !updating
                        stages = 4; phase = .review; jobID = nil; return
                    }
                    if job.status == "failed" || job.status == "cancelled" { throw ImportFailure.unreadable }
                    guard ["queued", "running"].contains(job.status) else { throw ImportFailure.incomplete }
                    if Date() > deadline { throw ImportFailure.timeout }
                    try await Task.sleep(for: .seconds(1.5))
                    job = try await service.poll(job.id)
                }
            } catch is CancellationError { return }
            catch {
                guard run == generation else { return }
                if let id = jobID { await service.cancel(id) }
                guard run == generation else { return }
                jobID = nil; message = (error as? ImportFailure)?.localizedDescription ?? "网络连接中断，请重试。"; phase = .failure
            }
        }
    }
    func cancel() {
        generation = UUID(); task?.cancel(); task = nil
        if let id = jobID { Task { await service.cancel(id) } }
        jobID = nil; phase = .input
    }
}
