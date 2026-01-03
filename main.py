from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import uuid

app = FastAPI()

# Izinkan Frontend mengakses Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Backend is running with FFmpeg"}

@app.get("/download")
def download_media(url: str, type: str, codec: str):
    # Buat nama file unik sementara
    file_id = str(uuid.uuid4())
    output_template = f"downloads/{file_id}.%(ext)s"
    
    # Konfigurasi yt-dlp
    ydl_opts = {
        'outtmpl': output_template,
        'addmetadata': True,
        'writethumbnail': True,
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0', # Memaksa penggunaan IPv4
        'referer': 'https://www.youtube.com/',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

    # Logika Video
    if type == 'video':
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        # Konversi Kodek Video
        if codec == 'h264':
            ydl_opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
        elif codec == 'vp9':
            ydl_opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'webm'}]
        # Catatan: AV1/H265 membutuhkan waktu transcoding lama, mungkin timeout di free tier
        
    # Logika Audio
    elif type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': codec, # mp3, wav, aac
            'preferredquality': '192',
        },
        {'key': 'FFmpegMetadata'}, # Embed metadata audio
        ]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Koreksi ekstensi file jika diubah oleh post-processor
            if type == 'audio':
                base, _ = os.path.splitext(filename)
                filename = f"{base}.{codec}"
            elif type == 'video' and codec == 'vp9':
                 base, _ = os.path.splitext(filename)
                 filename = f"{base}.webm"
            elif type == 'video' and codec == 'h264':
                 base, _ = os.path.splitext(filename)
                 filename = f"{base}.mp4"

            return FileResponse(path=filename, filename=os.path.basename(filename), media_type='application/octet-stream')

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)