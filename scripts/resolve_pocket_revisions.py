from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from huggingface_hub import hf_hub_download

CONFIG_PATH = ROOT / "data" / "config" / "tts_provider.json"


def _pin_hf_uri(uri: str, revision: str) -> str:
    # Pocket-TTS accepts hf://<repo>/<path>[@revision] for downloadable resources.
    return uri if "@" in uri else f"{uri}@{revision}"


def main() -> int:
    doc = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    cfg = doc["pocket_fa_v2"]
    if not cfg.get("model_revision") or not cfg.get("g2p_revision"):
        raise RuntimeError("Package is missing frozen model/G2P revisions")
    for key in ("model_revision", "g2p_revision"):
        value = str(cfg[key])
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            raise RuntimeError(f"{key} is not an immutable 40-hex Hugging Face commit: {value!r}")

    cache_dir = ROOT / "data" / "cache" / "pocket_fa"
    cache_dir.mkdir(parents=True, exist_ok=True)

    source_yaml = Path(hf_hub_download(
        repo_id=cfg["model_id"], filename="model.yaml", revision=cfg["model_revision"]
    ))
    yaml_text = source_yaml.read_text(encoding="utf-8")
    required_yaml = [
        "capitalize_first_letter: false",
        "append_terminal_punctuation: false",
        "pad_with_spaces_for_short_inputs: false",
        "sample_rate: 24000",
        f"hf://{cfg['model_id']}/model.safetensors",
        f"hf://{cfg['model_id']}/tokenizer_ph.model",
    ]
    missing = [x for x in required_yaml if x not in yaml_text]
    if missing:
        raise RuntimeError(f"Resolved Pocket model config no longer matches the audited Farsi-v2 frontend invariants: {missing}")
    # Pin every hf:// path inside the model config to the same immutable model commit.
    def repl(match: re.Match[str]) -> str:
        return _pin_hf_uri(match.group(0), cfg["model_revision"])
    yaml_text = re.sub(r"hf://[^\s#]+", repl, yaml_text)
    pinned = ROOT / cfg["pinned_model_config"]
    pinned.parent.mkdir(parents=True, exist_ok=True)
    pinned.write_text(yaml_text, encoding="utf-8")

    normalizer_src = Path(hf_hub_download(
        repo_id=cfg["model_id"], filename="normalize_fa.py", revision=cfg["model_revision"]
    ))
    normalizer_dst = ROOT / cfg["normalizer_path"]
    normalizer_dst.parent.mkdir(parents=True, exist_ok=True)
    normalizer_text = normalizer_src.read_text(encoding="utf-8")
    if "def normalize_for_model" not in normalizer_text:
        raise RuntimeError("Resolved Pocket normalize_fa.py no longer exposes normalize_for_model")
    shutil.copyfile(normalizer_src, normalizer_dst)

    # Do not rewrite refs to moving heads. The package already freezes both SHAs.
    CONFIG_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "model_revision": cfg["model_revision"],
        "g2p_revision": cfg["g2p_revision"],
        "pinned_model_config": str(pinned.relative_to(ROOT)).replace("\\", "/"),
        "normalizer": str(normalizer_dst.relative_to(ROOT)).replace("\\", "/"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
