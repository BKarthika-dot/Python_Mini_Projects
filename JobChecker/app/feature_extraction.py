"""
Rule-based heuristic layer .

This is the "baseline layer" - fast, explainable checks
that catch obvious red flags before the ML/RAG layers even run.
"""
import re
from typing import List, Optional, Tuple

URGENCY_PHRASES = [
    "apply immediately", "act now", "limited seats", "urgent hiring",
    "immediate joining", "hurry up", "only few slots left",
    "limited time offer", "apply within 24 hours", "no time to waste",
]

PAYMENT_PHRASES = [
    "registration fee", "processing fee", "security deposit",
    "pay before joining", "send money", "wire transfer",
    "bank details required", "refundable deposit", "training fee",
    "kit fee", "pay to confirm", "activation fee",
]

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "rediffmail.com",
}

VAGUE_MIN_WORDS = 25

_SALARY_PATTERN = re.compile(
    r"(?:\$|rs\.?|₹)\s?[\d,]{3,7}\s?(?:/|\s?per\s?)?\s?(day|week|month|hour)", re.I
)
_EMAIL_PATTERN = re.compile(r"[\w.\-]+@[\w.\-]+\.\w+")


def _contains_any(text_lower: str, phrases: List[str]) -> List[str]:
    return [p for p in phrases if p in text_lower]


def _extract_email(text: str) -> Optional[str]:
    match = _EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def compute_rule_score(text: str, company_domain: Optional[str] = None) -> Tuple[float, List[str]]:
    """Return (score in [0,1], list of human-readable flags)."""
    text_lower = text.lower()
    flags: List[str] = []
    score = 0.0

    urgency_hits = _contains_any(text_lower, URGENCY_PHRASES)
    if urgency_hits:
        flags.append(f"Urgency language detected: {', '.join(urgency_hits[:3])}")
        score += 0.20

    payment_hits = _contains_any(text_lower, PAYMENT_PHRASES)
    if payment_hits:
        flags.append(f"Upfront payment / fee request detected: {', '.join(payment_hits[:3])}")
        score += 0.35

    if _SALARY_PATTERN.search(text):
        flags.append("Unusually specific or high salary claim detected")
        score += 0.15

    word_count = max(len(text.split()), 1)
    if word_count < VAGUE_MIN_WORDS:
        flags.append("Job description is unusually short or vague")
        score += 0.10

    email = _extract_email(text)
    if email:
        domain = email.split("@")[-1].lower()
        if domain in FREE_EMAIL_DOMAINS:
            flags.append(f"Contact email uses a free/generic domain ({domain}) instead of a company domain")
            score += 0.15
        if company_domain and domain != company_domain.lower():
            flags.append(
                f"Contact email domain ({domain}) does not match the claimed company domain ({company_domain})"
            )
            score += 0.10

    exclam_ratio = text.count("!") / word_count
    if exclam_ratio > 0.05:
        flags.append("Excessive use of exclamation marks")
        score += 0.05

    return min(score, 1.0), flags
