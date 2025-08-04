# DEVELOPMENT GUIDELINES

## Swift / SwiftUI

### 💡 Core Principles
- **Use Modern Swift**: Always target the latest stable Swift and iOS versions supported by the project. Leverage modern features like `ResultBuilders`, `async/await`, `some View`, and `macros` if available.
- **Follow MVVM Strictly**: Keep all logic in the ViewModel (`VM`). Views (`V`) must only describe layout and user interaction. Avoid business logic or navigation logic in Views.
- **Follow SRP, DRY, separation of interests and other OOP core principles.**
- **Check your work**: Does the server still start? Does the app build? etc. Also check as per the style guidelines above and below
- **Commment your work**:  
- **Break large work into modular chunks** and git commit in between.   

---

### 🧠 Architecture

#### MVVM Pattern
- `View`: Declarative layout only. Minimal logic.
- `ViewModel`: All business logic, state, and side-effects live here.
- `Model`: Codable structs/enums mirroring API or internal app structure.

#### Services and Organisation
- If a file, particularly a View or a ViewModel exceed 350-500 lines, consider breaking it up into smaller components
- Long Views should be broken into sub-views. Stylised components that re-occur should be made into shared view components
- With long VMs, consider creating Service classes, or moving extensions, enums and related features into their own files
- Prefer composition over inheritance or extension. 
- Views should only ever access methods and parameters of a ViewModel
- ViewModels as much as is reasonably should work only with app-specific DSL, abstracting away direct iOS and library dependencies in services and utilities. 



#### Global State & DI
- Use Factory for DI including it's property wrappers.  Its docs are here: https://hmlongco.github.io/Factory/documentation/factorykit/
- Do not pass dependencies to constructors
- Assign all deps to class ivars at the top


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
