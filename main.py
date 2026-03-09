from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse, Response
import yt_dlp
import httpx
import tempfile
import os
import shutil
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

app = FastAPI()


@app.get("/")
async def health():
    """Health-check endpoint – pinged by cron-job.org to keep the free-tier instance awake."""
    return {"status": "ok"}


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, detail="Only http and https URLs are allowed.")
    if not parsed.netloc:
        raise HTTPException(400, detail="Invalid URL: missing host.")
    return url


@app.get("/info")
async def get_info(url: str = Query(...)):
    validate_url(url)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "cookies": "/app/cookies.txt",          # ← must be here
    }   
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {"title": info.get("title"), "duration": info.get("duration"), "formats": info.get("formats")}
        except Exception as e:
            raise HTTPException(400, detail=str(e))


DEFAULT_FORMAT = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"


@app.get("/download")
async def download(url: str = Query(...), format_id: str = Query(DEFAULT_FORMAT, alias="format")):
    validate_url(url)

    temp_dir = tempfile.mkdtemp()
    outtmpl = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": format_id,
        "merge_output_format": "mp4",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "continuedl": True,
        "cookies": "/app/cookies.txt",  # path inside container
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "referer": "https://www.youtube.com/",
        "sleep_interval": 3,          # seconds between requests
        "max_sleep_interval": 10,
    }
   
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            path = Path(filename)

        media_type, _ = mimetypes.guess_type(path.name)
        if not media_type:
            media_type = "application/octet-stream"

        def iterfile():
            try:
                with open(path, "rb") as f:
                    while chunk := f.read(8192):
                        yield chunk
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{path.name.replace(chr(34), "_")}"'}
        )
    except HTTPException:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(500, detail=str(e))


@app.get("/thumbnail")
async def thumbnail(url: str = Query(...)):
    """Return the video thumbnail image. Uses yt-dlp to find the best thumbnail URL, then proxies it."""
    validate_url(url)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "cookies": "/app/cookies.txt",
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise HTTPException(400, detail=str(e))

    thumb_url = info.get("thumbnail")
    if not thumb_url:
        thumbnails = info.get("thumbnails") or []
        if thumbnails:
            thumb_url = thumbnails[-1].get("url")
    if not thumb_url:
        raise HTTPException(404, detail="No thumbnail found for this video.")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(thumb_url, timeout=15)
        if resp.status_code != 200:
            raise HTTPException(502, detail="Failed to fetch thumbnail from upstream.")

    content_type = resp.headers.get("content-type", "image/jpeg")
    ext = "jpg"
    if "png" in content_type:
        ext = "png"
    elif "webp" in content_type:
        ext = "webp"

    title = re.sub(r'[^\w\s-]', '', info.get("title", "thumbnail")).strip()
    filename = f"{title}.{ext}"

    return Response(
        content=resp.content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@app.get("/debug-cookies")
async def debug_cookies():
    import os
  
    path = "/app/cookies.txt"
    if not os.path.exists(path):
        return {"status": "missing", "path": path}
    try:
        with open(path, "r") as f:
            first_lines = f.readlines()[:5]
        return {
            "status": "exists",
            "size": os.path.getsize(path),
            "first_lines": first_lines,
            "readable": os.access(path, os.R_OK)
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
        
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
