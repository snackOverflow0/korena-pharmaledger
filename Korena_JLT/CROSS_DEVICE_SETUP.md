# Korena Pharmacy — Cross-device PharmaLedger

This edition uses the original Flask app with a responsive browser interface, a **single shared PostgreSQL database**, and the original login, journal, general ledger, trial balance and audit features. It is intended for authorized Korena Pharmacy use only.

## Quick local demo on Windows / Mac / Linux
1. Install Docker Desktop. Extract this project folder.
2. Make a copy of `.env.server.example` named `.env`. Set **unique strong** values for `POSTGRES_PASSWORD`, `FLASK_SECRET_KEY`, `INITIAL_ADMIN_PASSWORD`, and `ADMIN_EMAIL`. Keep the `.env` private.
3. In the project folder run `docker compose up --build -d`.
4. Visit **http://localhost:8000** on the host computer. The shared database and original accounting tables initialize automatically.
5. To access from other devices on the same Wi-Fi network, edit compose.yaml `127.0.0.1:8000:8000` to `8000:8000`, then run `docker compose up -d`. Obtain the server computer's LAN IP with `ipconfig` (Windows) and visit `http://YOUR-LAN-IP:8000` on the phone. Allow port 8000 in the Windows firewall only on your trusted private network. For a real pharmacy deployment use HTTPS, not an unencrypted Wi-Fi login.

## Internet access on any device
Deploy this folder on a host with persistent PostgreSQL and HTTPS (for example a VPS running Docker and a reverse proxy such as Caddy). Configure a domain, HTTPS certificates, firewall, backups and account access controls. Set `KORENA_HTTPS=1` once HTTPS is operational. Never expose the PostgreSQL port or commit the `.env` file. The sample compose binds to localhost deliberately and **is not publicly hosted**.

## Important limitations
- This is a **responsive web application** that runs in modern Windows, macOS, Linux, Android and iOS browsers. It is NOT a native iOS/Android app or an installable APK/IPA.
- Multiple devices connect to **the same hosted database**. The previous single-file Windows `.exe` stores separate local SQLite data. This project does **not** migrate those existing local records automatically.
- Keep the server running for clients to connect. A phone cannot connect when the host is off or unreachable.
- Initial admin account is provisioned only if no user exists; changing credentials in `.env` later does NOT reset the existing password. Only share admin access with authorized people.
- Back up the PostgreSQL data volume regularly; test backup restoration and full accounting workflows before any real-world use.
- For internet/public access, add rate limiting/login lockout, HTTPS, appropriate compliance safeguards and operational monitoring before production use. Current login has CSRF protections but no login rate limiting.
