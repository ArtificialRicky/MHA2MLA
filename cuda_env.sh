#!/bin/bash
# CUDA 12.4 环境配置
export CUDA_HOME=/opt/packages/cuda/v12.4.0
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
