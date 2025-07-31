# DEVELOPMENT GUIDELINES

## Swift / SwiftUI

### 💡 Core Principles
- **Use Modern Swift**: Always target the latest stable Swift and iOS versions supported by the project. Leverage modern features like `ResultBuilders`, `async/await`, `some View`, and `macros` if available.
- **Follow MVVM Strictly**: Keep all logic in the ViewModel (`VM`). Views (`V`) must only describe layout and user interaction. Avoid business logic or navigation logic in Views.

---

### 🧠 Architecture

#### MVVM Pattern
- `View`: Declarative layout only. Minimal logic.
- `ViewModel`: All business logic, state, and side-effects live here.
- `Model`: Codable structs/enums mirroring API or internal app structure.

#### Global State & DI
- Use a lightweight **Dependency Injection** system (e.g. environment objects, `@MainActor class AppContainer`) to inject services and global state.
- Shared state should be managed via a **single source of truth** pattern (e.g. `@Observable`, `@Published`, or modern `ObservableStateObject` pattern).

#### Navigation
- Use `NavigationStack` and route via a `Router` abstraction controlled by the ViewModel.
- Support programmatic deep links and testability.

---

### 📁 Code Organization

```
/App
    AppEntry.swift
    AppContainer.swift
    Config.swift
/Features
    /Login
        LoginView.swift
        LoginViewModel.swift
        LoginModel.swift
    /Dashboard
        ...
/Shared
    /Components
    /Extensions
    /Services
    /Theme
/Resources
```

---

### 🎨 Styling & UI

- Create a central **Theme system** (e.g. `AppColors`, `AppFonts`, `Spacing`, `Corners`) using enums or structs.
- Follow **Apple HIG**. Use native components unless there's a strong UX/UI reason not to.
- Use `ViewModifier` and `Style` abstractions for repeated layout patterns.

---

### 🌍 Config & Constants

- All constants in a single `Config.swift` file:
```swift
enum Config {
    static let baseURL = URL(string: "https://api.example.com")!
    static let isDebugMode = true
    static let defaultLaunchScreen = "login"
}
```
- Use `#if DEBUG` blocks to control dev-only behaviors.
- Support dynamic config changes via feature flags or local settings if needed.

---

### 🪵 Logging & Debugging

- Use a **file-based logging system**:
```swift
func log(_ message: String, file: String = #file) {
    let filename = URL(fileURLWithPath: file).lastPathComponent
    print("[\(filename)] \(message)")
}
```
- Support log filtering per channel and log levels.
- Provide a dev overlay or console toggle in debug builds.
- Include debug tools to:
  - Launch directly to any screen (`Config.defaultLaunchScreen`)
  - Trigger mock data or states
  - Visualize state (e.g. via debug menu or overlay)

---

### 🔁 Reactive & State

- Use `@Observable`, `@Published`, or Combine as appropriate for ViewModel <-> View binding.
- Handle async calls with `async/await`, showing loading indicators immediately on interaction.
- Gracefully degrade behavior on failure (fallbacks, retries, user messages).

---

### 🔌 Networking

- Use native `URLSession` with lightweight abstraction.
- Decode with `Codable`, errors with clear models.
- Retry + loading state handled in the ViewModel.
- Use dependency injection to mock services for testing.

---

### 📦 Third-Party Libraries

- Only add if:
  - It brings major, **non-trivial value**
  - Or can’t be replicated easily in-house
  - Or is a single-file utility that’s auditable and can be imported directly
- **Always ask first**, presenting the case for using them

---

### ✅ UX Guidelines

- Always provide **immediate feedback** (animation, progress indicator) on tap or interaction. Organise the business logic so this is possible (e.g. no long running processes between user tap and segwey to new view — pre-cache them, or indicate loading)
- Prioritize perceived performance and responsiveness.

---

### 🔬 Testing & Debugability

- All ViewModels should be unit-testable.
- Inject services for mockability.
- Feature flags or config toggles for test/dev-only behavior.
- Use UITests to test components and more complex user journeys
- Implement fixtures, including media (e.g. video, images) for integration tests. Pause and request such media if it cannot be easily sourced.
