import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "house.fill")
                }
                .tag(0)
            
            PreviousAnalysesView()
                .tabItem {
                    Label("Previous", systemImage: "clock.arrow.circlepath")
                }
                .tag(1)
            
            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
                .tag(2)
            
            SupportView()
                .tabItem {
                    Label("Support", systemImage: "questionmark.circle")
                }
                .tag(3)
            
            AboutView()
                .tabItem {
                    Label("About", systemImage: "info.circle")
                }
                .tag(4)
        }
        .tint(.fairwayGreen)
        .onAppear {
            // Configure tab bar appearance with Liquid Glass style
            let appearance = UITabBarAppearance()
            appearance.configureWithDefaultBackground()
            
            // iOS 26 enhanced blur effect
            if #available(iOS 26.0, *) {
                appearance.backgroundEffect = UIBlurEffect(style: .systemChromeMaterial)
            } else {
                appearance.backgroundEffect = UIBlurEffect(style: .systemThinMaterial)
            }
            
            appearance.backgroundColor = UIColor.systemBackground.withAlphaComponent(0.3)
            
            UITabBar.appearance().standardAppearance = appearance
            UITabBar.appearance().scrollEdgeAppearance = appearance
        }
    }
}

#Preview {
    MainTabView()
}