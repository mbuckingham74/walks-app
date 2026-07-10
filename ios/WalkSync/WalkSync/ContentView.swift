import SwiftUI

struct ContentView: View {
    @AppStorage(WalkSyncConfig.baseURLKey) private var baseURL: String = WalkSyncConfig.defaultBaseURL
    @State private var status: String = "Ready."
    @State private var isSyncing = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Server") {
                    TextField("Base URL", text: $baseURL)
                        .autocapitalization(.none)
                        .keyboardType(.URL)
                }
                .listRowBackground(Color(white: 0.08))

                Section("Action") {
                    Button {
                        Task { await syncLastWeek() }
                    } label: {
                        primarySyncLabel("Sync Last 7 Days")
                    }
                    .disabled(isSyncing)
                    .buttonStyle(.plain)
                    .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
                    .listRowBackground(Color.clear)
                }

                Section("Status") {
                    Text(status)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
                .listRowBackground(Color(white: 0.08))
            }
            .scrollContentBackground(.hidden)
            .background(Color.black)
            .navigationTitle("Walks Sync")
            .toolbarBackground(Color.black, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbarColorScheme(.dark, for: .navigationBar)
            .onAppear {
                baseURL = WalkSyncConfig.persistNormalizedBaseURL()
            }
        }
        .preferredColorScheme(.dark)
    }

    private var configuredBaseURL: String {
        WalkSyncConfig.normalizedBaseURL(baseURL)
    }

    private var configuredSecret: String {
        WalkSyncConfig.configuredSecret()
    }

    private func syncLastWeek() async {
        isSyncing = true
        defer { isSyncing = false }

        do {
            status = try await HealthKitManager.shared.syncRecentDays(
                count: WalkSyncConfig.refreshDayCount,
                baseURL: configuredBaseURL,
                secret: configuredSecret,
                force: true
            )
        } catch {
            status = "Error: \(error.localizedDescription)"
        }
    }

    private func primarySyncLabel(_ title: String) -> some View {
        HStack(spacing: 8) {
            Text(title)
                .font(.headline)
            if isSyncing {
                ProgressView()
                    .tint(.white)
            }
        }
        .frame(maxWidth: .infinity, minHeight: 48)
        .foregroundStyle(.white)
        .background(isSyncing ? Color.blue.opacity(0.65) : Color.blue)
        .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
        .contentShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}
