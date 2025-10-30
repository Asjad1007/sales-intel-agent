# 🧠 Sales Intelligence AI Agent  
**Fully headless, HPC-ready AI agent for automated company research and personalized outreach generation.**

![HuggingFace](https://img.shields.io/badge/HuggingFace-Transformers-orange?logo=huggingface)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?logo=sqlite)
![Slurm](https://img.shields.io/badge/HPC-Slurm-green?logo=linux)

---

## 🚀 Overview
This project builds an **end-to-end Sales Intelligence Agent** that autonomously:
1. **Collects** public company signals (RSS feeds, job postings, etc.).
2. **Scores** companies for “buying intent.”
3. **Retrieves** relevant evidence via vector search (FAISS).
4. **Generates** concise, evidence-cited outreach emails using a **Hugging Face LLM** — all fully offline on HPC GPUs.

It’s a production-style example of an **AI-driven data + generation pipeline** — no APIs, no UI, and fully privacy-safe.

---

## 🧩 Features
✅ **Data Ingestion:**  
Fetches company updates from RSS/press feeds and job boards, normalizes them into structured “event” data.  

✅ **Feature Extraction & Scoring:**  
Identifies hiring surges, funding events, or compliance mentions via regex + rules to rank intent signals.  

✅ **Retrieval-Augmented Generation (RAG):**  
Uses a FAISS embedding index to retrieve contextual evidence for top-ranked companies.  

✅ **LLM Draft Generation (HF-only):**  
Generates JSON-structured email drafts (`subject`, `body`, `sources`) using small open-weight models like **Phi-3-Mini** or **Mistral-7B**.  

✅ **HPC-Optimized:**  
Runs on UVA’s HPC cluster with **Slurm**, supports GPU inference, 4-bit quantization, and batch job scheduling.  

✅ **Headless CLI:**  
Everything runs via a clean CLI (`python -m src.cli ...`) — no web server or frontend.

---

## 🧠 System Architecture
```
companies.yaml ─▶ ingest (RSS, Jobs)
                     ↓
                  events.db
                     ↓
         feature extraction + scoring
                     ↓
          account_scores_daily
                     ↓
     embedding index (FAISS vectors)
                     ↓
      evidence context (contexts.json)
                     ↓
     Hugging Face LLM (draft.py)
                     ↓
    drafts table + .json + .md outputs
```

---

## 📂 Project Structure
```
sales-intel-agent/
│
├── config/
│   ├── companies.yaml        # companies + data sources
│   └── rules.yaml            # scoring weights
│
├── data/
│   ├── raw/                  # cached RSS + job HTML
│   ├── processed/            # evidence bundles (contexts.json)
│   ├── vectors/              # FAISS index files
│   └── drafts/               # generated emails (.json + .md)
│
├── db/
│   ├── schema.sql            # SQLite schema
│   └── salesintel.db         # main database
│
├── src/
│   ├── cli.py                # Typer CLI entrypoint
│   ├── ingest/               # RSS + job data collectors
│   ├── features/             # signal extractor
│   ├── score/                # scoring engine
│   ├── rag/                  # embedding + retrieval
│   ├── llm/                  # Hugging Face draft generator
│   └── delivery/             # approval/sending logic
│
├── logs/                     # job logs
├── run_salesagent_hf.slurm   # HPC job script
└── requirements.txt
```

---

## ⚙️ Installation

### 1. Clone & setup environment
```bash
git clone <repo-url>
cd sales-intel-agent
python3 -m venv NewEnv
source NewEnv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
Edit:
- `config/companies.yaml` → target companies + RSS/job URLs.
- `config/rules.yaml` → adjust feature weights.

### 3. Initialize database
```bash
sqlite3 db/salesintel.db < db/schema.sql
```

---

## 🧮 Usage

### Local / Interactive
```bash
source NewEnv/bin/activate
export HF_MODEL_ID="microsoft/Phi-3-mini-4k-instruct"
export HF_4BIT=1
export HF_MAX_NEW_TOKENS=512

python -m src.cli ingest
python -m src.cli score
python -m src.cli draft --top-n 10 --variants 1
```

### HPC (Slurm)
```bash
sbatch run_salesagent_hf.slurm
```

### Outputs
- Email drafts → `data/drafts/`
- DB entries → `db/salesintel.db`
- Logs → `logs/`

---

## 🧰 Key Technologies
| Category | Tools |
|-----------|-------|
| Language | Python 3.11 |
| LLM | Hugging Face Transformers (Phi-3, Mistral, Qwen) |
| Retrieval | FAISS, sentence-transformers |
| Data | SQLite, YAML |
| Web Scraping | httpx, BeautifulSoup |
| Workflow | Typer CLI, Slurm |
| Validation | Pydantic |
| HPC | CUDA, bitsandbytes (4-bit), Slurm job scheduler |

---

## 🧪 Example Output
```markdown
# Streamline Compliance and Onboarding with AI

Leverage AI to enhance your fintech operations. Sanas uses AI for accent modification,
Substack secures funding for growth, and Capsule innovates with AI for video editing.

Sources:
https://techcrunch.com/...sanas...,
https://techcrunch.com/...substack...,
https://techcrunch.com/...capsule...
```

---

## 📊 Next Improvements
- [ ] Add automatic daily scheduling (cron or recurring Slurm job)
- [ ] Expand data sources (BuiltWith, Crunchbase, Product Hunt)
- [ ] Add semantic deduplication & draft quality scoring
- [ ] Streamlit dashboard for browsing drafts & scores

---

## 🧑‍💻 Author
**Asjad [Your Last Name]**  
*AI Engineer / Data Engineer*  
University of Virginia – HPC-based Applied AI Research  
📧 asjad@virginia.edu
