import nanotron.serialize
from ..mla.mla_patch_hf import mla_patch_hf
import importlib
import torch

model_path_hf = "/home/binguo/data/models/HuggingFaceTB/SmolLM-135M_mla"
model_path_nt = "/home/binguo/data/models/HuggingFaceTB/SmolLM-135M_nt"

head_dim = 64
rope_scale = 8
rope_cfgs = [
    {
        "partial_rope_version": 1,  # 1 2 3 4 5
        "top_k_rope_dim": head_dim // (2 * rope_scale),
        "last_k_rope_dim": 0,
        "uniform_start_point": 0,
        "uniform_step": rope_scale,
        "qk_tensor_path": "/home/binguo/data/MLA-FT/utils/qk_tensor_135M.pth",
        "n_gqa_group": 3,
    },
    {
        "partial_rope_version": 2,  # 1 2 3 4 5
        "top_k_rope_dim": 0,
        "last_k_rope_dim": 0,
        "uniform_start_point": 0,
        "uniform_step": rope_scale,
        "qk_tensor_path": "/home/binguo/data/MLA-FT/utils/qk_tensor_135M.pth",
        "n_gqa_group": 3,
    },
    {
        "partial_rope_version": 3,  # 1 2 3 4 5
        "top_k_rope_dim": head_dim // (4 * rope_scale),
        "last_k_rope_dim": head_dim // (4 * rope_scale),
        "uniform_start_point": 0,
        "uniform_step": rope_scale,
        "qk_tensor_path": "/home/binguo/data/MLA-FT/utils/qk_tensor_135M.pth",
        "n_gqa_group": 3,
    },
    {
        "partial_rope_version": 4,  # 1 2 3 4 5
        "top_k_rope_dim": head_dim // (2 * rope_scale),
        "last_k_rope_dim": 0,
        "uniform_start_point": 0,
        "uniform_step": rope_scale,
        "qk_tensor_path": "/home/binguo/data/MLA-FT/utils/qk_tensor_135M.pth",
        "n_gqa_group": 3,
    },
    {
        "partial_rope_version": 5,  # 1 2 3 4 5
        "top_k_rope_dim": 0,
        "last_k_rope_dim": head_dim // (2 * rope_scale),
        "uniform_start_point": 0,
        "uniform_step": rope_scale,
        "qk_tensor_path": "/home/binguo/data/MLA-FT/utils/qk_tensor_135M.pth",
        "n_gqa_group": 3,
    },
]
svd_cfgs = [
    {"method": 1, "low_rank": 8},
    {"method": 2, "low_rank": 8},
    {"method": 3, "low_rank": 8},
    {"method": 4, "low_rank": 8},
    {"method": 5, "low_rank": 8},
    {"method": 6, "low_rank": 8},
    {"method": 7, "low_rank": 8},
]


def test_load_weight_hf():
    # from transformers.models.llama import LlamaForCausalLM
    from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
    tokenizer = AutoTokenizer.from_pretrained(model_path_hf)
    config = AutoConfig.from_pretrained(model_path_hf)
    for rope_cfg in rope_cfgs:
        for svd_cfg in svd_cfgs:
            for attn_implementation in [
                "eager",
                "flash_attention_2",
                "sdpa",
            ]:
                setattr(config, "RoPE", rope_cfg)
                setattr(config, "SVD", svd_cfg)
                setattr(config, "_attn_implementation", attn_implementation)
                import importlib,transformers.models.llama.modeling_llama
                importlib.reload(transformers.models.llama.modeling_llama)
                mla_patch_hf(rope_cfg)
                model = AutoModelForCausalLM.from_pretrained(
                    model_path_hf,
                    config=config,
                ).to(dtype=torch.float16)
                model.eval()
                model = model.cuda()
                inputs = tokenizer("Hello, my dog is cute", return_tensors="pt").to("cuda")
                outputs = model(**inputs)
                outputs = model.generate(
                    inputs.input_ids, max_length=50, pad_token_id=tokenizer.eos_token_id, use_cache=False
                )
                outputs = model.generate(
                    inputs.input_ids,
                    max_length=50,
                    pad_token_id=tokenizer.eos_token_id,
                    use_cache=True,
                )
            # except Exception as e:
            #     with open("log.txt","a",encoding="utf-8") as f:
            #         f.write(str(e))
            #         f.write(str(rope_cfg))
            #         f.write(str(svd_cfg))
            #     return


def test_load_weight_nt():
    # package
    from transformers import AutoTokenizer
    import json,os
    from ..mla.mla_patch_nt import mla_patch_nt
    from nanotron.models import build_model
    from nanotron.config import (
        GenerationArgs,
        LoggingArgs,
        ParallelismArgs,
        get_config_from_file,
        LlamaConfig
    )
    from nanotron.parallel.parameters import sanity_check
    from nanotron.generation.decode import (
        GenerationInput,
        TokenizerConfig,
        decode_text,
        decode_tokenized,
    )
    from nanotron.parallel import ParallelContext
    from nanotron.parallel.pipeline_parallel.engine import (
    OneForwardOneBackwardPipelineEngine,
    )
    from nanotron.trainer import CONFIG_TO_MODEL_CLASS, mark_tied_parameters
    from nanotron.parallel.tensor_parallel.enum import TensorParallelLinearMode
    from nanotron.random import (
    RandomStates,
    get_current_random_state,
    get_synced_random_state,
    set_random_seed,
    )
    import nanotron
    from pathlib import Path
    # settings
    mla_patch_nt()
    config = get_config_from_file((Path(model_path_nt) / "config.yaml").as_posix())
    model_config = config.model.model_config
    tokenizer = AutoTokenizer.from_pretrained(model_path_hf)
    if tokenizer.pad_token_id is None:
        if tokenizer.eos_token_id is not None:
            tokenizer.pad_token_id = tokenizer.eos_token_id
        elif getattr(model.config, "pad_token_id", None) is not None:
            tokenizer.pad_token_id = int(model.config.pad_token_id)
        elif getattr(model.config, "eos_token_id", None) is not None:
            tokenizer.pad_token_id = int(model.config.eos_token_id)
        else:
            tokenizer.add_special_tokens({"pad_token": "[PAD]"})
    tokenizer.padding_side = "left"
    tokenizer.truncation_side = "left"  # TODO @nouamane: do we want this?
    parallel_config = ParallelismArgs(
        dp=1,
        pp=1,
        tp=1,
        pp_engine=OneForwardOneBackwardPipelineEngine(),
        tp_mode=TensorParallelLinearMode.ALL_REDUCE,
        tp_linear_async_communication=False,
    )
    parallel_context = ParallelContext(
        data_parallel_size=parallel_config.dp,
        pipeline_parallel_size=parallel_config.pp,
        tensor_parallel_size=parallel_config.tp,
    )
    dtype = torch.bfloat16
    if parallel_config.tp_mode is TensorParallelLinearMode.ALL_REDUCE:
        random_states = RandomStates(
            {"tp_synced": get_synced_random_state(random_state=get_current_random_state(), pg=parallel_context.tp_pg)}
        )
    else:
        # We don't need to sync across TP when using sequence parallel (REDUCE_SCATTER)
        random_states = RandomStates({})
    model_config_cls = model_config.__class__.__name__
    print(model_config_cls)
    for rope_cfg in rope_cfgs:
        for svd_cfg in svd_cfgs:
                setattr(model_config, "RoPE", rope_cfg)
                setattr(model_config, "SVD", svd_cfg)
                from nanotron.models import llama
                importlib.reload(llama)
                mla_patch_nt(rope_cfg)
                model = build_model(
                    model_builder=lambda: CONFIG_TO_MODEL_CLASS[model_config_cls](
                        config=model_config,
                        parallel_context=parallel_context,
                        parallel_config=parallel_config,
                        random_states=random_states,
                    ),
                    dtype=dtype,
                    parallel_context=parallel_context,
                )
                mark_tied_parameters(model=model, parallel_context=parallel_context, parallel_config=parallel_config)
                sanity_check(root_module=model)
                nanotron.serialize.weights.load_weights(model=model, parallel_context=parallel_context, root_folder=Path(model_path_nt))
                model.eval()
                dummy_inputs=["Hello, my dog is cute","I am a student","I am a teacher"]
                outputs = decode_text(
                    input_iter=(GenerationInput(text=text) for text in dummy_inputs),
                    tokenizer=tokenizer,
                    # TODO @thomasw21: From ModelWithLoss extract the model.
                    model=model.model,
                    parallel_context=parallel_context,
                    max_new_tokens=50,
                    max_micro_batch_size=3,
                    generation_config=GenerationArgs(sampler="greedy", use_cache=True),
                    tokenizer_config=TokenizerConfig(max_input_length=None),
                    is_bench=False,
                )
                for output in outputs:
                    print(tokenizer.decode(output.generation_ids,clean_up_tokenization_spaces=False))
                outputs = decode_text(
                    input_iter=(GenerationInput(text=text) for text in dummy_inputs),          
                    tokenizer=tokenizer,
                    # TODO @thomasw21: From ModelWithLoss extract the model.
                    model=model.model,
                    parallel_context=parallel_context,
                    max_new_tokens=50,
                    max_micro_batch_size=3,
                    generation_config=GenerationArgs(sampler="greedy", use_cache=False),
                    tokenizer_config=TokenizerConfig(max_input_length=None),
                    is_bench=False,
                )
                for output in outputs:
                    print(tokenizer.decode(output.generation_ids,clean_up_tokenization_spaces=False))
                if hasattr(model,"_store"):
                    delattr(model,"_store")
                


if __name__ == "__main__":
    # test_load_weight_hf()
    test_load_weight_nt()