#!/usr/bin/env bash
# Convert a merged model (from merge_lora.py) to GGUF, quantize it to Q4_K_M and write an Ollama Modelfile,
# so the fine-tuned model can be tested with evaluation/run_ollama.py exactly like the base model.
#
#   bash finetune/export_gguf.sh finetune/runs/A-7b/merged cargo-a-7b
#
# Needs a llama.cpp checkout with its Python requirements and a build of llama-quantize:
#   git clone https://github.com/ggml-org/llama.cpp && pip install -r llama.cpp/requirements.txt
#   cmake -S llama.cpp -B llama.cpp/build && cmake --build llama.cpp/build --target llama-quantize -j
# Set LLAMA_CPP=/path/to/llama.cpp if it is not ./llama.cpp. Q4_K_M matches the quantization of the
# qwen2.5-coder models in the Ollama library, so base and fine-tuned models are compared at the same precision.
#
# Then, on the machine that runs Ollama (copy the .gguf and the Modelfile there, in one folder):
#   ollama create cargo-a-7b -f Modelfile
#   python evaluation/run_ollama.py --variant normal --split test --model cargo-a-7b --evaluate
#   (condition B models: add --reasoning hint)
set -euo pipefail
MERGED=${1:?usage: export_gguf.sh <merged model folder> <name>}
NAME=${2:?usage: export_gguf.sh <merged model folder> <name>}
LLAMA_CPP=${LLAMA_CPP:-llama.cpp}
QUANT=${QUANT:-Q4_K_M}
OUTDIR=$(dirname "$MERGED")/gguf
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUTDIR"

python "$LLAMA_CPP/convert_hf_to_gguf.py" "$MERGED" --outtype f16 --outfile "$OUTDIR/$NAME-f16.gguf"
QUANTIZE=$(ls "$LLAMA_CPP"/build/bin/llama-quantize "$LLAMA_CPP"/llama-quantize 2>/dev/null | head -n1)
"$QUANTIZE" "$OUTDIR/$NAME-f16.gguf" "$OUTDIR/$NAME-$QUANT.gguf" "$QUANT"
sed "s|__GGUF__|./$NAME-$QUANT.gguf|" "$HERE/Modelfile.template" > "$OUTDIR/Modelfile"
rm -f "$OUTDIR/$NAME-f16.gguf"
echo "GGUF     -> $OUTDIR/$NAME-$QUANT.gguf"
echo "Modelfile -> $OUTDIR/Modelfile   (then: ollama create $NAME -f Modelfile)"
