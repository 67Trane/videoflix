import subprocess
from pathlib import Path

from django.conf import settings
from .models import Video

# Supported output resolutions for HLS transcoding
ALLOWED_RESOLUTIONS = {"480p", "720p", "1080p"}


def convert_to_hls(source: str) -> str:
    """Convert a video file into HLS format with multiple renditions.

    Generates HLS playlists and segments for 480p, 720p, and 1080p resolutions.
    Uses ffmpeg with H.264 (libx264) and AAC encoding.

    Args:
        source (str): Absolute path to the input video file.

    Returns:
        str: Path to the last generated playlist file (index.m3u8).
    """
    src = Path(source)
    RENDITIONS = {
        "480p": {"height": 480, "v_bitrate": "1200k", "a_bitrate": "128k"},
        "720p": {"height": 720, "v_bitrate": "2800k", "a_bitrate": "128k"},
        "1080p": {"height": 1080, "v_bitrate": "5000k", "a_bitrate": "192k"},
    }

    for res, cfg in RENDITIONS.items():
        out_dir = src.parent / f"{src.stem}_hls_{res}"
        out_dir.mkdir(parents=True, exist_ok=True)
        playlist = out_dir / "index.m3u8"
        segments = out_dir / "%03d.ts"

        # ffmpeg command for HLS conversion
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            f"scale=-2:{cfg['height']}",
            "-c:v",
            "libx264",
            "-crf",
            "23",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            "-b:a",
            cfg["a_bitrate"],
            "-hls_time",
            "6",
            "-hls_playlist_type",
            "vod",
            "-hls_flags",
            "independent_segments",
            "-hls_segment_filename",
            str(segments),
            str(playlist),
        ]
        subprocess.run(cmd, check=True)

    return str(playlist)


def extract_thumbnail(
    video_id: int,
    src_path: str,
    thumb_rel: str,
    second: float = 2.0,
    max_width: int = 480,
) -> Path:
    """Extract a single thumbnail image from a video.

    Uses ffmpeg to capture one frame at the given timestamp and stores it
    as a JPEG file. Updates the Video model with the thumbnail path.

    Args:
        video_id (int): ID of the Video model instance to update.
        src_path (str): Path to the source video file.
        thumb_rel (str): Relative path (within MEDIA_ROOT) for saving the thumbnail.
        second (float, optional): Timestamp (in seconds) to capture the frame.
                                  Defaults to 2.0.
        max_width (int, optional): Maximum width of the thumbnail (aspect ratio preserved).
                                   Defaults to 480.

    Returns:
        Path: Absolute path of the generated thumbnail image.
    """
    thumb_abs = Path(settings.MEDIA_ROOT) / thumb_rel
    print("Absolute thumbnail path:", thumb_abs)
    thumb_abs.parent.mkdir(parents=True, exist_ok=True)

    # ffmpeg command for extracting a single frame
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(second),  # seek position before input (faster)
        "-i",
        str(src_path),
        "-frames:v",
        "1",  # extract exactly one frame
        "-vf",
        f"scale=min({max_width},iw):-2:force_original_aspect_ratio=decrease",
        "-q:v",
        "2",  # JPEG quality (2 = high, 31 = worst)
        str(thumb_abs),
    ]

    subprocess.run(cmd, check=True)

    # Update Video model with thumbnail reference
    video = Video.objects.get(pk=video_id)
    video.thumbnail_url.name = thumb_rel
    video.save(update_fields=["thumbnail_url"])

    return thumb_abs


def get_hls_dir(video: Video, resolution: str) -> Path:
    """Return the directory path containing HLS segments for a given resolution.

    Args:
        video (Video): Video model instance.
        resolution (str): Desired resolution (must be in ALLOWED_RESOLUTIONS).

    Raises:
        ValueError: If the resolution is not supported.

    Returns:
        Path: Directory path of the HLS output files for the given video.
    """
    if resolution not in ALLOWED_RESOLUTIONS:
        raise ValueError("unsupported resolution")

    source_absolute_path = Path(video.video_file.path)
    suffix = {"480p": "_hls_480p", "720p": "_hls_720p", "1080p": "_hls_1080p"}[
        resolution
    ]

    hls_dir = (
        Path(settings.MEDIA_ROOT) / "videos" / f"{source_absolute_path.stem}{suffix}"
    )
    return hls_dir
