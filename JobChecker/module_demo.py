#!/usr/bin/env python3
"""
Module-wise demonstration script.

Runs each pipeline module independently and prints its own output.
Usage:
    python module_demo.py --text "software engineering job offer - internship for 1year with 25000 stipend pay 2000rs registration free and unlock multiple benefits"
    python module_demo.py --url "http://localhost:8000"
"""
import argparse
import json

from app.classifier import ScamClassifier
from app.feature_extraction import compute_rule_score
from app.knowledge_base import KnowledgeBase
from app.scraper import fetch_job_posting

RULE_WEIGHT, ML_WEIGHT, RAG_WEIGHT = 0.30, 0.40, 0.30
SAFE_THRESHOLD, UNSAFE_THRESHOLD = 0.35, 0.65


def section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="Show each pipeline module's output separately.")
    parser.add_argument("--text", help="Pasted job posting text")
    parser.add_argument("--url", help="Job posting URL")
    parser.add_argument("--company-domain", default=None, help="Optional known employer domain")
    args = parser.parse_args()
    if not args.text and not args.url:
        parser.error("Provide --text or --url")

    # ---------------- Module 1: Input Handling ----------------
    section("MODULE 1 -- INPUT HANDLING  (app/scraper.py)")
    if args.url:
        print(f"Input type  : url")
        print(f"Source URL  : {args.url}")
        text = fetch_job_posting(args.url)
        print(f"Extraction  : trafilatura (falls back to BeautifulSoup if needed)")
    else:
        print(f"Input type  : text")
        text = args.text

    print(f"Text length : {len(text)} characters")
    preview = text[:300] + ("..." if len(text) > 300 else "")
    print(f"Preview     : {preview}")

    # ---------------- Module 2: Feature Extraction (rule-based) ----------------
    section("MODULE 2 -- FEATURE EXTRACTION / RULE-BASED HEURISTICS  (app/feature_extraction.py)")
    rule_score, rule_flags = compute_rule_score(text, company_domain=args.company_domain)
    print(f"Rule-based score : {rule_score:.3f}   (0 = no red flags, 1 = many red flags)")
    print("Flags triggered  :")
    for f in (rule_flags or ["(none)"]):
        print(f"  - {f}")

    # ---------------- Module 3: RAG Retrieval ----------------
    section("MODULE 3 -- RAG RETRIEVAL  (app/knowledge_base.py)")
    kb = KnowledgeBase()
    rag_score, matches = kb.rag_score(text, k=3)
    print(f"RAG score        : {rag_score:.3f}   (similarity-weighted fraction pointing to scam patterns)")
    print("Top-3 matches    :")
    for m in matches:
        print(f"  [{m['label'].upper():5}] sim={m['similarity']:.3f}  {m['pattern_id']} - {m['description']}")

    # ---------------- Module 4: ML Classifier ----------------
    section("MODULE 4 -- ML CLASSIFIER  (app/classifier.py)")
    clf = ScamClassifier()
    ml_score = clf.predict_proba(text)
    print(f"ML fraud probability : {ml_score:.3f}   (TF-IDF + Logistic Regression, P(class=scam))")

    # ---------------- Module 5: Score Fusion / Final Classification ----------------
    section("MODULE 5 -- SCORE FUSION & FINAL CLASSIFICATION  (app/pipeline.py)")
    final_score = round(min(max(
        RULE_WEIGHT * rule_score + ML_WEIGHT * ml_score + RAG_WEIGHT * rag_score, 0), 1), 3)
    category = "Unsafe" if final_score >= UNSAFE_THRESHOLD else ("Suspicious" if final_score >= SAFE_THRESHOLD else "Safe")

    print(f"Formula : {RULE_WEIGHT}*rule + {ML_WEIGHT}*ml + {RAG_WEIGHT}*rag")
    print(f"        = {RULE_WEIGHT}*{rule_score:.3f} + {ML_WEIGHT}*{ml_score:.3f} + {RAG_WEIGHT}*{rag_score:.3f}")
    print(f"        = {final_score}")
    print(f"\nFinal category : {category}")

    section("END-TO-END RESULT (JSON)")
    print(json.dumps({
        "category": category,
        "confidence_score": final_score,
        "rule_based_score": round(rule_score, 3),
        "ml_score": round(ml_score, 3),
        "rag_score": round(rag_score, 3),
    }, indent=2))


if __name__ == "__main__":
    main()
