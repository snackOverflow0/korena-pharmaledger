# Korena Pharmacy PharmaLedger — Integrated Installable Edition

This edition keeps **one existing Flask accounting application** and provides desktop, Android, and iOS **native window/WebView clients**. The backend is the source of truth: it handles authentication, journal posting, ledger, trial balance, audit log and exports.

## Deployment first (required)

1. Extract the ZIP. Open a terminal in `Korena_JLT` on a server with Docker Desktop / Docker Engine.
2. Copy `.env.server.example` to `.env` and replace the placeholders with unique strong credentials. The `POSTGRES_PASSWORD` should use URL-safe alphanumeric characters for this compose configuration. Keep `.env` private.
3. Start: `docker compose up --build -d`.
4. On the server, confirm `http://localhost:8000/health` works and log into `http://localhost:8000/`.
5. For multiple devices **outside the server**, deploy behind a real HTTPS domain and reverse proxy/load balancer, with TLS certificate and appropriate firewall/routing. The compose file binds only to localhost by design; it is NOT directly accessible by other computers/phones. Do not expose port 8000 or PostgreSQL directly to the public Internet.
6. Set `KORENA_HTTPS=1` when the public site is exclusively served through HTTPS. Preserve a strong `FLASK_SECRET_KEY`. Set regular encrypted database backups, audit/log retention, monitoring and access restrictions before using genuine financial data.

**Important:** The database is PostgreSQL in this integrated server edition, not the offline SQLite database. Records from an existing offline `.exe` or earlier MySQL database are **not migrated automatically**. Make a backup and plan an explicit validated migration if needed.

## Windows desktop EXE

1. Edit or set `KORENA_SERVER_URL` in your system environment to `https://your-real-domain` before launching the compiled EXE; it is read at runtime, not built in.
2. From `windows_client`, run `build_windows.bat` on Windows (Python 3 and PyInstaller required). Find `dist/KorenaPharmaLedger.exe`.
3. To test on the same PC as the backend, run `run_windows_dev.bat` after building/creating the local venv; it uses localhost HTTP only for development.
4. Share the built EXE with authorized staff. All of them must have network access to the SAME server. This EXE is an online client, not the earlier offline SQLite product.

## Android APK

1. Install Android Studio + JDK 17 and open `android_client` as an existing Gradle project.
2. In `app/src/main/java/ph/korena/pharmaledger/MainActivity.kt`, set `serverUrl` to your real HTTPS URL.
3. Let Gradle sync and select **Build > Build APK(s)**. Debug APK path is typically `app/build/outputs/apk/debug/app-debug.apk`.
4. Verify login, journal/ledger, export and audit with an Android device. Use a signed release build for distribution; Google Play publication has additional rules.

## iOS App

Follow `ios_client/README.md` using Xcode on macOS. Apple signing is required for installation on ordinary iPhones; distributing to others generally requires TestFlight/Apple Developer distribution. iOS SwiftUI source is supplied but no built IPA or Xcode project.

## What is integrated—and what is not

- **Shared**: hosted authentication, database (PostgreSQL), journal, general ledger, trial balance, audit trail, and CSV exports.
- **Preserved**: existing Flask page templates and business logic in `Korena_JLT`; thin client wrappers present them on supported devices.
- **Not provided**: compiled Windows EXE, Android APK, iOS IPA, production server hosting, DNS/TLS certificates, automatic migration of existing database contents, offline sync, app store distribution.
- **Need testing**: Windows, physical Android/iPhone behavior, login persistence, PDF/CSV download handling, backups, app update process and concurrent accounting entry load.

## Security and operational boundaries

Only authorized Korena Pharmacy users should receive access. Client code never contains database passwords; users authenticate to Flask using server-issued sessions. HTTPS is required for remote clients. The current repository's admin initialization uses existing `ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD`; it does **not** add public account registration. On first server boot the existing admin account is created. Rotate the initial password and remove it from running service configuration after first setup where practical, without removing the account from the database.

## Simplified client setup (updated)

- **Windows:** Run the compiled `KorenaPharmaLedger.exe`. If no `KORENA_SERVER_URL` environment variable is defined, the app prompts for the shared HTTPS address and stores **only that address** in the current user's `%LOCALAPPDATA%/KorenaPharmaLedger/client.json`. No password is saved there. To switch servers, edit/remove that local client.json file or provide the environment variable.
- **Android:** The app now prompts for the shared HTTPS URL on its first run and stores **only the address** in local app preferences. The server still needs to be deployed first. To change it, clear the Android app's data and re-enter the URL.
- **Check server:** From `Korena_JLT`, run `python check_server.py` to check the local server, or set `KORENA_SERVER_URL=https://yourdomain` and run that script. This verifies `/health` only, not login, database migration, or accounting correctness.
- **Not yet production-ready:** The APK, EXE, and iOS IPA are not compiled in this archive. Android build requires a suitable Gradle installation / wrapper and Android Studio; iOS source requires a macOS Xcode project and signing. A public deployment requires hosting, DNS, HTTPS, backups, and testing. Never use demonstration secrets for real pharmacy transactions.
