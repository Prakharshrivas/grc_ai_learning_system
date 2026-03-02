"""Extract audio track from a video using FFmpeg."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def extract_audio(
    video_path: str | Path,
    output_dir: str | Path,
    filename: str = "audio.mp3",
) -> Path:
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    output_path = output_dir / filename

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "2",
        "-y",
        str(output_path),
    ]

    print(f"Extracting audio from: {video_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0 or not output_path.exists():
        print("Standard extraction failed, trying with error tolerance...")
        cmd_fallback = [
            "ffmpeg",
            "-err_detect", "ignore_err",
            "-i", str(video_path),
            "-vn",
            "-acodec", "libmp3lame",
            "-q:a", "2",
            "-y",
            str(output_path),
        ]
        result = subprocess.run(cmd_fallback, capture_output=True, text=True)
        if not output_path.exists():
            raise RuntimeError(f"FFmpeg audio extraction failed:\n{result.stderr}")

    print(f"Audio saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    from config import VIDEO_DATA_DIR, PROCESSED_DIR

    videos = {
        "part1": VIDEO_DATA_DIR / "GRC Practical Approach - Part 1 Introduction - Prabh Nair (720p, h264).mp4",
        "part2": VIDEO_DATA_DIR / "GRC Practical Approach - Part 2 Governance - Prabh Nair (720p, h264).mp4",
    }

    for part, video in videos.items():
        if video.exists():
            extract_audio(video, PROCESSED_DIR / part)
        else:
            print(f"Skipping {part}: {video.name} not found")
