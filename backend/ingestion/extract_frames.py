"""Extract frames from a video at regular intervals using FFmpeg."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FRAME_INTERVAL_SECONDS


def extract_frames(
    video_path: str | Path,
    output_dir: str | Path,
    interval: int = FRAME_INTERVAL_SECONDS,
) -> list[Path]:
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    output_pattern = str(output_dir / "frame_%04d.jpg")

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"fps=1/{interval}",
        "-q:v", "2",
        "-y",
        output_pattern,
    ]

    print(f"Extracting frames every {interval}s from: {video_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg frame extraction failed:\n{result.stderr}")

    frames = sorted(output_dir.glob("frame_*.jpg"))
    print(f"Extracted {len(frames)} frames to {output_dir}")
    return frames


if __name__ == "__main__":
    from config import VIDEO_DATA_DIR, PROCESSED_DIR

    videos = {
        "part1": VIDEO_DATA_DIR / "GRC Practical Approach - Part 1 Introduction - Prabh Nair (720p, h264).mp4",
        "part2": VIDEO_DATA_DIR / "GRC Practical Approach - Part 2 Governance - Prabh Nair (720p, h264).mp4",
    }

    for part, video in videos.items():
        if video.exists():
            frames_dir = PROCESSED_DIR / part / "frames"
            extract_frames(video, frames_dir)
        else:
            print(f"Skipping {part}: {video.name} not found")
