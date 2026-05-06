"""
Deep multimodal model service.

This module provides an optional deep cross-modal fusion path on top of the
existing feature extraction outputs. It is designed to be runtime-switchable:

- If PyTorch/checkpoint is available: run deep inference.
- If unavailable: report reason and let caller fall back to rule-based engine.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import settings

LOGGER = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn

    TORCH_AVAILABLE = True
except Exception:  # pragma: no cover - executed only when torch missing
    torch = None
    class _NNStub:  # pragma: no cover - fallback for import safety
        Module = object

    nn = _NNStub()
    TORCH_AVAILABLE = False


DOMAIN_ORDER = ["memory", "orientation", "language", "attention", "visuospatial", "executive"]
MODALITY_ORDER = ["questionnaire", "voice", "drawing", "behavior"]

QUESTIONNAIRE_KEYS = [
    ("available", 1.0),
    ("quality", 1.0),
    ("choice_accuracy", 1.0),
    ("avg_score", 1.0),
    ("scale_mean", 1.0),
    ("coverage", 1.0),
    ("sample_count", 20.0),
]

VOICE_KEYS = [
    ("available", 1.0),
    ("quality", 1.0),
    ("word_richness", 1.0),
    ("avg_words", 40.0),
    ("avg_duration_sec", 90.0),
    ("pause_density", 2.0),
    ("audio_file_ratio", 1.0),
    ("sample_count", 10.0),
]

DRAWING_KEYS = [
    ("available", 1.0),
    ("quality", 1.0),
    ("structure_score", 1.0),
    ("avg_strokes", 40.0),
    ("avg_points", 800.0),
    ("image_ratio", 1.0),
    ("sample_count", 10.0),
]

BEHAVIOR_KEYS = [
    ("available", 1.0),
    ("quality", 1.0),
    ("avg_reaction_ms", 60000.0),
    ("std_reaction_ms", 40000.0),
    ("slow_ratio", 1.0),
    ("fast_ratio", 1.0),
    ("stability_score", 1.0),
    ("sample_count", 20.0),
]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _vectorize(features: Dict[str, Any], keys: List[Tuple[str, float]]) -> np.ndarray:
    output: List[float] = []
    for key, scale in keys:
        raw = _to_float(features.get(key), 0.0)
        norm = raw / scale if scale > 0 else raw
        output.append(_clamp(norm, 0.0, 1.0))
    return np.asarray(output, dtype=np.float32)


class _DeepCrossModalFusionNet(nn.Module):
    def __init__(self, d_model: int = 96, n_heads: int = 4):
        super().__init__()
        self.questionnaire_proj = self._build_modal_encoder(len(QUESTIONNAIRE_KEYS), d_model)
        self.voice_proj = self._build_modal_encoder(len(VOICE_KEYS), d_model)
        self.drawing_proj = self._build_modal_encoder(len(DRAWING_KEYS), d_model)
        self.behavior_proj = self._build_modal_encoder(len(BEHAVIOR_KEYS), d_model)

        self.cross_attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_model * 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        fused_dim = d_model * 4
        self.fusion = nn.Sequential(
            nn.Linear(fused_dim, 256),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(256, 128),
            nn.GELU(),
        )
        self.risk_head = nn.Linear(128, 3)
        self.domain_head = nn.Linear(128, len(DOMAIN_ORDER))
        self.modality_head = nn.Linear(128, len(MODALITY_ORDER))

    @staticmethod
    def _build_modal_encoder(input_dim: int, d_model: int) -> nn.Sequential:
        return nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.GELU(),
            nn.LayerNorm(64),
            nn.Linear(64, d_model),
            nn.GELU(),
            nn.LayerNorm(d_model),
        )

    def forward(
        self,
        questionnaire: torch.Tensor,
        voice: torch.Tensor,
        drawing: torch.Tensor,
        behavior: torch.Tensor,
    ):
        q = self.questionnaire_proj(questionnaire)
        v = self.voice_proj(voice)
        d = self.drawing_proj(drawing)
        b = self.behavior_proj(behavior)

        tokens = torch.stack([q, v, d, b], dim=1)  # (B, 4, d_model)
        attn_out, attn_weights = self.cross_attn(
            tokens,
            tokens,
            tokens,
            need_weights=True,
            average_attn_weights=False,
        )
        tokens = self.norm1(tokens + attn_out)
        tokens = self.norm2(tokens + self.ffn(tokens))

        fused = self.fusion(tokens.reshape(tokens.size(0), -1))
        risk_logits = self.risk_head(fused)
        domain_scores = torch.sigmoid(self.domain_head(fused)) * 10.0
        modality_logits = self.modality_head(fused)
        return risk_logits, domain_scores, modality_logits, attn_weights


class DeepMultimodalService:
    def __init__(self):
        self.ready = False
        self.reason = ""
        self.device = "cpu"
        self.model: Optional[_DeepCrossModalFusionNet] = None
        self.info: Dict[str, Any] = {
            "engine": "deep_cross_modal",
            "checkpoint_loaded": False,
            "checkpoint_path": None,
        }
        self._initialize()

    def _initialize(self) -> None:
        if not TORCH_AVAILABLE:
            self.reason = "torch_not_installed"
            LOGGER.warning("Deep model unavailable: %s", self.reason)
            return

        device_name = settings.DEEP_MODEL_DEVICE.lower().strip()
        if device_name == "cuda" and not torch.cuda.is_available():
            LOGGER.warning("DEEP_MODEL_DEVICE=cuda but CUDA not available, fallback to cpu.")
            device_name = "cpu"
        self.device = device_name

        model = _DeepCrossModalFusionNet()
        checkpoint_path = Path(settings.DEEP_MODEL_CHECKPOINT)
        self.info["checkpoint_path"] = str(checkpoint_path)

        if checkpoint_path.exists():
            payload = torch.load(checkpoint_path, map_location=self.device)
            state_dict = payload.get("state_dict", payload)
            model.load_state_dict(state_dict, strict=False)
            self.info["checkpoint_loaded"] = True
        elif not settings.DEEP_MODEL_ALLOW_RANDOM_INIT:
            self.reason = f"checkpoint_not_found:{checkpoint_path}"
            LOGGER.warning("Deep model unavailable: %s", self.reason)
            return
        else:
            LOGGER.warning(
                "Deep model checkpoint not found, using random initialization: %s",
                checkpoint_path,
            )

        model.to(self.device)
        model.eval()
        self.model = model
        self.ready = True
        self.reason = ""

    def available(self) -> bool:
        return self.ready and self.model is not None

    def predict(self, modality_features: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not self.available():
            return None

        questionnaire_vec = _vectorize(modality_features.get("questionnaire", {}), QUESTIONNAIRE_KEYS)
        voice_vec = _vectorize(modality_features.get("voice", {}), VOICE_KEYS)
        drawing_vec = _vectorize(modality_features.get("drawing", {}), DRAWING_KEYS)
        behavior_vec = _vectorize(modality_features.get("behavior", {}), BEHAVIOR_KEYS)

        with torch.no_grad():
            q = torch.tensor(questionnaire_vec, device=self.device).unsqueeze(0)
            v = torch.tensor(voice_vec, device=self.device).unsqueeze(0)
            d = torch.tensor(drawing_vec, device=self.device).unsqueeze(0)
            b = torch.tensor(behavior_vec, device=self.device).unsqueeze(0)

            risk_logits, domain_raw, modality_logits, attn_weights = self.model(q, v, d, b)

            probs = torch.softmax(risk_logits, dim=-1).squeeze(0).detach().cpu().numpy()
            domains = domain_raw.squeeze(0).detach().cpu().numpy()
            modality_w = torch.softmax(modality_logits, dim=-1).squeeze(0).detach().cpu().numpy()

        domain_scores = {
            domain: round(_clamp(float(score), 0.0, 10.0), 2)
            for domain, score in zip(DOMAIN_ORDER, domains)
        }
        probabilities = {
            "nc": round(_clamp(float(probs[0]), 0.0, 1.0), 4),
            "mci": round(_clamp(float(probs[1]), 0.0, 1.0), 4),
            "ad": round(_clamp(float(probs[2]), 0.0, 1.0), 4),
        }
        prob_sum = probabilities["nc"] + probabilities["mci"] + probabilities["ad"]
        if prob_sum > 0:
            probabilities = {
                key: round(value / prob_sum, 4)
                for key, value in probabilities.items()
            }

        modality_contributions = {
            key: round(float(weight) * 100.0, 2)
            for key, weight in zip(MODALITY_ORDER, modality_w)
        }
        confidence = self._confidence_from_probs(probabilities, modality_features)
        attention_matrix = self._attention_matrix(attn_weights)

        return {
            "domain_scores": domain_scores,
            "probabilities": probabilities,
            "confidence": confidence,
            "modality_contributions": modality_contributions,
            "attention_matrix": attention_matrix,
            "engine_info": {
                **self.info,
                "device": self.device,
            },
        }

    @staticmethod
    def _confidence_from_probs(
        probabilities: Dict[str, float],
        modality_features: Dict[str, Dict[str, Any]],
    ) -> float:
        ranked = sorted(probabilities.values(), reverse=True)
        margin = ranked[0] - ranked[1]
        entropy = -sum(max(p, 1e-7) * np.log(max(p, 1e-7)) for p in probabilities.values())
        entropy_norm = entropy / np.log(3.0)
        quality_mean = float(
            np.mean(
                [
                    _to_float(modality_features.get(modality, {}).get("quality"), 0.55)
                    for modality in MODALITY_ORDER
                ]
            )
        )
        confidence = 0.40 + margin * 0.38 + (1.0 - entropy_norm) * 0.18 + quality_mean * 0.16
        return round(_clamp(confidence, 0.35, 0.98), 4)

    @staticmethod
    def _attention_matrix(attn_weights: torch.Tensor) -> List[List[float]]:
        """
        Return 4x4 modality attention matrix.
        Modality order: questionnaire, voice, drawing, behavior.
        """
        arr = attn_weights.detach().cpu().numpy()
        if arr.ndim == 4:
            matrix = arr[0].mean(axis=0)
        elif arr.ndim == 3:
            matrix = arr[0]
        else:
            matrix = np.zeros((4, 4), dtype=np.float32)

        matrix = np.asarray(matrix, dtype=np.float32)
        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        matrix = matrix / row_sums
        return [[round(float(v), 4) for v in row] for row in matrix.tolist()]


@lru_cache(maxsize=1)
def get_deep_model_service() -> DeepMultimodalService:
    return DeepMultimodalService()
