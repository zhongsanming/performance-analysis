#!/usr/bin/env bash
set -euo pipefail

PYVER=$($VENV/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

VENV_PAC="$VENV/lib/python${PYVER}/site-packages/"
LLVM_BUILD_DIR="build-mlir-$LLVM_HASH"

if [ ! -d "$LLVM_PREFIX" ]; then
  # download prebuild binary, may have a different version of glibc
  # wget https://oaitriton.blob.core.windows.net/public/llvm-builds/llvm-$LLVM_HASH-ubuntu-x64.tar.gz
  # tar xpvf llvm-$LLVM_HASH-ubuntu-x64.tar.gz
  # mv llvm-$LLVM_HASH-ubuntu-x64 $HOME/.triton/llvm/

  pushd "$WORK/llvm-project"

  git checkout $LLVM_HASH
  # you'll have to install clang lld
  # export PATH=$PATH:$HOME/.local/triton/3.6/clang/bin
  # export PATH=$PATH:$HOME/.local/triton/3.6/lld/bin
  rm -rf "$LLVM_BUILD_DIR" && mkdir "$LLVM_BUILD_DIR" && cd "$LLVM_BUILD_DIR"

  cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$LLVM_PREFIX -DLLVM_ENABLE_PROJECTS="mlir;llvm;lld" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DLLVM_TARGETS_TO_BUILD="host;NVPTX;AMDGPU" -DLLVM_INSTALL_UTILS=ON -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DLLVM_ENABLE_LLD=ON -DMLIR_ENABLE_BINDINGS_PYTHON=ON -Dpybind11_DIR=$VENV_PAC/pybind11/share/cmake/pybind11/ -Dnanobind_DIR=$VENV_PAC/nanobind/cmake/ -DCMAKE_EXE_LINKER_FLAGS="-L/usr/lib/gcc/x86_64-linux-gnu/11 -lstdc++" -DMLIR_GENERATE_PYTHON_BINDINGS=ON ../llvm/ && ninja -j128 && ninja install

  popd
fi
