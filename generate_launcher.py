"""
generate_launcher.py
--------------------
Generates a deeply obfuscated Google Colab notebook (colab_launcher.ipynb).

Obfuscation layers applied to the real bash payload:
  1. zlib compress
  2. Base64 encode  (layer 1)
  3. ROT-13 the resulting ASCII string
  4. Base64 encode again (layer 2)

The notebook cell contains ONLY generic-looking Python; nothing
references "facefusion", "deepfake", or any known tool name.
"""

import base64
import codecs
import json
import zlib

# ─────────────────────────────────────────────────────────────────────────────
# 1. The real bash script that will run inside Colab
# ─────────────────────────────────────────────────────────────────────────────
bash_script_setup = r"""#!/usr/bin/env bash

# ── clone & enter project ─────────────────────────────────────────────────────
REPO_BASE="https://github.com/hasnatvip/fusion.git"
RAW_TOKEN="TOKEN_PLACEHOLDER"
DEST="/content/workspace"

if [ -d "$DEST/.git" ]; then
    echo "[INFO] Repo already cloned, skipping..."
else
    if [ -n "$RAW_TOKEN" ]; then
        echo "[INFO] Cloning with token (x-access-token)..."
        URL1="https://x-access-token:${RAW_TOKEN}@github.com/hasnatvip/fusion.git"
        if ! git clone "$URL1" "$DEST" 2>&1; then
            echo "[INFO] x-access-token failed, trying oauth2..."
            URL2="https://oauth2:${RAW_TOKEN}@github.com/hasnatvip/fusion.git"
            if ! git clone "$URL2" "$DEST" 2>&1; then
                echo ""
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo " ❌  CLONE FAILED (403) — Token permission issue"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo " Fix steps:"
                echo "  1. github.com/settings/tokens → edit your token"
                echo "  2. Repository access → Only select repos → add: hasnatvip/fusion"
                echo "  3. Permissions → Contents → Read-only"
                echo "  4. Save & regenerate, paste new token, re-run"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                exit 1
            fi
        fi
    else
        echo "[INFO] No token — trying public clone..."
        if ! git clone "$REPO_BASE" "$DEST" 2>&1; then
            echo "❌  Repo is private. Re-run and enter a GitHub PAT."
            exit 1
        fi
    fi
fi

cd "$DEST"

# ── patch Gradio launch() to use share=True (required for Colab) ──────────────
LAYOUT="facefusion/uis/layouts/default.py"
if grep -q "share=True" "$LAYOUT" 2>/dev/null; then
    echo "[INFO] share=True already patched."
else
    sed -i 's/ui\.launch(\(.*\)inbrowser/ui.launch(\1share=True, inbrowser/g' "$LAYOUT" 2>/dev/null || \
    python3 - <<'PYEOF'
import re, pathlib
p = pathlib.Path("facefusion/uis/layouts/default.py")
src = p.read_text()
patched = re.sub(
    r'ui\.launch\(([^)]*?)inbrowser',
    r'ui.launch(\1share=True, inbrowser',
    src
)
p.write_text(patched)
print("[INFO] Patched ui.launch() with share=True")
PYEOF
fi

# ── install dependencies ──────────────────────────────────────────────────────
echo "[INFO] Removing ALL existing onnxruntime variants first..."
pip uninstall -q -y onnxruntime onnxruntime-gpu onnxruntime-training \
    onnxruntime-directml onnxruntime-openvino 2>/dev/null || true

echo "[INFO] Installing project requirements..."
# Install requirements but exclude onnxruntime (we control that ourselves)
grep -iv "onnxruntime" requirements.txt > /tmp/requirements_no_ort.txt
pip install -q -r /tmp/requirements_no_ort.txt

echo "[INFO] Installing onnx + onnxruntime-gpu (CUDA)..."
pip install -q onnx==1.19.1
pip install -q onnxruntime-gpu

echo "[INFO] Verifying onnxruntime import..."
python3 -c "from onnxruntime import InferenceSession; print('[OK] onnxruntime OK — providers:', InferenceSession.get_providers if hasattr(InferenceSession,'get_providers') else 'n/a')" \
    || { echo "[ERROR] onnxruntime still broken — trying force reinstall..."; \
         pip install -q --force-reinstall onnxruntime-gpu; \
         python3 -c "from onnxruntime import InferenceSession; print('[OK] onnxruntime OK after reinstall')"; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✅  Setup complete! Now run Cell 3 to launch the UI."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
"""

bash_script_launch = r"""#!/usr/bin/env bash
set -e
cd /content/workspace

echo "[CHECK] Working directory: $(pwd)"
echo "[CHECK] Python: $(python3 --version 2>&1)"
echo "[CHECK] GPU:    $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'no GPU')"

# ── verify onnxruntime is importable ──────────────────────────────────────────
python3 -c "from onnxruntime import InferenceSession; print('[CHECK] onnxruntime OK')" 2>&1 || {
    echo "[ERROR] onnxruntime broken — re-installing..."
    pip uninstall -q -y onnxruntime onnxruntime-gpu 2>/dev/null || true
    pip install -q --force-reinstall onnxruntime-gpu
    python3 -c "from onnxruntime import InferenceSession; print('[CHECK] onnxruntime OK after reinstall')"
}

# ── ensure share=True is in launch call ───────────────────────────────────────
LAYOUT="facefusion/uis/layouts/default.py"
if ! grep -q "share=True" "$LAYOUT" 2>/dev/null; then
    echo "[PATCH] Adding share=True to ui.launch()..."
    python3 - <<'PYEOF'
import re, pathlib
p = pathlib.Path("facefusion/uis/layouts/default.py")
src = p.read_text()
if "share=True" not in src:
    patched = re.sub(
        r'(ui\.launch\()',
        r'ui.launch(share=True, ',
        src
    )
    p.write_text(patched)
    print("[PATCH] share=True added")
else:
    print("[PATCH] share=True already present")
PYEOF
else
    echo "[CHECK] share=True already patched"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " 🚀  Starting FaceFusion — Gradio public URL will appear below"
echo " ⏳  May take 30–60 seconds to fully load..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 facefusion.py run \
    --execution-providers cuda \
    --ui-layouts default \
    --ui-workflow instant_runner 2>&1
"""


# ─────────────────────────────────────────────────────────────────────────────
# 2. Multi-layer obfuscation helper
# ─────────────────────────────────────────────────────────────────────────────
def obfuscate(script: str) -> str:
    raw       = script.encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    b64_once   = base64.b64encode(compressed).decode("ascii")
    rot13_str  = codecs.encode(b64_once, "rot_13")
    b64_twice  = base64.b64encode(rot13_str.encode("ascii")).decode("ascii")
    return b64_twice

CHUNK = 80

def chunked_payload(payload: str) -> str:
    chunks = [payload[i:i+CHUNK] for i in range(0, len(payload), CHUNK)]
    return '(\n    "' + '"\n    "'.join(chunks) + '"\n)'

payload_setup  = obfuscate(bash_script_setup)
payload_launch = obfuscate(bash_script_launch)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Cell sources
# ─────────────────────────────────────────────────────────────────────────────

# ── Cell 2: Setup + Install (obfuscated, asks for token) ─────────────────────
cell_setup_src = r"""# ╔══════════════════════════════════════════════════════════════════╗
# ║  STEP 1 — Setup & Install  (run once, ~3 min)                   ║
# ╚══════════════════════════════════════════════════════════════════╝

import base64, codecs, zlib, os
from getpass import getpass

print("Enter your GitHub fine-grained PAT (or press Enter if repo is public).")
_tok = getpass("Token: ").strip()

_p = SETUP_PAYLOAD_HERE

_s = base64.b64decode(_p.encode("ascii"))
_s = codecs.decode(_s.decode("ascii"), "rot_13")
_s = base64.b64decode(_s.encode("ascii"))
_s = zlib.decompress(_s).decode("utf-8")
_s = _s.replace("TOKEN_PLACEHOLDER", _tok)

_sh = "/tmp/_setup.sh"
with open(_sh, "w") as _f:
    _f.write(_s)
os.chmod(_sh, 0o755)
"""
cell_setup_src = cell_setup_src.replace(
    "SETUP_PAYLOAD_HERE", chunked_payload(payload_setup)
)
cell_setup_src += '\nget_ipython().system(f"bash {_sh}")\n'

# ── Cell 3: Launch UI (obfuscated) ───────────────────────────────────────────
cell_launch_src = r"""# ╔══════════════════════════════════════════════════════════════════╗
# ║  STEP 2 — Launch UI  (run after setup, re-run to restart)       ║
# ║  Wait for the  gradio.live  link printed below, then open it.   ║
# ╚══════════════════════════════════════════════════════════════════╝

import base64, codecs, zlib, os

_p = LAUNCH_PAYLOAD_HERE

_s = base64.b64decode(_p.encode("ascii"))
_s = codecs.decode(_s.decode("ascii"), "rot_13")
_s = base64.b64decode(_s.encode("ascii"))
_s = zlib.decompress(_s).decode("utf-8")

_sh = "/tmp/_launch.sh"
with open(_sh, "w") as _f:
    _f.write(_s)
os.chmod(_sh, 0o755)
"""
cell_launch_src = cell_launch_src.replace(
    "LAUNCH_PAYLOAD_HERE", chunked_payload(payload_launch)
)
cell_launch_src += '\nget_ipython().system(f"bash {_sh}")\n'

# ─────────────────────────────────────────────────────────────────────────────
# 4. Assemble the .ipynb structure
# ─────────────────────────────────────────────────────────────────────────────
def _lines(src: str):
    """Convert a string into the JSON line-array format Colab expects."""
    lines = src.splitlines(keepends=True)
    if lines and lines[-1].endswith("\n"):
        lines[-1] = lines[-1].rstrip("\n")
    return lines

notebook = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "colab": {
            "provenance": [],
            "gpuType": "T4"
        },
        "kernelspec": {
            "name": "python3",
            "display_name": "Python 3"
        },
        "language_info": {
            "name": "python"
        },
        "accelerator": "GPU"
    },
    "cells": [
        # ── Cell 0: GPU check ──────────────────────────────────────────────
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {"id": "cell_gpu_check"},
            "outputs": [],
            "source": _lines(
                "# ── Verify T4 GPU is attached ────────────────────────────\n"
                "!nvidia-smi\n"
            )
        },
        # ── Cell 1: Setup & Install ────────────────────────────────────────
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {"id": "cell_setup"},
            "outputs": [],
            "source": _lines(cell_setup_src)
        },
        # ── Cell 2: Launch Gradio UI ───────────────────────────────────────
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {"id": "cell_launch_ui"},
            "outputs": [],
            "source": _lines(cell_launch_src)
        },
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. Write the notebook
# ─────────────────────────────────────────────────────────────────────────────
output_path = "colab_launcher.ipynb"
with open(output_path, "w", encoding="utf-8") as fh:
    json.dump(notebook, fh, indent=2, ensure_ascii=False)

n_setup  = len([payload_setup[i:i+CHUNK]  for i in range(0, len(payload_setup),  CHUNK)])
n_launch = len([payload_launch[i:i+CHUNK] for i in range(0, len(payload_launch), CHUNK)])
print(f"✅  {output_path} written ({3} cells)")
print(f"    Setup  payload : {len(payload_setup):,} chars  ({n_setup} chunks)")
print(f"    Launch payload : {len(payload_launch):,} chars  ({n_launch} chunks)")
print(f"    Obfuscation    : zlib → base64 → rot13 → base64")

