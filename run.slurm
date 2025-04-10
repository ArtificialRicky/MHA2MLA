#!/bin/bash
#SBATCH --job-name=mpi_test
#SBATCH --nodes=1
#SBATCH --ntasks=2
#SBATCH --gres=gpu:1
#SBATCH --partition=GPU-shared
#SBATCH --time=01:00:00
#SBATCH --output=out.log
#SBATCH --error=err.log
#SBATCH --account=cis240126p

module purge
module load cuda/12.4
export CUDA_HOME=/opt/packages/cuda/v12.4.0
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

conda activate mla

mpiexec -n 2 python base.py
