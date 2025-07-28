import SwiftUI

struct AnalysisResultView: View {
    let result: AnalysisResult
    @State private var selectedPhaseIndex: Int = 0
    @State private var showContent = false
    @State private var showVideoPlayer = false
    
    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Header Section with Score
                LiquidGlassCard(
                    cornerRadius: 24,
                    glassIntensity: .medium,
                    depthLevel: .elevated,
                    content: {
                        VStack(spacing: 16) {
                            // Swing Score Visual
                            ZStack {
                                Circle()
                                    .stroke(Color.glassSecondaryText.opacity(0.2), lineWidth: 12)
                                    .frame(width: 120, height: 120)
                                
                                Circle()
                                    .trim(from: 0, to: CGFloat(calculateOverallScore()) / 100.0)
                                    .stroke(
                                        LinearGradient(
                                            gradient: Gradient(colors: [.fairwayGreen, .golfGreen]),
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        ),
                                        style: StrokeStyle(lineWidth: 12, lineCap: .round)
                                    )
                                    .frame(width: 120, height: 120)
                                    .rotationEffect(.degrees(-90))
                                
                                VStack(spacing: 4) {
                                    Text("\(calculateOverallScore())")
                                        .font(.system(size: 42, weight: .bold, design: .rounded))
                                        .foregroundColor(.glassText)
                                    Text("Overall Score")
                                        .font(.caption)
                                        .foregroundColor(.glassSecondaryText)
                                }
                            }
                            
                            Text("Golf Swing Analysis")
                                .font(.title2)
                                .fontWeight(.bold)
                                .foregroundColor(.glassText)
                        }
                        .padding(.vertical, 8)
                        .frame(maxWidth: .infinity)
                    }
                )
                .padding(.horizontal)
                .liquidGlassTransition(isVisible: showContent)
                
                // Video Player Button
                Button(action: {
                    showVideoPlayer = true
                    HapticManager.impact(.medium)
                }) {
                    HStack {
                        Image(systemName: "play.circle.fill")
                            .font(.title2)
                            .symbolRenderingMode(.hierarchical)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Watch Video with Coaching")
                                .font(.headline)
                            Text("Interactive coaching overlay")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        
                        Spacer()
                        
                        Image(systemName: "chevron.right")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
                .padding(.horizontal)
                
                // Key Metrics Grid
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                    SwingAnalysisGlassOverlay(
                        title: "Club Speed",
                        value: "\(result.swingSpeed) mph",
                        trend: determineSpeedTrend()
                    )
                    SwingAnalysisGlassOverlay(
                        title: "Tempo",
                        value: result.tempo,
                        trend: .neutral
                    )
                    SwingAnalysisGlassOverlay(
                        title: "Balance",
                        value: "\(result.balance)%",
                        trend: determineBalanceTrend()
                    )
                    SwingAnalysisGlassOverlay(
                        title: "Consistency",
                        value: "Good",
                        trend: .up
                    )
                }
                .padding(.horizontal)
                
                // Overall Analysis
                VStack(alignment: .leading, spacing: 12) {
                    Text("Overall Analysis")
                        .font(.headline)
                        .foregroundColor(.glassText)
                    
                    LiquidGlassCard(
                        cornerRadius: 16,
                        glassIntensity: .light,
                        content: {
                            Text(result.overallAnalysis)
                                .font(.body)
                                .foregroundColor(.glassText)
                                .padding()
                        }
                    )
                }
                .padding(.horizontal)
                
                // Key Points with Icons
                VStack(alignment: .leading, spacing: 12) {
                    Text("Key Points")
                        .font(.headline)
                        .foregroundColor(.glassText)
                    
                    VStack(spacing: 12) {
                        ForEach(Array(result.keyPoints.enumerated()), id: \.offset) { index, point in
                            HStack(alignment: .top, spacing: 12) {
                                ZStack {
                                    Circle()
                                        .fill(Color.fairwayGreen.opacity(0.2))
                                        .frame(width: 32, height: 32)
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundColor(.fairwayGreen)
                                        .font(.system(size: 18))
                                }
                                
                                Text(point)
                                    .font(.subheadline)
                                    .foregroundColor(.glassText)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            .padding()
                            .liquidGlassBackground(intensity: .ultraLight, cornerRadius: 12)
                            .animation(.liquidGlassSpring.delay(Double(index) * 0.1), value: showContent)
                        }
                    }
                }
                .padding(.horizontal)
                
                // Swing Phases with Interactive Selection
                VStack(alignment: .leading, spacing: 12) {
                    Text("Swing Phases")
                        .font(.headline)
                        .foregroundColor(.glassText)
                    
                    // Phase Selector
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(Array(result.swingPhases.enumerated()), id: \.offset) { index, phase in
                                Button(action: {
                                    withAnimation(.liquidGlassSpring) {
                                        selectedPhaseIndex = index
                                        LiquidGlassHaptics.selection()
                                    }
                                }) {
                                    Text(phase.name)
                                        .font(.subheadline)
                                        .fontWeight(selectedPhaseIndex == index ? .semibold : .regular)
                                        .foregroundColor(selectedPhaseIndex == index ? .white : .glassText)
                                        .padding(.horizontal, 16)
                                        .padding(.vertical, 8)
                                        .background {
                                            if selectedPhaseIndex == index {
                                                Capsule()
                                                    .fill(Color.golfGreen)
                                            } else {
                                                Capsule()
                                                    .fill(Material.ultraThin)
                                            }
                                        }
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding(.horizontal, 4)
                    }
                    .padding(.horizontal, -4)
                    
                    // Selected Phase Details
                    if result.swingPhases.indices.contains(selectedPhaseIndex) {
                        let phase = result.swingPhases[selectedPhaseIndex]
                        LiquidGlassCard(
                            content: {
                                VStack(alignment: .leading, spacing: 12) {
                                    HStack {
                                        VStack(alignment: .leading, spacing: 4) {
                                            Text(phase.name)
                                                .font(.headline)
                                                .foregroundColor(.glassText)
                                            Text("Timestamp: \(phase.timestamp, specifier: "%.1f")s")
                                                .font(.caption)
                                                .foregroundColor(.glassSecondaryText)
                                        }
                                        
                                        Spacer()
                                        
                                        // Phase Icon
                                        Image(systemName: phaseIcon(for: phase.name))
                                            .font(.title2)
                                            .foregroundColor(.fairwayGreen)
                                            .padding(12)
                                            .background(Circle().fill(Material.ultraThin))
                                    }
                                    
                                    Divider()
                                        .overlay(Color.glassSecondaryText.opacity(0.2))
                                    
                                    VStack(alignment: .leading, spacing: 12) {
                                        Text("Description")
                                            .font(.caption)
                                            .foregroundColor(.glassSecondaryText)
                                        Text(phase.description)
                                            .font(.subheadline)
                                            .foregroundColor(.glassText)
                                        
                                        Text("Feedback")
                                            .font(.caption)
                                            .foregroundColor(.glassSecondaryText)
                                            .padding(.top, 4)
                                        Text(phase.feedback)
                                            .font(.subheadline)
                                            .foregroundColor(.glassText)
                                    }
                                }
                                .padding()
                            },
                            cornerRadius: 16,
                            glassIntensity: .medium,
                            depthLevel: .raised
                        )
                        .id(selectedPhaseIndex) // Force re-render on selection change
                        .transition(.asymmetric(
                            insertion: .scale.combined(with: .opacity),
                            removal: .scale.combined(with: .opacity)
                        ))
                    }
                }
                .padding(.horizontal)
                
                // Coaching Feedback
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "person.fill.questionmark")
                            .font(.title3)
                            .foregroundColor(.fairwayGreen)
                        Text("Coaching Feedback")
                            .font(.headline)
                            .foregroundColor(.glassText)
                    }
                    
                    LiquidGlassCard(
                        content: {
                            VStack(alignment: .leading, spacing: 12) {
                                Text(result.coachingScript)
                                    .font(.body)
                                    .foregroundColor(.glassText)
                                
                                // Action Button
                                Button(action: {
                                    LiquidGlassHaptics.impact(.medium)
                                    // Handle coaching session booking
                                }) {
                                    HStack {
                                        Image(systemName: "calendar.badge.plus")
                                        Text("Schedule Coaching Session")
                                            .fontWeight(.medium)
                                    }
                                    .foregroundColor(.white)
                                    .frame(maxWidth: .infinity)
                                }
                                .buttonStyle(LiquidGlassButtonStyle(isProminent: true))
                            }
                            .padding()
                        },
                        cornerRadius: 16,
                        glassIntensity: .light,
                        depthLevel: .raised
                    )
                }
                .padding(.horizontal)
                .padding(.bottom, 32)
            }
        }
        .background(Color.glassBackground.ignoresSafeArea())
        .navigationBarTitleDisplayMode(.inline)
        .liquidGlassNavigationBar()
        .onAppear {
            withAnimation(.liquidGlassSpring.delay(0.2)) {
                showContent = true
            }
        }
        .sheet(isPresented: $showVideoPlayer) {
            NavigationStack {
                // For demo purposes, using a bundled video
                // In production, this would use the actual analyzed video URL
                if let videoURL = Bundle.main.url(forResource: "golf1", withExtension: "mp4") {
                    VideoPlayerWithCoaching(
                        analysisResult: result,
                        videoURL: videoURL
                    )
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar {
                        ToolbarItem(placement: .navigationBarLeading) {
                            Button("Done") {
                                showVideoPlayer = false
                            }
                        }
                    }
                } else {
                    // Fallback for demo - use the file from app directory
                    let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
                    let videoPath = documentsPath.appendingPathComponent("golf1.mp4")
                    VideoPlayerWithCoaching(
                        analysisResult: result,
                        videoURL: videoPath
                    )
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar {
                        ToolbarItem(placement: .navigationBarLeading) {
                            Button("Done") {
                                showVideoPlayer = false
                            }
                        }
                    }
                }
            }
        }
    }
    
    private func phaseIcon(for phaseName: String) -> String {
        switch phaseName.lowercased() {
        case let name where name.contains("setup"): return "figure.stand"
        case let name where name.contains("backswing"): return "arrow.turn.up.left"
        case let name where name.contains("downswing"): return "arrow.turn.down.right"
        case let name where name.contains("impact"): return "bolt.fill"
        case let name where name.contains("follow"): return "arrow.up.right"
        default: return "figure.golf"
        }
    }
    
    private func calculateOverallScore() -> Int {
        // Calculate overall score based on metrics
        let speedScore = min(100, result.swingSpeed * 100 / 120) // Normalize to 120mph max
        let balanceScore = result.balance
        let tempoScore = result.tempo == "3:1" ? 100 : 85 // Ideal tempo is 3:1
        
        return (speedScore + balanceScore + tempoScore) / 3
    }
    
    private func determineSpeedTrend() -> SwingAnalysisGlassOverlay.Trend {
        if result.swingSpeed >= 95 {
            return .up
        } else if result.swingSpeed >= 85 {
            return .neutral
        } else {
            return .down
        }
    }
    
    private func determineBalanceTrend() -> SwingAnalysisGlassOverlay.Trend {
        if result.balance >= 90 {
            return .up
        } else if result.balance >= 80 {
            return .neutral
        } else {
            return .down
        }
    }
}

#Preview {
    NavigationStack {
        AnalysisResultView(result: AnalysisResult(
            id: "123",
            status: "completed",
            swingPhases: [
                SwingPhase(
                    name: "Setup",
                    timestamp: 0.0,
                    description: "Initial stance and club positioning",
                    feedback: "Good posture with proper spine angle"
                ),
                SwingPhase(
                    name: "Backswing",
                    timestamp: 1.2,
                    description: "Club movement to the top of the swing",
                    feedback: "Excellent shoulder rotation and club position at the top"
                ),
                SwingPhase(
                    name: "Downswing",
                    timestamp: 2.5,
                    description: "Transition and acceleration through impact",
                    feedback: "Great hip rotation, could improve lag slightly"
                ),
                SwingPhase(
                    name: "Follow Through",
                    timestamp: 3.8,
                    description: "Post-impact club path and finish position",
                    feedback: "Complete your rotation for better balance"
                )
            ],
            keyPoints: ["Great tempo", "Good balance throughout swing", "Excellent shoulder rotation", "Strong impact position"],
            overallAnalysis: "Your golf swing shows excellent fundamentals with room for minor improvements in the downswing transition and follow-through completion.",
            coachingScript: "Let's work on your follow-through to maximize distance and improve your lag in the downswing for more power.",
            swingSpeed: 92,
            tempo: "3:1",
            balance: 88
        ))
    }
}
