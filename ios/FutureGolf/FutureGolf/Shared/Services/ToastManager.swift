import SwiftUI
import Combine
import Factory

// MARK: - Toast Model

struct Toast: Identifiable {
    let id: String
    var message: String
    var type: ToastType
    var duration: TimeInterval
    var showProgress: Bool
    var progress: Double?
    var progressLabel: String?
    var isPersistent: Bool
    
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
         progressLabel: String? = nil,
         id: String? = nil) {
        self.id = id ?? UUID().uuidString
        self.message = message
        self.type = type
        self.duration = duration
        self.showProgress = showProgress
        self.progress = progress
        self.progressLabel = progressLabel
        self.isPersistent = duration == .infinity
    }
}

// MARK: - Toast Manager

@MainActor
class ToastManager: ObservableObject {
    @Published var activeToasts: [Toast] = []
    @Published var toastQueue: [Toast] = []
    
    private var dismissTasks: [String: Task<Void, Never>] = [:]
    private var progressToasts: [String: Toast] = [:]
    
    init() {}
    
    // MARK: - Public Methods
    
    func show(_ message: String, type: Toast.ToastType = .info, duration: TimeInterval = 3.0, id: String? = nil) {
        // Check if a toast with this ID already exists
        if let id = id, activeToasts.contains(where: { $0.id == id }) {
            // Update existing toast
            if let index = activeToasts.firstIndex(where: { $0.id == id }) {
                withAnimation(.spring()) {
                    activeToasts[index].message = message
                    activeToasts[index].type = type
                }
            }
            return
        }
        
        let toast = Toast(message: message, type: type, duration: duration, id: id)
        enqueueToast(toast)
    }
    
    func showProgress(_ label: String, progress: Double = 0.0) -> String {
        let toastId = UUID().uuidString
        let toast = Toast(
            message: "",
            type: .info,
            duration: .infinity,
            showProgress: true,
            progress: progress,
            progressLabel: label,
            id: toastId
        )
        
        progressToasts[toast.id] = toast
        
        // Add to active toasts
        withAnimation(.spring()) {
            activeToasts.append(toast)
        }
        
        return toast.id
    }
    
    func updateProgress(id: String, progress: Double, label: String? = nil) {
        guard let existingToast = progressToasts[id] else { return }
        
        // Create updated toast keeping the same ID
        var updatedToast = existingToast
        updatedToast.progress = progress
        if let label = label {
            updatedToast.progressLabel = label
        }
        
        progressToasts[id] = updatedToast
        
        // Update in active toasts
        if let index = activeToasts.firstIndex(where: { $0.id == id }) {
            withAnimation(.easeInOut(duration: 0.2)) {
                activeToasts[index] = updatedToast
            }
        }
    }
    
    func dismissProgress(id: String) {
        progressToasts.removeValue(forKey: id)
        dismiss(id: id)
    }
    
    func dismissCurrent() {
        // Dismiss the oldest non-persistent toast
        if let firstNonPersistent = activeToasts.first(where: { !$0.isPersistent }) {
            dismiss(id: firstNonPersistent.id)
        }
    }
    
    func dismiss(id: String) {
        // Cancel any dismiss task
        dismissTasks[id]?.cancel()
        dismissTasks.removeValue(forKey: id)
        
        // Remove from active toasts
        withAnimation(.easeOut(duration: 0.3)) {
            activeToasts.removeAll { $0.id == id }
        }
        
        // Show next queued toast if any
        showNextToast()
    }
    
    // MARK: - Private Methods
    
    private func enqueueToast(_ toast: Toast) {
        // Allow up to 3 active toasts
        if activeToasts.count < 3 {
            showToast(toast)
        } else {
            toastQueue.append(toast)
        }
    }
    
    private func showToast(_ toast: Toast) {
        withAnimation(.spring()) {
            activeToasts.append(toast)
        }
        
        if !toast.isPersistent {
            let task = Task {
                try? await Task.sleep(nanoseconds: UInt64(toast.duration * 1_000_000_000))
                
                if !Task.isCancelled {
                    await MainActor.run {
                        self.dismiss(id: toast.id)
                    }
                }
            }
            dismissTasks[toast.id] = task
        }
    }
    
    private func showNextToast() {
        guard !toastQueue.isEmpty && activeToasts.count < 3 else { return }
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
    @InjectedObject(\.toastManager) private var toastManager
    @State private var dragOffsets: [String: CGFloat] = [:]
    
    func body(content: Content) -> some View {
        content
            .overlay(alignment: .bottom) {
                VStack(spacing: 8) {
                    ForEach(toastManager.activeToasts) { toast in
                        ToastView(toast: toast)
                            .offset(y: dragOffsets[toast.id] ?? 0)
                            .transition(.asymmetric(
                                insertion: .move(edge: .bottom).combined(with: .opacity),
                                removal: .move(edge: .bottom).combined(with: .opacity)
                            ))
                            .gesture(
                                DragGesture()
                                    .onChanged { value in
                                        // Only allow downward swipes
                                        if value.translation.height > 0 {
                                            dragOffsets[toast.id] = value.translation.height
                                        }
                                    }
                                    .onEnded { value in
                                        // If swiped down more than 50 points, dismiss
                                        if value.translation.height > 50 {
                                            withAnimation(.easeOut(duration: 0.2)) {
                                                dragOffsets[toast.id] = 300
                                            }
                                            DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) {
                                                toastManager.dismiss(id: toast.id)
                                                dragOffsets.removeValue(forKey: toast.id)
                                            }
                                        } else {
                                            // Snap back
                                            withAnimation(.spring()) {
                                                dragOffsets[toast.id] = 0
                                            }
                                        }
                                    }
                            )
                            .onTapGesture {
                                if !toast.isPersistent {
                                    toastManager.dismiss(id: toast.id)
                                }
                            }
                    }
                }
                .padding(16) // Equal padding on all sides
            }
    }
}

// MARK: - View Extension

extension View {
    func withToastOverlay() -> some View {
        modifier(ToastOverlay())
    }
}