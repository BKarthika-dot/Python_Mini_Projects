"""
Retrieval-Augmented layer (SRS section 3.3 - RAG Module) using genuine
semantic similarity.

Earlier versions of this module reused the ML classifier's TF-IDF vectorizer
for retrieval. TF-IDF only matches on *shared vocabulary* -- two scam
descriptions that mean the same thing but share no words (e.g. "pay a
registration fee to confirm your slot" vs. "a small deposit is required to
secure your position") would score near-zero similarity. This version
embeds text with a sentence-transformers model instead, placing text into a
vector space based on meaning, so retrieval generalizes to paraphrased or
reworded scam patterns that were never seen verbatim in the knowledge base.

Requires: pip install sentence-transformers
First run downloads the embedding model (~80MB) from Hugging Face, so it
needs outbound internet access once; the model is then cached locally
(default: ~/.cache/huggingface) and no further downloads are needed after
that.

NOTE: this module is now fully decoupled from the ML classifier's TF-IDF
vectorizer (models/vectorizer.joblib) -- it manages its own embedding model
independently, so classifier.py can change its feature representation
without affecting RAG retrieval, and vice versa.
"""
import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Small, fast, general-purpose sentence embedding model (384-dim output).
# Good accuracy/speed trade-off for a prototype. Swap for a larger model
# (e.g. "all-mpnet-base-v2") if retrieval quality matters more than latency,
# or a domain-tuned model if one becomes available for scam/fraud text.
_EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Cosine similarity between two normalized sentence embeddings for
# semantically *unrelated* text still tends to sit well above 0 (often
# 0.1-0.3), unlike TF-IDF where unrelated text scores near-zero. Matches
# below this floor are treated as noise and excluded from scoring/display.
_MIN_RELEVANT_SIMILARITY = 0.25


class KnowledgeBase:
    def __init__(self):
        patterns_path = DATA_DIR / "scam_patterns.json"
        with open(patterns_path, encoding="utf-8") as f:
            self.patterns = json.load(f)

        self.model = SentenceTransformer(_EMBEDDING_MODEL_NAME)

        self._pattern_texts = [p["text"] for p in self.patterns]
        self._pattern_embeddings = self.model.encode(
            self._pattern_texts, convert_to_numpy=True, normalize_embeddings=True
        )

    def retrieve_similar(self, text: str, k: int = 3) -> List[dict]:
        query_embedding = self.model.encode(
            [text], convert_to_numpy=True, normalize_embeddings=True
        )
        sims = cosine_similarity(query_embedding, self._pattern_embeddings)[0]
        ranked_idx = np.argsort(sims)[::-1][:k]

        results = []
        for idx in ranked_idx:
            p = self.patterns[idx]
            results.append({
                "pattern_id": p["id"],
                "label": p["label"],
                "description": p["description"],
                "similarity": float(sims[idx]),
            })
        return results

    def rag_score(self, text: str, k: int = 3) -> Tuple[float, List[dict]]:
        """Return (fraud-likelihood score in [0,1], top-k matched patterns)."""
        matches = self.retrieve_similar(text, k=k)
        relevant = [m for m in matches if m["similarity"] >= _MIN_RELEVANT_SIMILARITY]

        if not relevant:
            return 0.0, matches

        weighted, total_weight = 0.0, 0.0
        for m in relevant:
            w = m["similarity"]
            total_weight += w
            if m["label"] == "scam":
                weighted += w
            # legit matches contribute 0 toward the scam-likelihood score

        score = weighted / total_weight if total_weight > 0 else 0.0
        return score, matches