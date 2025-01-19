#!/bin/bash
#################### 环境变量 ####################

export CUDA_VISIBLE_DEVICES="0,1,2"
export HF_HOME="/home/binguo/data/hf-home"
export NUM_GPUS=$(echo $CUDA_VISIBLE_DEVICES | awk -F "," '{print NF}')
export MASTER_PORT="auto"
export export PYTHONPATH=..:$PYTHONPATH

#################### 函数定义 ####################

eval_one_ckpt() {
    local model_name_or_path=$1
    local output_dir=$2
    local cfg_RoPE=$3

    torchrun --nproc_per_node=1 \
        ../modules/nanotron/examples/llama/convert_nanotron_to_hf.py \
        --checkpoint_path ${model_name_or_path} \
        --save_path "${model_name_or_path}_hf" \
        --tokenizer_name /home/binguo/data/models/HuggingFaceTB/SmolLM-135M

    accelerate launch --multi_gpu --num_processes=${NUM_GPUS} \
        -m src.evaluation.eval_partial_rope --cfg_RoPE ${cfg_RoPE} \
        accelerate \
        --model_args "pretrained=${model_name_or_path}_hf,revision=main,dtype=bfloat16,max_length=2048" \
        --override_batch_size 48 \
        --custom_tasks "../src/evaluation/tasks.py" \
        --tasks "../src/evaluation/smollm1_base_new.txt" \
        --output_dir "../eval_results/${output_dir}"
}


#################### 任务执行 ####################


eval_one_ckpt "/home/binguo/data/MLA-FT/checkpoints/v3_top4_last4_rope/18000" "hf_test" ../configs/rope/v3_top4_last4_rope.yaml
