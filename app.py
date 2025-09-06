import streamlit as st
import pandas as pd
import re
import imaplib, email
from email.header import decode_header
from dateutil import parser as dtparser
from utils.rules import is_support_subject, sentiment_label, classify_priority, extract_info
from utils.rag import SimpleRAG
from utils.generator import generate_reply

st.set_page_config(page_title="AI Communication Assistant", layout="wide")

st.title("📧 AI-Powered Communication Assistant")

with st.sidebar:
    st.header("Data Sources")
    st.write("**Option A:** Upload CSV with columns: from, subject, body, date")
    csv_file = st.file_uploader("Upload CSV", type=["csv"])
    st.write("---")
    st.write("**Option B:** Connect IMAP (demo)")
    imap_host = st.text_input("IMAP Host", "imap.gmail.com")
    imap_port = st.number_input("IMAP Port", value=993, step=1)
    imap_user = st.text_input("Email")
    imap_pass = st.text_input("App Password", type="password")
    use_imap = st.checkbox("Use IMAP fetch (insecure demo)")
    fetch_btn = st.button("Fetch Emails")

    st.write("---")
    st.header("SMTP (Optional)")
    smtp_host = st.text_input("SMTP Host", "smtp.gmail.com")
    smtp_port = st.number_input("SMTP Port", value=587, step=1)
    smtp_user = st.text_input("SMTP User (email)")
    smtp_pass = st.text_input("SMTP Password", type="password")

@st.cache_data
def fetch_from_imap(host, port, user, password, mailbox="INBOX", limit=100):
    data = []
    try:
        M = imaplib.IMAP4_SSL(host, port)
        M.login(user, password)
        M.select(mailbox)
        status, msgnums = M.search(None, "ALL")
        if status != "OK":
            return pd.DataFrame(columns=["from","subject","body","date"])
        ids = msgnums[0].split()[-limit:]
        for num in reversed(ids):
            res, msg_data = M.fetch(num, "(RFC822)")
            if res != "OK": 
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            subj, enc = decode_header(msg.get("Subject") or "")[0]
            if isinstance(subj, bytes):
                subj = subj.decode(enc or "utf-8", errors="ignore")
            frm = msg.get("From") or ""
            date = msg.get("Date") or ""
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        except:
                            pass
            else:
                try:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                except:
                    body = str(msg.get_payload())
            data.append({"from": frm, "subject": subj, "body": body, "date": date})
        M.close()
        M.logout()
    except Exception as e:
        st.warning(f"IMAP error: {e}")
    return pd.DataFrame(data)

def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    def pick(name):
        for k in cols:
            if k == name: return cols[k]
        return None
    m = {
        "from": pick("from"),
        "subject": pick("subject"),
        "body": pick("body"),
        "date": pick("date"),
    }
    new = pd.DataFrame({
        "from": df.get(m["from"], ""),
        "subject": df.get(m["subject"], ""),
        "body": df.get(m["body"], ""),
        "date": df.get(m["date"], ""),
    })
    return new

def support_filter(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["subject"].fillna("").map(is_support_subject)
    return df[mask].copy()

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sentiment"] = df.apply(lambda r: sentiment_label(f"{r['subject']}\n{r['body']}"), axis=1)
    df["priority"] = df.apply(lambda r: classify_priority(f"{r['subject']}\n{r['body']}"), axis=1)
    extr = df["body"].fillna("").map(extract_info)
    df["contacts"] = extr.map(lambda x: ", ".join(x.get("emails", []) + x.get("phones", [])))
    df["ids"] = extr.map(lambda x: ", ".join(x.get("ids", [])))
    # Parse date for sorting + last 24h stats
    def parse_date(x):
        try:
            return dtparser.parse(str(x))
        except:
            return pd.NaT
    df["parsed_date"] = df["date"].map(parse_date)
    return df

def priority_sort(df: pd.DataFrame) -> pd.DataFrame:
    # Urgent first, then newest
    pri = {"Urgent": 0, "Not urgent": 1}
    return df.sort_values(by=["priority","parsed_date"], ascending=[True, False], key=lambda s: s.map(lambda v: pri.get(v, 2)) if s.name=="priority" else s)

# Load data
if csv_file is not None and not use_imap:
    df = pd.read_csv(csv_file)
    df = normalize_df(df)
elif use_imap and fetch_btn and imap_user and imap_pass:
    df = fetch_from_imap(imap_host, imap_port, imap_user, imap_pass)
else:
    df = pd.DataFrame(columns=["from","subject","body","date"])

if not df.empty:
    df = support_filter(df)
    df = enrich(df)
    df = priority_sort(df)

# Analytics
st.subheader("📊 Analytics (last 24 hours)")
now = pd.Timestamp.utcnow()
last24 = df[df["parsed_date"] >= (now - pd.Timedelta(hours=24))] if not df.empty else df
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total emails (24h)", len(last24))
c2.metric("Urgent", int((last24["priority"]=="Urgent").sum()))
c3.metric("Resolved", 0)
c4.metric("Pending", len(last24))

# Sentiment + Priority breakdown
if not df.empty:
    sc1, sc2 = st.columns(2)
    with sc1:
        st.bar_chart(df["sentiment"].value_counts())
    with sc2:
        st.bar_chart(df["priority"].value_counts())

# RAG
rag = SimpleRAG("kb")

# Table
st.subheader("📥 Filtered Support Emails")
if df.empty:
    st.info("Upload a CSV or fetch from IMAP to see results.")
else:
    st.dataframe(df[["from","subject","date","sentiment","priority","contacts","ids"]], use_container_width=True, hide_index=True)

# Detailed view + draft response
st.subheader("🧩 Email Detail & Draft Reply")
if not df.empty:
    idx = st.selectbox("Select email to review", options=df.index.tolist(), format_func=lambda i: f"{df.loc[i,'subject']} — {df.loc[i,'from']}")
    row = df.loc[idx]
    st.markdown(f"**From:** {row['from']}  
**Subject:** {row['subject']}  
**Date:** {row['date']}  
**Priority:** {row['priority']}  
**Sentiment:** {row['sentiment']}  
**Contacts:** {row['contacts']}  
**IDs:** {row['ids']}")
    with st.expander("Show raw body"):
        st.write(row["body"] or "(empty)")
    draft = generate_reply({"from": row["from"], "subject": row["subject"], "body": row["body"]}, rag)
    edited = st.text_area("Draft reply (editable before sending)", value=draft, height=350)
    st.button("Send Reply (SMTP)", disabled=True, help="Enable and implement sending with SMTP credentials above for live use.")
