from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
import yt_dlp
import tempfile
import os
import shutil
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

app = FastAPI()


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
    ydl_opts = {"quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {"title": info.get("title"), "duration": info.get("duration"), "formats": info.get("formats")}
        except Exception as e:
            raise HTTPException(400, detail=str(e))


@app.get("/download")
async def download(url: str = Query(...), format_id: str = Query("best", alias="format")):
    validate_url(url)

    temp_dir = tempfile.mkdtemp()
    outtmpl = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "format": format_id,
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "continuedl": True,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
