import SwiftUI

struct SupportView: View {
    var body: some View {
        NavigationStack {
            List {
                Section("Get Help") {
                    Link(destination: URL(string: "mailto:support@futuregolf.com")!) {
                        HStack {
                            Image(systemName: "envelope")
                                .foregroundColor(.blue)
                            Text("Email Support")
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                    }
                    
                    Link(destination: URL(string: "https://futuregolf.com/faq")!) {
                        HStack {
                            Image(systemName: "questionmark.circle")
                                .foregroundColor(.blue)
                            Text("FAQ")
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                                .foregroundColor(.secondary)
                                .font(.caption)
                        }
                    }
                }
                
                Section("Resources") {
                    HStack {
                        Image(systemName: "book")
                            .foregroundColor(.green)
                        Text("User Guide")
                    }
                    
                    HStack {
                        Image(systemName: "video.circle")
                            .foregroundColor(.purple)
                        Text("Video Tutorials")
                    }
                }
                
                Section("Feedback") {
                    Button(action: {
                        // TODO: Implement feedback form
                    }) {
                        HStack {
                            Image(systemName: "exclamationmark.bubble")
                                .foregroundColor(.orange)
                            Text("Report an Issue")
                        }
                    }
                    
                    Button(action: {
                        // TODO: Implement feature request
                    }) {
                        HStack {
                            Image(systemName: "lightbulb")
                                .foregroundColor(.yellow)
                            Text("Request a Feature")
                        }
                    }
                }
            }
            .navigationTitle("Support")
        }
    }
}

#Preview {
    SupportView()
}