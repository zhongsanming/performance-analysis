#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=null
source "$VENV"/bin/activate

if pip show flagtree; then
  pip uninstall -y flagtree
fi

if pip show triton; then
  pip uninstall -y triton
fi

cd "$WORK"/FlagTree

git checkout triton_v$VER.x

pip install -r python/requirements.txt

LLVM_HASH=$(head -c 8 cmake/llvm-hash.txt)
export LLVM_HASH
export LLVM_PREFIX=${HOME}/.triton/llvm/llvm-${LLVM_HASH}-ubuntu-x64

bash "$WORK"/install-llvm.sh

export LLVM_SYS_PATH=$LLVM_PREFIX
export LLVM_LIBRARY_DIR=$LLVM_SYS_PATH/lib/
export LLVM_INCLUDE_DIRS=$LLVM_SYS_PATH/include/
export MAX_JOBS=32

export PYTHONPATH=$LLVM_SYS_PATH/python_packages/mlir_core

rm -rf build

if [[ $VER == "3.3" ]]; then
  # don't install libanalysis.lib from amd to avoid permission issue
  git apply "$WORK/flagtree-no-amd-libanalysis.patch"
fi

if [ ! -f setup.py ];  then
  cd ./python
fi

for i in $(seq 1 5); do
  rm -rf build
  pip install . --no-build-isolation -v && break
  sleep 10
done

git stash
