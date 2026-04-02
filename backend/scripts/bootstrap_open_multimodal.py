"""
Bootstrap a trainable multimodal CSV from public web assets, then train.

This script is intentionally pragmatic for engineering integration:
- Downloads open audio/image/video files from public GitHub repositories.
- Extracts lightweight modality statistics.
- Builds the CSV format required by scripts.train_deep_multimodal.
- Optionally launches training and produces a deep checkpoint.

Notes:
- This is for pipeline bootstrapping and integration verification.
- It is NOT a clinically validated dataset.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import shutil
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None


DOMAIN_ORDER = ["memory", "orientation", "language", "attention", "visuospatial", "executive"]

QUESTIONNAIRE_KEYS = [
    "available",
    "quality",
    "choice_accuracy",
    "avg_score",
    "scale_mean",
    "coverage",
    "sample_count",
]
VOICE_KEYS = [
    "available",
    "quality",
    "word_richness",
    "avg_words",
    "avg_duration_sec",
    "pause_density",
    "audio_file_ratio",
    "sample_count",
]
DRAWING_KEYS = [
    "available",
    "quality",
    "structure_score",
    "avg_strokes",
    "avg_points",
    "image_ratio",
    "sample_count",
]
BEHAVIOR_KEYS = [
    "available",
    "quality",
    "avg_reaction_ms",
    "std_reaction_ms",
    "slow_ratio",
    "fast_ratio",
    "stability_score",
    "sample_count",
]

QUESTIONNAIRE_PROMPTS = [
    "今天是星期几，你现在在什么地方？",
    "请复述这三个词：苹果、钥匙、河流。",
    "从100开始每次减7，连续说五次。",
    "请说出一分钟内尽可能多的动物名称。",
    "请描述一下你今天早餐吃了什么。",
    "请解释一下为什么要按时服药和复诊。",
    "请按顺序复述数字 4-1-8-3-6。",
    "请说出当前季节和大致日期。",
    "请描述你从家到社区卫生站的路线。",
    "请说出两种记忆力变差时常见的生活表现。",
]

SOURCE_APIS = {
    "audio": "https://api.github.com/repos/Jakobovski/free-spoken-digit-dataset/contents/recordings?per_page=1000",
    "vision": "https://api.github.com/repos/opencv/opencv/contents/samples/data?per_page=1000",
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _safe_mean(values: Iterable[float], default: float = 0.0) -> float:
    arr = [float(v) for v in values]
    if not arr:
        return default
    return float(np.mean(np.asarray(arr, dtype=np.float32)))


def _http_json(url: str, timeout: int = 40) -> object:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "mindguard-bootstrap/1.0",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download(url: str, target: Path, timeout: int = 40) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mindguard-bootstrap/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp, target.open("wb") as out:
            shutil.copyfileobj(resp, out)
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _sample_remote_files(
    api_url: str,
    allowed_exts: Sequence[str],
    limit: int,
    rng: random.Random,
) -> List[Dict[str, str]]:
    payload = _http_json(api_url)
    items = payload if isinstance(payload, list) else []
    allowed = tuple(ext.lower() for ext in allowed_exts)
    candidates = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        download_url = str(item.get("download_url", ""))
        if not name or not download_url:
            continue
        if name.lower().endswith(allowed):
            candidates.append({"name": name, "download_url": download_url})

    if not candidates:
        return []
    if len(candidates) <= limit:
        return candidates
    return rng.sample(candidates, limit)


def _read_wave(path: Path) -> Optional[Dict[str, float]]:
    try:
        with wave.open(str(path), "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            frames = wf.readframes(n_frames)
    except Exception:
        return None

    if framerate <= 0 or n_frames <= 0 or not frames:
        return None

    if sampwidth == 2:
        arr = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        full_scale = 32768.0
    elif sampwidth == 1:
        arr = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0
        full_scale = 128.0
    else:
        return None

    if n_channels > 1:
        arr = arr.reshape(-1, n_channels).mean(axis=1)

    duration = float(n_frames) / float(framerate)
    if duration <= 0:
        return None

    amp = float(np.mean(np.abs(arr)) / full_scale)
    norm = arr / full_scale
    sign = np.sign(norm)
    zcr = float(np.mean(sign[1:] != sign[:-1])) if sign.shape[0] > 1 else 0.0
    silence_ratio = float(np.mean(np.abs(norm) < 0.02))

    return {
        "duration_sec": duration,
        "amplitude": _clamp(amp, 0.0, 1.0),
        "zcr": _clamp(zcr, 0.0, 1.0),
        "silence_ratio": _clamp(silence_ratio, 0.0, 1.0),
    }


def _image_gray(path: Path) -> Optional[np.ndarray]:
    if cv2 is not None:
        # Use imdecode to avoid Windows unicode-path issues in cv2.imread.
        try:
            data = np.fromfile(str(path), dtype=np.uint8)
            if data.size > 0:
                img = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    return img
        except Exception:
            pass
    if Image is not None:
        try:
            return np.asarray(Image.open(path).convert("L"))
        except Exception:
            return None
    return None


def _extract_image_features(path: Path) -> Optional[Dict[str, float]]:
    gray = _image_gray(path)
    if gray is None or gray.size == 0:
        return None

    h, w = gray.shape[:2]
    if h <= 0 or w <= 0:
        return None

    if cv2 is not None:
        edges = cv2.Canny(gray, 80, 180)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    else:
        gy = np.diff(gray.astype(np.float32), axis=0, prepend=gray[:1, :])
        gx = np.diff(gray.astype(np.float32), axis=1, prepend=gray[:, :1])
        grad = np.abs(gx) + np.abs(gy)
        edges = (grad > np.percentile(grad, 75)).astype(np.uint8) * 255
        lap_var = float(np.var(gx - gy))

    edge_density = float(np.mean(edges > 0))
    points = float(np.sum(edges > 0))
    strokes = float(max(3.0, min(60.0, points / 1500.0)))
    quality = _clamp(0.35 + math.log1p(max(lap_var, 0.0)) / 12.0, 0.0, 1.0)
    ratio = float(w) / float(h)

    return {
        "quality": quality,
        "structure_score": _clamp(edge_density * 1.8, 0.0, 1.0),
        "avg_strokes": strokes,
        "avg_points": _clamp(points, 0.0, 2000.0),
        "image_ratio": _clamp(ratio / 2.0, 0.0, 1.0),
    }


def _extract_video_features(path: Path) -> Optional[Dict[str, float]]:
    if cv2 is None:
        size_hint = float(path.stat().st_size)
        motion = _clamp(math.log1p(size_hint) / 20.0, 0.05, 0.85)
        return {
            "motion_mean": motion,
            "motion_std": 0.10,
            "frame_count": 90.0,
            "fps": 25.0,
            "duration_sec": 3.6,
        }

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return None

    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if fps <= 1e-6:
        fps = 25.0

    prev = None
    motions: List[float] = []
    frame_count = 0
    max_frames = 220

    while frame_count < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev is not None:
            diff = cv2.absdiff(gray, prev)
            motions.append(float(np.mean(diff) / 255.0))
        prev = gray

    cap.release()
    if frame_count <= 2:
        return None

    motion_mean = _safe_mean(motions, 0.18)
    motion_std = float(np.std(np.asarray(motions, dtype=np.float32))) if motions else 0.08
    duration = frame_count / fps

    return {
        "motion_mean": _clamp(motion_mean, 0.0, 1.0),
        "motion_std": _clamp(motion_std, 0.0, 1.0),
        "frame_count": float(frame_count),
        "fps": fps,
        "duration_sec": duration,
    }


def _class_profile(cls: int) -> Dict[str, float]:
    if cls == 0:  # NC
        return {
            "q_quality": 0.90,
            "choice_accuracy": 0.88,
            "scale_mean": 0.84,
            "voice_quality_bias": 0.10,
            "drawing_bias": 0.08,
            "behavior_slow_bias": -0.10,
        }
    if cls == 1:  # MCI
        return {
            "q_quality": 0.68,
            "choice_accuracy": 0.62,
            "scale_mean": 0.60,
            "voice_quality_bias": -0.02,
            "drawing_bias": -0.05,
            "behavior_slow_bias": 0.08,
        }
    # AD
    return {
        "q_quality": 0.45,
        "choice_accuracy": 0.38,
        "scale_mean": 0.36,
        "voice_quality_bias": -0.14,
        "drawing_bias": -0.16,
        "behavior_slow_bias": 0.18,
    }


def _domain_targets(cls: int, rng: random.Random) -> Dict[str, float]:
    base = {
        0: [8.8, 8.5, 8.2, 8.0, 8.2, 8.3],
        1: [6.3, 6.1, 5.8, 5.6, 5.8, 5.7],
        2: [3.9, 3.7, 3.3, 3.4, 3.2, 3.1],
    }[cls]
    out: Dict[str, float] = {}
    for domain, value in zip(DOMAIN_ORDER, base):
        jitter = rng.uniform(-0.45, 0.45)
        out[f"target_domain_{domain}"] = round(_clamp(value + jitter, 0.0, 10.0), 3)
    return out


def _extract_audio_catalog(audio_dir: Path) -> List[Dict[str, float]]:
    items: List[Dict[str, float]] = []
    for path in sorted(audio_dir.glob("*.wav")):
        feat = _read_wave(path)
        if feat is None:
            continue
        items.append(feat)
    return items


def _extract_image_catalog(image_dir: Path) -> List[Dict[str, float]]:
    items: List[Dict[str, float]] = []
    for path in sorted(image_dir.iterdir()):
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
            continue
        feat = _extract_image_features(path)
        if feat is None:
            continue
        items.append(feat)
    return items


def _extract_video_catalog(video_dir: Path) -> List[Dict[str, float]]:
    items: List[Dict[str, float]] = []
    for path in sorted(video_dir.iterdir()):
        if path.suffix.lower() not in {".avi", ".mp4", ".mov", ".webm", ".mkv"}:
            continue
        feat = _extract_video_features(path)
        if feat is None:
            continue
        items.append(feat)
    return items


def _download_modalities(
    root: Path,
    rng: random.Random,
    audio_count: int,
    image_count: int,
    video_count: int,
) -> Dict[str, int]:
    audio_dir = root / "raw" / "audio"
    image_dir = root / "raw" / "image"
    video_dir = root / "raw" / "video"
    audio_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    audio_files = _sample_remote_files(
        SOURCE_APIS["audio"],
        allowed_exts=[".wav"],
        limit=audio_count,
        rng=rng,
    )
    vision_files = _sample_remote_files(
        SOURCE_APIS["vision"],
        allowed_exts=[".jpg", ".jpeg", ".png", ".bmp", ".avi", ".mp4", ".mov", ".webm"],
        limit=max(image_count + video_count, 40),
        rng=rng,
    )
    image_files = [it for it in vision_files if it["name"].lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))][:image_count]
    video_files = [it for it in vision_files if it["name"].lower().endswith((".avi", ".mp4", ".mov", ".webm"))][:video_count]

    stats = {"audio": 0, "image": 0, "video": 0}
    for item in audio_files:
        if _download(item["download_url"], audio_dir / item["name"]):
            stats["audio"] += 1
    for item in image_files:
        if _download(item["download_url"], image_dir / item["name"]):
            stats["image"] += 1
    for item in video_files:
        if _download(item["download_url"], video_dir / item["name"]):
            stats["video"] += 1
    return stats


def _build_rows(
    sample_count: int,
    audio_catalog: List[Dict[str, float]],
    image_catalog: List[Dict[str, float]],
    video_catalog: List[Dict[str, float]],
    rng: random.Random,
) -> List[Dict[str, float]]:
    if not audio_catalog:
        raise RuntimeError("No usable audio samples found after download.")
    if not image_catalog:
        raise RuntimeError("No usable image samples found after download.")
    if not video_catalog:
        raise RuntimeError("No usable video samples found after download.")

    rows: List[Dict[str, float]] = []
    for i in range(sample_count):
        cls = i % 3
        profile = _class_profile(cls)

        audio = audio_catalog[i % len(audio_catalog)]
        image = image_catalog[(i * 3) % len(image_catalog)]
        video = video_catalog[(i * 5) % len(video_catalog)]
        prompt = QUESTIONNAIRE_PROMPTS[(i * 7) % len(QUESTIONNAIRE_PROMPTS)]
        words = [w for w in prompt.replace("，", " ").replace("。", " ").split() if w]
        unique_ratio = len(set(words)) / max(1, len(words))

        questionnaire_quality = _clamp(profile["q_quality"] + rng.uniform(-0.06, 0.06), 0.0, 1.0)
        choice_accuracy = _clamp(profile["choice_accuracy"] + rng.uniform(-0.10, 0.10), 0.0, 1.0)
        scale_mean = _clamp(profile["scale_mean"] + rng.uniform(-0.08, 0.08), 0.0, 1.0)
        avg_score = _clamp((choice_accuracy * 0.65 + scale_mean * 0.35) + rng.uniform(-0.04, 0.04), 0.0, 1.0)

        voice_quality = _clamp(0.45 + audio["amplitude"] * 0.55 + profile["voice_quality_bias"], 0.0, 1.0)
        pause_density = _clamp(audio["silence_ratio"] + (0.08 if cls == 2 else 0.0), 0.0, 1.0)
        avg_words = _clamp(8.0 + len(words) * (3.5 if cls == 0 else (2.6 if cls == 1 else 2.0)) + rng.uniform(-2.0, 2.0), 4.0, 40.0)
        word_richness = _clamp(unique_ratio * (1.0 if cls == 0 else (0.88 if cls == 1 else 0.76)), 0.0, 1.0)

        drawing_quality = _clamp(image["quality"] + profile["drawing_bias"], 0.0, 1.0)
        structure_score = _clamp(image["structure_score"] + (0.06 if cls == 0 else (-0.06 if cls == 2 else 0.0)), 0.0, 1.0)
        avg_strokes = _clamp(image["avg_strokes"] + (6.0 if cls == 0 else (-6.0 if cls == 2 else 0.0)), 5.0, 60.0)
        avg_points = _clamp(image["avg_points"] + (120.0 if cls == 0 else (-120.0 if cls == 2 else 0.0)), 120.0, 1800.0)

        motion = video["motion_mean"]
        motion_std = video["motion_std"]
        avg_reaction_ms = _clamp((58000.0 - motion * 33000.0) + profile["behavior_slow_bias"] * 18000.0 + rng.uniform(-3000, 3000), 600.0, 60000.0)
        std_reaction_ms = _clamp(4500.0 + motion_std * 19000.0 + (2200.0 if cls == 2 else 0.0), 500.0, 40000.0)
        slow_ratio = _clamp(0.30 + (1.0 - motion) * 0.40 + (0.06 if cls == 2 else (-0.05 if cls == 0 else 0.0)), 0.0, 1.0)
        fast_ratio = _clamp(0.15 + motion * 0.50 + (0.06 if cls == 0 else (-0.05 if cls == 2 else 0.0)), 0.0, 1.0)
        stability_score = _clamp(0.75 - motion_std * 0.55 + (0.08 if cls == 0 else (-0.08 if cls == 2 else 0.0)), 0.0, 1.0)
        behavior_quality = _clamp(0.45 + stability_score * 0.45, 0.0, 1.0)

        row: Dict[str, float] = {
            "target_class": cls,
            "questionnaire_available": 1.0,
            "questionnaire_quality": round(questionnaire_quality, 6),
            "questionnaire_choice_accuracy": round(choice_accuracy, 6),
            "questionnaire_avg_score": round(avg_score, 6),
            "questionnaire_scale_mean": round(scale_mean, 6),
            "questionnaire_coverage": round(_clamp(0.74 + rng.uniform(-0.12, 0.14), 0.0, 1.0), 6),
            "questionnaire_sample_count": round(_clamp(8.0 + rng.uniform(0.0, 12.0), 1.0, 20.0), 6),
            "voice_available": 1.0,
            "voice_quality": round(voice_quality, 6),
            "voice_word_richness": round(word_richness, 6),
            "voice_avg_words": round(avg_words, 6),
            "voice_avg_duration_sec": round(_clamp(audio["duration_sec"] + rng.uniform(0.0, 1.8), 1.2, 90.0), 6),
            "voice_pause_density": round(pause_density, 6),
            "voice_audio_file_ratio": 1.0,
            "voice_sample_count": round(_clamp(3.0 + rng.uniform(0.0, 7.0), 1.0, 10.0), 6),
            "drawing_available": 1.0,
            "drawing_quality": round(drawing_quality, 6),
            "drawing_structure_score": round(structure_score, 6),
            "drawing_avg_strokes": round(avg_strokes, 6),
            "drawing_avg_points": round(avg_points, 6),
            "drawing_image_ratio": round(image["image_ratio"], 6),
            "drawing_sample_count": round(_clamp(2.0 + rng.uniform(0.0, 7.0), 1.0, 10.0), 6),
            "behavior_available": 1.0,
            "behavior_quality": round(behavior_quality, 6),
            "behavior_avg_reaction_ms": round(avg_reaction_ms, 6),
            "behavior_std_reaction_ms": round(std_reaction_ms, 6),
            "behavior_slow_ratio": round(slow_ratio, 6),
            "behavior_fast_ratio": round(fast_ratio, 6),
            "behavior_stability_score": round(stability_score, 6),
            "behavior_sample_count": round(_clamp(video["frame_count"] / 20.0, 1.0, 20.0), 6),
        }
        row.update(_domain_targets(cls, rng))
        rows.append(row)
    return rows


def _fieldnames() -> List[str]:
    fields = ["target_class"]
    fields.extend([f"target_domain_{x}" for x in DOMAIN_ORDER])
    fields.extend([f"questionnaire_{x}" for x in QUESTIONNAIRE_KEYS])
    fields.extend([f"voice_{x}" for x in VOICE_KEYS])
    fields.extend([f"drawing_{x}" for x in DRAWING_KEYS])
    fields.extend([f"behavior_{x}" for x in BEHAVIOR_KEYS])
    return fields


def _write_csv(rows: List[Dict[str, float]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_fieldnames())
        writer.writeheader()
        writer.writerows(rows)


def _train_if_requested(
    csv_path: Path,
    checkpoint: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    skip_train: bool,
) -> str:
    if skip_train:
        return "skipped_by_flag"

    try:
        import torch  # noqa: F401
    except Exception:
        return "skipped_torch_missing"

    from scripts.train_deep_multimodal import train

    train(
        input_csv=csv_path,
        output_ckpt=checkpoint,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
    )
    return "trained"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap open multimodal data and train deep model.")
    parser.add_argument("--root", default="../data/open_multimodal_seed", help="Raw asset root directory.")
    parser.add_argument("--output-csv", default="../data/deep_train_auto.csv", help="Generated train CSV path.")
    parser.add_argument("--checkpoint", default="models/deep_multimodal_fusion.pt", help="Output checkpoint path.")
    parser.add_argument("--samples", type=int, default=180, help="Generated sample count.")
    parser.add_argument("--audio-count", type=int, default=120, help="How many remote wav files to download.")
    parser.add_argument("--image-count", type=int, default=48, help="How many remote images to download.")
    parser.add_argument("--video-count", type=int, default=4, help="How many remote videos to download.")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-train", action="store_true", help="Only generate CSV, do not train.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    root = Path(args.root).resolve()
    output_csv = Path(args.output_csv).resolve()
    checkpoint = Path(args.checkpoint).resolve()

    print(f"[1/4] downloading open multimodal assets -> {root}")
    stats = _download_modalities(
        root=root,
        rng=rng,
        audio_count=max(8, args.audio_count),
        image_count=max(8, args.image_count),
        video_count=max(1, args.video_count),
    )
    print(f"downloaded: audio={stats['audio']} image={stats['image']} video={stats['video']}")

    print("[2/4] extracting lightweight modality features")
    audio_catalog = _extract_audio_catalog(root / "raw" / "audio")
    image_catalog = _extract_image_catalog(root / "raw" / "image")
    video_catalog = _extract_video_catalog(root / "raw" / "video")
    print(
        "usable assets: "
        f"audio={len(audio_catalog)} image={len(image_catalog)} video={len(video_catalog)}"
    )

    print("[3/4] building train csv for deep multimodal model")
    rows = _build_rows(
        sample_count=max(32, args.samples),
        audio_catalog=audio_catalog,
        image_catalog=image_catalog,
        video_catalog=video_catalog,
        rng=rng,
    )
    _write_csv(rows, output_csv)
    print(f"csv saved: {output_csv} (rows={len(rows)})")

    print("[4/4] train checkpoint")
    train_status = _train_if_requested(
        csv_path=output_csv,
        checkpoint=checkpoint,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        skip_train=args.skip_train,
    )
    if train_status == "trained":
        print(f"checkpoint saved: {checkpoint}")
    elif train_status == "skipped_torch_missing":
        print("torch not found in current python env. dataset is ready; install torch then rerun without --skip-train.")
    else:
        print("training skipped.")

    manifest = {
        "raw_root": str(root),
        "output_csv": str(output_csv),
        "checkpoint": str(checkpoint),
        "downloaded": stats,
        "usable_assets": {
            "audio": len(audio_catalog),
            "image": len(image_catalog),
            "video": len(video_catalog),
        },
        "rows": len(rows),
        "train_status": train_status,
    }
    manifest_path = output_csv.parent / "deep_train_auto_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"manifest saved: {manifest_path}")


if __name__ == "__main__":
    main()
