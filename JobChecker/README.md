# JobCheck — Fake Job Posting Checker

A web application and REST API that checks a job posting (a link or pasted text) and returns a
**Safe / Suspicious / Unsafe** verdict with a confidence score and a plain-language explanation.
Users can report wrong verdicts, and administrators confirm them and retrain the model.

## Features

| Area | What it does |
|---|---|
| **Checker** | Accepts a job URL (fetched and cleaned automatically) or pasted text, plus an optional company domain |
| **Three-signal detection** | Rule-based checks + XGBoost ML classifier + knowledge-base retrieval, fused into one score |
| **Explanations** | Lists the red flags found and the known scam patterns the posting resembles |
| **Accounts** | Register / log in with JWT tokens; roles: Job Seeker and Administrator |
| **History** | Logged-in users can list their previous checks |
| **Feedback loop** | Users report a wrong verdict, an admin confirms the true label, then retrains the model on confirmed labels |
| **Admin dashboard** | Review queue, whitelist/blacklist of employer domains, knowledge-base management, analytics |
| **Persistence** | SQLAlchemy models for users, submissions (with results) and companies; SQLite by default |

## How the verdict is computed

Three scores, each between 0 and 1:

- **Rule score** — hand-written checks: urgency language, upfront fee requests, free-email contacts, vague text, unrealistic salary claims.
- **ML score** — XGBoost's estimated probability that the text is a scam, using TF-IDF features. For long pages, only the opening and the sentences containing red-flag terms are fed to the model, so a short scam section is not diluted.
- **Retrieval score** — the 3 most similar patterns are retrieved from the knowledge base; the score is the scam-labelled share of their similarity weight.

```
final = 0.30 × rule + 0.40 × ML + 0.30 × retrieval

final < 0.35        → Safe
0.35 ≤ final < 0.65 → Suspicious
final ≥ 0.65        → Unsafe
```

After scoring, the admin lists apply: a **blacklisted** employer domain forces the score to at least 0.9;
a **whitelisted** domain multiplies the score by 0.6. The category is then recalculated.

## Quick start

Requires Python 3.10+.

```bash
pip install -r requirements.txt
python data/generate_data.py      # creates data/training_data.csv (skip if it already exists)
python run.py                     # starts the server and opens http://127.0.0.1:8000
```

You can also run `uvicorn app.main:app --port 8000` and open the URL yourself.

- The first start trains the classifier automatically, so it may take a moment.
- The SQLite database `fjpc.db` is created on first run. Delete it (with the server stopped) to reset all data.
- If you see scikit-learn / XGBoost version warnings, delete `models/classifier.joblib` and
  `models/vectorizer.joblib` and restart. They are regenerated using your installed versions.

### Default administrator

`admin@jobcheck.local` / `admin123`, created on first run. **Change it** and set `JOBCHECK_SECRET`
before using the project anywhere beyond your own machine. New registrations are always Job Seekers.

### Configuration

| Environment variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy database URL (e.g. `postgresql://user:pass@localhost:5432/jobcheck`, needs `psycopg2-binary`) | `sqlite:///fjpc.db` |
| `JOBCHECK_SECRET` | Key used to sign JWT tokens | `dev-secret-change-me` |

## Using the web app

1. Open **http://127.0.0.1:8000**.
2. Choose **Job URL** or **Paste text**, fill it in, and click **Check job posting**. Use the *scam example* /
   *legit example* links for a quick demo.
3. The result shows the verdict, the three score rings, the fraud-likelihood bar, the reasons it was flagged and the matching patterns.
4. To report a wrong verdict, log in (nav bar) and click **Report wrong verdict**.
5. As an administrator, open **/admin**:
   - **Review queue** — Suspicious posts and reported verdicts; confirm each as Scam or Legit, then click **Retrain model on confirmed labels**.
   - **Whitelist / Blacklist** — manage employer domains.
   - **Knowledge base** — add or remove scam / legitimate patterns.
   - **Analytics** — totals, verdict counts, pending reports, and how often the model agreed with confirmed labels.

## API

Interactive docs: **http://127.0.0.1:8000/docs**

| Method & path | Access | Purpose |
|---|---|---|
| `POST /classify-url` | public (optional token) | Check a job URL: `{"url": "...", "company_domain": null}` |
| `POST /classify` | public (optional token) | Check a URL or text: `{"input_type": "text", "content": "..."}` |
| `POST /auth/register`, `POST /auth/login` | public | Returns `{token, role, email}` |
| `GET /history` | logged in | Your previous checks |
| `POST /submissions/{id}/report` | logged in | Report a wrong verdict: `{"suggested_label": 1}` (1 = scam, 0 = legit) |
| `GET /admin/review` | admin | Review queue |
| `POST /admin/submissions/{id}/resolve` | admin | Confirm the true label: `{"label": 1}` |
| `GET/POST/DELETE /admin/companies` | admin | Whitelist / blacklist |
| `POST/DELETE /admin/patterns` | admin | Manage knowledge-base patterns |
| `GET /admin/analytics` | admin | Dashboard statistics |
| `POST /admin/retrain` | admin | Append confirmed labels to the training data and retrain |
| `GET /patterns`, `GET /health` | public | Knowledge-base patterns, health check |

Send the token as `Authorization: Bearer <token>`.

Example:

```bash
curl -X POST http://127.0.0.1:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"input_type":"text","content":"Urgent hiring! Pay a $99 registration fee to start."}'
```

## Command-line tools

```bash
python test_cli.py https://example.com/careers/job/123       # check a URL
python test_cli.py --text "Pay a registration fee..."         # check pasted text
python module_demo.py --text "Pay a registration fee..."      # show each module's output separately
```

`module_demo.py` prints the output of each stage (input handling, rules, retrieval, ML, score fusion), which is useful for reports and demos.

## Project layout

```
run.py                     Starts the server and opens the browser
app/
  main.py                  FastAPI app: classification, auth, feedback, admin APIs, serves the UI
  db.py                    SQLAlchemy models: User, Submission, Company
  schemas.py               Request/response models
  pipeline.py              Runs rules + ML + retrieval and fuses the scores
  feature_extraction.py    Rule-based checks
  classifier.py            XGBoost classifier (self-trains from data/training_data.csv)
  knowledge_base.py        Retrieval over known scam / legitimate patterns
  scraper.py               URL fetch (session, retries) and text extraction
static/
  index.html               Checker UI
  admin.html               Admin dashboard
data/
  generate_data.py         Builds the synthetic training dataset
  training_data.csv        Training data (generated; retraining appends to it)
  scam_patterns.json       Knowledge base patterns
models/                    Generated: classifier.joblib, vectorizer.joblib
train_model.py             Standalone Logistic Regression baseline (see note below)
test_cli.py, module_demo.py
requirements.txt
```

## Optional: semantic retrieval

`knowledge_base.py` can use TF-IDF similarity (matches shared words) or a **sentence-transformers** embedding
model (matches meaning, so reworded scams still match). The semantic version needs
`pip install sentence-transformers` and downloads a small model (~80 MB) on first run, so it needs internet
access once. Both versions expose the same interface, so nothing else changes.

## Known limitations

- **Training data is synthetic.** The ML model is trained on template-generated examples, so its near-perfect test accuracy only shows the pipeline works, not real-world accuracy. Replace it with a real dataset (e.g. EMSCAD) and report precision, recall and F1 for a proper evaluation.
- **Score weights and thresholds are set by hand** (0.30 / 0.40 / 0.30, and 0.35 / 0.65), and the ML score is not a calibrated probability.
- **Retrieval, not full RAG.** The retrieval layer finds similar patterns and uses them to score and explain, but no language model generates the explanation.
- **Some sites block scraping.** Large job boards (Indeed, LinkedIn) often return 403 even with the session and retry logic. Paste the text instead.
- **Retraining is manual and simple.** One click retrains the whole model on the original data plus confirmed labels; there is no scheduling or model versioning.
- **`train_model.py` overwrites the XGBoost model.** It trains a Logistic Regression baseline and writes to the same `models/` files. Delete those files and restart to return to XGBoost.
- **Security hardening still to do:** CORS is open (`*`), there is no rate limiting, and the scraper does not block internal addresses (SSRF). Fix these before any public deployment.
- Results are advisory. Always verify an employer independently before paying or sharing personal details.