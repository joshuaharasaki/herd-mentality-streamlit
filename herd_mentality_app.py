import streamlit as st
import pandas as pd
from collections import Counter
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import os
import certifi
import json

# --- Setup SSL ---
os.environ['SSL_CERT_FILE'] = certifi.where()

# --- Google Sheets setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Herd Mentality")

# Reference worksheets
answers_ws = sheet.worksheet("answers")
scores_ws = sheet.worksheet("scores")
questions_ws = sheet.worksheet("questions")

# Ensure headers exist
if not questions_ws.get_all_values():
    questions_ws.append_row(["QUESTION_TEXT"])
if not answers_ws.get_all_values():
    answers_ws.append_row(["QUESTION_TEXT", "Player", "Answer"])
if not scores_ws.get_all_values():
    scores_ws.append_row(["Player", "Score", "Pink Cow"])

# --- Layout ---
st.set_page_config(page_title="🐄 Herd Mentality", layout="centered")
st.title("🐄 Herd Mentality Game")
host_tab, player_tab = st.tabs(["👑 Host", "🙋 Player"])

# --- HOST VIEW ---
with host_tab:
    st.subheader("👑 Host Controls")
    question = st.text_input("Enter new question")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Round"):
            questions_ws.append_row([question])
            answers_ws.resize(rows=1)  # Keep header only
            st.session_state["question"] = question
            st.success("New round started!")

    with col2:
        if st.button("Reset Game ❌"):
            # Clear answers and questions, keep score
            questions_ws.resize(rows=1)
            answers_ws.resize(rows=1)
            st.session_state.clear()
            st.success("Game reset (scores preserved)")

    # Show current question
    q_records = questions_ws.get_all_records()
    current_q = q_records[-1]["QUESTION_TEXT"] if q_records else "No question yet."
    st.markdown(f"### ❓ Current Question:\n**{current_q}**")

    # Reveal answers and update scores
    records = answers_ws.get_all_records()
    df_answers = pd.DataFrame(records)

    if not df_answers.empty:
        if st.button("Reveal Answers"):
            st.markdown("### 📥 Submitted Answers")
            st.dataframe(df_answers[["Player", "Answer"]])

            counts = Counter(df_answers["Answer"].str.lower())
            max_count = max(counts.values())
            majority = [ans for ans, count in counts.items() if count == max_count]
            st.markdown(f"🧠 **Majority Answer(s):** {majority}")

            # Update scores
            score_records = scores_ws.get_all_records()
            score_dict = {row["Player"]: int(row["Score"]) for row in score_records}
            pink_holder = None

            for _, row in df_answers.iterrows():
                player = row["Player"]
                answer = row["Answer"].lower()
                if answer in majority and len(majority) == 1:
                    score_dict[player] = score_dict.get(player, 0) + 1
                if counts[answer] == 1 and pink_holder is None:
                    pink_holder = player

            scores_ws.resize(rows=1)
            for player, score in score_dict.items():
                scores_ws.append_row([player, score, "🐄" if player == pink_holder else ""])
            st.success("Scores updated!")

    # Show scores
    score_data = scores_ws.get_all_records()
    if score_data:
        st.markdown("### 🏆 Scores")
        st.dataframe(pd.DataFrame(score_data))

# --- PLAYER VIEW ---
with player_tab:
    st.subheader("🙋 Submit Your Answer")
    q_records = questions_ws.get_all_records()
    latest_question = q_records[-1]["QUESTION_TEXT"] if q_records else None

    if latest_question:
        st.markdown(f"**Current Question:** {latest_question}")
        pname = st.text_input("Your Name", value=st.session_state.get("pname", ""))
        pans = st.text_input("Your Answer")

        if st.button("Submit Answer"):
            if pname.strip() and pans.strip():
                st.session_state["pname"] = pname.strip()
                answers_ws.append_row([latest_question, pname.strip(), pans.strip().lower()])
                st.success("Answer submitted!")
            else:
                st.error("Please enter both name and answer.")
    else:
        st.info("Waiting for host to start the round.")


