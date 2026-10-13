import SwiftUI

struct HomeView: View {
    @EnvironmentObject var store: KitchenStore
    @Binding var tab: KitchenTab
    @Binding var showImport: Bool
    @State private var reset = false
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("留一点时间给晚餐").font(.caption).foregroundStyle(KitchenStyle.muted)
                Text(store.selected.isEmpty ? "今晚想吃什么？" : "今晚，好好吃饭。").font(.system(size: 32, weight: .bold))
                if store.selected.isEmpty {
                    if store.recipes.isEmpty {
                        PrimaryButton(title: "粘贴链接，收藏第一道菜") { showImport = true }
                    } else {
                        EmptyMeal { tab = .library }
                        VStack(alignment: .leading, spacing: 8) {
                            Text("常做的菜").font(.title3.bold()).padding(.bottom, 4)
                            ForEach(Array(store.meal.frequentlyCooked(in: store.recipes).prefix(4))) { recipe in
                                HStack(spacing: 8) {
                                    NavigationLink { RecipeDetail(recipe: recipe) } label: {
                                        HStack(spacing: 10) {
                                            RecipePhoto(name: recipe.cover, height: 48).frame(width: 48)
                                                .clipShape(RoundedRectangle(cornerRadius: 10))
                                            VStack(alignment: .leading, spacing: 4) {
                                                Text(recipe.title).font(.system(size: 15, weight: .semibold))
                                                Text(recipe.duration).font(.caption).foregroundStyle(KitchenStyle.muted)
                                            }
                                            Spacer(minLength: 4)
                                            Text("已做 \(store.meal.cookingCount(recipe)) 次")
                                                .font(.caption).foregroundStyle(KitchenStyle.muted).fixedSize()
                                        }.contentShape(Rectangle())
                                    }.buttonStyle(.plain)
                                    Button { store.toggle(recipe) } label: {
                                        Image(systemName: "plus.circle.fill").font(.title2).frame(width: 44, height: 44).contentShape(Rectangle())
                                    }.accessibilityLabel("加入这一餐：\(recipe.title)")
                                }.padding(10).background(.white, in: RoundedRectangle(cornerRadius: 16))
                            }
                        }
                    }
                } else {
                    ZStack(alignment: .leading) {
                        RecipePhoto(name: store.selected.first?.cover, height: 180)
                        LinearGradient(colors: [.black.opacity(0.65), .clear], startPoint: .leading, endPoint: .trailing)
                        VStack(alignment: .leading, spacing: 12) {
                            Text("TONIGHT’S MENU").font(.caption2)
                            Text("\(store.selected.count) 道家常菜，\n一顿踏实的饭。").font(.title2.bold())
                        }.foregroundStyle(.white).padding(22)
                    }.frame(height: 180).clipShape(RoundedRectangle(cornerRadius: 22))
                    HStack {
                        Text("这一餐 · \(store.selected.count) 道菜").font(.title3.bold()); Spacer()
                        SecondaryButton(title: "编辑") { tab = .library }.font(.subheadline)
                    }
                    ForEach(store.selected) { recipe in
                        NavigationLink { RecipeDetail(recipe: recipe) } label: { RecipeRow(recipe: recipe) }.buttonStyle(.plain)
                    }
                    RecommendationView()
                    PrimaryButton(title: "开始备菜 →") { tab = .prep }
                    SecondaryButton(title: "开始新的一餐", expanded: true) { reset = true }.font(.caption)
                }
            }.padding(20).frame(maxWidth: 850)
        }.kitchenPage()
            .confirmationDialog("开始新的一餐？", isPresented: $reset, titleVisibility: .visible) {
                Button("清空本餐与计时，重新选菜", role: .destructive) { store.startNewMeal() }
            }
    }
}
struct LibraryView: View {
    @EnvironmentObject var store: KitchenStore
    @Binding var tab: KitchenTab
    @State private var query = ""
    @State private var filter = "全部"
    private var filtered: [Recipe] {
        store.recipes.filter { recipe in
            (query.isEmpty || recipe.title.localizedCaseInsensitiveContains(query) || recipe.ingredients.contains { $0.name.contains(query) }) &&
            (filter == "全部" || (filter == "本餐已选" ? store.meal.selected.contains(recipe.id) : (recipe.timing.map { ($0.prep + $0.cook).reduce(0) { $0 + $1.max } <= 30 } ?? false)))
        }
    }
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                Text("你的拿手菜，都在这里。").font(.system(size: 28, weight: .bold))
                Picker("菜谱分类", selection: $filter) {
                    ForEach(["全部", "30 分钟内", "本餐已选"], id: \.self) { Text($0) }
                }.pickerStyle(.segmented)
                if filtered.isEmpty { ContentUnavailableView.search(text: query) }
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 155, maximum: 260), spacing: 14)], spacing: 14) {
                    ForEach(filtered) { recipe in
                        VStack(alignment: .leading, spacing: 0) {
                            NavigationLink { RecipeDetail(recipe: recipe) } label: {
                                VStack(alignment: .leading, spacing: 9) {
                                    RecipePhoto(name: recipe.cover, height: 130)
                                    Text(recipe.title).font(.subheadline.bold()).padding(.horizontal, 12)
                                    Text(recipe.duration).font(.caption2).foregroundStyle(KitchenStyle.muted).padding(.horizontal, 12)
                                }.contentShape(Rectangle())
                            }.buttonStyle(.plain).accessibilityIdentifier("recipe-\(recipe.id)")
                            Button { store.toggle(recipe) } label: {
                                Label(store.meal.selected.contains(recipe.id) ? "已加入这一餐" : "加入这一餐", systemImage: store.meal.selected.contains(recipe.id) ? "checkmark.circle.fill" : "plus.circle")
                                    .font(.caption).frame(maxWidth: .infinity, minHeight: 44).contentShape(Rectangle())
                            }.accessibilityIdentifier("select-\(recipe.id)")
                        }.background(.white, in: RoundedRectangle(cornerRadius: 17)).clipShape(RoundedRectangle(cornerRadius: 17))
                    }
                }
            }.padding(20)
        }.searchable(text: $query, prompt: "搜索菜名或食材").kitchenPage()
            .safeAreaInset(edge: .bottom) {
                if !store.selected.isEmpty {
                    PrimaryButton(title: "已选 \(store.selected.count) 道菜 · 去备菜 →") { tab = .prep }.padding(16).background(KitchenStyle.background)
                }
            }
    }
}
