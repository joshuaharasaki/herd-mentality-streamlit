import streamlit as st
import pandas as pd
from collections import Counter
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import os
import certifi
import json
os.environ['SSL_CERT_FILE'] = certifi.where()

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# Convert the Google creds from secret string to dict
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

# Tabs for Host and Player
host_tab, player_tab = st.tabs(["👑 Host", "🙋 Player"])

# --- HOST VIEW ---
with host_tab:
    st.subheader("👑 Host Dashboard")

    # Set question
    question = st.text_input("Enter question for this round:")

    if st.button("Start Round"):
        questions_ws.append_row([question])
        st.session_state.question = question

    # Load answers from Google Sheet
    df_answers = pd.DataFrame(answers_ws.get_all_records())

    st.markdown(f"### ❓ Current Question: {st.session_state.get('question', 'No question yet.')}")
    st.markdown("### 📥 Submitted Answers")
    st.dataframe(df_answers)

    if not df_answers.empty:
        counts = Counter(df_answers["Answer"].str.lower())
        max_count = max(counts.values())
        majority = [ans for ans, count in counts.items() if count == max_count]

        st.markdown(f"🧠 **Majority Answer(s):** {majority}")

        # Update scores in memory
        score_dict = {row["Player"]: row["Score"] for row in scores_ws.get_all_records()}
        pink_holder = None

        for idx, row in df_answers.iterrows():
            player, answer = row["Player"], row["Answer"].lower()
            if answer in majority and len(majority) == 1:
                score_dict[player] = score_dict.get(player, 0) + 1
            if counts[answer] == 1 and pink_holder is None:
                pink_holder = player

        # Update score sheet
        scores_ws.clear()
        scores_data = [{"Player": k, "Score": v, "Pink Cow": "🐄" if k == pink_holder else ""} for k, v in score_dict.items()]
        score_df = pd.DataFrame(scores_data)
        set_with_dataframe(scores_ws, score_df)

        st.markdown("### 🏆 Scores")
        st.dataframe(score_df)

# --- PLAYER VIEW ---
with player_tab:
    st.subheader("🙋 Player View")

    latest_question = questions_ws.get_all_records()[-1]["QUESTION_TEXT"] if questions_ws.get_all_records() else None

    if latest_question:
        st.markdown(f"**Current Question:** {latest_question}")
        with st.form("player_submission_form"):
            pname = st.text_input("Your Name")
            pans = st.text_input("Your Answer")
            psubmit = st.form_submit_button("Submit Answer")
            if psubmit:
                answers_ws.append_row([latest_question, pname.strip(), pans.strip().lower()])
                st.success("Answer submitted!")
    else:
        st.info("Waiting for host to set a question.")
