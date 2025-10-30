# src/llm/draft.py  -- Hugging Face 

import os, json, uuid, re, time
from typing import List, Dict
from pydantic import BaseModel, Field
from src.util.io import db, now_iso, write_json, read_json
from src.util.log import info

# -------------------------------
# Model config (small + fast)
# -------------------------------
HF_MODEL_ID = os.environ.get("HF_MODEL_ID", "microsoft/Phi-3-mini-4k-instruct")  # or: Qwen/Qwen2.5-3B-Instruct, mistralai/Mistral-7B-Instruct-v0.3
HF_MAX_NEW_TOKENS = int(os.environ.get("HF_MAX_NEW_TOKENS", "512"))
HF_LOAD_4BIT = bool(int(os.environ.get("HF_4BIT", "0")))  # set HF_4BIT=1 if VRAM is tight

# -------------------------------
# Output schema
# -------------------------------
class Draft(BaseModel):
    subject: str = Field(..., max_length=70)
    body: str    # keep under ~120 words
    sources: List[str]

# -------------------------------
# Singleton model loader
# -------------------------------
_HF = {"tok": None, "model": None}

def _ensure_model():
    if _HF["tok"] is not None:
        return _HF["tok"], _HF["model"]

    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch

    tok = AutoTokenizer.from_pretrained(HF_MODEL_ID, use_fast=True)

    qargs = {}
    if HF_LOAD_4BIT:
        try:
            from transformers import BitsAndBytesConfig
            qargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
        except Exception:
            pass

    model = AutoModelForCausalLM.from_pretrained(
        HF_MODEL_ID,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
        **qargs
    )

    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.padding_side = "left"

    _HF["tok"], _HF["model"] = tok, model
    return tok, model

# -------------------------------
# Prompt helpers
# -------------------------------
def _build_prompt(icp_tags: List[str], evidence: List[Dict]) -> str:
    ev_lines = "\n".join(f"- {e.get('title','')[:80]} :: {e.get('url','')}" for e in evidence)
    return (
        "SYSTEM:\n"
        "You are a concise B2B SDR assistant. Use ONLY the evidence links provided.\n"
        "Return JSON ONLY with keys exactly: subject, body, sources. No extra text or markdown.\n"
        "Constraints:\n"
        "- <= 120 words total in `body`\n"
        "- 1 paragraph + 1 short CTA line\n"
        "- Cite 1-3 URLs you used in `sources` (array of strings)\n\n"
        "USER:\n"
        f"ICP_TAGS: {', '.join(icp_tags)}\n"
        "VALUE_PROP: Help automate compliance and accelerate onboarding with minimal engineering effort.\n"
        "EVIDENCE:\n"
        f"{ev_lines}\n"
    )

# _JSON_FENCE = re.compile(r"\{(?:[^{}]|(?R))*\}", re.S)
_JSON_FENCE = re.compile(r"\{.*?\}", re.S)

def _extract_json(text: str) -> Dict:
    if not text:
        return {}
    matches = _JSON_FENCE.findall(text)
    for candidate in reversed(matches):  # prefer the last JSON block
        try:
            return json.loads(candidate)
        except Exception:
            continue
    return {}

# -------------------------------
# HF generate (chat template)
# -------------------------------
def _generate_json(prompt: str) -> Dict:
    tok, model = _ensure_model()
    system = "Return ONLY valid JSON with keys: subject, body, sources. No prose."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(text, return_tensors="pt").to(model.device)

    import torch
    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=HF_MAX_NEW_TOKENS,
            do_sample=False,
            temperature=0.0,
            pad_token_id=tok.pad_token_id,
            eos_token_id=tok.eos_token_id,
        )

    gen = tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
    data = _extract_json(gen)

    # If model forgot sources, keep pipeline moving (we’ll fill later)
    if "sources" not in data or not isinstance(data.get("sources"), list):
        data["sources"] = []
    return data

# -------------------------------
# Main draft function (CLI calls this)
# -------------------------------
def make_drafts(top_n: int = 10, variants: int = 2):
    contexts = read_json("data/processed/contexts.json") if os.path.exists("data/processed/contexts.json") else {}

    conn = db(); cur = conn.cursor()
    cur.execute("SELECT company_id, name, icp_tags FROM companies")
    cmap = {r[0]: {"name": r[1], "icp": [t for t in (r[2] or '').split(',') if t]} for r in cur.fetchall()}

    made = 0
    for cid, evid in contexts.items():
        icp = cmap.get(int(cid), {}).get("icp", [])
        evid_urls = [e.get("url","") for e in evid if e.get("url")]

        for v in range(variants):
            prompt = _build_prompt(icp, evid)

            # call HF model (retry lightly)
            data = {}
            for attempt in range(2):
                try:
                    data = _generate_json(prompt)
                    break
                except Exception:
                    time.sleep(1.0 + attempt)

            # validate into Draft; fallback if invalid
            try:
                if not data.get("sources"):
                    data["sources"] = evid_urls[:3]
                d = Draft(**data)
            except Exception:
                d = Draft(
                    subject="[fallback] Quick idea",
                    body="We saw relevant updates and can help. Open to a 15-min chat?",
                    sources=evid_urls[:2]
                )

            did = str(uuid.uuid4())[:8]
            draft_rec = {
                "draft_id": did,
                "company_id": int(cid),
                "created_at": now_iso(),
                "persona": "sdr",
                "variant": v,
                "subject": d.subject,
                "body": d.body,
                "evidence_json": json.dumps(evid),
                "status": "queued",
                "metrics_json": "{}"
            }

            cur.execute(
                """INSERT OR REPLACE INTO drafts
                   (draft_id, company_id, created_at, persona, variant, subject, body, evidence_json, status, metrics_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (did, int(cid), draft_rec["created_at"], "sdr", v, d.subject, d.body, draft_rec["evidence_json"], "queued", "{}")
            )

            os.makedirs("data/drafts", exist_ok=True)
            # JSON file
            write_json(f"data/drafts/{cmap[int(cid)]['name'].replace(' ','_')}_{did}.json", draft_rec)
            # MD file
            md_path = f"data/drafts/{cmap[int(cid)]['name'].replace(' ','_')}_{did}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("# " + d.subject + "\n\n" + d.body + "\n\n" + "Sources: " + ", ".join(evid_urls[:3]))

            made += 1

    conn.commit()
    info(f"Drafted {made} emails.")