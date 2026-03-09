# yt-dlp-web (web-dlp-api)

A lightweight web API for downloading media via [yt-dlp](https://github.com/yt-dlp/yt-dlp), built with FastAPI and deployed on **Render.com**.

**Live URL:** <https://web-dlp-api.onrender.com/>

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/info` | Fetch video metadata |
| `GET` | `/download` | Download video as MP4 |
| `GET` | `/thumbnail` | Get video thumbnail image |
| `GET` | `/debug-cookies` | Inspect cookies.txt inside container |

---

### `GET /`

Health check endpoint. Pinged by cron-job.org to keep the free-tier instance awake.

**Parameters:** None

**Response:**
```json
{"status": "ok"}
```

**Example:**
```
https://web-dlp-api.onrender.com/
```

---

### `GET /info`

Fetches video metadata without downloading. Returns title, duration, and all available formats.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `url` | Yes | Full video URL (YouTube, Vimeo, Twitter, etc.) |

**Response:**
```json
{
  "title": "Video Title",
  "duration": 240,
  "formats": [ ... ]
}
```

**Examples:**
```
https://web-dlp-api.onrender.com/info?url=https://www.youtube.com/watch?v=VIDEO_ID
https://web-dlp-api.onrender.com/info?url=https://vimeo.com/123456789
https://web-dlp-api.onrender.com/info?url=https://x.com/user/status/123456789
```

> Use this to inspect available format codes before passing a custom `format` to `/download`.

---

### `GET /download`

Downloads the video and streams it back as an MP4 file attachment.

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `url` | Yes | — | Full video URL |
| `format` | No | `bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best` | yt-dlp format selector |

**Response:** Binary file stream with `Content-Disposition: attachment` header.

**Examples:**

Download 720p MP4 (default — no `format` param needed):
```
https://web-dlp-api.onrender.com/download?url=https://www.youtube.com/watch?v=VIDEO_ID
```

Download 1080p:
```
https://web-dlp-api.onrender.com/download?url=https://www.youtube.com/watch?v=VIDEO_ID&format=bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]
```

Download 480p (lower bandwidth):
```
https://web-dlp-api.onrender.com/download?url=https://www.youtube.com/watch?v=VIDEO_ID&format=bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]
```

Download audio only (m4a):
```
https://web-dlp-api.onrender.com/download?url=https://www.youtube.com/watch?v=VIDEO_ID&format=bestaudio[ext=m4a]/bestaudio
```

Download best quality (no height limit):
```
https://web-dlp-api.onrender.com/download?url=https://www.youtube.com/watch?v=VIDEO_ID&format=bestvideo[ext=mp4]+bestaudio[ext=m4a]/best
```

Download by specific format code (use `/info` to find codes):
```
https://web-dlp-api.onrender.com/download?url=https://www.youtube.com/watch?v=VIDEO_ID&format=22
```

> **Note:** Output is always merged to `.mp4` regardless of format selector.

---

### `GET /thumbnail`

Returns the video's thumbnail image directly (proxied through the server).

| Parameter | Required | Description |
|-----------|----------|-------------|
| `url` | Yes | Full video URL |

**Response:** Image file (`image/jpeg`, `image/png`, or `image/webp`) with `Content-Disposition: inline` header.

**Examples:**
```
https://web-dlp-api.onrender.com/thumbnail?url=https://www.youtube.com/watch?v=VIDEO_ID
https://web-dlp-api.onrender.com/thumbnail?url=https://vimeo.com/123456789
```

> Can be used directly in HTML: `<img src="https://web-dlp-api.onrender.com/thumbnail?url=...">`

---

### `GET /debug-cookies`

Inspects the `cookies.txt` file inside the running container. Useful for verifying cookie deployment.

**Parameters:** None

**Response:**
```json
{
  "status": "exists",
  "size": 12345,
  "first_lines": ["# Netscape HTTP Cookie File", "..."],
  "readable": true
}
```

If missing:
```json
{"status": "missing", "path": "/app/cookies.txt"}
```

**Example:**
```
https://web-dlp-api.onrender.com/debug-cookies
```

---

### Supported Sites

This API supports **any site** that [yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md), including:
YouTube, Vimeo, Twitter/X, Reddit, TikTok, Instagram, SoundCloud, Twitch, Dailymotion, and 1000+ more.

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
