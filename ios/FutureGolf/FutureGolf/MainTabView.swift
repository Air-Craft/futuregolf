import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0
    
    var body: some View {
        TabView(selection: $selectedTab) {
            ContentView()
                .tabItem {
                    Label("Analyze", systemImage: "camera.viewfinder")
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
        .tint(.accentColor)
    }
}

#Preview {
    MainTabView()
}