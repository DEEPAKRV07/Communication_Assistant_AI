import re
from dataclasses import dataclass
from typing import Dict, Any, List

URGENT_KEYWORDS = [
    "urgent", "immediately", "asap", "as soon as possible", "critical",
    "cannot login", "can't login", "down", "not working", "escalate", "priority 1",
    "p1", "outage", "blocked", "fail", "failed", "failure"
]

POSITIVE_WORDS = {"great","thanks","thank you","love","awesome","amazing","perfect","good","appreciate"}
NEGATIVE_WORDS = {"angry","frustrated","upset","bad","terrible","horrible","disappointed","issue","problem","not working","broken","worst"}

CONTACT_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CONTACT_PHONE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})")
ORDER_ID = re.compile(r"\b(?:order|ticket|case|id)[:\s#-]*([A-Z0-9-]{5,})", re.I)

SUPPORT_SUBJECT_TERMS = {"support","query","request","help"}

def is_support_subject(subj: str) -> bool:
    s = (subj or "").lower()
    return any(term in s for term in SUPPORT_SUBJECT_TERMS)

def classify_priority(text: str) -> str:
    t = (text or "").lower()
    return "Urgent" if any(k in t for k in URGENT_KEYWORDS) else "Not urgent"

def sentiment_score(text: str) -> int:
    t = (text or "").lower()
    score = 0
    for w in POSITIVE_WORDS:
        if w in t: score += 1
    for w in NEGATIVE_WORDS:
        if w in t: score -= 1
    return score

def sentiment_label(text: str) -> str:
    s = sentiment_score(text)
    if s > 0: return "Positive"
    if s < 0: return "Negative"
    return "Neutral"

def extract_info(text: str) -> Dict[str, Any]:
    emails = CONTACT_EMAIL.findall(text or "") or []
    phones = CONTACT_PHONE.findall(text or "") or []
    order_ids = ORDER_ID.findall(text or "") or []
    return {
        "emails": list(set(e.strip() for e in emails)),
        "phones": list(set(p.strip() for p in phones)),
        "ids": list(set(o.strip() for o in order_ids)),
    }
