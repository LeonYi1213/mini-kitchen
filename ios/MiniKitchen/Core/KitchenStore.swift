import SwiftUI

@MainActor final class KitchenStore: ObservableObject {
    @Published private(set) var recipes: [Recipe] = []
    @Published private(set) var meal = MealState()
    @Published var error: String?
    private let file: URL
    private let cloud = NSUbiquitousKeyValueStore.default
    private var cloudObserver: NSObjectProtocol?
    init() {
        let folder = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        file = folder.appendingPathComponent("kitchen.json")
        do {
            try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
            guard let url = Bundle.main.url(forResource: "recipes", withExtension: "json") else { throw CocoaError(.fileNoSuchFile) }
            recipes = try JSONDecoder().decode([Recipe].self, from: Data(contentsOf: url))
            if FileManager.default.fileExists(atPath: file.path) {
                meal = try JSONDecoder().decode(MealState.self, from: Data(contentsOf: file))
            }
            recipes += meal.imported.filter { r in !recipes.contains { $0.id == r.id } }
            meal.selected = meal.selected.filter { id in recipes.contains { $0.id == id } }
        } catch { self.error = "读取菜谱失败，请重新打开小厨房。" }
        cloudObserver = NotificationCenter.default.addObserver(forName: NSUbiquitousKeyValueStore.didChangeExternallyNotification, object: cloud, queue: .main) { [weak self] _ in
            Task { @MainActor [weak self] in self?.mergeCloud() }
        }
        cloud.synchronize()
        mergeCloud()
    }
    var selected: [Recipe] { meal.selected.compactMap { id in recipes.first { $0.id == id } } }
    func progress(_ recipe: Recipe) -> DishProgress {
        var value = meal.progress[recipe.id] ?? DishProgress()
        value.step = max(0, min(value.step, recipe.steps.count))
        value.checked = value.checked.filter { recipe.ingredients.indices.contains($0) }
        return value
    }
    func update(_ recipe: Recipe, _ change: (inout DishProgress) -> Void) {
        let before = progress(recipe)
        var state = before; change(&state); meal.progress[recipe.id] = state
        if before.checked != state.checked { publish(state.checked, key: "checks.\(meal.id).\(recipe.id)") }
        if before.step != state.step || before.timer != state.timer {
            publish(StepSnapshot(step: state.step, timer: state.timer), key: "steps.\(meal.id).\(recipe.id)")
        }
        save()
    }
    func toggle(_ recipe: Recipe) {
        meal.toggle(recipe.id)
        publish(MealHeader(id: meal.id, selected: meal.selected), key: "meal")
        save()
    }
    func advance(_ recipe: Recipe) {
        update(recipe) { $0.step = min(recipe.steps.count, $0.step + 1); $0.timer = nil }
    }
    func startNewMeal() {
        let oldID = meal.id
        meal.id = UUID().uuidString; meal.selected = []; meal.progress = [:]
        publish(MealHeader(id: meal.id, selected: []), key: "meal")
        for key in cloud.dictionaryRepresentation.keys where key.hasPrefix("steps.\(oldID).") || key.hasPrefix("checks.\(oldID).") {
            cloud.removeObject(forKey: key); meal.revisions.removeValue(forKey: key)
        }
        save()
    }
    func add(_ recipe: Recipe) -> Recipe {
        if let existing = recipes.first(where: { $0.id == recipe.id || $0.source == recipe.source }) {
            guard recipe.valid, recipe.upgrades(existing), meal.imported.contains(where: { $0.id == existing.id }) else { return existing }
            installUpdate(recipe)
            publish(recipe, key: "recipe.\(recipe.id)")
            publish(Set<Int>(), key: "checks.\(meal.id).\(recipe.id)")
            publish(StepSnapshot(step: 0, timer: nil), key: "steps.\(meal.id).\(recipe.id)")
            save(); return recipe
        }
        guard recipe.valid else { error = "菜谱信息不完整，请重新生成。"; return recipe }
        recipes.insert(recipe, at: 0); meal.imported.insert(recipe, at: 0)
        publish(recipe, key: "recipe.\(recipe.id)"); save(); return recipe
    }
    private func installUpdate(_ recipe: Recipe) {
        guard let index = recipes.firstIndex(where: { $0.id == recipe.id }),
              let imported = meal.imported.firstIndex(where: { $0.id == recipe.id }) else { return }
        recipes[index] = recipe; meal.imported[imported] = recipe
        // Re-generated steps cannot inherit numeric indexes from the older recipe.
        meal.progress[recipe.id] = DishProgress()
    }
    private struct MealHeader: Codable { var id: String; var selected: [String] }
    private struct StepSnapshot: Codable { var step: Int; var timer: CookingTimer? }
    private struct CloudValue<T: Codable>: Codable { var timestamp: Double; var value: T }
    private func publish<T: Codable>(_ value: T, key: String) {
        let timestamp = Date().timeIntervalSince1970
        guard let data = try? JSONEncoder().encode(CloudValue(timestamp: timestamp, value: value)) else { return }
        let used = cloud.dictionaryRepresentation.filter { $0.key != key }.values.compactMap { $0 as? Data }.reduce(0) { $0 + $1.count }
        guard data.count < 60_000, used + data.count < 900_000 else {
            error = "内容已保存在本机，云端空间暂不足以同步。"; return
        }
        meal.revisions[key] = timestamp; cloud.set(data, forKey: key); cloud.synchronize()
    }
    private func incoming<T: Codable>(_ type: T.Type, key: String) -> T? {
        guard let data = cloud.data(forKey: key),
              let envelope = try? JSONDecoder().decode(CloudValue<T>.self, from: data),
              envelope.timestamp > (meal.revisions[key] ?? 0) else { return nil }
        meal.revisions[key] = envelope.timestamp
        return envelope.value
    }
    private func mergeCloud() {
        for key in cloud.dictionaryRepresentation.keys where key.hasPrefix("recipe.") {
            if let recipe = incoming(Recipe.self, key: key), recipe.valid {
                if let old = recipes.first(where: { $0.id == recipe.id }) {
                    if recipe.upgrades(old) { installUpdate(recipe) }
                } else {
                    recipes.insert(recipe, at: 0); meal.imported.insert(recipe, at: 0)
                }
            }
        }
        if let header = incoming(MealHeader.self, key: "meal") {
            if header.id != meal.id { meal.id = header.id; meal.progress = [:] }
            var seen = Set<String>()
            meal.selected = header.selected.filter { seen.insert($0).inserted }
        }
        for recipe in recipes {
            var value = progress(recipe)
            if let checks = incoming(Set<Int>.self, key: "checks.\(meal.id).\(recipe.id)") {
                value.checked = checks.filter { recipe.ingredients.indices.contains($0) }
            }
            if let steps = incoming(StepSnapshot.self, key: "steps.\(meal.id).\(recipe.id)") {
                value.step = max(0, min(steps.step, recipe.steps.count)); value.timer = steps.timer
            }
            meal.progress[recipe.id] = value
        }
        save()
    }
    private func save() {
        do { try JSONEncoder().encode(meal).write(to: file, options: .atomic) }
        catch { self.error = "保存失败，请检查设备剩余空间后重试。" }
    }
}
