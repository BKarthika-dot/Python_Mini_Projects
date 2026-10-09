"""
Classification pipeline orchestrator (SRS section 3.4 - Classification and
Scoring Module, and section 5.1-B - Model Selection / Algorithmic Approach).

Fuses three signals into one verdict:
  1. rule-based heuristic score   (feature_extraction.compute_rule_score)
  2. ML classifier probability    (classifier.ScamClassifier)
  3. RAG similarity score         (knowledge_base.KnowledgeBase)
"""
from typing import Optional

from .classifier import ScamClassifier
from .feature_extraction import compute_rule_score
from .knowledge_base import KnowledgeBase
from .scraper import fetch_job_posting

RULE_WEIGHT = 0.30
ML_WEIGHT = 0.40
RAG_WEIGHT = 0.30

SAFE_THRESHOLD = 0.35     # below this -> Safe
UNSAFE_THRESHOLD = 0.65   # at or above this -> Unsafe; between -> Suspicious


class ClassificationPipeline:
    def __init__(self):
        self.classifier = ScamClassifier()
        self.kb = KnowledgeBase()

    def classify(self, input_type: str, content: str, company_domain: Optional[str] = None) -> dict:
        if input_type == "url":
            text = fetch_job_posting(content)
            source_url = content
        elif input_type == "text":
            text = content
            source_url = None
        else:
            raise ValueError(f"Unsupported input_type: {input_type!r}")

        if not text or not text.strip():
            raise ValueError("No usable text could be extracted from the submission.")

        rule_score, rule_flags = compute_rule_score(text, company_domain=company_domain)
        ml_score = self.classifier.predict_proba(text)
        rag_score, rag_matches = self.kb.rag_score(text, k=3)

        final_score = (RULE_WEIGHT * rule_score) + (ML_WEIGHT * ml_score) + (RAG_WEIGHT * rag_score)
        final_score = round(min(max(final_score, 0.0), 1.0), 3)

        if final_score >= UNSAFE_THRESHOLD:
            category = "Unsafe"
        elif final_score >= SAFE_THRESHOLD:
            category = "Suspicious"
        else:
            category = "Safe"

        explanation = list(rule_flags)
        for m in rag_matches:
            if m["label"] == "scam" and m["similarity"] > 0.15:
                explanation.append(
                    f"Similar to a known scam pattern: \"{m['description']}\" "
                    f"(similarity {m['similarity']:.2f})"
                )
        if not explanation:
            explanation.append("No strong red-flag indicators detected.")

        return {
            "source_url": source_url,
            "category": category,
            "confidence_score": final_score,
            "rule_based_score": round(rule_score, 3),
            "ml_score": round(ml_score, 3),
            "rag_score": round(rag_score, 3),
            "explanation": explanation,
            "matched_patterns": rag_matches,
            "extracted_text_preview": text[:400],
            "full_text": text,
        }
