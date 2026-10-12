import SwiftUI

struct PrepView: View {
    @EnvironmentObject var store: KitchenStore
    @Binding var tab: KitchenTab
    @State private var filter: String?
    private var dishes: [Recipe] { store.selected.filter { filter == nil || $0.id == filter } }
    private var total: Int { store.selected.reduce(0) { $0 + $1.ingredients.count } }
    private var checked: Int { store.selected.reduce(0) { $0 + store.progress($1).checked.count } }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                if store.selected.isEmpty { EmptyMeal { tab = .library } }
                else {
                    Text("一次备齐，做饭不慌。").font(.system(size: 28, weight: .bold))
                    HStack { Text("备菜清单"); Spacer(); Text("\(checked) / \(total)") }.font(.caption).foregroundStyle(KitchenStyle.muted)
                    ProgressView(value: Double(checked), total: Double(max(total, 1)))
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            chip("全部", id: nil)
                            ForEach(store.selected) { recipe in chip(recipe.title, id: recipe.id) }
                        }
                    }
                    RecommendationView()
                    ForEach(dishes) { recipe in
                        Text(recipe.title).font(.headline)
                        VStack(spacing: 0) {
                            ForEach(Array(recipe.ingredients.enumerated()), id: \.offset) { index, ingredient in
                                let isChecked = store.progress(recipe).checked.contains(index)
                                Button {
                                    store.update(recipe) { state in
                                        if state.checked.contains(index) { state.checked.remove(index) } else { state.checked.insert(index) }
                                    }
                                } label: {
                                    HStack(spacing: 12) {
                                        Image(systemName: isChecked ? "checkmark.circle.fill" : "circle").font(.title3)
                                        Text(ingredient.name).strikethrough(isChecked); Spacer()
                                        Text(ingredient.quantity).font(.subheadline)
                                    }.foregroundStyle(isChecked ? KitchenStyle.muted : KitchenStyle.ink).padding(15)
                                }.buttonStyle(.plain).accessibilityValue(isChecked ? "已备好" : "未备好")
                                if index < recipe.ingredients.count - 1 { Divider().padding(.leading, 48) }
                            }
                        }.background(.white, in: RoundedRectangle(cornerRadius: 18))
                    }
                    PrimaryButton(title: "进入多菜同做 →") { tab = .cook }
                }
            }.padding(20).frame(maxWidth: 850)
        }.kitchenPage().onChange(of: store.meal.selected) { _, ids in if let filter, !ids.contains(filter) { self.filter = nil } }
    }
    private func chip(_ title: String, id: String?) -> some View {
        Button { filter = id } label: { Text(title).font(.caption).padding(.horizontal, 14).frame(minHeight: 44) }
            .foregroundStyle(filter == id ? .white : KitchenStyle.ink)
            .background(filter == id ? KitchenStyle.green : .white, in: Capsule())
    }
}
struct RecipeDetail: View {
    @EnvironmentObject var store: KitchenStore
    let recipe: Recipe
    @State private var section = "食材"
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                RecipePhoto(name: recipe.cover, height: 245).clipShape(RoundedRectangle(cornerRadius: 20))
                Text(recipe.title).font(.largeTitle.bold())
                Label(recipe.duration, systemImage: "clock").font(.subheadline).foregroundStyle(KitchenStyle.muted)
                Picker("菜谱内容", selection: $section) {
                    ForEach(["食材", "备菜", "做法"], id: \.self) { Text($0) }
                }.pickerStyle(.segmented)
                if section == "食材" { IngredientsView(recipe: recipe) }
                else {
                    RecipeSteps(recipe: recipe, preparation: section == "备菜", showHeading: false)
                }
                RecipeNotes(recipe: recipe)
                if let source = URL(string: recipe.source), source.scheme == "https" { Link("查看原笔记 ↗", destination: source).font(.caption) }
            }.padding(20).frame(maxWidth: 850)
        }.kitchenPage().navigationTitle("菜谱详情").navigationBarTitleDisplayMode(.inline)
            .safeAreaInset(edge: .bottom) {
                PrimaryButton(title: store.meal.selected.contains(recipe.id) ? "已加入这一餐 · 移除" : "加入这一餐") { store.toggle(recipe) }
                    .padding(16).background(KitchenStyle.background)
            }
    }
}

struct RecipeSteps: View {
    let recipe: Recipe
    let preparation: Bool
    var showHeading = true
    var body: some View {
        if showHeading { Text(preparation ? "备菜" : "做法").font(.headline) }
        let steps = preparation ? recipe.prep : recipe.cook
        ForEach(Array(steps.enumerated()), id: \.offset) { index, text in
            let absolute = preparation ? index : recipe.prep.count + index
            let illustration = recipe.illustrated_steps?.first { $0.text == text }
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Text("\(index + 1)").font(.title2.bold())
                    if let illustration { Text(illustration.title).font(.headline) }
                    Spacer()
                    if let time = recipe.time(at: absolute) { Text(time.label).font(.caption).foregroundStyle(KitchenStyle.muted) }
                }
                if let image = illustration?.image {
                    RecipePhoto(name: image, height: 190).clipShape(RoundedRectangle(cornerRadius: 12))
                }
                Text(text).font(.body).lineSpacing(6)
                if let time = illustration?.source_time {
                    Text("视频 \(time)").font(.caption).foregroundStyle(KitchenStyle.muted)
                }
            }.padding(18).frame(maxWidth: .infinity, alignment: .leading).background(.white, in: RoundedRectangle(cornerRadius: 18))
        }
    }
}
struct RecipeNotes: View {
    let recipe: Recipe
    var body: some View {
        if let notes = recipe.notes, !notes.isEmpty {
            VStack(alignment: .leading, spacing: 8) {
                Text("用量与时间说明").font(.headline)
                ForEach(Array(notes.enumerated()), id: \.offset) { _, note in
                    Text(note).font(.caption).foregroundStyle(KitchenStyle.muted)
                }
            }
        }
    }
}
