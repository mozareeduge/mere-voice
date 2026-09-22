from __future__ import annotations

import importlib.util
from pathlib import Path

from .storage import ROOT, read_json

CONFIG = ROOT / "data" / "config" / "tts_provider.json"


def load_provider_config() -> dict:
    return read_json(CONFIG, {"active_provider": "piper", "fallback_provider": "piper"})


def _pocket_ready(cfg: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    p = cfg.get("pocket_fa_v2") or {}
    ref = ROOT / p.get("reference_audio", "")
    model_config = ROOT / p.get("pinned_model_config", "")
    normalizer = ROOT / p.get("normalizer_path", "")
    if importlib.util.find_spec("pocket_tts") is None:
        reasons.append("pocket_tts package missing")
    if importlib.util.find_spec("transformers") is None:
        reasons.append("transformers package missing")
    if not ref.is_file():
        reasons.append("reference audio missing")
    if not model_config.is_file():
        reasons.append("pinned Pocket model config missing")
    if not normalizer.is_file():
        reasons.append("pinned Persian normalizer missing")
    if not p.get("model_revision") or not p.get("g2p_revision"):
        reasons.append("Hugging Face revisions unresolved; rerun installer")
    return not reasons, reasons


def provider_status(*, piper_ready: bool | None = None) -> dict:
    cfg = load_provider_config()
    active = cfg.get("active_provider", "piper")
    pocket_ok, pocket_reasons = _pocket_ready(cfg)
    if piper_ready is None:
        # Importability is enough here; app.py still performs its stricter model-file probe.
        piper_ready = importlib.util.find_spec("piper") is not None
    available = {"pocket_fa_v2": pocket_ok, "piper": bool(piper_ready), "fixture_espeak": True}
    recommended = active if available.get(active) else ("piper" if piper_ready else "fixture_espeak")
    return {
        "active_provider": active,
        "recommended_render_mode": recommended,
        "providers": {
            "pocket_fa_v2": {"ready": pocket_ok, "reasons": pocket_reasons},
            "piper": {"ready": bool(piper_ready)},
            "fixture_espeak": {"ready": True, "purpose": "temporal/UI fixture only"},
        },
        "piper_ready": bool(piper_ready),
    }


def render_dry(provider: str | None = None, line_ids=None):
    cfg = load_provider_config()
    provider = provider or cfg.get("active_provider", "piper")
    if provider == "pocket_fa_v2":
        from .tts_pocket_fa import render_with_pocket
        return render_with_pocket(line_ids)
    if provider == "piper":
        from .tts import render_with_piper
        return render_with_piper(line_ids)
    if provider == "fixture_espeak":
        from .tts import render_fixture_espeak
        return render_fixture_espeak(line_ids)
    raise ValueError(f"unknown TTS provider: {provider}")
