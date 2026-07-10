import Foundation

enum WalkSyncConfig {
    nonisolated static let baseURLKey = "walksBaseURL"
    nonisolated static let syncHistoryKey = "successfulStepSyncsByDate"
    nonisolated static let refreshDayCount = 7

    nonisolated static let defaultBaseURL = "https://walks.tachyonfuture.com"
    nonisolated private static let shortcutSecret = "0f4af2e709017949ac71f6b29b2df0e91abd34d983a21eecf61318122be8df2a"

    nonisolated static func configuredBaseURL(defaults: UserDefaults = .standard) -> String {
        normalizedBaseURL(defaults.string(forKey: baseURLKey))
    }

    nonisolated static func configuredSecret() -> String {
        shortcutSecret
    }

    @discardableResult
    nonisolated static func persistNormalizedBaseURL(defaults: UserDefaults = .standard) -> String {
        let normalized = configuredBaseURL(defaults: defaults)
        defaults.set(normalized, forKey: baseURLKey)
        return normalized
    }

    nonisolated static func normalizedBaseURL(_ value: String?) -> String {
        guard var trimmed = nonEmpty(value) else {
            return defaultBaseURL
        }

        while trimmed.hasSuffix("/") {
            trimmed.removeLast()
        }

        if trimmed.hasPrefix("http://62.72.5.248") || trimmed.hasPrefix("https://62.72.5.248") {
            return defaultBaseURL
        }

        if !trimmed.contains("://") {
            trimmed = "https://\(trimmed)"
        }

        guard var components = URLComponents(string: trimmed) else {
            return defaultBaseURL
        }

        components.scheme = "https"
        return components.string ?? defaultBaseURL
    }

    nonisolated static func nonEmpty(_ value: String?) -> String? {
        guard let trimmed = value?.trimmingCharacters(in: .whitespacesAndNewlines),
              !trimmed.isEmpty else {
            return nil
        }
        return trimmed
    }
}

struct SuccessfulStepSync: Codable {
    let steps: Int
    let syncedAt: Date
}

enum StepSyncHistoryStore {
    nonisolated static func record(for dateString: String, defaults: UserDefaults = .standard) -> SuccessfulStepSync? {
        load(defaults: defaults)[dateString]
    }

    nonisolated static func hasSuccessfulSync(dateString: String, steps: Int, defaults: UserDefaults = .standard) -> Bool {
        record(for: dateString, defaults: defaults)?.steps == steps
    }

    nonisolated static func markSuccessfulSync(dateString: String, steps: Int, defaults: UserDefaults = .standard) {
        var records = load(defaults: defaults)
        records[dateString] = SuccessfulStepSync(steps: steps, syncedAt: Date())
        save(records, defaults: defaults)
    }

    nonisolated private static func load(defaults: UserDefaults) -> [String: SuccessfulStepSync] {
        guard let data = defaults.data(forKey: WalkSyncConfig.syncHistoryKey) else {
            return [:]
        }
        return (try? JSONDecoder().decode([String: SuccessfulStepSync].self, from: data)) ?? [:]
    }

    nonisolated private static func save(_ records: [String: SuccessfulStepSync], defaults: UserDefaults) {
        guard let data = try? JSONEncoder().encode(records) else {
            return
        }
        defaults.set(data, forKey: WalkSyncConfig.syncHistoryKey)
    }
}
