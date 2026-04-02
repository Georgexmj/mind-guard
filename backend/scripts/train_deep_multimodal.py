"""
Train deep multimodal fusion checkpoint from tabular features.

Input CSV requirements:
- One row per assessment sample.
- Label columns:
    - target_class: 0(NC) / 1(MCI) / 2(AD)
    - target_domain_memory ... target_domain_executive (optional, 0~10)
- Feature columns:
    - questionnaire_<feature>
    - voice_<feature>
    - drawing_<feature>
    - behavior_<feature>

Feature names follow backend/app/services/deep_model_service.py key definitions.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from app.services.deep_model_service import (
    DOMAIN_ORDER,
    BEHAVIOR_KEYS,
    DRAWING_KEYS,
    QUESTIONNAIRE_KEYS,
    VOICE_KEYS,
    _DeepCrossModalFusionNet,
    _clamp,
    _to_float,
)


def _read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _vec(row: Dict[str, str], prefix: str, keys: List[Tuple[str, float]]) -> np.ndarray:
    out = []
    for key, scale in keys:
        col = f"{prefix}_{key}"
        value = _to_float(row.get(col), 0.0)
        value = value / scale if scale > 0 else value
        out.append(_clamp(value, 0.0, 1.0))
    return np.asarray(out, dtype=np.float32)


def _domain_targets(row: Dict[str, str], cls_label: int) -> np.ndarray:
    values = []
    for domain in DOMAIN_ORDER:
        col = f"target_domain_{domain}"
        raw = row.get(col)
        if raw is None or raw == "":
            # Fallback synthetic targets if domain labels missing.
            if cls_label == 0:
                values.append(8.2)
            elif cls_label == 1:
                values.append(5.6)
            else:
                values.append(3.1)
        else:
            values.append(_clamp(_to_float(raw, 5.0), 0.0, 10.0))
    return np.asarray(values, dtype=np.float32)


def build_dataset(rows: List[Dict[str, str]]):
    q_all, v_all, d_all, b_all, cls_all, dom_all = [], [], [], [], [], []
    for row in rows:
        cls = int(_clamp(_to_float(row.get("target_class"), 0), 0, 2))
        q_all.append(_vec(row, "questionnaire", QUESTIONNAIRE_KEYS))
        v_all.append(_vec(row, "voice", VOICE_KEYS))
        d_all.append(_vec(row, "drawing", DRAWING_KEYS))
        b_all.append(_vec(row, "behavior", BEHAVIOR_KEYS))
        cls_all.append(cls)
        dom_all.append(_domain_targets(row, cls))

    q = torch.tensor(np.stack(q_all), dtype=torch.float32)
    v = torch.tensor(np.stack(v_all), dtype=torch.float32)
    d = torch.tensor(np.stack(d_all), dtype=torch.float32)
    b = torch.tensor(np.stack(b_all), dtype=torch.float32)
    y_cls = torch.tensor(np.asarray(cls_all, dtype=np.int64), dtype=torch.long)
    y_dom = torch.tensor(np.stack(dom_all), dtype=torch.float32)
    return TensorDataset(q, v, d, b, y_cls, y_dom)


def train(
    input_csv: Path,
    output_ckpt: Path,
    epochs: int = 40,
    batch_size: int = 64,
    lr: float = 1e-3,
):
    rows = _read_rows(input_csv)
    if len(rows) < 32:
        raise ValueError("Training data too small. Please provide at least 32 samples.")

    dataset = build_dataset(rows)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = _DeepCrossModalFusionNet()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    model.train()
    for epoch in range(epochs):
        loss_meter = []
        for q, v, d, b, y_cls, y_dom in loader:
            logits, domain_pred, modality_logits, _ = model(q, v, d, b)
            cls_loss = F.cross_entropy(logits, y_cls)
            dom_loss = F.mse_loss(domain_pred, y_dom)
            # Keep modality head from collapsing into one-hot without supervision.
            modality_entropy = -(torch.softmax(modality_logits, dim=-1) * torch.log_softmax(modality_logits, dim=-1)).sum(dim=-1).mean()
            loss = cls_loss + dom_loss * 0.35 - modality_entropy * 0.01

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            loss_meter.append(float(loss.detach().cpu().item()))

        avg_loss = float(np.mean(loss_meter))
        print(f"epoch={epoch + 1:03d}/{epochs:03d} loss={avg_loss:.5f}")

    output_ckpt.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "meta": {
                "epochs": epochs,
                "batch_size": batch_size,
                "lr": lr,
                "samples": len(rows),
            },
        },
        output_ckpt,
    )
    print(f"checkpoint saved: {output_ckpt}")


def parse_args():
    parser = argparse.ArgumentParser(description="Train deep multimodal fusion model")
    parser.add_argument("--input", required=True, help="Path to CSV training data")
    parser.add_argument(
        "--output",
        default="models/deep_multimodal_fusion.pt",
        help="Checkpoint output path",
    )
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(
        input_csv=Path(args.input),
        output_ckpt=Path(args.output),
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
    )

