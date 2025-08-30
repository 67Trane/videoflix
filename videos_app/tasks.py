import subprocess
from pathlib import Path

from django.conf import settings
from .models import Video

ALLOWED_RESOLUTIONS = {"480p", "720p", "1080p"}

def convert_to_hls(source: str) -> str:
    src = Path(source)
    out_dir = src.parent / f"{src.stem}_hls_480p"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    playlist = out_dir / "index.m3u8"
    segments = out_dir / "seg_%03d.ts"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-vf", "scale=-2:480",
        "-c:v", "libx264", "-crf", "23", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k",
        "-hls_time", "6",
        "-hls_playlist_type", "vod",
        "-hls_flags", "independent_segments",
        "-hls_segment_filename", str(segments),
        str(playlist),
    ]
    
    subprocess.run(cmd, check=True)
    return str(playlist)


def extract_thumbnail(src_path: str, out_path: str | Path, second: float = 2.0, max_width: int = 480) -> Path:
    src = Path(src_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(second),      # Position im Video (vor -i = schneller)
        "-i", str(src),
        "-frames:v", "1",        # genau 1 Frame
        "-vf", f"scale='min({max_width},iw)':-2:force_original_aspect_ratio=decrease",
        "-q:v", "2",             # JPG-Qualität (2 = hoch, 31 = schlecht)
        str(out),
    ]
    
    subprocess.run(cmd, check=True)
    return out

def get_hls_dir(video: Video, resolution:str) -> Path:
    if resolution not in ALLOWED_RESOLUTIONS:
        raise ValueError("unsupported resolution")
    
    source_absolute_path = Path(video.video_file.path)
    
    suffix = {
        "480p": "_hls_480p",
        "720p": "_hls_720p",
        "1080p": "_hls_1080p"
    }[resolution]
    
    hls_dir = Path(settings.MEDIA_ROOT) /"videos"/ f"{source_absolute_path.stem}{suffix}"
    return hls_dir