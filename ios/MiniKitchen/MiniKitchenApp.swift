import SwiftUI

@main struct MiniKitchenApp: App {
    @StateObject private var store = KitchenStore()
    var body: some Scene {
        WindowGroup {
            KitchenRoot().environmentObject(store).tint(KitchenStyle.green).preferredColorScheme(.light)
        }
    }
}
enum KitchenTab: String, CaseIterable, Identifiable {
    case home = "这一餐", library = "菜谱", prep = "备菜", cook = "做饭"
    var id: String { rawValue }
    var icon: String {
        switch self {
        case .home: "house"
        case .library: "book.closed"
        case .prep: "checklist"
        case .cook: "frying.pan"
        }
    }
}
struct KitchenRoot: View {
    @EnvironmentObject var store: KitchenStore
    @Environment(\.horizontalSizeClass) private var sizeClass
    @State private var tab: KitchenTab = .home
    @State private var showImport = false
    @State private var incomingShare = ""
    var body: some View {
        Group {
            if sizeClass == .regular {
                NavigationSplitView {
                    List {
                        Section {
                            ForEach(KitchenTab.allCases) { item in
                                Button { tab = item } label: {
                                    Label(item.rawValue, systemImage: item.icon).padding(.vertical, 8)
                                        .foregroundStyle(tab == item ? KitchenStyle.green : KitchenStyle.muted)
                                }.listRowBackground(tab == item ? KitchenStyle.pale : Color.clear)
                            }
                        }
                        if !store.selected.isEmpty {
                            Section("这一餐 · \(store.selected.count) 道菜") {
                                ForEach(store.selected) { recipe in Text(recipe.title).font(.subheadline) }
                            }
                        }
                    }.navigationTitle("小厨房").scrollContentBackground(.hidden).background(KitchenStyle.pale.opacity(0.5))
                } detail: { NavigationStack { page(tab) } }
            } else {
                TabView(selection: $tab) {
                    ForEach(KitchenTab.allCases) { item in
                        NavigationStack { page(item) }.tabItem { Label(item.rawValue, systemImage: item.icon) }.tag(item)
                    }
                }
            }
        }
        .sheet(isPresented: $showImport) { ImportView(initialText: incomingShare) }
        .onOpenURL { url in
            guard url.scheme == "minikitchen", url.host == "import" else { return }
            incomingShare = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems?.first(where: { $0.name == "text" })?.value ?? ""
            showImport = true
        }
        .alert("暂时无法完成", isPresented: Binding(get: { store.error != nil }, set: { if !$0 { store.error = nil } })) {
            Button("知道了") { store.error = nil }
        } message: { Text(store.error ?? "") }
    }
    @ViewBuilder private func page(_ item: KitchenTab) -> some View {
        Group {
            switch item {
            case .home: HomeView(tab: $tab, showImport: $showImport)
            case .library: LibraryView(tab: $tab)
            case .prep: PrepView(tab: $tab)
            case .cook: CookView(tab: $tab)
            }
        }.navigationTitle(item == .home ? "小厨房" : item.rawValue).navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button { incomingShare = ""; showImport = true } label: {
                        Image(systemName: "plus").frame(width: 34, height: 34).background(KitchenStyle.pale, in: Circle()).frame(width: 44, height: 44).contentShape(Rectangle())
                    }.accessibilityLabel("收藏新菜")
                }
            }
    }
}
