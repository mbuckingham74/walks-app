import AppIntents
import Foundation

struct SyncStepsIntent: AppIntent {
    static var title: LocalizedStringResource = "Sync Steps"
    static var description = IntentDescription("Refresh and sync the last seven days of steps to the Walks Tracker server.")

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        let defaults = UserDefaults.standard
        let baseURL = WalkSyncConfig.configuredBaseURL(defaults: defaults)
        let secret = WalkSyncConfig.configuredSecret()

        let result = try await HealthKitManager.shared.syncRecentDays(
            count: WalkSyncConfig.refreshDayCount,
            baseURL: baseURL,
            secret: secret,
            force: true
        )
        return .result(value: result)
    }
}

struct SyncRecentStepsIntent: AppIntent {
    static var title: LocalizedStringResource = "Sync Recent Steps"
    static var description = IntentDescription("Refresh and sync the last seven days of steps to the Walks Tracker server.")

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        let defaults = UserDefaults.standard
        let baseURL = WalkSyncConfig.configuredBaseURL(defaults: defaults)
        let secret = WalkSyncConfig.configuredSecret()

        let result = try await HealthKitManager.shared.syncRecentDays(
            count: WalkSyncConfig.refreshDayCount,
            baseURL: baseURL,
            secret: secret,
            force: true
        )
        return .result(value: result)
    }
}

struct WalkSyncShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: SyncStepsIntent(),
            phrases: [
                "Sync my steps with ${applicationName}",
                "Refresh my steps with ${applicationName}"
            ],
            shortTitle: "Sync Steps",
            systemImageName: "calendar.badge.clock"
        )
    }
}
