import XCTest
@testable import MiniKitchen

final class KitchenTests: XCTestCase {
    func testServiceOnlyAllowsHTTPSAndDebugSimulatorLoopback() {
        XCTAssertTrue(ImportService.allowedEndpoint(URL(string: "https://kitchen.example.com")!))
        XCTAssertFalse(ImportService.allowedEndpoint(URL(string: "http://kitchen.example.com")!))
        XCTAssertFalse(ImportService.allowedEndpoint(URL(string: "http://localhost.evil.example")!))
        #if DEBUG && targetEnvironment(simulator)
        XCTAssertTrue(ImportService.allowedEndpoint(URL(string: "http://localhost:18080")!))
        #else
        XCTAssertFalse(ImportService.allowedEndpoint(URL(string: "http://localhost:18080")!))
        #endif
    }
    func testImportedRecipeUpgradeAndImageReferences() throws {
        let old = recipe("xhs-" + String(repeating: "a", count: 24), wait: 30)
        var updated = old
        let image = "assets/\(old.id)/\(String(repeating: "b", count: 32))/frame-001.jpg"
        updated.cover = image
        updated.illustrated_steps = updated.cook.map { IllustratedStep(title: "操作", text: $0, source_time: "约 00:10", image: image) }
        updated.notes = ["用时为估算。"]
        updated.format_version = 3
        XCTAssertTrue(updated.upgrades(old))
        XCTAssertFalse(old.upgrades(updated))
        XCTAssertFalse(updated.upgrades(updated))
        XCTAssertFalse(updated.needsFormatUpgrade)
        var previous = updated; previous.format_version = 2
        XCTAssertTrue(previous.needsFormatUpgrade)
        XCTAssertTrue(updated.upgrades(previous))
        let restored = try JSONDecoder().decode(Recipe.self, from: JSONEncoder().encode(updated))
        XCTAssertEqual(restored.notes, updated.notes)
        XCTAssertEqual(restored.image(at: 1), image)
        XCTAssertNotNil(RecipeAssets.localURL(image))
        XCTAssertNil(RecipeAssets.localURL("assets/../../kitchen.json"))
        XCTAssertNil(RecipeAssets.localURL("https://evil.example/frame-001.jpg"))
        updated.illustrated_steps?[0].text = "不相关的步骤"
        XCTAssertFalse(updated.hasIllustratedFormat)
    }
    func testUploadedVideoImageReferencesAndPrivateCopy() throws {
        let ref = "assets/video-" + String(repeating: "a", count: 24) + "/" + String(repeating: "b", count: 32) + "/frame-001.jpg"
        XCTAssertNotNil(RecipeAssets.localURL(ref))
        XCTAssertNil(RecipeAssets.localURL(ref.replacingOccurrences(of: "frame-001.jpg", with: "../../private.json")))
        let source = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString + ".mov")
        defer { try? FileManager.default.removeItem(at: source) }
        try Data([1, 2, 3]).write(to: source)
        let copy = try ImportService.copyVideo(source)
        defer { try? FileManager.default.removeItem(at: copy) }
        XCTAssertNotEqual(source, copy)
        XCTAssertEqual(try Data(contentsOf: copy), Data([1, 2, 3]))
        try Data().write(to: source)
        XCTAssertThrowsError(try ImportService.copyVideo(source))
    }
    private func recipe(_ id: String, wait: Int) -> Recipe {
        Recipe(id: id, title: id, source: "https://www.xiaohongshu.com/explore/" + id,
               ingredients: [Ingredient(name: "水", unit: "适量")], prep: ["清洗"], cook: ["炖煮", "出锅"],
               timing: RecipeTiming(prep: [StepTime(min: 1, max: 2)], cook: [StepTime(min: wait, max: wait, wait: true), StepTime(min: 1, max: 1)]))
    }
    func testFirstMealIsEmptyAndTogglingDoesNotDuplicate() {
        var state = MealState()
        XCTAssertTrue(state.selected.isEmpty)
        state.toggle("a"); state.toggle("b"); state.toggle("a")
        XCTAssertEqual(state.selected, ["b"])
        state.toggle("a")
        XCTAssertEqual(state.selected, ["b", "a"])
    }
    func testDifferentDishesKeepIndependentStepsAndChecklist() throws {
        let ribs = recipe("ribs", wait: 45), fish = recipe("fish", wait: 10)
        var state = MealState(); state.selected = [ribs.id, fish.id]
        state.progress[ribs.id] = DishProgress(step: 1, checked: [0])
        state.advance(fish)
        XCTAssertEqual(state.progress[ribs.id]?.step, 1)
        XCTAssertEqual(state.progress[fish.id]?.step, 1)
        let restored = try JSONDecoder().decode(MealState.self, from: JSONEncoder().encode(state))
        XCTAssertEqual(restored.progress[ribs.id]?.checked, [0])
        for _ in 0..<10 { state.advance(fish) }
        XCTAssertEqual(state.progress[fish.id]?.step, fish.steps.count)
    }
    func testCookingHistorySurvivesNewMealsAndDeduplicatesCompletion() throws {
        let fish = recipe("fish", wait: 10), ribs = recipe("ribs", wait: 45)
        var state = MealState()
        state.advance(fish)
        XCTAssertEqual(state.cookingCount(fish), 0)
        for _ in 0..<5 { state.advance(fish) }
        XCTAssertEqual(state.cookingCount(fish), 1)
        state.progress[fish.id]?.step = fish.steps.count - 1
        state.advance(fish)
        XCTAssertEqual(state.cookingCount(fish), 1)
        state.id = UUID().uuidString; state.progress = [:]
        for _ in fish.steps { state.advance(fish) }
        let restored = try JSONDecoder().decode(MealState.self, from: JSONEncoder().encode(state))
        XCTAssertEqual(restored.cookingCount(fish), 2)
        XCTAssertEqual(restored.frequentlyCooked(in: [ribs, fish]).map(\.id), [fish.id, ribs.id])
        XCTAssertEqual(MealState().frequentlyCooked(in: [ribs, fish]).map(\.id), [ribs.id, fish.id])
        var legacy = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(state)) as? [String: Any])
        legacy.removeValue(forKey: "completedMeals")
        let migrated = try JSONDecoder().decode(MealState.self, from: JSONSerialization.data(withJSONObject: legacy))
        XCTAssertEqual(migrated.cookingCount(fish), 0)
        XCTAssertEqual(migrated.progress[fish.id]?.step, fish.steps.count)
    }
    func testLongWaitFirstThenOtherDishDuringTimerThenExpiredTimerFirst() {
        let ribs = recipe("ribs", wait: 45), fish = recipe("fish", wait: 10)
        let now = Date(timeIntervalSince1970: 1000)
        var state = MealState(); state.selected = [fish.id, ribs.id]
        XCTAssertEqual(state.recommendation(in: [fish, ribs], now: now)?.id, ribs.id)
        state.progress[ribs.id] = DishProgress(step: 1, timer: CookingTimer(deadline: now.addingTimeInterval(120)))
        XCTAssertEqual(state.recommendation(in: [fish, ribs], now: now)?.id, fish.id)
        XCTAssertEqual(state.recommendation(in: [fish, ribs], now: now.addingTimeInterval(121))?.id, ribs.id)
    }
    func testTimerRestoresAndPausesUsingAbsoluteDeadline() throws {
        let now = Date(timeIntervalSince1970: 1000)
        var timer = CookingTimer(deadline: now.addingTimeInterval(100))
        timer.toggle(at: now.addingTimeInterval(10))
        XCTAssertEqual(timer.remaining(at: now.addingTimeInterval(1000)), 90)
        timer.toggle(at: now.addingTimeInterval(30))
        let restored = try JSONDecoder().decode(CookingTimer.self, from: JSONEncoder().encode(timer))
        XCTAssertEqual(restored.remaining(at: now.addingTimeInterval(40)), 80)
        XCTAssertEqual(restored.remaining(at: now.addingTimeInterval(200)), 0)
    }
    func testUnknownAmountAndInvalidTiming() {
        XCTAssertEqual(Ingredient(name: "盐", unit: "克").quantity, "适量")
        XCTAssertEqual(Ingredient(name: "酒", unit: "适量（可选）").quantity, "适量（可选）")
        XCTAssertEqual(Ingredient(name: "水", unit: "适量（炖煮用）").quantity, "适量（炖煮用）")
        var r = recipe("a", wait: 10); XCTAssertTrue(r.valid)
        r.timing?.cook = []; XCTAssertFalse(r.valid)
    }
    func testShareLinkValidation() {
        XCTAssertNotNil(ImportService.link(in: "好吃！ https://xhslink.cn/o/test 来看看"))
        XCTAssertNil(ImportService.link(in: "https://xiaohongshu.com.evil.test/explore/a"))
        XCTAssertNil(ImportService.link(in: "http://xhslink.cn/o/test"))
    }
    func testBundledCatalogAndImages() throws {
        let url = try XCTUnwrap(Bundle.main.url(forResource: "recipes", withExtension: "json"))
        let recipes = try JSONDecoder().decode([Recipe].self, from: Data(contentsOf: url))
        XCTAssertEqual(recipes.count, 42)
        XCTAssertEqual(Set(recipes.map(\.id)).count, recipes.count)
        for recipe in recipes {
            XCTAssertTrue(recipe.valid, recipe.title)
            for step in recipe.illustrated_steps ?? [] {
                if let image = step.image { XCTAssertNotNil(Bundle.main.url(forResource: image, withExtension: nil), image) }
            }
        }
    }
}
