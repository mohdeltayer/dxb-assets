#!/bin/bash
# Chatterbox Multilingual (Resemble AI, MIT) in its own venv for the voice clone trial
# (advisor, 14 Oct 2026). Needs about 2 GB for the venv and 3.3 GB for the weights
# (~/.cache/huggingface: t3_mtl23ls_v2.safetensors 2.1 GB, s3gen.pt 1.1 GB, ve.pt, conds.pt,
# the tokenizers). gradio and the Chinese and Japanese tokenizers are left out.
set -e
V=${1:-/root/venvs/chatterbox}
python3 -m venv "$V"
"$V/bin/pip" install -q --upgrade pip
"$V/bin/pip" install -q torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
"$V/bin/pip" install -q --no-deps chatterbox-tts==0.1.7
"$V/bin/pip" install -q "numpy<2" librosa==0.11.0 s3tokenizer transformers==5.2.0 diffusers==0.29.0 \
    resemble-perth conformer==0.3.2 safetensors==0.5.3 omegaconf pyloudnorm huggingface_hub soundfile
mkdir -p /root/models/mishkal
pip install -q --target /root/models/mishkal mishkal
echo "CHATTERBOX_PY=$V/bin/python  MISHKAL_LIBS=/root/models/mishkal"
