import XCTest
@testable import MiniKitchen

final class KitchenTests: XCTestCase {
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
        XCTAssertEqual(recipes.count, 18)
        XCTAssertEqual(Set(recipes.map(\.id)).count, recipes.count)
        for recipe in recipes {
            XCTAssertTrue(recipe.valid, recipe.title)
            for step in recipe.illustrated_steps ?? [] {
                if let image = step.image { XCTAssertNotNil(Bundle.main.url(forResource: image, withExtension: nil), image) }
            }
        }
    }
}
