# AI-Powered Communication Assistant

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) ![RAG](https://img.shields.io/badge/RAG-087F5B?style=flat-square)

A simple end-to-end demo that ingests emails (via CSV or IMAP), filters for support-related messages,
extracts key info, prioritizes by urgency, analyzes sentiment, retrieves context from a local KB (RAG),
and generates draft responses. Includes a Streamlit dashboard for review and sending replies.

## Workflow

Email ingestion → Support filtering → Information extraction → Urgency and sentiment → Knowledge-base retrieval → Draft response → Human review

## Quick Start (Local Demo)
1) Create and activate a virtual environment (optional).
2) Install dependencies:
```bash
pip install -r requirements.txt
```
3) Run the dashboard:
```bash
streamlit run app.py
```
4) In the app, upload the provided sample CSV (or your own), or connect to IMAP in the sidebar.

## IMAP/Gmail/Outlook (Optional)
- In the sidebar, provide IMAP host (e.g., imap.gmail.com), port (usually 993), email, and app password.
- Click "Fetch Emails". For Gmail, you may need an app password or OAuth; for Outlook, consider Microsoft Graph API.

## RAG (Local Knowledge Base)
- Place your markdown files in `kb/`. The app builds a TF‑IDF index to retrieve the top snippets for context.
- Edit `kb/getting_started.md` and `kb/shipping_and_returns.md` as examples.

## Notes
- Sentiment and urgency are rule-based for offline use.
- SMTP sending is supported via settings in the sidebar (host, port, username, password). Use with care. Review generated drafts before sending, use authorized mailboxes only, and do not commit credentials or real customer messages.
