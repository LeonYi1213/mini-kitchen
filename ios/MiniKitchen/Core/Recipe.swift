import Foundation

struct Ingredient: Codable, Hashable {
    var name: String
    var amount: Double?
    var unit: String
    var quantity: String {
        guard let amount else { return "适量" }
        return amount.formatted(.number.precision(.fractionLength(0...2))) + " " + unit
    }
}
struct StepTime: Codable, Hashable {
    var min: Int
    var max: Int
    var wait: Bool?
    var label: String { min == max ? "约 \(min) 分钟" : "约 \(min)–\(max) 分钟" }
}
struct RecipeTiming: Codable, Hashable {
    var prep: [StepTime]
    var cook: [StepTime]
}
struct IllustratedStep: Codable, Hashable {
    var title: String
    var text: String
    var source_time: String?
    var image: String?
}
struct Recipe: Codable, Identifiable, Hashable {
    var id: String
    var title: String
    var source: String
    var ingredients: [Ingredient]
    var prep: [String]
    var cook: [String]
    var timing: RecipeTiming?
    var illustrated_steps: [IllustratedStep]?
    var cover: String?
    var steps: [String] { prep + cook }
    func time(at index: Int) -> StepTime? {
        let values = (timing?.prep ?? []) + (timing?.cook ?? [])
        return values.indices.contains(index) ? values[index] : nil
    }
    var duration: String {
        guard let timing else { return "用时待确认" }
        let values = timing.prep + timing.cook
        return StepTime(min: values.reduce(0) { $0 + $1.min }, max: values.reduce(0) { $0 + $1.max }).label
    }
    func image(at index: Int) -> String? {
        guard steps.indices.contains(index) else { return cover }
        return illustrated_steps?.first(where: { $0.text == steps[index] })?.image ?? cover
    }
    var valid: Bool {
        !id.isEmpty && !title.trimmingCharacters(in: .whitespaces).isEmpty && !ingredients.isEmpty && !cook.isEmpty &&
        steps.allSatisfy { !$0.trimmingCharacters(in: .whitespaces).isEmpty } &&
        ingredients.allSatisfy { !$0.name.isEmpty && ($0.amount == nil || $0.amount! >= 0) } &&
        (timing == nil || (timing!.prep.count == prep.count && timing!.cook.count == cook.count &&
         (timing!.prep + timing!.cook).allSatisfy { $0.min >= 0 && $0.max >= $0.min }))
    }
}

struct CookingTimer: Codable, Equatable {
    var deadline: Date?
    var pausedSeconds: TimeInterval?
    func remaining(at now: Date) -> TimeInterval { max(0, deadline?.timeIntervalSince(now) ?? pausedSeconds ?? 0) }
    mutating func toggle(at now: Date) {
        if deadline != nil { pausedSeconds = remaining(at: now); deadline = nil }
        else if let seconds = pausedSeconds { deadline = now.addingTimeInterval(seconds); pausedSeconds = nil }
    }
}
struct DishProgress: Codable {
    var step = 0
    var checked: Set<Int> = []
    var timer: CookingTimer?
}
struct MealState: Codable {
    var id = UUID().uuidString
    var revisions: [String: Double] = [:]
    var selected: [String] = []
    var progress: [String: DishProgress] = [:]
    var imported: [Recipe] = []
    mutating func toggle(_ id: String) {
        if selected.contains(id) { selected.removeAll { $0 == id } }
        else { selected.append(id) }
    }
    mutating func advance(_ recipe: Recipe) {
        var dish = progress[recipe.id] ?? DishProgress()
        dish.step = min(recipe.steps.count, dish.step + 1)
        dish.timer = nil
        progress[recipe.id] = dish
    }
    func recommendation(in recipes: [Recipe], now: Date = Date()) -> Recipe? {
        let candidates = recipes.filter { recipe in
            let state = progress[recipe.id] ?? DishProgress()
            return selected.contains(recipe.id) && state.step < recipe.steps.count
        }
        func rank(_ recipe: Recipe) -> Int {
            let state = progress[recipe.id] ?? DishProgress()
            if let timer = state.timer {
                if timer.deadline != nil && timer.remaining(at: now) == 0 { return 100000 }
                return -100000
            }
            // Active cooking first, then the dish with the longest upcoming wait.
            if state.step >= recipe.prep.count { return 10000 }
            let upcoming = (state.step..<recipe.steps.count).compactMap { recipe.time(at: $0) }
            return upcoming.filter { $0.wait == true }.map(\.max).max() ?? 0
        }
        return candidates.sorted {
            let a = rank($0), b = rank($1)
            if a == b { return selected.firstIndex(of: $0.id)! < selected.firstIndex(of: $1.id)! }
            return a > b
        }.first
    }
}
