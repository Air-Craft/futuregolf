//
//  LiquidGlassDesignSystem.swift
//  FutureGolf
//
//  Comprehensive Liquid Glass Design System for iOS 17 and later
//  Following Apple's WWDC 2025 Liquid Glass guidelines
//

import SwiftUI
import UIKit

// MARK: - Color Palette
extension Color {
    // Primary Glass Colors with optimal translucency
    static let glassBackground = Color(white: 0.95, opacity: 0.7)
    static let glassDarkBackground = Color(white: 0.1, opacity: 0.75)
    static let glassSecondary = Color(white: 0.85, opacity: 0.6)
    static let glassTertiary = Color(white: 0.75, opacity: 0.5)
    
    // Accent Colors for Golf Theme
    static let golfGreen = Color(red: 0.133, green: 0.545, blue: 0.133)
    static let fairwayGreen = Color(red: 0.196, green: 0.804, blue: 0.196).opacity(0.9)
    static let teeBoxBrown = Color(red: 0.545, green: 0.271, blue: 0.075).opacity(0.8)
    
    // Specular Highlight Colors
    static let specularHighlight = Color.white.opacity(0.8)
    static let specularSubtle = Color.white.opacity(0.3)
    
    // Text Colors with proper contrast
    static let glassText = Color.primary.opacity(0.95)
    static let glassSecondaryText = Color.secondary.opacity(0.85)
    
    // Dynamic Colors for different lighting conditions
    static let dynamicGlass = Color(UIColor { traitCollection in
        switch traitCollection.userInterfaceStyle {
        case .dark:
            return UIColor(white: 0.15, alpha: 0.75)
        default:
            return UIColor(white: 0.95, alpha: 0.7)
        }
    })
}

// MARK: - Glass Materials
@available(iOS 16.0, *)
struct LiquidGlassMaterial {
    static let ultraThin = Material.ultraThinMaterial
    static let thin = Material.thinMaterial
    static let regular = Material.regularMaterial
    static let thick = Material.thickMaterial
    static let ultraThick = Material.ultraThickMaterial
    
    // iOS 17 specific materials with enhanced blur
    @available(iOS 17.0, *)
    static var adaptiveGlass: some ShapeStyle {
        return Material.thinMaterial  // Using available material
    }
}

// MARK: - Glass View Modifiers
struct LiquidGlassBackgroundModifier: ViewModifier {
    let intensity: GlassIntensity
    let cornerRadius: CGFloat
    let specularHighlight: Bool
    
    enum GlassIntensity {
        case ultraLight
        case light
        case medium
        case heavy
        case ultraHeavy
        
        var material: Material {
            switch self {
            case .ultraLight: return .ultraThinMaterial
            case .light: return .thinMaterial
            case .medium: return .regularMaterial
            case .heavy: return .thickMaterial
            case .ultraHeavy: return .ultraThickMaterial
            }
        }
    }
    
    func body(content: Content) -> some View {
        content
            .background {
                RoundedRectangle(cornerRadius: cornerRadius)
                    .fill(intensity.material)
                    .overlay {
                        if specularHighlight {
                            SpecularHighlightOverlay(cornerRadius: cornerRadius)
                        }
                    }
            }
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius))
    }
}

// MARK: - Specular Highlight Component
struct SpecularHighlightOverlay: View {
    let cornerRadius: CGFloat
    @State private var phase: CGFloat = 0
    
    var body: some View {
        GeometryReader { geometry in
            LinearGradient(
                gradient: Gradient(stops: [
                    .init(color: .clear, location: 0),
                    .init(color: .specularHighlight, location: 0.3),
                    .init(color: .specularSubtle, location: 0.5),
                    .init(color: .clear, location: 0.7),
                    .init(color: .clear, location: 1)
                ]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .mask(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(lineWidth: 2)
            )
            .offset(x: phase * geometry.size.width * 0.5)
            .opacity(0.6)
            .animation(
                Animation.easeInOut(duration: 3)
                    .repeatForever(autoreverses: true),
                value: phase
            )
            .onAppear {
                phase = 1
            }
        }
    }
}

// MARK: - Depth Layer System
struct DepthLayerModifier: ViewModifier {
    let level: DepthLevel
    
    enum DepthLevel: Int {
        case base = 0
        case raised = 1
        case elevated = 2
        case floating = 3
        
        var shadowRadius: CGFloat {
            switch self {
            case .base: return 0
            case .raised: return 4
            case .elevated: return 8
            case .floating: return 16
            }
        }
        
        var shadowOpacity: Double {
            switch self {
            case .base: return 0
            case .raised: return 0.1
            case .elevated: return 0.15
            case .floating: return 0.2
            }
        }
        
        var yOffset: CGFloat {
            CGFloat(rawValue) * 2
        }
    }
    
    func body(content: Content) -> some View {
        content
            .shadow(
                color: Color.black.opacity(level.shadowOpacity),
                radius: level.shadowRadius,
                y: level.yOffset
            )
    }
}

// MARK: - Glass Button Styles
struct LiquidGlassButtonStyle: ButtonStyle {
    let isProminent: Bool
    
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
            .background {
                if isProminent {
                    Capsule()
                        .fill(Color.fairwayGreen)
                        .overlay {
                            Capsule()
                                .fill(Material.thin)
                                .opacity(configuration.isPressed ? 0.3 : 0.5)
                        }
                } else {
                    Capsule()
                        .fill(Material.regularMaterial)
                }
            }
            .overlay {
                if !configuration.isPressed {
                    Capsule()
                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                }
            }
            .scaleEffect(configuration.isPressed ? 0.95 : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.6), value: configuration.isPressed)
    }
}

// MARK: - Navigation Bar Style
struct LiquidGlassNavigationBarModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbarBackground(Material.thin, for: .navigationBar)
            .toolbarColorScheme(.dark, for: .navigationBar)
    }
}

// MARK: - Card Component
struct LiquidGlassCard<Content: View>: View {
    let content: () -> Content
    var cornerRadius: CGFloat = 16
    var glassIntensity: LiquidGlassBackgroundModifier.GlassIntensity = .medium
    var depthLevel: DepthLayerModifier.DepthLevel = .raised
    
    var body: some View {
        content()
            .liquidGlassBackground(intensity: glassIntensity, cornerRadius: cornerRadius)
            .depthLayer(level: depthLevel)
    }
}

// MARK: - Animated Glass Transition
struct LiquidGlassTransition: ViewModifier {
    let isVisible: Bool
    
    func body(content: Content) -> some View {
        content
            .opacity(isVisible ? 1 : 0)
            .blur(radius: isVisible ? 0 : 10)
            .scaleEffect(isVisible ? 1 : 0.8)
            .animation(.spring(response: 0.5, dampingFraction: 0.8), value: isVisible)
    }
}

// MARK: - View Extensions
extension View {
    func liquidGlassBackground(
        intensity: LiquidGlassBackgroundModifier.GlassIntensity = .medium,
        cornerRadius: CGFloat = 12,
        specularHighlight: Bool = true
    ) -> some View {
        modifier(LiquidGlassBackgroundModifier(
            intensity: intensity,
            cornerRadius: cornerRadius,
            specularHighlight: specularHighlight
        ))
    }
    
    func depthLayer(level: DepthLayerModifier.DepthLevel) -> some View {
        modifier(DepthLayerModifier(level: level))
    }
    
    func liquidGlassNavigationBar() -> some View {
        modifier(LiquidGlassNavigationBarModifier())
    }
    
    func liquidGlassTransition(isVisible: Bool) -> some View {
        modifier(LiquidGlassTransition(isVisible: isVisible))
    }
}

// MARK: - Compatibility Helpers
struct LiquidGlassCompatibility {
    static var isIOS26Available: Bool {
        if #available(iOS 17, *) {
            return true
        }
        return false
    }
    
    static func adaptiveMaterial() -> any ShapeStyle {
        return Material.thinMaterial
    }
}

// MARK: - Animation Presets
extension Animation {
    static let liquidGlassSpring = Animation.spring(response: 0.5, dampingFraction: 0.8)
    static let liquidGlassBounce = Animation.spring(response: 0.6, dampingFraction: 0.6)
    static let liquidGlassSmooth = Animation.easeInOut(duration: 0.3)
}

// MARK: - Haptic Feedback Helper
struct LiquidGlassHaptics {
    static func impact(_ style: UIImpactFeedbackGenerator.FeedbackStyle = .light) {
        let generator = UIImpactFeedbackGenerator(style: style)
        generator.prepare()
        generator.impactOccurred()
    }
    
    static func selection() {
        let generator = UISelectionFeedbackGenerator()
        generator.prepare()
        generator.selectionChanged()
    }
}

// MARK: - Golf-Specific Components
struct SwingAnalysisGlassOverlay: View {
    let title: String
    let value: String
    let trend: Trend?
    
    enum Trend {
        case up, down, neutral
        
        var icon: String {
            switch self {
            case .up: return "arrow.up.circle.fill"
            case .down: return "arrow.down.circle.fill"
            case .neutral: return "minus.circle.fill"
            }
        }
        
        var color: Color {
            switch self {
            case .up: return .fairwayGreen
            case .down: return .red.opacity(0.8)
            case .neutral: return .secondary
            }
        }
    }
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.caption)
                    .foregroundColor(.glassSecondaryText)
                Text(value)
                    .font(.title2)
                    .fontWeight(.semibold)
                    .foregroundColor(.glassText)
            }
            
            Spacer()
            
            if let trend = trend {
                Image(systemName: trend.icon)
                    .font(.title2)
                    .foregroundColor(trend.color)
            }
        }
        .padding()
        .liquidGlassBackground(intensity: .light, cornerRadius: 12)
    }
}