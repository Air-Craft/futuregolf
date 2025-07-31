import SwiftUI
import Combine

// MARK: - Toast Model

struct Toast: Identifiable {
    let id = UUID()
    var message: String
    var type: ToastType
    var duration: TimeInterval
    var showProgress: Bool
    var progress: Double?
    var progressLabel: String?
    
    enum ToastType {
        case info
        case success
        case warning
        case error
        
        var backgroundColor: Color {
            switch self {
            case .info: return Color(red: 0.6, green: 0.8, blue: 0.4).opacity(0.85)  // Green-yellow translucent
            case .success: return Color(red: 0.5, green: 0.8, blue: 0.3).opacity(0.85)
            case .warning: return Color(red: 0.8, green: 0.7, blue: 0.3).opacity(0.85)
            case .error: return Color(red: 0.8, green: 0.3, blue: 0.3).opacity(0.85)
            }
        }
        
        var iconName: String {
            switch self {
            case .info: return "info.circle.fill"
            case .success: return "checkmark.circle.fill"
            case .warning: return "exclamationmark.triangle.fill"
            case .error: return "xmark.circle.fill"
            }
        }
    }
    
    init(message: String, 
         type: ToastType = .info, 
         duration: TimeInterval = 3.0,
         showProgress: Bool = false,
         progress: Double? = nil,
         progressLabel: String? = nil) {
        self.message = message
        self.type = type
        self.duration = duration
        self.showProgress = showProgress
        self.progress = progress
        self.progressLabel = progressLabel
    }
}

// MARK: - Toast Manager

@MainActor
class ToastManager: ObservableObject {
    static let shared = ToastManager()
    
    @Published var currentToast: Toast?
    @Published var toastQueue: [Toast] = []
    
    private var dismissTask: Task<Void, Never>?
    private var progressToasts: [UUID: Toast] = [:]
    
    private init() {}
    
    // MARK: - Public Methods
    
    func show(_ message: String, type: Toast.ToastType = .info, duration: TimeInterval = 3.0) {
        let toast = Toast(message: message, type: type, duration: duration)
        enqueueToast(toast)
    }
    
    func showProgress(_ label: String, progress: Double = 0.0) -> UUID {
        let toast = Toast(
            message: "",
            type: .info,
            duration: .infinity,
            showProgress: true,
            progress: progress,
            progressLabel: label
        )
        
        progressToasts[toast.id] = toast
        
        // Always show progress toast immediately
        withAnimation(.spring()) {
            currentToast = toast
        }
        
        return toast.id
    }
    
    func updateProgress(id: UUID, progress: Double, label: String? = nil) {
        guard let existingToast = progressToasts[id] else { return }
        
        // Create updated toast keeping the same ID
        var updatedToast = existingToast
        updatedToast.progress = progress
        if let label = label {
            updatedToast.progressLabel = label
        }
        
        progressToasts[id] = updatedToast
        
        // Update current toast if it's the same one
        if currentToast?.id == id {
            withAnimation(.easeInOut(duration: 0.2)) {
                currentToast = updatedToast
            }
        }
    }
    
    func dismissProgress(id: UUID) {
        progressToasts.removeValue(forKey: id)
        
        if currentToast?.id == id {
            currentToast = nil
            showNextToast()
        }
    }
    
    func dismissCurrent() {
        dismissTask?.cancel()
        withAnimation(.easeOut(duration: 0.3)) {
            currentToast = nil
        }
        showNextToast()
    }
    
    // MARK: - Private Methods
    
    private func enqueueToast(_ toast: Toast) {
        if currentToast == nil {
            showToast(toast)
        } else {
            toastQueue.append(toast)
        }
    }
    
    private func showToast(_ toast: Toast) {
        withAnimation(.spring()) {
            currentToast = toast
        }
        
        if toast.duration != .infinity {
            dismissTask?.cancel()
            dismissTask = Task {
                try? await Task.sleep(nanoseconds: UInt64(toast.duration * 1_000_000_000))
                
                if !Task.isCancelled {
                    await MainActor.run {
                        self.dismissCurrent()
                    }
                }
            }
        }
    }
    
    private func showNextToast() {
        guard !toastQueue.isEmpty else { return }
        let nextToast = toastQueue.removeFirst()
        showToast(nextToast)
    }
}

// MARK: - Toast View

struct ToastView: View {
    let toast: Toast
    
    var body: some View {
        VStack(spacing: 8) {
            if !toast.message.isEmpty || toast.progressLabel != nil {
                HStack(spacing: 12) {
                    if !toast.showProgress {
                        Image(systemName: toast.type.iconName)
                            .font(.system(size: 20))
                            .foregroundColor(.white)
                    }
                    
                    Text(toast.progressLabel ?? toast.message)
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                    
                    Spacer(minLength: 0)
                }
            }
            
            if toast.showProgress {
                VStack(spacing: 6) {
                    // Always show progress bar with a background for visibility
                    GeometryReader { geometry in
                        ZStack(alignment: .leading) {
                            // Background track
                            RoundedRectangle(cornerRadius: 3)
                                .fill(Color.white.opacity(0.3))
                                .frame(height: 6)
                            
                            // Progress fill
                            if let progress = toast.progress, progress > 0 {
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(Color.white)
                                    .frame(width: progress * geometry.size.width, height: 6)
                                    .animation(.easeInOut(duration: 0.3), value: progress)
                            }
                        }
                    }
                    .frame(height: 6)
                    
                    if let progress = toast.progress {
                        Text("\(Int(progress * 100))%")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(.white)
                    }
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(toast.type.backgroundColor)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                )
        )
        .shadow(color: .black.opacity(0.15), radius: 8, x: 0, y: 2)
    }
}

// MARK: - Toast Overlay View Modifier

struct ToastOverlay: ViewModifier {
    @ObservedObject private var toastManager = ToastManager.shared
    @State private var dragOffset: CGSize = .zero
    
    func body(content: Content) -> some View {
        content
            .overlay(alignment: .bottom) {
                if let toast = toastManager.currentToast {
                    ToastView(toast: toast)
                        .padding(16) // Equal padding on all sides
                        .offset(y: dragOffset.height)
                        .transition(.asymmetric(
                            insertion: .move(edge: .bottom).combined(with: .opacity),
                            removal: .move(edge: .bottom).combined(with: .opacity)
                        ))
                        .gesture(
                            DragGesture()
                                .onChanged { value in
                                    // Only allow downward swipes
                                    if value.translation.height > 0 {
                                        dragOffset = value.translation
                                    }
                                }
                                .onEnded { value in
                                    // If swiped down more than 50 points, dismiss
                                    if value.translation.height > 50 {
                                        withAnimation(.easeOut(duration: 0.2)) {
                                            dragOffset.height = 300
                                        }
                                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                                            toastManager.dismissCurrent()
                                            dragOffset = .zero
                                        }
                                    } else {
                                        // Snap back
                                        withAnimation(.spring()) {
                                            dragOffset = .zero
                                        }
                                    }
                                }
                        )
                        .onTapGesture {
                            if toast.duration != .infinity {
                                toastManager.dismissCurrent()
                            }
                        }
                }
            }
    }
}

// MARK: - View Extension

extension View {
    func withToastOverlay() -> some View {
        modifier(ToastOverlay())
    }
}