# iOS client (Xcode project creation required)
1. On a Mac with Xcode, File > New > Project > iOS > App (SwiftUI, Swift).
2. Set bundle identifier, e.g. `ph.korena.pharmaledger`; target iOS 15 or later.
3. Replace the default app source with `KorenaPharmaLedgerApp.swift` and add `WebContentView.swift`.
4. Change `urlString` to your real HTTPS server URL. Add an app icon and signing team.
5. Build on a connected iPhone or distribute through approved Apple workflows.

This folder is Swift source, not a compiled IPA or complete Xcode project.
