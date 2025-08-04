# Development Status

## iOS Frontend Tasks

**Objective:** Standardize dependency injection by removing all singleton (`.shared`) patterns and fully integrate `AppState` as the global state container.

DI is using FactoryKit. Consult the docs for reference: https://hmlongco.github.io/Factory/documentation/factorykit/

### Files to be Updated

The following files have been identified as not fully conforming to the new architecture. Each file requires one or more of the actions listed in the "Remaining Tasks" section below.

-   **`ios/FutureGolf/FutureGolf/App/FutureGolfApp.swift`**: Still uses singletons for `DebugService`, `ToastManager`, and `TTSService`. 
-   **`ios/FutureGolf/FutureGolf/Features/Analysis/Services/AnalysisReportGenerator.swift`**: Uses singletons for `AnalysisMediaStorage` and `TTSService`.
-   **`ios/FutureGolf/FutureGolf/Features/Analysis/Services/TTSCacheService.swift`**: Uses singletons for `TTSPhraseManager` and `TTSService`.
-   **`ios/FutureGolf/FutureGolf/Features/Debug/DebugPanelView.swift`**: Uses singletons for `TTSService` and `OnDeviceSTTService`.
-   **`ios/FutureGolf/FutureGolf/Features/Recording/RecordingScreen.swift`**: Directly accesses a `deps` object that is not defined in the file, which should be replaced with injected dependencies.
-   **`ios/FutureGolf/FutureGolf/Shared/Services/DebugService.swift`**: Implemented as a singleton and needs to be registered with the DI container.
-   **`ios/FutureGolf/FutureGolf/Shared/Services/OnDeviceSTTService.swift`**: Implemented as a singleton and needs to be registered with the DI container.
-   **`ios/FutureGolf/FutureGolf/Shared/Services/RecordingAPIService.swift`**: Implemented as a singleton and needs to be registered with the DI container.
-   **`ios/FutureGolf/FutureGolf/Shared/Services/TTSCacheManager.swift`**: Uses singletons for `ConnectivityService` and `TTSPhraseManager`. 
-   **`ios/FutureGolf/FutureGolf/Shared/Services/TTSService.swift`**: Implemented as a singleton and needs to be registered with the DI container.
-   **`ios/FutureGolf/FutureGolf/Shared/Services/VoiceCommandService.swift`**: Uses the `OnDeviceSTTService` singleton.
-   **`ios/FutureGolf/FutureGolf/Shared/Testing/TestConfiguration.swift`**: Uses the `ToastManager` singleton.

### Remaining Tasks

1.  **Integrate `AppState` as the Global State:**
    -   Update all views and view models to source global state (e.g., `currentRecordingId`, `currentRecordingURL`) from the `AppState` environment object.

2.  **Standardize Dependency Injection with `Factory`:**
    -   **Register Singletons in DI Container:** For each service currently implemented as a singleton (`.shared`), register it in `Container+Injection.swift`.
    -   **Update Call Sites:** Replace all calls to `.shared` with `@Injected` property wrappers to retrieve dependencies from the `Factory` container.
    -   **Constructor Injection:** Ensure that all services and view models receive their dependencies through FactoryKit DI container via @Injected, @InjectedObject, etc.

