import streamlit as st
import pandas as pd
from collections import Counter
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import os
import certifi
import json

# SSL fix
os.environ['SSL_CERT_FILE'] = certifi.where()

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Herd Mentality")

# Reference worksheets
answers_ws = sheet.worksheet("answers")
scores_ws = sheet.worksheet("scores")
questions_ws = sheet.worksheet("questions")

# Page layout
st.set_page_config(page_title="🐄 Herd Mentality", layout="centered")
st.title("🐄 Herd Mentality Game")
host_tab, player_tab = st.tabs(["👑 Host", "🙋 Player"])

# Utility to safely load data
def safe_load(ws, cols):
    try:
        records = ws.get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=cols)
    except:
        return pd.DataFrame(columns=cols)

# --- HOST TAB ---
with host_tab:
    st.subheader("👑 Host Dashboard")

    if st.button("🔄 Reset Game"):
        answers_ws.clear()
        scores_ws.clear()
        questions_ws.clear()
        set_with_dataframe(answers_ws, pd.DataFrame(columns=["QUESTION_TEXT", "Player", "Answer"]))
        set_with_dataframe(scores_ws, pd.DataFrame(columns=["Player", "Score", "Pink Cow"]))
        set_with_dataframe(questions_ws, pd.DataFrame(columns=["QUESTION_TEXT"]))
        st.success("Game has been reset.")

    question = st.text_input("Enter question for this round:")
    if st.button("Start Round"):
        questions_ws.append_row([question])
        st.session_state["question"] = question
        st.success("Question started!")

    current_question = st.session_state.get("question", "No question yet.")
    st.markdown(f"### ❓ Current Question: {current_question}")

    df_answers = safe_load(answers_ws, ["QUESTION_TEXT", "Player", "Answer"])
    st.markdown("### 📥 Submitted Answers")
    st.dataframe(df_answers)

    if st.button("✅ Reveal Answers & Update Score") and not df_answers.empty:
        counts = Counter(df_answers["Answer"].str.lower())
        max_count = max(counts.values())
        majority = [ans for ans, count in counts.items() if count == max_count]

        st.markdown(f"🧠 **Majority Answer(s):** {majority}")

        df_scores = safe_load(scores_ws, ["Player", "Score", "Pink Cow"])
        score_dict = dict(zip(df_scores["Player"], df_scores["Score"])) if not df_scores.empty else {}
        pink_holder = None

        for _, row in df_answers.iterrows():
            player, answer = row["Player"], row["Answer"].lower()
            if answer in majority and len(majority) == 1:
                score_dict[player] = score_dict.get(player, 0) + 1
            if counts[answer] == 1 and pink_holder is None:
                pink_holder = player

        scores_ws.clear()
        updated = [{"Player": p, "Score": s, "Pink Cow": "🐄" if p == pink_holder else ""} for p, s in score_dict.items()]
        set_with_dataframe(scores_ws, pd.DataFrame(updated))
        st.markdown("### 🏆 Scores")
        st.dataframe(pd.DataFrame(updated))

# --- PLAYER VIEW ---
with player_tab:
    st.subheader("🙋 Player View")

    # Add a refresh button
    if st.button("🔄 Refresh Question"):
        st.session_state.pop("submitted", None)
        st.session_state.pop("answer_input", None)
        st.experimental_rerun()

    # Get latest question
    q_records = questions_ws.get_all_records()
    latest_question = q_records[-1]["QUESTION_TEXT"] if q_records else None

    if latest_question:
        st.markdown(f"**Current Question:** {latest_question}")
        with st.form("player_submission_form", clear_on_submit=True):
            pname = st.text_input("Your Name", key="player_name")
            pans = st.text_input("Your Answer", key="answer_input")
            psubmit = st.form_submit_button("Submit Answer")
            if psubmit and pname.strip() and pans.strip():
                answers_ws.append_row([latest_question, pname.strip(), pans.strip().lower()])
                st.session_state.submitted = True

        if st.session_state.get("submitted"):
            st.success("Answer submitted!", icon="✅")
            # Hide message after 4 seconds
            st.experimental_rerun()
    else:
        st.info("Waiting for host to set a question.")
