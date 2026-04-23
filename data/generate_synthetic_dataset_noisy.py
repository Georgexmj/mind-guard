import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(20260422 + 99)

root = Path(r"D:\张家界学院材料\竞赛\竞赛项目\基于多模态交互的社区老年认知障碍早期筛查与干预系统")
out_dir = root / "data" / "synthetic_multimodal_dataset_v2_noisy"
out_dir.mkdir(parents=True, exist_ok=True)

N = 220
classes = (
    ["normal"] * 77 +
    ["mci_risk"] * 88 +
    ["high_risk"] * 55
)
random.shuffle(classes)

start_date = date(2026, 1, 1)
communities = ["C001", "C002", "C003", "C004", "C005", "C006", "C007", "C008"]
# 方言重：普通话占比下降
language_pool = ["xiang", "xiang", "southwest_mandarin", "southwest_mandarin", "mandarin"]
devices = ["tablet", "phone", "phone"]

master_rows, voice_rows, drawing_rows, behavior_rows, questionnaire_rows = [], [], [], [], []


def clip(x, low, high):
    return max(low, min(high, x))


def maybe_missing(v, p):
    return "" if random.random() < p else v


def infer_split(i):
    r = i % 10
    if r < 7:
        return "train"
    if r == 7:
        return "val"
    return "test"


def gen_scores(label, edu_years):
    if label == "normal":
        mmse = random.gauss(27.8, 1.6)
        moca = random.gauss(26.2, 1.9)
    elif label == "mci_risk":
        mmse = random.gauss(24.6, 1.9)
        moca = random.gauss(21.6, 2.3)
    else:
        mmse = random.gauss(19.8, 2.7)
        moca = random.gauss(16.0, 2.8)

    mmse = round(clip(mmse, 6, 30), 1)
    moca_raw = round(clip(moca, 2, 30), 1)
    moca_corr = round(clip(moca_raw + (1.0 if edu_years <= 0 else 0.0), 2, 30), 1)
    return mmse, moca_raw, moca_corr


def gen_domains(label):
    if label == "normal":
        base = random.uniform(0.66, 0.9)
    elif label == "mci_risk":
        base = random.uniform(0.45, 0.74)
    else:
        base = random.uniform(0.2, 0.56)

    n = lambda s=0.13: random.uniform(-s, s)
    return {
        "memory": clip(base + n(0.16), 0.03, 0.98),
        "attention": clip(base + n(), 0.03, 0.98),
        "language": clip(base + n(), 0.03, 0.98),
        "visuospatial": clip(base + n(0.18), 0.03, 0.98),
        "executive": clip(base + n(0.17), 0.03, 0.98),
        "orientation": clip(base + n(0.14), 0.03, 0.98),
    }

for i, label in enumerate(classes, start=1):
    sample_id = f"MGN2026_{i:04d}"
    participant_id = f"PN{110000+i}"
    session_id = f"SN{210000+i}"
    collect_date = (start_date + timedelta(days=random.randint(0, 120))).isoformat()

    community_id = random.choice(communities)
    age = int(clip(round(random.gauss(71.5 if label != 'normal' else 68.0, 6.4)), 60, 92))
    sex = random.choice(["F", "M"])
    edu_years = int(clip(round(random.gauss(6.4, 4.8)), 0, 16))
    device_type = random.choice(devices)
    dialect = random.choice(language_pool)

    mmse_raw, moca_raw, moca_corr = gen_scores(label, edu_years)

    # 更高标签噪声（15%）
    if random.random() < 0.15:
        doctor_label = random.choice([x for x in ["normal", "mci_risk", "high_risk"] if x != label])
        label_conf = round(random.uniform(0.5, 0.76), 2)
        retest_required = 1
    else:
        doctor_label = label
        label_conf = round(random.uniform(0.74, 0.96), 2)
        retest_required = 0

    consensus_label = label
    label_source = random.choices(["doctor+scale", "scale_only", "doctor_only"], weights=[0.76, 0.19, 0.05])[0]

    # 更高剔除率（8%）
    exclude_flag = 1 if random.random() < 0.08 else 0
    exclude_reason = random.choice(["low_audio_quality", "drawing_missing", "network_interrupt"]) if exclude_flag else ""

    master_rows.append({
        "sample_id": sample_id,
        "participant_id": participant_id,
        "session_id": session_id,
        "collect_date": collect_date,
        "community_id": community_id,
        "age": age,
        "sex": sex,
        "education_years": edu_years,
        "device_type": device_type,
        "language_dialect": dialect,
        "mmse_raw": maybe_missing(mmse_raw, 0.03),
        "moca_raw": maybe_missing(moca_raw, 0.05),
        "moca_edu_corrected": maybe_missing(moca_corr, 0.05),
        "doctor_label": doctor_label,
        "consensus_label": consensus_label,
        "label_source": label_source,
        "label_confidence": label_conf,
        "retest_required": retest_required,
        "exclude_flag": exclude_flag,
        "exclude_reason": exclude_reason,
        "split": infer_split(i),
    })

    domains = gen_domains(label)

    # Voice with more poor quality / missing
    if label == "normal":
        dur = clip(random.gauss(25, 8), 6, 60)
        wc = clip(random.gauss(45, 15), 5, 100)
        pauses = clip(random.gauss(3.8, 2.3), 0, 18)
        snr = clip(random.gauss(17, 5), 2, 30)
    elif label == "mci_risk":
        dur = clip(random.gauss(21, 9), 5, 58)
        wc = clip(random.gauss(31, 14), 3, 85)
        pauses = clip(random.gauss(5.9, 2.9), 0, 22)
        snr = clip(random.gauss(14, 5.5), 1, 28)
    else:
        dur = clip(random.gauss(17, 10), 4, 56)
        wc = clip(random.gauss(19, 12), 2, 65)
        pauses = clip(random.gauss(8.5, 3.5), 0, 26)
        snr = clip(random.gauss(11.5, 5.8), 0.5, 25)

    # 12% asr文本缺失，10%音频url缺失
    asr_text = "<synthetic_transcript_noisy>" if random.random() > 0.12 else ""
    audio_url = f"minio://cognitive-files/sessions/{session_id}/audio/{sample_id}.mp3" if random.random() > 0.10 else ""

    speech_rate = round(float(wc) / max(float(dur), 1.0), 2)
    voice_rows.append({
        "sample_id": sample_id,
        "voice_task_id": f"VT_{sample_id}",
        "duration_sec": maybe_missing(round(dur, 2), 0.06),
        "word_count": maybe_missing(int(round(wc)), 0.06),
        "speech_rate": maybe_missing(speech_rate, 0.08),
        "pause_count": maybe_missing(int(round(pauses)), 0.06),
        "snr_score": maybe_missing(round(snr, 2), 0.05),
        "asr_text": asr_text,
        "audio_url": audio_url,
    })

    # Drawing with higher missing rate
    if label == "normal":
        stroke = clip(random.gauss(16.5, 6), 3, 40)
        points = clip(random.gauss(270, 120), 25, 700)
        layout = clip(random.gauss(0.75, 0.15), 0.03, 1.0)
        angle = clip(random.gauss(0.72, 0.17), 0.02, 1.0)
    elif label == "mci_risk":
        stroke = clip(random.gauss(13.5, 6), 2, 36)
        points = clip(random.gauss(215, 115), 20, 640)
        layout = clip(random.gauss(0.56, 0.18), 0.02, 0.95)
        angle = clip(random.gauss(0.52, 0.2), 0.02, 0.9)
    else:
        stroke = clip(random.gauss(10.5, 6), 1, 32)
        points = clip(random.gauss(165, 120), 15, 600)
        layout = clip(random.gauss(0.36, 0.2), 0.01, 0.85)
        angle = clip(random.gauss(0.34, 0.22), 0.01, 0.82)

    image_url = f"minio://cognitive-files/sessions/{session_id}/drawing/{sample_id}.png" if random.random() > 0.14 else ""
    drawing_rows.append({
        "sample_id": sample_id,
        "drawing_task_id": f"DT_{sample_id}",
        "stroke_count": maybe_missing(int(round(stroke)), 0.08),
        "total_points": maybe_missing(int(round(points)), 0.08),
        "clock_layout_score": maybe_missing(round(layout, 3), 0.1),
        "hand_angle_score": maybe_missing(round(angle, 3), 0.1),
        "image_url": image_url,
    })

    # Behavior with outliers + missing
    if label == "normal":
        rt_mean = clip(random.gauss(3000, 1200), 500, 12000)
        rt_std = clip(random.gauss(1000, 500), 100, 4500)
        fast = clip(random.gauss(0.09, 0.06), 0, 0.4)
        slow = clip(random.gauss(0.05, 0.05), 0, 0.3)
        modify = clip(random.gauss(1.8, 1.5), 0, 10)
        click_acc = clip(random.gauss(0.81, 0.13), 0.08, 1.0)
    elif label == "mci_risk":
        rt_mean = clip(random.gauss(4800, 1700), 700, 18000)
        rt_std = clip(random.gauss(1650, 700), 150, 7000)
        fast = clip(random.gauss(0.12, 0.07), 0, 0.5)
        slow = clip(random.gauss(0.1, 0.08), 0, 0.5)
        modify = clip(random.gauss(2.9, 2.0), 0, 14)
        click_acc = clip(random.gauss(0.68, 0.16), 0.05, 0.98)
    else:
        rt_mean = clip(random.gauss(6700, 2300), 900, 24000)
        rt_std = clip(random.gauss(2600, 1100), 220, 9500)
        fast = clip(random.gauss(0.14, 0.08), 0, 0.55)
        slow = clip(random.gauss(0.2, 0.11), 0, 0.7)
        modify = clip(random.gauss(4.2, 2.6), 0, 18)
        click_acc = clip(random.gauss(0.53, 0.19), 0.03, 0.95)

    # inject 4% extreme outliers
    if random.random() < 0.04:
        rt_mean = clip(rt_mean * random.uniform(1.8, 2.8), 500, 30000)

    behavior_rows.append({
        "sample_id": sample_id,
        "reaction_time_mean_ms": maybe_missing(int(round(rt_mean)), 0.07),
        "reaction_time_std_ms": maybe_missing(int(round(rt_std)), 0.07),
        "fast_ratio": maybe_missing(round(fast, 3), 0.08),
        "slow_ratio": maybe_missing(round(slow, 3), 0.08),
        "answer_modify_count": maybe_missing(int(round(modify)), 0.08),
        "click_accuracy": maybe_missing(round(click_acc, 3), 0.08),
    })

    questionnaire_rows.append({
        "sample_id": sample_id,
        "question_count": random.randint(10, 20),
        "choice_accuracy": maybe_missing(round(clip((domains["orientation"] + domains["attention"] + domains["language"]) / 3.0 + random.uniform(-0.14, 0.14), 0.0, 1.0), 3), 0.06),
        "scale_mean": maybe_missing(round(clip((domains["memory"] + domains["executive"] + domains["visuospatial"]) / 3.0 * 10 + random.uniform(-1.5, 1.5), 0, 10), 2), 0.06),
        "domain_memory": maybe_missing(round(domains["memory"], 3), 0.07),
        "domain_attention": maybe_missing(round(domains["attention"], 3), 0.07),
        "domain_language": maybe_missing(round(domains["language"], 3), 0.07),
        "domain_visuospatial": maybe_missing(round(domains["visuospatial"], 3), 0.07),
        "domain_executive": maybe_missing(round(domains["executive"], 3), 0.07),
        "domain_orientation": maybe_missing(round(domains["orientation"], 3), 0.07),
    })


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

write_csv(out_dir / "dataset_master.csv", master_rows)
write_csv(out_dir / "feature_voice.csv", voice_rows)
write_csv(out_dir / "feature_drawing.csv", drawing_rows)
write_csv(out_dir / "feature_behavior.csv", behavior_rows)
write_csv(out_dir / "feature_questionnaire.csv", questionnaire_rows)

label_counts = {"normal": 0, "mci_risk": 0, "high_risk": 0}
for r in master_rows:
    label_counts[r["consensus_label"]] += 1

# quick missing stats for readme
missing_counter = {}
for name, rows in [
    ("master", master_rows),
    ("voice", voice_rows),
    ("drawing", drawing_rows),
    ("behavior", behavior_rows),
    ("questionnaire", questionnaire_rows),
]:
    total = len(rows)
    keys = rows[0].keys()
    miss = {}
    for k in keys:
        miss[k] = round(sum(1 for r in rows if str(r.get(k, "")) == "") / total, 3)
    missing_counter[name] = miss

readme = out_dir / "README.md"
readme.write_text(
    "\n".join([
        "# Synthetic Multimodal Dataset v2 (Noisy)",
        "",
        "- Type: synthetic noisy dataset (for robustness testing)",
        "- Samples: 220",
        "- Label distribution: " + str(label_counts),
        "- Characteristics:",
        "  - dialect-heavy composition",
        "  - higher missing values",
        "  - lower audio quality & more outliers",
        "  - higher annotation noise vs v1",
        "",
        "## Files",
        "- dataset_master.csv",
        "- feature_voice.csv",
        "- feature_drawing.csv",
        "- feature_behavior.csv",
        "- feature_questionnaire.csv",
        "",
        "## Important",
        "1. Synthetic only, not clinical evidence.",
        "2. Use with v1 for stress/ablation/robustness comparison.",
        "",
        "## Missing-rate snapshot",
        str(missing_counter),
    ]),
    encoding="utf-8",
)

print(f"Generated noisy dataset at: {out_dir}")
print(label_counts)
