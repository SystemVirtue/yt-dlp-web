# yt-dlp-web (web-dlp-api)

A lightweight web API for downloading media via [yt-dlp](https://github.com/yt-dlp/yt-dlp), built with FastAPI and deployed on **Render.com**.

**Live URL:** <https://web-dlp-api.onrender.com/>

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check – returns `{"status": "ok"}` |
| `GET` | `/info?url=<URL>` | Fetch video metadata (title, duration, formats) |
| `GET` | `/download?url=<URL>&format=<FMT>` | Download media as a streamed MP4 file (default: 720p) |
| `GET` | `/thumbnail?url=<URL>` | Returns the video thumbnail image |
| `GET` | `/debug-cookies` | Debug the cookies.txt file inside the container |

### Examples

**Download 720p MP4** (default — no `format` param needed):
```
https://web-dlp-api.onrender.com/download?url=https://www.youtube.com/watch?v=VIDEO_ID
```

**Download with custom format:**
```
https://web-dlp-api.onrender.com/download?url=https://www.youtube.com/watch?v=VIDEO_ID&format=bestvideo[height<=1080]+bestaudio/best
```

**Get thumbnail:**
```
https://web-dlp-api.onrender.com/thumbnail?url=https://www.youtube.com/watch?v=VIDEO_ID
```

---

## Deploy to Render.com

### One-click (Blueprint)

1. Push this repo to GitHub.
2. Go to <https://dashboard.render.com/blueprints> → **New Blueprint Instance**.
3. Connect the repo – Render reads `render.yaml` and creates the service automatically.

### Manual

1. Go to <https://dashboard.render.com> → **New** → **Web Service**.
2. Connect your GitHub repo.
3. Settings:
   - **Name:** `web-dlp-api`
   - **Region:** Oregon (or preferred)
   - **Runtime:** Docker
   - **Plan:** Free
4. Click **Create Web Service**.

> **Note:** Render's free tier uses port `10000` by default. The Dockerfile and
> `main.py` both respect the `PORT` environment variable that Render sets.

---

## Keep-Alive with cron-job.org

Render free-tier services spin down after 15 minutes of inactivity.
Use [cron-job.org](https://cron-job.org) to prevent this:

1. Sign up / log in at <https://console.cron-job.org>.
2. **Create** a new cron job:
   - **Title:** `keep-alive web-dlp-api`
   - **URL:** `https://web-dlp-api.onrender.com/`
   - **Schedule:** Every 5 minutes (`*/5 * * * *`)
   - **Request method:** `GET`
   - **Request timeout:** 30 seconds
3. **Save** and enable the job.

This pings the `/` health-check endpoint every 5 minutes, keeping the
free-tier instance awake.

---

## Cookies (YouTube auth)

If you need authenticated downloads, place a Netscape-format `cookies.txt` in
the project root before building. The Dockerfile copies it into the container
at `/app/cookies.txt`.

---

## Local Development

```bash
pip install -r requirements.txt
python main.py
# → http://localhost:10000
```

Or with Docker:

```bash
docker build -t web-dlp-api .
docker run -p 10000:10000 web-dlp-api
```
