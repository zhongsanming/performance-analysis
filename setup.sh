#!/usr/bin/env bash
set -euo pipefail

# before running this, you should have clang & lld available in your PATH
# try: sudo apt install clang lld

export VER=$1
export WORK=$PWD
export VENV=$WORK/.venv-triton-$VER

# just export proxy outside this script
# export http_proxy=http://10.6.212.22:17890
# export https_proxy=http://10.6.212.22:17890

if [ ! -d "$WORK/FlagGems" ]; then
  git clone https://github.com/zhongsanming/FlagGems "$WORK/FlagGems"
fi

if [ ! -d "$WORK/FlagTree" ]; then
  git clone https://github.com/zhongsanming/FlagTree "$WORK/FlagTree"
fi

# almost always fail, try manually clone it
if [ ! -d "$WORK/llvm-project" ]; then
  # llvm-project is difficult to clone
  for _i in $(seq 1 5); do
    git clone https://github.com/llvm/llvm-project "$WORK/llvm-project" && break
    sleep 10
  done
fi

python3 -m venv "$VENV"

# shellcheck source=null
source "$VENV"/bin/activate

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install pybind11 nanobind
pip install 'vllm==0.17.0'

bash "$WORK"/install-flagtree.sh

cd "$WORK"/FlagGems

pip install .
