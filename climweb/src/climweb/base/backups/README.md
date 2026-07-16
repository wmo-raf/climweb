# Google Drive backups (CMS admin)

ClimWeb can upload its nightly database and media backups to Google Drive,
configured entirely from **Settings → Backup** in the CMS admin. This replaces
the old command-line `climweb-backup-sync` container.

There are two parts: a **one-time central setup** (create one Google OAuth app,
done once for all countries) and a **per-site setup** (each country connects its
own Google account in the browser).

---

## Part 1 — One-time central setup (Google Cloud)

Do this once. The same OAuth client serves every ClimWeb deployment.

1. **Create / pick a project** at [console.cloud.google.com](https://console.cloud.google.com).
2. **Enable the Drive API**: APIs & Services → Enable APIs → search **Google Drive API** → Enable.
3. **Configure the consent screen**: APIs & Services → OAuth consent screen.
   - User type: **External**.
   - Fill in app name, support email, developer contact.
   - **Data access → Add scopes** → add `.../auth/drive.file` (plus `openid` and
     `.../auth/userinfo.email`). `drive.file` gives per-file access — the app
     only ever sees files it created, never the rest of the Drive.
4. **Publish to Production.** Under *Publishing status*, click **Publish app**.
   - This is important: while an app is in **Testing**, Google-issued refresh
     tokens **expire after 7 days**, which would silently break backups a week
     later. Production tokens don't expire like that.
   - `drive.file` is a **non-sensitive** scope, so publishing does **not**
     require Google's verification/security-audit review. You can publish
     immediately. (You may still see a one-time "Google hasn't verified this
     app" interstitial — continue via *Advanced → Continue*.)
5. **Create the OAuth client**: APIs & Services → Credentials → Create
   Credentials → **OAuth client ID** → application type **Web application**.
   - **Authorised redirect URI** — add exactly:
     `https://YOUR-CMS-DOMAIN/<admin-path>/backup/google/callback`
     (this is `WAGTAILADMIN_BASE_URL` + `/backup/google/callback`; the admin
     path is usually `/admin` or `/cms-admin`).
6. Copy the generated **Client ID** and **Client Secret** — you'll paste them
   into each site once.

> The Client ID/Secret can be reused across all country sites, or you can create
> one client per site. Either works.

---

## Part 2 — Per-site setup (CMS admin)

In each country's CMS: **Settings → Backup**.

1. **Google credentials**: paste the **Client ID** and **Client Secret**, then
   **Save**. (The secret is stored encrypted and never shown again.)
2. Click **Connect Google Drive**. On Google's consent screen, sign in with the
   site's Google account and **make sure the Google Drive permission checkbox is
   ticked** before continuing — Google leaves these granular checkboxes opt-in,
   and skipping it is the most common connection failure.
   - *Alternative (no button):* paste a refresh token into the **Paste a token**
     field instead (e.g. from Google's OAuth Playground), then Save.
3. Once it shows **Connected as …**, tick **Enable cloud backups** and Save.
4. Set the options as needed: remote folder name, DB copies to keep, media
   copies to keep, and which weekday the (larger) media archive uploads.
5. Click **Back up now**, wait a minute, refresh — **Last upload** should show
   *Success* with the uploaded filenames.

> Recommended: use a **dedicated Google account per site**, not someone's
> personal account. Drive's free 15 GB is shared with that account's Gmail/Photos.

---

## Verify recovery

A backup you haven't restored isn't a backup yet. After the first successful
upload, download the `.psql.bin` from Drive and test-restore it into a throwaway
database before relying on it.

---

## How it runs

The nightly `run_backup` Celery task dumps the DB and media locally, then uploads
the newest files to Drive: the **database snapshot every day**, and the **media
archive only on the configured weekday**. Old copies are pruned per the retention
settings. Each run records status/time/message under *Last upload*. **Back up
now** triggers the same task on demand.

---

## Troubleshooting

| Symptom | Cause & fix |
|---|---|
| **Access blocked: … has not completed the Google verification process** | App is in *Testing*. **Publish to Production** (see Part 1 step 4). Don't just add a test user — Testing-mode tokens expire in 7 days. |
| **(insecure_transport) OAuth 2 MUST utilize https** | Django behind a TLS-terminating proxy sees the callback as `http`. The callback code forces `https`, so ensure the updated code is deployed. Proper app-wide fix: set `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` and have nginx send `X-Forwarded-Proto`. |
| **Scope has changed … to "… openid"** (drive.file dropped) | The Drive permission wasn't granted. Re-Connect and **tick the Drive checkbox**. Also confirm `drive.file` is added under the consent screen's *Data access* scopes. |
| **Back up now** does nothing visible | It runs in the background. Refresh after a minute to see *Last upload*. Requires an account connected **and** "Enable cloud backups" ticked + saved. |
