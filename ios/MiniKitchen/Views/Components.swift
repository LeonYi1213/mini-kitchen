import SwiftUI
import UIKit

enum KitchenStyle {
    static let background = Color(red: 245/255, green: 245/255, blue: 242/255)
    static let ink = Color(red: 34/255, green: 56/255, blue: 44/255)
    static let green = Color(red: 40/255, green: 83/255, blue: 62/255)
    static let muted = Color(red: 114/255, green: 131/255, blue: 105/255)
    static let pale = Color(red: 234/255, green: 240/255, blue: 229/255)
}
struct PrimaryButton: View {
    let title: String
    var action: () -> Void
    var body: some View {
        Button(action: action) {
            Text(title).font(.system(size: 16, weight: .semibold)).frame(maxWidth: .infinity).padding(.vertical, 16)
                .foregroundStyle(.white).background(KitchenStyle.green, in: RoundedRectangle(cornerRadius: 14))
                .contentShape(RoundedRectangle(cornerRadius: 14))
        }.buttonStyle(.plain)
    }
}
// Keep the visible label, padding, and interactive rectangle in the same layout.
struct SecondaryButton: View {
    let title: String
    var expanded = false
    var action: () -> Void
    var body: some View {
        Button(action: action) {
            Text(title).frame(maxWidth: expanded ? .infinity : nil, minHeight: 44)
                .padding(.horizontal, 8).contentShape(Rectangle())
        }.buttonStyle(.plain)
    }
}
struct RecipePhoto: View {
    let name: String?
    var height: CGFloat = 160
    @State private var importedImage: UIImage?
    var body: some View {
        GeometryReader { proxy in
            Group {
                if let name, let url = Bundle.main.url(forResource: name, withExtension: nil), let image = UIImage(contentsOfFile: url.path) {
                    Image(uiImage: image).resizable().scaledToFill()
                } else if let importedImage {
                    Image(uiImage: importedImage).resizable().scaledToFill()
                } else if let name, let url = URL(string: name), url.scheme == "https" {
                    AsyncImage(url: url) { image in image.resizable().scaledToFill() } placeholder: { placeholder }
                } else { placeholder }
            }.frame(width: proxy.size.width, height: height).clipped()
        }.frame(height: height).clipped().contentShape(Rectangle()).allowsHitTesting(false).accessibilityHidden(true)
            .task(id: name) {
                importedImage = nil
                guard let name, RecipeAssets.localURL(name) != nil else { return }
                if let data = try? await ImportService().imageData(name), !Task.isCancelled {
                    importedImage = UIImage(data: data)
                }
            }
    }
    private var placeholder: some View {
        Rectangle().fill(KitchenStyle.pale).overlay { Image(systemName: "fork.knife").font(.largeTitle).foregroundStyle(KitchenStyle.muted) }
    }
}
struct RecipeRow: View {
    let recipe: Recipe
    var body: some View {
        HStack(spacing: 13) {
            RecipePhoto(name: recipe.cover, height: 58).frame(width: 58).clipShape(RoundedRectangle(cornerRadius: 12))
            VStack(alignment: .leading, spacing: 6) {
                Text(recipe.title).font(.system(size: 15, weight: .semibold))
                Text(recipe.duration).font(.caption).foregroundStyle(KitchenStyle.muted)
            }
            Spacer()
        }.padding(14).background(.white, in: RoundedRectangle(cornerRadius: 18)).contentShape(Rectangle())
    }
}
struct EmptyMeal: View {
    var action: () -> Void
    var body: some View {
        VStack(spacing: 20) {
            ZStack {
                Circle().fill(KitchenStyle.pale).frame(width: 130, height: 130)
                Circle().stroke(KitchenStyle.muted.opacity(0.3), lineWidth: 2).frame(width: 89, height: 89)
                Image(systemName: "fork.knife").font(.system(size: 32, weight: .light)).foregroundStyle(KitchenStyle.green)
            }.padding(.top, 24)
            Text("今晚想吃什么？").font(.title2.bold())
            Text("选几道菜，一起备、一起做").font(.subheadline).foregroundStyle(KitchenStyle.muted)
            PrimaryButton(title: "从菜谱库选菜", action: action)
        }.padding(24).background(.white, in: RoundedRectangle(cornerRadius: 24))
    }
}
struct RecommendationView: View {
    @EnvironmentObject var store: KitchenStore
    var body: some View {
        if store.selected.count > 1 {
            TimelineView(.periodic(from: .now, by: 1)) { context in
                if let recipe = store.meal.recommendation(in: store.selected, now: context.date) {
                    let state = store.progress(recipe)
                    VStack(alignment: .leading, spacing: 6) {
                        Label("建议先做", systemImage: "sparkles").font(.caption)
                        Text(recipe.title).font(.subheadline.bold())
                        if let timer = state.timer, timer.deadline != nil, timer.remaining(at: context.date) == 0 {
                            Text("计时到了，先检查火候与熟度。")
                        } else if state.timer != nil {
                            Text("正在等待中，留意火候与计时。")
                        } else { Text(recipe.steps[state.step]).lineLimit(3) }
                    }.font(.caption).foregroundStyle(Color(red: 0.53, green: 0.38, blue: 0.24))
                        .frame(maxWidth: .infinity, alignment: .leading).padding(15)
                        .background(Color(red: 0.95, green: 0.92, blue: 0.86), in: RoundedRectangle(cornerRadius: 16))
                }
            }
        }
    }
}
struct IngredientsView: View {
    let recipe: Recipe
    var body: some View {
        VStack(spacing: 0) {
            ForEach(Array(recipe.ingredients.enumerated()), id: \.offset) { _, ingredient in
                HStack { Text(ingredient.name); Spacer(); Text(ingredient.quantity).foregroundStyle(KitchenStyle.muted) }
                    .font(.subheadline).padding(.vertical, 13)
                Divider().overlay(KitchenStyle.background)
            }
        }.padding(.horizontal, 16).background(.white, in: RoundedRectangle(cornerRadius: 18))
    }
}
extension View {
    func kitchenPage() -> some View {
        self.frame(maxWidth: .infinity, maxHeight: .infinity).background(KitchenStyle.background).foregroundStyle(KitchenStyle.ink)
    }
}
