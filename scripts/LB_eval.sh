#!/bin/bash
#################### 环境变量 ####################

export CUDA_VISIBLE_DEVICES="0,1,2,3"
export HF_HOME="~/data/hf-home"
export NUM_GPUS=$(echo $CUDA_VISIBLE_DEVICES | awk -F "," '{print NF}')
export MASTER_PORT="auto"
export PYTHONPATH=..:$PYTHONPATH
export HF_ENDPOINT=https://hf-mirror.com
export FEISHU_START_TIME=$(date +'%Y-%m-%d %H:%M:%S')

# BaseModel="../checkpoints/7B_rope_v4_topk8_svd_method7_rank32"
BSZ=16
# OUTPUT_DIR="../images/longbench_7B"

#################### 任务执行 ####################

set -e

model_names=(
#     "rope_v2_start0_step8_svd_method2_rank4"
#     "rope_v2_start0_step8_svd_method2_rank8"
#     "rope_v2_start0_step8_svd_method2_rank16"
#     "rope_v2_start0_step8_svd_method7_rank8"
#     "rope_v2_start0_step8_svd_method7_rank16"
#     "rope_v2_start0_step8_svd_method7_rank32"
#     "rope_v4_topk4_svd_method2_rank4"
#     "rope_v4_topk4_svd_method2_rank8"
#     "rope_v4_topk4_svd_method2_rank16"
    "360M_rope_v4_topk4_svd_method7_rank8"
    "360M_rope_v4_topk4_svd_method7_rank16"
    "360M_rope_v4_topk4_svd_method7_rank32"
)

# torchrun --nproc_per_node=${NUM_GPUS} \
#     -m src.evaluation.longbench \
#     --model_path ${BaseModel} \
#     --tokenizer_path ${BaseModel} \
#     --longbench True \
#     --lb_max_tokens 2048 \
#     --lb_batch_size ${BSZ} \
#     --output_dir ../images/longbench/bf16 \
#     --dtype "bfloat16"
# 2GPU 46min 

for model_name in "${model_names[@]}"; do
    torchrun --nproc_per_node=${NUM_GPUS} \
        -m src.evaluation.longbench \
        --model_path /home/binguo/data/MLA-FT/checkpoints/${model_name}/24000_hf \
        --tokenizer_path /home/binguo/data/MLA-FT/checkpoints/${model_name}/24000_hf \
        --longbench True \
        --lb_max_tokens 2048 \
        --lb_batch_size ${BSZ} \
        --output_dir ../images/longbench/${model_name} \
        --dtype "bfloat16" \
        --is_mla   

    torchrun --nproc_per_node=${NUM_GPUS} \
        -m src.evaluation.longbench \
        --model_path /home/binguo/data/MLA-FT/checkpoints/${model_name}/24000_hf \
        --tokenizer_path /home/binguo/data/MLA-FT/checkpoints/${model_name}/24000_hf \
        --longbench True \
        --lb_max_tokens 2048 \
        --lb_batch_size ${BSZ} \
        --output_dir ../images/longbench/${model_name}_quanto_int4 \
        --dtype "bfloat16" \
        --cache_implementation "quantized" \
        --backend "quanto" \
        --nbits 4 \
        --residual_length 128 \
        --is_mla

    torchrun --nproc_per_node=${NUM_GPUS} \
        -m src.evaluation.longbench \
        --model_path /home/binguo/data/MLA-FT/checkpoints/${model_name}/24000_hf \
        --tokenizer_path /home/binguo/data/MLA-FT/checkpoints/${model_name}/24000_hf \
        --longbench True \
        --lb_max_tokens 2048 \
        --lb_batch_size ${BSZ} \
        --output_dir ../images/longbench/${model_name}_hqq_int4 \
        --dtype "bfloat16" \
        --cache_implementation "quantized" \
        --backend "HQQ" \
        --nbits 4 \
        --residual_length 128 \
        --is_mla

    feishu_msg -u 18055481550 -m "finish ${model_name}"
done



# torchrun --nproc_per_node=${NUM_GPUS} \
#     -m src.evaluation.longbench \
#     --model_path ${BaseModel} \
#     --tokenizer_path ${BaseModel} \
#     --output_dir ${OUTPUT_DIR}/${BaseModel}_quanto_int4 \
#     --dtype "bfloat16" \
#     --cache_implementation "quantized" \
#     --backend "quanto" \
#     --nbits 4 \
#     --lb_max_tokens 4096 \
#     --lb_batch_size ${BSZ} \
#     --residual_length 128 \
#     --is_mla

# 2GPU 90min

# torchrun --nproc_per_node=${NUM_GPUS} \
#     -m src.evaluation.longbench \
#     --model_path ${BaseModel} \
#     --tokenizer_path ${BaseModel} \
#     --output_dir ../images/longbench/quanto_int2 \
#     --dtype "bfloat16" \
#     --cache_implementation "quantized" \
#     --backend "quanto" \
#     --nbits 2 \
#     --lb_batch_size ${BSZ} \
#     --residual_length 0

# torchrun --nproc_per_node=${NUM_GPUS} \
#     -m src.evaluation.longbench \
#     --model_path ${BaseModel} \
#     --tokenizer_path ${BaseModel} \
#     --output_dir ../images/longbench/HQQ_int4 \
#     --dtype "bfloat16" \
#     --cache_implementation "quantized" \
#     --backend "HQQ" \
#     --lb_batch_size ${BSZ} \
#     --nbits 4 \
#     --residual_length 0

# torchrun --nproc_per_node=${NUM_GPUS} \
#     -m src.evaluation.longbench \
#     --model_path ${BaseModel} \
#     --tokenizer_path ${BaseModel} \
#     --output_dir ../images/longbench/HQQ_int2 \
#     --dtype "bfloat16" \
#     --cache_implementation "quantized" \
#     --backend "HQQ" \
#     --lb_batch_size ${BSZ} \
#     --nbits 2 \
#     --residual_length 0

# torchrun --nproc_per_node=1 \
#     -m src.evaluation.lb_table \
#     --path /home/binguo/data/MLA-FT/images/longbench-135M_mla_q
