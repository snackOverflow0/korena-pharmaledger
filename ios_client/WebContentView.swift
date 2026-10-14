import SwiftUI
import WebKit

private let korenaServerURL = "https://YOUR-KORENA-SERVER.example/" // EDIT this once

struct WebContentView: UIViewRepresentable {
    // Use the same production HTTPS URL as Windows and Android.
    private let urlString = korenaServerURL
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .default()
        let view = WKWebView(frame: .zero, configuration: config)
        view.navigationDelegate = context.coordinator
        if let url = URL(string: urlString), url.scheme == "https", url.host?.hasSuffix(".example") == false {
            view.load(URLRequest(url: url))
        }
        return view
    }
    func updateUIView(_ uiView: WKWebView, context: Context) { }
    func makeCoordinator() -> Coordinator { Coordinator() }
    final class Coordinator: NSObject, WKNavigationDelegate {
        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let target = navigationAction.request.url else { decisionHandler(.cancel); return }
            if target.scheme == "https" && target.host == URL(string: korenaServerURL)?.host { decisionHandler(.allow) }
            else if target.scheme == "https" || target.scheme == "mailto" { UIApplication.shared.open(target); decisionHandler(.cancel) }
            else { decisionHandler(.cancel) }
        }
    }
}
