"""FastAPI app: classification, JWT auth + roles, history, feedback loop, admin APIs, web UI."""
import csv, datetime as dt, hashlib, hmac, json, os
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .classifier import ScamClassifier
from .db import Base, Company, SessionLocal, Submission, User, engine, get_db
from .knowledge_base import KnowledgeBase
from .pipeline import ClassificationPipeline
from .schemas import ClassifyRequest, ClassifyResponse, ClassifyUrlRequest

BASE = Path(__file__).resolve().parent.parent
STATIC_DIR, DATA_DIR = BASE / "static", BASE / "data"
SECRET = os.getenv("JOBCHECK_SECRET", "dev-secret-change-me")

app = FastAPI(title="Fake Job Posting Checker API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
pipeline = ClassificationPipeline()
Base.metadata.create_all(engine)


# ---------- auth helpers ----------
def hash_pw(p, salt=None):
    salt = salt or os.urandom(16).hex()
    return f"{salt}${hashlib.pbkdf2_hmac('sha256', p.encode(), bytes.fromhex(salt), 100_000).hex()}"


def check_pw(p, stored):
    return hmac.compare_digest(hash_pw(p, stored.split("$")[0]), stored)


def make_token(u: User):
    return jwt.encode({"sub": str(u.id), "role": u.role, "exp": dt.datetime.utcnow() + dt.timedelta(hours=12)}, SECRET, "HS256")


def current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return db.get(User, int(jwt.decode(authorization[7:], SECRET, ["HS256"])["sub"]))
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


def require_user(u: Optional[User] = Depends(current_user)):
    if not u:
        raise HTTPException(401, "Login required")
    return u


def require_admin(u: User = Depends(require_user)):
    if u.role != "admin":
        raise HTTPException(403, "Administrator access required")
    return u


with SessionLocal() as _db:  # seed a default admin on first run
    if not _db.query(User).filter_by(role="admin").first():
        _db.add(User(email="admin@jobcheck.local", pw_hash=hash_pw("admin123"), role="admin"))
        _db.commit()
        print("[auth] Seeded admin: admin@jobcheck.local / admin123  (change this!)")


class Creds(BaseModel):
    email: str
    password: str


@app.post("/auth/register")
def register(c: Creds, db: Session = Depends(get_db)):
    if len(c.password) < 6 or "@" not in c.email:
        raise HTTPException(400, "Enter a valid email and a password of 6+ characters")
    if db.query(User).filter_by(email=c.email.lower()).first():
        raise HTTPException(400, "Email already registered")
    u = User(email=c.email.lower(), pw_hash=hash_pw(c.password), role="job_seeker")
    db.add(u); db.commit()
    return {"token": make_token(u), "role": u.role, "email": u.email}


@app.post("/auth/login")
def login(c: Creds, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(email=c.email.lower()).first()
    if not u or not check_pw(c.password, u.pw_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": make_token(u), "role": u.role, "email": u.email}


# ---------- classification ----------
def _run(input_type, content, domain, user, db):
    try:
        r = pipeline.classify(input_type, content, domain)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Could not process submission: {e}")
    host = (domain or (urlparse(content).hostname if input_type == "url" else "") or "").lower().removeprefix("www.")
    co = db.query(Company).filter_by(domain=host).first() if host else None
    if co and co.status == "blacklist":
        r["confidence_score"] = max(r["confidence_score"], 0.9)
        r["explanation"].insert(0, f"Employer domain {host} is on the administrator blacklist")
    elif co and co.status == "whitelist":
        r["confidence_score"] = round(r["confidence_score"] * 0.6, 3)
        r["explanation"].insert(0, f"Employer domain {host} is on the verified whitelist")
    s = r["confidence_score"]
    r["category"] = "Unsafe" if s >= 0.65 else "Suspicious" if s >= 0.35 else "Safe"
    sub = Submission(user_id=user.id if user else None, input_type=input_type, source_url=r["source_url"],
                     content=(r.get("full_text") or r["extracted_text_preview"])[:5000], category=r["category"], confidence=s,
                     rule_score=r["rule_based_score"], ml_score=r["ml_score"], rag_score=r["rag_score"],
                     explanation=json.dumps(r["explanation"]))
    db.add(sub); db.commit()
    r["submission_id"] = sub.id
    return r


@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest, db: Session = Depends(get_db), user: Optional[User] = Depends(current_user)):
    return _run(req.input_type, req.content, req.company_domain, user, db)


@app.post("/classify-url", response_model=ClassifyResponse)
def classify_url(req: ClassifyUrlRequest, db: Session = Depends(get_db), user: Optional[User] = Depends(current_user)):
    return _run("url", req.url, req.company_domain, user, db)


def _row(s: Submission):
    return {"id": s.id, "category": s.category, "confidence": s.confidence, "source_url": s.source_url,
            "preview": (s.content or "")[:200], "status": s.feedback_status, "suggested_label": s.suggested_label,
            "final_label": s.final_label, "created_at": s.created_at.isoformat()}


@app.get("/history")
def history(u: User = Depends(require_user), db: Session = Depends(get_db)):
    return [_row(s) for s in db.query(Submission).filter_by(user_id=u.id).order_by(Submission.id.desc()).limit(50)]


class Report(BaseModel):
    suggested_label: int  # 1 = actually a scam, 0 = actually legit


@app.post("/submissions/{sid}/report")
def report(sid: int, body: Report, u: User = Depends(require_user), db: Session = Depends(get_db)):
    s = db.get(Submission, sid)
    if not s:
        raise HTTPException(404, "Submission not found")
    s.feedback_status, s.suggested_label = "reported", int(body.suggested_label)
    db.commit()
    return {"ok": True}


# ---------- admin ----------
@app.get("/admin/review")
def review_queue(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.query(Submission).filter(Submission.final_label.is_(None)).filter(
        (Submission.feedback_status == "reported") | (Submission.category == "Suspicious")).order_by(Submission.id.desc()).limit(100)
    return [_row(s) for s in q]


class Resolve(BaseModel):
    label: int


@app.post("/admin/submissions/{sid}/resolve")
def resolve(sid: int, body: Resolve, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = db.get(Submission, sid)
    if not s:
        raise HTTPException(404, "Submission not found")
    s.final_label, s.feedback_status = int(body.label), "confirmed"
    db.commit()
    return {"ok": True}


class CompanyIn(BaseModel):
    domain: str
    status: str  # whitelist | blacklist


@app.get("/admin/companies")
def companies(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [{"id": c.id, "domain": c.domain, "status": c.status} for c in db.query(Company).order_by(Company.domain)]


@app.post("/admin/companies")
def add_company(c: CompanyIn, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    d = c.domain.lower().strip().removeprefix("www.")
    if c.status not in ("whitelist", "blacklist") or not d:
        raise HTTPException(400, "Provide a domain and status whitelist|blacklist")
    row = db.query(Company).filter_by(domain=d).first() or Company(domain=d, status=c.status)
    row.status = c.status
    db.add(row); db.commit()
    return {"ok": True}


@app.delete("/admin/companies/{cid}")
def del_company(cid: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    db.query(Company).filter_by(id=cid).delete(); db.commit()
    return {"ok": True}


class PatternIn(BaseModel):
    label: str  # scam | legit
    description: str
    text: Optional[str] = None


def _patterns():
    return json.loads((DATA_DIR / "scam_patterns.json").read_text(encoding="utf-8"))


def _save_patterns(p):
    (DATA_DIR / "scam_patterns.json").write_text(json.dumps(p, indent=2), encoding="utf-8")
    pipeline.kb = KnowledgeBase()  # re-embed with the updated knowledge base


@app.get("/patterns")
def patterns():
    return [{"id": p["id"], "label": p["label"], "description": p["description"]} for p in pipeline.kb.patterns]


@app.post("/admin/patterns")
def add_pattern(p: PatternIn, _: User = Depends(require_admin)):
    if p.label not in ("scam", "legit") or not p.description.strip():
        raise HTTPException(400, "Provide label scam|legit and a description")
    items, pre = _patterns(), "SP" if p.label == "scam" else "LP"
    n = max([int(x["id"][2:]) for x in items if x["id"].startswith(pre)] + [0]) + 1
    items.append({"id": f"{pre}{n:03d}", "label": p.label, "description": p.description.strip(), "text": (p.text or p.description).strip()})
    _save_patterns(items)
    return {"ok": True}


@app.delete("/admin/patterns/{pid}")
def del_pattern(pid: str, _: User = Depends(require_admin)):
    _save_patterns([x for x in _patterns() if x["id"] != pid])
    return {"ok": True}


@app.get("/admin/analytics")
def analytics(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    by_cat = dict(db.query(Submission.category, func.count()).group_by(Submission.category).all())
    conf = db.query(Submission).filter(Submission.final_label.isnot(None)).all()
    agree = sum((s.category == "Unsafe") == (s.final_label == 1) for s in conf)
    return {"total": db.query(Submission).count(), "by_category": by_cat, "users": db.query(User).count(),
            "reported_pending": db.query(Submission).filter_by(feedback_status="reported").count(),
            "confirmed_labels": len(conf), "awaiting_retrain": sum(not s.used_for_training for s in conf),
            "model_agreement": round(agree / len(conf), 3) if conf else None}


@app.post("/admin/retrain")
def retrain(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Submission).filter(Submission.final_label.isnot(None), Submission.used_for_training.is_(False)).all()
    if not rows:
        raise HTTPException(400, "No newly confirmed labels to learn from")
    with open(DATA_DIR / "training_data.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for s in rows:
            w.writerow([" ".join((s.content or "").split()), s.final_label])
            s.used_for_training = True
    db.commit()
    pipeline.classifier = ScamClassifier(force_retrain=True)
    pipeline.kb = KnowledgeBase()
    return {"ok": True, "added_examples": len(rows)}


# ---------- UI ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin", include_in_schema=False)
def admin_page():
    return FileResponse(STATIC_DIR / "admin.html")
