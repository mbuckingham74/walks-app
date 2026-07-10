import HealthKit
import Foundation

enum WalksSyncError: Error, LocalizedError {
    case healthKitUnavailable
    case invalidURL
    case serverError(statusCode: Int, body: String)
    case missingSecret

    var errorDescription: String? {
        switch self {
        case .healthKitUnavailable:
            return "HealthKit is not available on this device."
        case .invalidURL:
            return "The request URL is invalid. Check the base URL."
        case .serverError(let statusCode, let body):
            return "Server returned \(statusCode): \(body)"
        case .missingSecret:
            return "Shortcut secret is not configured in the app."
        }
    }
}

final class HealthKitManager {
    static let shared = HealthKitManager()

    private let store = HKHealthStore()

    func requestAuthorization() async throws {
        guard HKHealthStore.isHealthDataAvailable() else {
            throw WalksSyncError.healthKitUnavailable
        }

        let stepType = HKQuantityType.quantityType(forIdentifier: .stepCount)!
        try await store.requestAuthorization(toShare: [], read: [stepType])
    }

    func fetchSteps(for date: Date) async throws -> Int {
        guard HKHealthStore.isHealthDataAvailable() else {
            throw WalksSyncError.healthKitUnavailable
        }

        let stepType = HKQuantityType.quantityType(forIdentifier: .stepCount)!
        try await requestAuthorization()

        let calendar = Calendar.current
        let start = calendar.startOfDay(for: date)
        let end = calendar.date(byAdding: .day, value: 1, to: start)!
        let predicate = HKQuery.predicateForSamples(
            withStart: start,
            end: end,
            options: .strictStartDate
        )

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKStatisticsQuery(
                quantityType: stepType,
                quantitySamplePredicate: predicate,
                options: .cumulativeSum
            ) { _, result, error in
                if let error = error {
                    continuation.resume(throwing: error)
                    return
                }

                let sum = result?.sumQuantity()?.doubleValue(for: HKUnit.count()) ?? 0
                continuation.resume(returning: Int(sum))
            }
            store.execute(query)
        }
    }

    func syncTodaySteps(baseURL: String, secret: String) async throws -> String {
        try await syncSteps(for: Date(), baseURL: baseURL, secret: secret)
    }

    func syncRecentDays(count: Int, baseURL: String, secret: String, force: Bool = false) async throws -> String {
        let calendar = Calendar.current
        let today = Date()
        var results: [String] = []

        for dayOffset in stride(from: count - 1, through: 0, by: -1) {
            guard let date = calendar.date(byAdding: .day, value: -dayOffset, to: today) else {
                continue
            }
            results.append(try await syncSteps(for: date, baseURL: baseURL, secret: secret, force: force))
        }

        return results.joined(separator: "\n")
    }

    func syncSteps(for date: Date, baseURL: String, secret: String, force: Bool = false) async throws -> String {
        guard !secret.isEmpty else {
            throw WalksSyncError.missingSecret
        }

        let steps = try await fetchSteps(for: date)
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dateString = formatter.string(from: date)

        if !force && StepSyncHistoryStore.hasSuccessfulSync(dateString: dateString, steps: steps) {
            return "Already synced \(steps) steps for \(dateString)."
        }

        var components = URLComponents(string: baseURL)
        components?.path = "/api/steps"

        guard let url = components?.url else {
            throw WalksSyncError.invalidURL
        }

        let body = StepsRequest(date: dateString, steps: steps)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(secret, forHTTPHeaderField: "X-Shortcut-Secret")
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw WalksSyncError.serverError(statusCode: 0, body: "No HTTP response")
        }

        let responseBody = String(data: data, encoding: .utf8) ?? ""
        guard (200...299).contains(httpResponse.statusCode) else {
            throw WalksSyncError.serverError(statusCode: httpResponse.statusCode, body: responseBody)
        }

        StepSyncHistoryStore.markSuccessfulSync(dateString: dateString, steps: steps)
        return "Synced \(steps) steps for \(dateString)."
    }
}

private struct StepsRequest: Encodable {
    let date: String
    let steps: Int
}
