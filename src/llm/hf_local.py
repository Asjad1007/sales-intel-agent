# src/llm/hf_local.py
import os, json, re, torch
from typing import Dict, List
from transformers import AutoTokenizer, AutoModelForCausalLM

DEFAULT_MODEL = os.getenv("HF_MODEL_ID", "microsoft/Phi-3-mini-4k-instruct")
# Good small choices:
# - "microsoft/Phi-3-mini-4k-instruct" (~3.8B, very light)
# - "Qwen/Qwen2.5-3B-Instruct"
# - "mistralai/Mistral-7B-Instruct-v0.3" (better quality, still modest)

class HFLocalLLM:
    def __init__(self, model_id: str = DEFAULT_MODEL, load_4bit: bool = False):
        self.model_id = model_id
        # Tokenizer
        self.tok = AutoTokenizer.from_pretrained(model_id, use_fast=True)
        # Load model on GPU(s)
        quant_args = {}
        if load_4bit:
            try:
                from transformers import BitsAndBytesConfig
                quant_args["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
            except Exception:
                pass
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            **quant_args
        )
        # decoder-only models need a pad token for batching sometimes
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        self.tok.padding_side = "left"

    @torch.inference_mode()
    def chat_json(self, system: str, user: str, max_new_tokens: int = 256) -> Dict:
        # Build chat messages & apply the model's chat template
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        text = self.tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tok(text, return_tensors="pt").to(self.model.device)
        out = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,           # deterministic
            temperature=0.0,
            pad_token_id=self.tok.pad_token_id,
            eos_token_id=self.tok.eos_token_id
        )
        gen = self.tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        # Extract JSON block
        s, e = gen.find("{"), gen.rfind("}")
        if s != -1 and e != -1 and s < e:
            try:
                return json.loads(gen[s:e+1])
            except Exception:
                pass
        # last-resort simple fence
        m = re.search(r"\{.*\}\s*$", gen, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return {}
