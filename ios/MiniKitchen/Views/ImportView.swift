import SwiftUI
import UniformTypeIdentifiers
import PhotosUI

struct SelectedCookingVideo: Transferable {
    let url: URL
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(contentType: .movie) { video in SentTransferredFile(video.url) } importing: { received in
            SelectedCookingVideo(url: try ImportService.copyVideo(received.file))
        }
    }
}

struct ImportView: View {
    @EnvironmentObject var store: KitchenStore
    @Environment(\.dismiss) private var dismiss
    @StateObject private var model = ImportModel()
    let initialText: String
    @State private var saved: Recipe?
    @State private var selectedPhoto: PhotosPickerItem?
    @State private var video: URL?
    @State private var videoName = ""
    @State private var pickingVideo = false
    @State private var preparingVideo = false
    private var labels: [String] { [video == nil ? "读取分享内容" : "上传视频", "识别视频与字幕", "整理食材和步骤", "校验用量与耗时"] }
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    switch model.phase {
                    case .input: input
                    case .working: working
                    case .failure: failure
                    case .review: review
                    }
                }.padding(22).frame(maxWidth: 620)
            }.kitchenPage().navigationTitle("收藏新菜").navigationBarTitleDisplayMode(.inline)
                .toolbar { ToolbarItem(placement: .cancellationAction) { Button("关闭") { model.cancel(); dismiss() }.disabled(preparingVideo) } }
                .navigationDestination(item: $saved) { RecipeDetail(recipe: $0) }
        }.onAppear { if model.text.isEmpty { model.text = initialText } }
            .onDisappear { model.cancel(); if let video { try? FileManager.default.removeItem(at: video) } }
            .onChange(of: selectedPhoto) { _, item in
                guard let item else { return }
                preparingVideo = true
                Task {
                    defer { preparingVideo = false; selectedPhoto = nil }
                    do {
                        guard let selected = try await item.loadTransferable(type: SelectedCookingVideo.self) else { throw ImportFailure.invalidVideo }
                        if let video { try? FileManager.default.removeItem(at: video) }
                        video = selected.url; videoName = "已选择相册视频"; model.message = ""
                    } catch { model.message = (error as? ImportFailure)?.localizedDescription ?? "无法读取相册视频，请下载原视频后再试。" }
                }
            }
            .fileImporter(isPresented: $pickingVideo, allowedContentTypes: [.movie], allowsMultipleSelection: false) { result in
                guard case .success(let urls) = result, let source = urls.first else { return }
                preparingVideo = true
                Task {
                    do {
                        let copy = try await Task.detached { try ImportService.copyVideo(source) }.value
                        if let video { try? FileManager.default.removeItem(at: video) }
                        video = copy; videoName = source.lastPathComponent; model.message = ""
                    } catch { model.message = (error as? ImportFailure)?.localizedDescription ?? "无法打开视频，请先将它保存到文件。" }
                    preparingVideo = false
                }
            }
            .interactiveDismissDisabled(model.phase == .working || preparingVideo)
    }
    private var input: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("把做菜视频，\n变成你的菜谱。").font(.system(size: 30, weight: .bold))
            Text("上传已保存的视频，整理食材、备菜、步骤与耗时。").font(.subheadline).foregroundStyle(KitchenStyle.muted)
            VStack(alignment: .leading, spacing: 16) {
                PhotosPicker(selection: $selectedPhoto, matching: .videos) {
                    Label("从相册选择视频", systemImage: "photo.on.rectangle").foregroundStyle(.white).frame(maxWidth: .infinity, minHeight: 48).contentShape(Rectangle())
                }.buttonStyle(.borderedProminent).disabled(preparingVideo)
                Button { pickingVideo = true } label: {
                    Label(video == nil ? "选择视频文件" : videoName, systemImage: "video.badge.plus").lineLimit(2)
                        .frame(maxWidth: .infinity, minHeight: 48).contentShape(Rectangle())
                }.buttonStyle(.bordered).disabled(preparingVideo)
                if preparingVideo { ProgressView("正在准备视频…") }
                Text("支持 MP4、MOV，最长 15 分钟，最大 200 MB。视频上传至你的云端服务，画面交由 Kimi 整理；处理后删除原视频，保留菜谱配图。").font(.caption).foregroundStyle(KitchenStyle.muted)
                if video != nil {
                    Button("移除视频，改用链接") { if let video { try? FileManager.default.removeItem(at: video) }; video = nil }
                }
                if video == nil {

                DisclosureGroup("或粘贴分享链接") {
                TextEditor(text: $model.text).frame(minHeight: 115).padding(8).scrollContentBackground(.hidden)
                    .background(KitchenStyle.background, in: RoundedRectangle(cornerRadius: 14)).accessibilityLabel("小红书分享链接")
                HStack {
                    Text("整段分享文案也可以").font(.caption).foregroundStyle(KitchenStyle.muted); Spacer()
                    PasteButton(payloadType: String.self) { model.text = $0.joined(separator: "\n") }.buttonBorderShape(.capsule)
                }
                }
                }
                if !model.message.isEmpty { Text(model.message).font(.caption).foregroundStyle(.orange) }
                PrimaryButton(title: "✧ 生成菜谱") { model.start(existing: store.recipes, video: video) }.disabled(preparingVideo || (video == nil && model.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty))
            }.padding(22).background(.white, in: RoundedRectangle(cornerRadius: 24))
        }
    }
    private var working: some View {
        VStack(alignment: .leading, spacing: 24) {
            Label("AI 生成中", systemImage: "sparkles").font(.caption).foregroundStyle(KitchenStyle.muted)
            Text("正在把灵感\n整理成你的菜谱").font(.title.bold())
            HStack { Text("第 \(min(4, model.stages + 1)) / 4 步"); Spacer(); Text("\(model.stages * 25)%") }.font(.subheadline)
            ProgressView(value: Double(model.stages), total: 4)
            ForEach(Array(labels.enumerated()), id: \.offset) { index, title in
                HStack(spacing: 15) {
                    if index == model.stages { ProgressView().frame(width: 24) }
                    else { Image(systemName: index < model.stages ? "checkmark.circle.fill" : "circle").frame(width: 24) }
                    Text(title).font(.body)
                }.foregroundStyle(index <= model.stages ? KitchenStyle.green : KitchenStyle.muted.opacity(0.6)).padding(.vertical, 8)
            }
            SecondaryButton(title: "取消生成", expanded: true) { model.cancel() }
        }.padding(24).background(.white, in: RoundedRectangle(cornerRadius: 24))
    }
    private var failure: some View {
        VStack(alignment: .leading, spacing: 20) {
            Image(systemName: "exclamationmark.circle").font(.largeTitle)
            Text("这次没能生成菜谱").font(.title2.bold())
            Text(model.message).foregroundStyle(KitchenStyle.muted)
            PrimaryButton(title: "重新尝试") { model.start(existing: store.recipes, video: video) }
            SecondaryButton(title: "更换视频或链接", expanded: true) { model.phase = .input }
        }.padding(24).background(.white, in: RoundedRectangle(cornerRadius: 24))
    }
    @ViewBuilder private var review: some View {
        if let recipe = model.draft {
            Label("整理完成", systemImage: "checkmark.circle.fill").foregroundStyle(KitchenStyle.green)
            ProgressView(value: 1)
            RecipePhoto(name: recipe.cover, height: 180).clipShape(RoundedRectangle(cornerRadius: 20))
            Text(recipe.title).font(.title.bold())
            Text(recipe.duration).font(.subheadline).foregroundStyle(KitchenStyle.muted)
            if model.duplicate {
                Text("这篇笔记已经收藏过了。").font(.subheadline).padding(15).frame(maxWidth: .infinity, alignment: .leading).background(KitchenStyle.pale, in: RoundedRectangle(cornerRadius: 14))
            }
            Text("备菜清单").font(.headline)
            IngredientsView(recipe: recipe)
            if model.updating {
                Text("已为这道菜补齐图文。更新后，旧的备菜勾选和烹饪进度将重置。").font(.subheadline).foregroundStyle(KitchenStyle.muted)
            }
            RecipeSteps(recipe: recipe, preparation: true)
            RecipeSteps(recipe: recipe, preparation: false)
            RecipeNotes(recipe: recipe)
            PrimaryButton(title: model.duplicate ? "查看已有菜谱" : (model.updating ? "更新为图文菜谱" : "收藏这道菜")) {
                saved = model.duplicate ? recipe : store.add(recipe)
                model.duplicate = true
            }
        }
    }
}
