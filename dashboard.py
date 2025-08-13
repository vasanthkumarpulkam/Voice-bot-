import streamlit as st
import sqlite3
from pathlib import Path

st.set_page_config(page_title="Call Triage Dashboard", layout="wide")

db_path = Path("calls.db")
if not db_path.exists():
    st.warning("No database yet. Once calls arrive, this will populate.")
    st.stop()

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

st.title("📞 Call Triage — Prioritized View")
st.caption("High priority first. Click recording/voicemail links to play.")

priorities = ["high", "medium", "low"]
types = ["recruiter", "family", "friend", "promotion", "unknown"]

pri_filter = st.multiselect("Filter by priority", priorities, default=priorities)
type_filter = st.multiselect("Filter by caller type", types, default=types)

query = f"""
SELECT * FROM call_logs
WHERE priority IN ({','.join('?' * len(pri_filter))})
AND caller_type IN ({','.join('?' * len(type_filter))})
ORDER BY CASE priority
    WHEN 'high' THEN 1
    WHEN 'medium' THEN 2
    ELSE 3
END, timestamp DESC
"""

rows = conn.execute(query, [*pri_filter, *type_filter]).fetchall()

for r in rows:
    with st.container():
        c1, c2, c3, c4, c5 = st.columns([2, 2, 3, 2, 2])
        c1.markdown(f"**Time**\n\n{r['timestamp']}")
        c2.markdown(f"**From**\n\n{r['from_number']}")
        c3.markdown(f"**Name/Company**\n\n{r['caller_name'] or ''}")
        c4.markdown(f"**Type/Priority**\n\n{r['caller_type']} / **{r['priority']}**")
        c5.markdown(f"**Action**\n\n{r['action']}")

        st.markdown(f"**Reason**: {r['reason'] or ''}")
        
        if r['transcript']:
            with st.expander("Transcript"):
                st.write(r['transcript'])

        links = []
        if r['recording_url']:
            links.append(f"[Recording]({r['recording_url']}.mp3)")
        if r['voicemail_url']:
            links.append(f"[Voicemail]({r['voicemail_url']}.mp3)")
        if links:
            st.markdown(" ".join(links))
