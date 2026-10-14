package ph.korena.pharmaledger

import android.app.Activity
import android.os.Bundle
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebResourceRequest
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import android.app.AlertDialog
import android.widget.EditText

class MainActivity : Activity() {
    private lateinit var serverUrl: String
    private lateinit var browser: WebView
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val stored = getSharedPreferences("korena", MODE_PRIVATE).getString("server_url", null)
        if (stored == null) {
            showServerSetup()
        } else {
            startBrowser(stored, savedInstanceState)
        }
    }
    private fun showServerSetup() {
        val field = EditText(this).apply {
            hint = "https://your-korena-server.com"
            setSingleLine(true)
        }
        AlertDialog.Builder(this)
            .setTitle("Korena Pharmacy server")
            .setMessage("Enter the HTTPS address provided by the administrator.")
            .setView(field)
            .setCancelable(false)
            .setPositiveButton("Connect") { _, _ ->
                val candidate = field.text.toString().trim().trimEnd('/') + "/"
                val parsed = Uri.parse(candidate)
                if (parsed.scheme != "https" || parsed.host.isNullOrBlank() ||
                    parsed.host!!.endsWith(".example") || parsed.userInfo != null ||
                    !parsed.path.isNullOrEmpty() && parsed.path != "/") {
                    Toast.makeText(this, "Enter a valid HTTPS base URL", Toast.LENGTH_LONG).show()
                    showServerSetup()
                } else {
                    getSharedPreferences("korena", MODE_PRIVATE).edit().putString("server_url", candidate).apply()
                    startBrowser(candidate, null)
                }
            }
            .setNegativeButton("Exit") { _, _ -> finish() }
            .show()
    }
    private fun startBrowser(url: String, savedInstanceState: Bundle?) {
        serverUrl = url
        val target = Uri.parse(serverUrl)
        browser = WebView(this)
        setContentView(browser)
        browser.settings.javaScriptEnabled = true
        browser.settings.domStorageEnabled = true
        browser.settings.allowFileAccess = false
        browser.settings.allowContentAccess = false
        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(browser, false)
        browser.webChromeClient = WebChromeClient()
        browser.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val uri = request.url
                if (uri.scheme == "https" && uri.host == target.host) return false
                if (uri.scheme == "https" || uri.scheme == "mailto") {
                    startActivity(Intent(Intent.ACTION_VIEW, uri))
                }
                return true
            }
        }
        if (savedInstanceState == null) browser.loadUrl(serverUrl) else browser.restoreState(savedInstanceState)
    }
    override fun onSaveInstanceState(outState: Bundle) { if (::browser.isInitialized) browser.saveState(outState); super.onSaveInstanceState(outState) }
    @Deprecated("Use OnBackPressedDispatcher for newer AndroidX projects")
    override fun onBackPressed() { if (::browser.isInitialized && browser.canGoBack()) browser.goBack() else super.onBackPressed() }
}
