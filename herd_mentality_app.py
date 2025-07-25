import streamlit as st
import pandas as pd
from collections import Counter
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import os
import certifi
import json

# SSL cert fix for gspread on some platforms
os.environ['SSL_CERT_FILE'] = certifi.where()

# --- Google Sheets setup using st.secrets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_dict = st.secrets["GOOGLE_CREDS"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Herd Mentality")

# Reference worksheets
answers_ws = sheet.worksheet("answers")
scores_ws = sheet.worksheet("scores")
questions_ws = sheet.worksheet("questions")

# --- Streamlit layout ---
st.set_page_config(page_title="🐄 Herd Mentality", layout="centered")
st.title("🐄 Herd Mentality Game")
host_tab, player_tab = st.tabs(["👑 Host", "🙋 Player"])

# --- HOST VIEW ---
with host_tab:
    st.subheader("👑 Host Dashboard")

    question = st.text_input("Enter question for this round:")
    if st.button("Start Round") and question.strip():
        questions_ws.append_row([question.strip()])
        st.session_state.question = question.strip()

    # Load answers safely
    try:
        df_answers = pd.DataFrame(answers_ws.get_all_records())
    except:
        df_answers = pd.DataFrame(columns=["QUESTION_TEXT", "Player", "Answer"])

    st.markdown(f"### ❓ Current Question: {st.session_state.get('question', 'No question yet.')}")
    st.markdown("### 📥 Submitted Answers")
    st.dataframe(df_answers)

    if not df_answers.empty and "Answer" in df_answers:
        counts = Counter(df_answers["Answer"].str.lower())
        max_count = max(counts.values())
        majority = [ans for ans, count in counts.items() if count == max_count]

        st.markdown(f"🧠 **Majority Answer(s):** {majority}")

        try:
            score_dict = {row["Player"]: row["Score"] for row in scores_ws.get_all_records()}
        except:
            score_dict = {}

        pink_holder = None
        for _, row in df_answers.iterrows():
            player, answer = row["Player"], row["Answer"].lower()
            if answer in majority and len(majority) == 1:
                score_dict[player] = score_dict.get(player, 0) + 1
            if counts[answer] == 1 and pink_holder is None:
                pink_holder = player

        scores_data = [{"Player": k, "Score": v, "Pink Cow": "🐄" if k == pink_holder else ""} for k, v in score_dict.items()]
        score_df = pd.DataFrame(scores_data)

        try:
            scores_ws.clear()
            set_with_dataframe(scores_ws, score_df)
        except:
            st.warning("⚠️ Could not update scores in Google Sheet.")

        st.markdown("### 🏆 Scores")
        st.dataframe(score_df)

# --- PLAYER VIEW ---
with player_tab:
    st.subheader("🙋 Player View")

    try:
        questions = questions_ws.get_all_records()
        latest_question = questions[-1]["QUESTION_TEXT"] if questions else None
    except:
        latest_question = None

    if latest_question:
        st.markdown(f"**Current Question:** {latest_question}")
        with st.form("player_submission_form"):
            pname = st.text_input("Your Name")
            pans = st.text_input("Your Answer")
            psubmit = st.form_submit_button("Submit Answer")
            if psubmit and pname.strip() and pans.strip():
                try:
                    answers_ws.append_row([latest_question, pname.strip(), pans.strip().lower()])
                    st.success("✅ Answer submitted!")
                except:
                    st.error("❌ Failed to submit your answer.")
    else:
        st.info("Waiting for host to set a question.")
