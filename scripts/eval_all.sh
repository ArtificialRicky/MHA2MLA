#!/bin/bash
#################### 环境变量 ####################

export CUDA_VISIBLE_DEVICES="4,5,6,7"
export HF_HOME="/home/binguo/data/hf-home"
export NUM_GPUS=$(echo $CUDA_VISIBLE_DEVICES | awk -F "," '{print NF}')
export MASTER_PORT="auto"
export PYTHONPATH=..:$PYTHONPATH

#################### 函数定义 ####################

eval_one_ckpt() {
    local model_name_or_path=$1
    local output_dir=$2

    torchrun --nproc_per_node=1 \
        -m src.original_conversation.convert_nanotron_to_hf \
        --checkpoint_path ${model_name_or_path} \
        --save_path ${model_name_or_path}_hf \
        --tokenizer_name /home/binguo/data/models/HuggingFaceTB/SmolLM-360M

    accelerate launch --multi_gpu --num_processes=${NUM_GPUS} --main_process_port 25675 \
        -m  lighteval accelerate \
        --model_args "pretrained=${model_name_or_path}_hf,revision=main,dtype=bfloat16,max_length=2048" \
        --override_batch_size 48 \
        --custom_tasks "../src/evaluation/tasks.py" \
        --tasks "../src/evaluation/smollm1_base_v2.txt" \
        --output_dir "../eval_results/${output_dir}"
}

eval_all() {
    local model_name_path=$1
    local output_dir=$2

    # eval所有检查点
    matching_directories=$(find "$model_name_path" -mindepth 1 -maxdepth 1 -type d -regex '.*/[0-9]+')
    echo $matching_directories

    for dir in $matching_directories; do
        echo "Evaluating $dir"
        eval_one_ckpt $dir $output_dir
    done
}


eval_one_ckpt_hf() {
    local model_name_or_path=$1
    local output_dir=$2

    accelerate launch --multi_gpu --num_processes=${NUM_GPUS} --main_process_port 25675 \
        -m  lighteval accelerate \
        --model_args "pretrained=${model_name_or_path},revision=main,dtype=bfloat16,max_length=2048" \
        --override_batch_size 48 \
        --custom_tasks "../src/evaluation/tasks.py" \
        --tasks "../src/evaluation/smollm1_base_v2.txt" \
        --output_dir "../eval_results/${output_dir}"
}

eval_all_hf() {
    local model_name_path=$1
    local output_dir=$2

    # eval所有检查点
    matching_directories=$(find "$model_name_path" -type d -name "checkpoint-[0-9]*")
    echo $matching_directories

    for dir in $matching_directories; do
        echo "Evaluating $dir"
        eval_one_ckpt_hf $dir $output_dir
    done
}


#################### 任务执行 ####################

set -e

eval_one_ckpt ../checkpoints/360M_2/24000 360M_2
