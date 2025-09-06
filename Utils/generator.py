from typing import Dict, Any, List
from .rules import sentiment_label, classify_priority
from .rag import SimpleRAG

def build_context_snippets(rag: SimpleRAG, query: str, k: int = 2) -> List[str]:
    hits = rag.top_k(query, k=k)
    return [doc for name, doc, score in hits]

def generate_reply(email: Dict[str, Any], rag: SimpleRAG) -> str:
    sender = email.get("from","customer")
    subject = email.get("subject","(no subject)")
    body = email.get("body","")
    sent = sentiment_label(f"{subject}\n{body}")
    prio = classify_priority(f"{subject}\n{body}")
    context = "\n\n--- Knowledge Base ---\n" + "\n\n".join(build_context_snippets(rag, body, k=2))
    # Simple empathetic tone based on sentiment
    empathy = {
        "Positive": "Thanks for reaching out and for the positive note!",
        "Neutral": "Thanks for reaching out.",
        "Negative": "I’m sorry for the trouble you’re facing, and I appreciate your patience."
    }[sent]

    reply = f"""
Hi {sender},

{empathy} I’m here to help.

Regarding **{subject}**:
- I’ve reviewed your message and captured the details below.
- Priority assessed: **{prio}**
- Sentiment detected: **{sent}**

Here’s what you can try right away:
1) If this is about account access or activation, please try the steps in the KB below.
2) If it’s a product issue, let me know your order/ticket ID and any error messages so I can investigate faster.
3) If this is urgent (service down or blocked), I’ve flagged it and will escalate immediately.

Once you confirm a few details (screenshots, order/ticket ID, and the steps you tried), I’ll proceed with the next action or arrange a quick call.

Best regards,
Support Team

{context}
"""
    return reply.strip()
