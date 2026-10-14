import SwiftUI

struct CookView: View {
    @EnvironmentObject var store: KitchenStore
    @Environment(\.horizontalSizeClass) private var sizeClass
    @Binding var tab: KitchenTab
    @State private var focused: String?
    @State private var ingredients: Recipe?
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                if store.selected.isEmpty { EmptyMeal { tab = .library }.padding(20) }
                else {
                    Text("各有节奏，一起上桌。").font(.system(size: 28, weight: .bold)).padding(.horizontal, 20)
                    RecommendationView().padding(.horizontal, 20)
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(store.selected) { recipe in
                                Button { withAnimation { focused = recipe.id } } label: {
                                    VStack(spacing: 6) {
                                        Text(recipe.title).font(.caption.bold())
                                        Text(status(recipe)).font(.caption2)
                                    }.padding(12).frame(minHeight: 54).contentShape(Rectangle())
                                }.background(focused == recipe.id ? KitchenStyle.pale : .white, in: RoundedRectangle(cornerRadius: 12))
                                    .overlay(RoundedRectangle(cornerRadius: 12).stroke(focused == recipe.id ? KitchenStyle.muted : .clear).allowsHitTesting(false))
                            }
                        }.padding(.horizontal, 20)
                    }
                    if sizeClass == .regular {
                        ScrollViewReader { proxy in
                            ScrollView(.horizontal) {
                                HStack(alignment: .top, spacing: 16) {
                                    ForEach(store.selected) { recipe in
                                        CookingCard(recipe: recipe) { ingredients = recipe }.frame(width: 310).id(recipe.id)
                                    }
                                }.padding(.horizontal, 20)
                            }.onChange(of: focused) { _, id in if let id { withAnimation { proxy.scrollTo(id, anchor: .center) } } }
                        }
                    } else {
                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(alignment: .top, spacing: 12) {
                                ForEach(store.selected) { recipe in
                                    CookingCard(recipe: recipe) { ingredients = recipe }
                                        .containerRelativeFrame(.horizontal).id(recipe.id)
                                }
                            }.scrollTargetLayout()
                        }.contentMargins(.horizontal, 20, for: .scrollContent)
                            .scrollTargetBehavior(.viewAligned).scrollPosition(id: $focused)
                    }
                }
            }.padding(.top, 16).padding(.bottom, 32)
        }.kitchenPage()
            .onAppear { if focused == nil { focused = store.selected.first?.id } }
            .onChange(of: store.meal.selected) { _, ids in if focused == nil || !ids.contains(focused!) { focused = ids.first } }
            .sheet(item: $ingredients) { recipe in
                NavigationStack {
                    ScrollView { IngredientsView(recipe: recipe).padding(20) }.kitchenPage().navigationTitle(recipe.title)
                        .navigationBarTitleDisplayMode(.inline)
                        .toolbar { ToolbarItem(placement: .confirmationAction) { Button("完成") { ingredients = nil } } }
                }.presentationDetents([.medium, .large]).presentationDragIndicator(.visible)
            }
    }
    private func status(_ recipe: Recipe) -> String {
        let state = store.progress(recipe)
        if state.step >= recipe.steps.count { return "已完成" }
        if state.timer != nil { return "计时中" }
        return state.step < recipe.prep.count ? "备菜中" : "烹饪中"
    }
}
struct CookingCard: View {
    @EnvironmentObject var store: KitchenStore
    let recipe: Recipe
    var showIngredients: () -> Void
    @State private var confirmAdvance = false
    private var state: DishProgress { store.progress(recipe) }
    private var complete: Bool { state.step >= recipe.steps.count }
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            if let image = recipe.image(at: state.step) {
                RecipePhoto(name: image, height: 230)
            } else {
                Label("原素材未提供这一步的过程图", systemImage: "text.book.closed")
                    .font(.caption).foregroundStyle(KitchenStyle.muted).padding(18)
            }
            VStack(alignment: .leading, spacing: 16) {
                HStack {
                    Text(recipe.title).font(.headline); Spacer()
                    SecondaryButton(title: "用量", action: showIngredients).font(.caption)
                }
                if complete {
                    Image(systemName: "checkmark.circle.fill").font(.system(size: 42)).foregroundStyle(KitchenStyle.green)
                    Text("这道菜做好了").font(.title2.bold())
                    Text("趁热享用，也看看其他菜的进度。").font(.subheadline).foregroundStyle(KitchenStyle.muted)
                    SecondaryButton(title: "返回最后一步") { store.update(recipe) { $0.step = max(0, recipe.steps.count - 1) } }
                } else {
                    HStack {
                        Text(state.step < recipe.prep.count ? "备菜" : "烹饪"); Spacer()
                        Text("第 \(state.step + 1) / \(recipe.steps.count) 步")
                    }.font(.caption).foregroundStyle(KitchenStyle.muted)
                    ProgressView(value: Double(state.step), total: Double(max(1, recipe.steps.count)))
                    Text(recipe.steps[state.step]).font(.system(size: 19, weight: .medium)).lineSpacing(7).fixedSize(horizontal: false, vertical: true)
                    if let time = recipe.time(at: state.step) {
                        Label(time.label + (time.wait == true ? " · 可利用等待时间备其他菜" : ""), systemImage: "clock")
                            .font(.caption).foregroundStyle(KitchenStyle.muted)
                        if state.timer == nil {
                            Button { store.update(recipe) { $0.timer = CookingTimer(deadline: Date().addingTimeInterval(Double(max(1, time.min)) * 60)) } } label: {
                                Label("开始计时 \(max(1, time.min)) 分钟", systemImage: "timer").frame(maxWidth: .infinity, minHeight: 44).contentShape(Rectangle())
                            }.accessibilityIdentifier("start-timer-\(recipe.id)").font(.subheadline).background(KitchenStyle.pale, in: RoundedRectangle(cornerRadius: 12))
                        }
                    }
                    if let timer = state.timer {
                        TimelineView(.periodic(from: .now, by: 1)) { context in
                            VStack(alignment: .leading, spacing: 8) {
                                HStack {
                                    Text(clock(timer.remaining(at: context.date))).font(.system(size: 29, weight: .medium, design: .rounded)).monospacedDigit()
                                    Spacer()
                                    SecondaryButton(title: timer.deadline == nil ? "继续" : "暂停") {
                                        store.update(recipe) { $0.timer?.toggle(at: Date()) }
                                    }.accessibilityIdentifier("toggle-timer-\(recipe.id)").disabled(timer.remaining(at: context.date) <= 0)
                                }
                                if timer.remaining(at: context.date) <= 0 { Text("计时到了，请检查熟度").font(.caption.bold()) }
                                else if timer.deadline == nil { Text("计时已暂停").font(.caption) }
                            }.padding(13).background(KitchenStyle.pale, in: RoundedRectangle(cornerRadius: 13))
                        }
                    }
                    PrimaryButton(title: state.step == recipe.steps.count - 1 ? "做好了 ✓" : "完成这步 →") {
                        if state.timer != nil { confirmAdvance = true } else { store.advance(recipe) }
                    }.accessibilityIdentifier("advance-\(recipe.id)")
                    if state.step > 0 {
                        SecondaryButton(title: "上一步", expanded: true) { store.update(recipe) { $0.step -= 1; $0.timer = nil } }.accessibilityIdentifier("previous-\(recipe.id)").font(.caption).contentShape(Rectangle())
                    }
                }
            }.padding(18)
        }.fixedSize(horizontal: false, vertical: true).background(.white, in: RoundedRectangle(cornerRadius: 21)).clipShape(RoundedRectangle(cornerRadius: 21))
            .confirmationDialog("确认这一步已完成？", isPresented: $confirmAdvance, titleVisibility: .visible) {
                Button("结束计时并完成") { store.advance(recipe) }
            }
    }
    private func clock(_ remaining: TimeInterval) -> String {
        let value = Int(ceil(remaining))
        return String(format: "%02d:%02d", value / 60, value % 60)
    }
}
