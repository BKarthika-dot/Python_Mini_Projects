# Fake Job Posting Checker — Backend

A working backend implementation of the pipeline described in the project's
SRS: submit a job posting (link or pasted text) and get back a
**Safe / Suspicious / Unsafe** verdict, a confidence score, and a
human-readable explanation.

## How it works

Three signals are computed and fused into one score (see `app/pipeline.py`):

| Layer | Module | What it does |
|---|---|---|
| Rule-based heuristics | `app/feature_extraction.py` | Flags urgency language, upfront-payment requests, vague descriptions, suspicious contact emails, unrealistic salary claims |
| ML classifier | `app/classifier.py`, `train_model.py` | TF-IDF + Logistic Regression trained on `data/training_data.csv`, outputs a fraud probability |
| RAG-style retrieval | `app/knowledge_base.py`, `data/scam_patterns.json` | Finds the most similar known scam/legit patterns via cosine similarity in TF-IDF space, and uses them both to score and to explain the verdict |

`final_score = 0.30 * rule_score + 0.40 * ml_score + 0.30 * rag_score`
→ **Safe** (`< 0.35`), **Suspicious** (`0.35–0.65`), or **Unsafe** (`≥ 0.65`).

> The ML and RAG training data here are small, synthetic, template-generated
> examples meant to make the pipeline actually run end-to-end. Swap in a real
> labeled dataset (e.g. EMSCAD) and a real embedding model/vector store
> (e.g. sentence-transformers + FAISS/Chroma/Pinecone) for production use —
> the module interfaces (`predict_proba()`, `retrieve_similar()`) are
> designed so you can do that without touching the rest of the pipeline.

## Setup

```bash
pip install -r requirements.txt

# 1. Generate the synthetic training dataset (or supply your own CSV with
#    'text' and 'label' columns, label 1 = scam, 0 = legit)
python data/generate_data.py

# 2. Train the classifier (writes models/classifier.joblib and vectorizer.joblib)
python train_model.py
```

## Usage

**The primary input is a URL.** The system fetches the page, extracts the
job-relevant text (title + main content, with navigation/boilerplate/ads
stripped out via `trafilatura`, falling back to a BeautifulSoup pass if
needed), and runs it through the same rule + ML + RAG matching pipeline.
Pasted text is still supported as an alternate input mode (SRS 3.1), e.g.
for postings copied from an email or a page that blocks scraping.

### Option A — Command line (fastest way to test input → output)

```bash
# Primary flow: URL in, verdict out
python test_cli.py https://example.com/careers/job/123

# Equivalent explicit form
python test_cli.py --url "https://example.com/careers/job/123"

# Alternate flow: pasted text
python test_cli.py --text "Urgent hiring! Pay a $99 registration fee to start earning $2000/week from home."
```

On a bad/unreachable URL you get a clear error instead of a crash, e.g.:
`Error: The job posting URL returned 404 Not Found: https://example.com/careers/job/123`

### Option B — Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Then either open **http://127.0.0.1:8000/docs** for interactive Swagger UI, or call it directly.

**Primary endpoint — just a URL:**

```bash
curl -X POST http://127.0.0.1:8000/classify-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/careers/job/123"}'
```

**General endpoint — URL or pasted text:**

```bash
curl -X POST http://127.0.0.1:8000/classify \
  -H "Content-Type: application/json" \
  -d '{
        "input_type": "text",
        "content": "Congratulations! You have been selected. Pay a refundable security deposit of $150 to confirm your slot.",
        "company_domain": null
      }'
```

Sample response:

```json
{
  "source_url": null,
  "category": "Unsafe",
  "confidence_score": 0.734,
  "rule_based_score": 0.5,
  "ml_score": 0.711,
  "rag_score": 1.0,
  "explanation": [
    "Upfront payment / fee request detected: security deposit",
    "Job description is unusually short or vague",
    "Excessive use of exclamation marks"
  ],
  "matched_patterns": [ ... ],
  "extracted_text_preview": "..."
}
```

## Project layout

```
app/
  main.py               FastAPI app (/health, /classify, /classify-url)
  schemas.py             Pydantic request/response models
  feature_extraction.py  Rule-based heuristic layer
  classifier.py          ML classifier wrapper (loads trained model)
  knowledge_base.py      RAG-style retrieval over known scam/legit patterns
  pipeline.py             Orchestrates rule + ML + RAG -> final verdict
  scraper.py              Fetches a URL and extracts clean job-posting text
                          (trafilatura primary, BeautifulSoup fallback)
data/
  generate_data.py        Builds the synthetic training dataset
  training_data.csv        (generated)
  scam_patterns.json        Knowledge base used for RAG retrieval
models/                     (generated) classifier.joblib, vectorizer.joblib
train_model.py               Trains and saves the ML classifier
test_cli.py                   Command-line entry point for quick testing
requirements.txt
```

## Notes

- The `url` input mode requires outbound internet access to the target job
  site from wherever this runs. Fetch failures (404, timeout, blocked,
  non-HTML response, JS-only page with no extractable text, etc.) raise a
  clear error message rather than crashing.
- This maps directly onto the SRS/WBS document produced earlier: sections
  3.1–3.6 (Input Handling, Feature Extraction, RAG Classification,
  Classification & Scoring, Reporting & Feedback, Administrative modules) and
  the "5.1 REST API / 5.2 ML Classifier / 5.3 RAG Pipeline" work packages in
  the WBS.
- Not yet implemented (left as next steps per the WBS): PostgreSQL
  persistence for submissions/users, the admin dashboard UI, authentication,
  and the report/feedback retraining loop.
