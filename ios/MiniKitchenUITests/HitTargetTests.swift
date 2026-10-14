import XCTest

final class HitTargetTests: XCTestCase {
    func testFourDishesTimerControlsRemainScrollable() throws {
        let app = XCUIApplication()
        app.launchArguments = ["--visual-regression"]
        app.launch()
        app.tabBars.buttons["做饭"].tap()
        let id = "xhs-66f0f9b4000000001902f568"
        let start = app.buttons["start-timer-\(id)"]
        for _ in 0..<8 { if start.isHittable && start.frame.maxY < app.tabBars.firstMatch.frame.minY { break }; app.swipeUp() }
        XCTAssertTrue(start.isHittable)
        start.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        let pause = app.buttons["toggle-timer-\(id)"]
        for _ in 0..<8 { if pause.isHittable && pause.frame.maxY < app.tabBars.firstMatch.frame.minY { break }; app.swipeUp() }
        XCTAssertTrue(pause.isHittable)
        pause.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        let advance = app.buttons["advance-\(id)"]
        for _ in 0..<8 { if advance.isHittable && advance.frame.maxY < app.tabBars.firstMatch.frame.minY { break }; app.swipeUp() }
        XCTAssertTrue(advance.isHittable)
        XCTAssertLessThan(advance.frame.maxY, app.tabBars.firstMatch.frame.minY)
        let paused = XCTAttachment(screenshot: app.screenshot())
        paused.name = "Four dishes - paused timer and visible action"
        paused.lifetime = .keepAlways
        add(paused)
        advance.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        XCTAssertTrue(app.buttons["结束计时并完成"].waitForExistence(timeout: 3))
        app.buttons["结束计时并完成"].tap()
        let previous = app.buttons["previous-\(id)"]
        for _ in 0..<8 { if previous.isHittable { break }; app.swipeUp() }
        XCTAssertTrue(previous.isHittable)
        previous.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        for _ in 0..<4 { app.swipeDown() }
        let wholeImage = XCTAttachment(screenshot: app.screenshot())
        wholeImage.name = "Four dishes - preparation image fully contained"
        wholeImage.lifetime = .keepAlways
        add(wholeImage)
    }

    func testVisibleRecipeAndButtonEdgesReceiveTheirOwnTaps() throws {
        let app = XCUIApplication()
        app.launch()
        app.tabBars.buttons["菜谱"].tap()
        let card = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH %@", "recipe-")).firstMatch
        XCTAssertTrue(card.waitForExistence(timeout: 10))
        let id = String(card.identifier.dropFirst("recipe-".count))
        // Tap an image corner, not the accessibility activation point.
        card.coordinate(withNormalizedOffset: CGVector(dx: 0.12, dy: 0.15)).tap()
        XCTAssertTrue(app.navigationBars["菜谱详情"].waitForExistence(timeout: 5))
        let addButton = app.buttons["加入这一餐"]
        if addButton.exists {
            addButton.coordinate(withNormalizedOffset: CGVector(dx: 0.08, dy: 0.5)).tap()
            XCTAssertTrue(app.buttons["已加入这一餐 · 移除"].waitForExistence(timeout: 3))
        }
        app.navigationBars.buttons.firstMatch.tap()
        app.tabBars.buttons["备菜"].tap()
        let ingredient = app.buttons["ingredient-\(id)-0"]
        for _ in 0..<8 { if ingredient.isHittable { break }; app.swipeUp() }
        XCTAssertTrue(ingredient.exists)
        let before = ingredient.value as? String
        ingredient.coordinate(withNormalizedOffset: CGVector(dx: 0.82, dy: 0.5)).tap()
        XCTAssertNotEqual(ingredient.value as? String, before)
        ingredient.coordinate(withNormalizedOffset: CGVector(dx: 0.12, dy: 0.5)).tap()
        XCTAssertEqual(ingredient.value as? String, before)
        app.tabBars.buttons["做饭"].tap()
        let timer = app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", "开始计时")).firstMatch
        let pause = app.buttons["暂停"].firstMatch
        let resume = app.buttons["继续"].firstMatch
        for _ in 0..<6 { if timer.isHittable || pause.isHittable || resume.isHittable { break }; app.swipeUp() }
        if timer.isHittable {
            timer.coordinate(withNormalizedOffset: CGVector(dx: 0.08, dy: 0.5)).tap()
        } else if resume.isHittable { resume.tap() }

        XCTAssertTrue(pause.waitForExistence(timeout: 3))
        pause.coordinate(withNormalizedOffset: CGVector(dx: 0.1, dy: 0.5)).tap()
        XCTAssertTrue(app.buttons["继续"].firstMatch.waitForExistence(timeout: 3))
        let advance = app.buttons["完成这步 →"].firstMatch
        for _ in 0..<8 { if advance.isHittable && advance.frame.maxY < app.tabBars.firstMatch.frame.minY { break }; app.swipeUp() }
        XCTAssertTrue(advance.isHittable)
        XCTAssertLessThan(advance.frame.maxY, app.tabBars.firstMatch.frame.minY)
        advance.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        XCTAssertTrue(app.buttons["结束计时并完成"].waitForExistence(timeout: 3))
        app.buttons["结束计时并完成"].tap()
        let previous = app.buttons["上一步"].firstMatch
        for _ in 0..<6 { if previous.isHittable { break }; app.swipeUp() }
        XCTAssertTrue(previous.isHittable)
        previous.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).tap()
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = "Ingredient edge tap verified"
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
