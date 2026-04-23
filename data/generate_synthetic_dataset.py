import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(20260422)

root = Path(r"D:\张家界学院材料\竞赛\竞赛项目\基于多模态交互的社区老年认知障碍早期筛查与干预系统")
out_dir = root / "data" / "synthetic_multimodal_dataset_v1"
out_dir.mkdir(parents=True, exist_ok=True)

N = 180
classes = (
    ["normal"] * 72 +
    ["mci_risk"] * 72 +
    ["high_risk"] * 36
)
random.shuffle(classes)

start_date = date(2026, 1, 1)
communities = ["C001", "C002", "C003", "C004", "C005", "C006"]
dialects = ["mandarin", "xiang", "southwest_mandarin"]
devices = ["tablet", "phone"]

master_rows = []
voice_rows = []
drawing_rows = []
behavior_rows = []
questionnaire_rows = []


def clip(x, low, high):
    return max(low, min(high, x))


def gen_scores(label, edu_years):
    if label == "normal":
        mmse = random.gauss(28.2, 1.2)
        moca = random.gauss(27.1, 1.5)
    elif label == "mci_risk":
        mmse = random.gauss(25.1, 1.4)
        moca = random.gauss(22.6, 1.8)
    else:
        mmse = random.gauss(20.4, 2.3)
        moca = random.gauss(16.8, 2.4)

    mmse = round(clip(mmse, 8, 30), 1)
    moca_raw = round(clip(moca, 3, 30), 1)
    moca_corr = round(clip(moca_raw + (1.0 if edu_years <= 0 else 0.0), 3, 30), 1)
    return mmse, moca_raw, moca_corr


def gen_domains(label):
    if label == "normal":
        base = random.uniform(0.72, 0.9)
    elif label == "mci_risk":
        base = random.uniform(0.52, 0.74)
    else:
        base = random.uniform(0.28, 0.58)

    noise = lambda s=0.09: random.uniform(-s, s)
    d = {
        "memory": clip(base + noise(0.12), 0.05, 0.98),
        "attention": clip(base + noise(), 0.05, 0.98),
        "language": clip(base + noise(), 0.05, 0.98),
        "visuospatial": clip(base + noise(0.14), 0.05, 0.98),
        "executive": clip(base + noise(0.13), 0.05, 0.98),
        "orientation": clip(base + noise(0.1), 0.05, 0.98),
    }
    return d


def infer_split(i):
    r = i % 10
    if r < 7:
        return "train"
    if r == 7:
        return "val"
    return "test"

for i, label in enumerate(classes, start=1):
    sample_id = f"MG2026_{i:04d}"
    participant_id = f"P{100000+i}"
    session_id = f"S{200000+i}"
    collect_date = (start_date + timedelta(days=random.randint(0, 110))).isoformat()
    community_id = random.choice(communities)

    if label == "normal":
        age = int(round(random.gauss(66.5, 4.5)))
    elif label == "mci_risk":
        age = int(round(random.gauss(70.2, 5.5)))
    else:
        age = int(round(random.gauss(73.3, 5.8)))
    age = int(clip(age, 60, 89))

    sex = random.choice(["F", "M"])
    edu_years = int(clip(round(random.gauss(7.8, 4.0)), 0, 16))
    device_type = random.choice(devices)
    dialect = random.choice(dialects)

    mmse_raw, moca_raw, moca_corr = gen_scores(label, edu_years)

    # 10% doctor/source noise to mimic real annotation uncertainty
    if random.random() < 0.1:
        doctor_label = random.choice([x for x in ["normal", "mci_risk", "high_risk"] if x != label])
        label_conf = round(random.uniform(0.55, 0.78), 2)
        retest_required = 1
    else:
        doctor_label = label
        label_conf = round(random.uniform(0.79, 0.98), 2)
        retest_required = 0

    consensus_label = label
    label_source = "doctor+scale" if random.random() < 0.88 else "scale_only"

    exclude_flag = 1 if random.random() < 0.03 else 0
    exclude_reason = "low_audio_quality" if exclude_flag else ""

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
        "mmse_raw": mmse_raw,
        "moca_raw": moca_raw,
        "moca_edu_corrected": moca_corr,
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

    # voice
    if label == "normal":
        dur = clip(random.gauss(28, 6), 9, 58)
        wc = clip(random.gauss(52, 11), 10, 95)
        pauses = clip(random.gauss(2.8, 1.6), 0, 12)
        snr = clip(random.gauss(21, 3.5), 8, 32)
    elif label == "mci_risk":
        dur = clip(random.gauss(24, 7), 8, 56)
        wc = clip(random.gauss(38, 12), 6, 80)
        pauses = clip(random.gauss(4.7, 2.2), 0, 16)
        snr = clip(random.gauss(18.5, 4.2), 6, 30)
    else:
        dur = clip(random.gauss(19, 8), 7, 54)
        wc = clip(random.gauss(25, 11), 4, 62)
        pauses = clip(random.gauss(7.1, 2.8), 0, 20)
        snr = clip(random.gauss(16.2, 4.8), 4, 28)

    speech_rate = round(float(wc) / max(float(dur), 1.0), 2)
    voice_rows.append({
        "sample_id": sample_id,
        "voice_task_id": f"VT_{sample_id}",
        "duration_sec": round(dur, 2),
        "word_count": int(round(wc)),
        "speech_rate": speech_rate,
        "pause_count": int(round(pauses)),
        "snr_score": round(snr, 2),
        "asr_text": "<synthetic_transcript>",
        "audio_url": f"minio://cognitive-files/sessions/{session_id}/audio/{sample_id}.mp3",
    })

    # drawing
    if label == "normal":
        stroke = clip(random.gauss(18, 4.5), 6, 36)
        points = clip(random.gauss(310, 90), 70, 620)
        layout = clip(random.gauss(0.82, 0.1), 0.2, 1.0)
        angle = clip(random.gauss(0.8, 0.11), 0.15, 1.0)
    elif label == "mci_risk":
        stroke = clip(random.gauss(15, 4.8), 4, 32)
        points = clip(random.gauss(250, 95), 50, 560)
        layout = clip(random.gauss(0.62, 0.13), 0.1, 0.95)
        angle = clip(random.gauss(0.6, 0.14), 0.08, 0.92)
    else:
        stroke = clip(random.gauss(12, 5.2), 3, 30)
        points = clip(random.gauss(190, 100), 30, 520)
        layout = clip(random.gauss(0.42, 0.15), 0.05, 0.85)
        angle = clip(random.gauss(0.41, 0.17), 0.05, 0.82)

    drawing_rows.append({
        "sample_id": sample_id,
        "drawing_task_id": f"DT_{sample_id}",
        "stroke_count": int(round(stroke)),
        "total_points": int(round(points)),
        "clock_layout_score": round(layout, 3),
        "hand_angle_score": round(angle, 3),
        "image_url": f"minio://cognitive-files/sessions/{session_id}/drawing/{sample_id}.png",
    })

    # behavior
    if label == "normal":
        rt_mean = clip(random.gauss(2600, 700), 700, 7200)
        rt_std = clip(random.gauss(780, 260), 120, 2400)
        fast = clip(random.gauss(0.07, 0.04), 0, 0.28)
        slow = clip(random.gauss(0.03, 0.03), 0, 0.2)
        modify = clip(random.gauss(1.3, 1.0), 0, 6)
        click_acc = clip(random.gauss(0.88, 0.08), 0.35, 1.0)
    elif label == "mci_risk":
        rt_mean = clip(random.gauss(4200, 1100), 900, 10500)
        rt_std = clip(random.gauss(1300, 420), 180, 3600)
        fast = clip(random.gauss(0.1, 0.05), 0, 0.35)
        slow = clip(random.gauss(0.08, 0.05), 0, 0.35)
        modify = clip(random.gauss(2.4, 1.3), 0, 9)
        click_acc = clip(random.gauss(0.74, 0.11), 0.2, 1.0)
    else:
        rt_mean = clip(random.gauss(5900, 1500), 1200, 15000)
        rt_std = clip(random.gauss(2100, 700), 250, 6000)
        fast = clip(random.gauss(0.12, 0.06), 0, 0.45)
        slow = clip(random.gauss(0.18, 0.08), 0, 0.55)
        modify = clip(random.gauss(3.6, 1.8), 0, 12)
        click_acc = clip(random.gauss(0.59, 0.14), 0.1, 0.95)

    behavior_rows.append({
        "sample_id": sample_id,
        "reaction_time_mean_ms": int(round(rt_mean)),
        "reaction_time_std_ms": int(round(rt_std)),
        "fast_ratio": round(fast, 3),
        "slow_ratio": round(slow, 3),
        "answer_modify_count": int(round(modify)),
        "click_accuracy": round(click_acc, 3),
    })

    questionnaire_rows.append({
        "sample_id": sample_id,
        "question_count": random.randint(14, 20),
        "choice_accuracy": round(clip((domains["orientation"] + domains["attention"] + domains["language"]) / 3.0 + random.uniform(-0.08, 0.08), 0.0, 1.0), 3),
        "scale_mean": round(clip((domains["memory"] + domains["executive"] + domains["visuospatial"]) / 3.0 * 10 + random.uniform(-0.8, 0.8), 0, 10), 2),
        "domain_memory": round(domains["memory"], 3),
        "domain_attention": round(domains["attention"], 3),
        "domain_language": round(domains["language"], 3),
        "domain_visuospatial": round(domains["visuospatial"], 3),
        "domain_executive": round(domains["executive"], 3),
        "domain_orientation": round(domains["orientation"], 3),
    })


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

write_csv(out_dir / "dataset_master.csv", master_rows, list(master_rows[0].keys()))
write_csv(out_dir / "feature_voice.csv", voice_rows, list(voice_rows[0].keys()))
write_csv(out_dir / "feature_drawing.csv", drawing_rows, list(drawing_rows[0].keys()))
write_csv(out_dir / "feature_behavior.csv", behavior_rows, list(behavior_rows[0].keys()))
write_csv(out_dir / "feature_questionnaire.csv", questionnaire_rows, list(questionnaire_rows[0].keys()))

label_counts = {"normal": 0, "mci_risk": 0, "high_risk": 0}
for r in master_rows:
    label_counts[r["consensus_label"]] += 1

readme = out_dir / "README.md"
readme.write_text(
    "\n".join([
        "# Synthetic Multimodal Dataset v1",
        "",
        "- Type: synthetic (for development/testing/demo)",
        "- Samples: 180",
        "- Label distribution: " + str(label_counts),
        "- Files:",
        "  - dataset_master.csv",
        "  - feature_voice.csv",
        "  - feature_drawing.csv",
        "  - feature_behavior.csv",
        "  - feature_questionnaire.csv",
        "",
        "## Notes",
        "1. This dataset is synthetic and must not be used as clinical evidence.",
        "2. Labels follow project-level screening rules and include mild annotation noise.",
        "3. split column in master table: train/val/test.",
    ]),
    encoding="utf-8",
)

print(f"Generated dataset at: {out_dir}")
print(label_counts)
