import streamlit as st
import pandas as pd
from collections import Counter
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import os
import certifi
import json

os.environ['SSL_CERT_FILE'] = certifi.where()

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Herd Mentality")

answers_ws = sheet.worksheet("answers")
scores_ws = sheet.worksheet("scores")
questions_ws = sheet.worksheet("questions")

# --- Streamlit Setup ---
st.set_page_config(page_title="🐄 Herd Mentality", layout="centered")
st.title("🐄 Herd Mentality Game")
host_tab, player_tab = st.tabs(["👑 Host", "🙋 Player"])

# --- HOST TAB ---
with host_tab:
    st.subheader("👑 Host Dashboard")

    # Start Round
    question = st.text_input("Enter question for this round:")
    if st.button("Start Round"):
        questions_ws.append_row([question])
        st.session_state["current_question"] = question
        st.success("Question started!")

    # Reveal Answers
    if st.button("Reveal Answers"):
        answers_data = answers_ws.get_all_records()
        df_answers = pd.DataFrame(answers_data) if answers_data else pd.DataFrame(columns=["QUESTION_TEXT", "Player", "Answer"])

        st.markdown("### 📥 Submitted Answers")
        st.dataframe(df_answers)

        if not df_answers.empty:
            counts = Counter(df_answers["Answer"].str.lower())
            max_count = max(counts.values())
            majority = [ans for ans, count in counts.items() if count == max_count]
            st.markdown(f"🧠 **Majority Answer(s):** {majority}")

            # Score update
            score_dict = {row["Player"]: row.get("Score", 0) for row in scores_ws.get_all_records()}
            pink_holder = None

            for _, row in df_answers.iterrows():
                player, answer = row["Player"], row["Answer"].lower()
                if answer in majority and len(majority) == 1:
                    score_dict[player] = score_dict.get(player, 0) + 1
                if counts[answer] == 1 and pink_holder is None:
                    pink_holder = player

            scores_data = [{"Player": p, "Score": s, "Pink Cow": "🐄" if p == pink_holder else ""} for p, s in score_dict.items()]
            scores_ws.clear()
            set_with_dataframe(scores_ws, pd.DataFrame(scores_data))

    # View Scores
    score_records = scores_ws.get_all_records()
    score_df = pd.DataFrame(score_records) if score_records else pd.DataFrame(columns=["Player", "Score", "Pink Cow"])
    st.markdown("### 🏆 Scores")
    st.dataframe(score_df)

    # Reset Button
    if st.button("🔄 Reset Game"):
        answers_ws.clear()
        questions_ws.clear()
        scores_ws.clear()
        answers_ws.append_row(["QUESTION_TEXT", "Player", "Answer"])
        questions_ws.append_row(["QUESTION_TEXT"])
        scores_ws.append_row(["Player", "Score", "Pink Cow"])
        st.success("Game has been reset.")

# --- PLAYER TAB ---
with player_tab:
    st.subheader("🙋 Player View")

    # Remember name across rounds
    if "player_name" not in st.session_state:
        st.session_state["player_name"] = ""

    name = st.text_input("Your Name", value=st.session_state["player_name"])
    st.session_state["player_name"] = name

    latest_qs = questions_ws.get_all_records()
    latest_question = latest_qs[-1]["QUESTION_TEXT"] if latest_qs else None

    if latest_question:
        st.markdown(f"**Current Question:** {latest_question}")
        with st.form("answer_form"):
            answer = st.text_input("Your Answer")
            submitted = st.form_submit_button("Submit")
            if submitted and name.strip() and answer.strip():
                answers_ws.append_row([latest_question, name.strip(), answer.strip()])
                st.success("Answer submitted!")
    else:
        st.info("Waiting for the host to start a round.")
import streamlit as st
import pandas as pd
from collections import Counter
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import os
import certifi
import json

os.environ['SSL_CERT_FILE'] = certifi.where()

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Herd Mentality")

answers_ws = sheet.worksheet("answers")
scores_ws = sheet.worksheet("scores")
questions_ws = sheet.worksheet("questions")

# --- Streamlit Setup ---
st.set_page_config(page_title="🐄 Herd Mentality", layout="centered")
st.title("🐄 Herd Mentality Game")
host_tab, player_tab = st.tabs(["👑 Host", "🙋 Player"])

# --- HOST TAB ---
with host_tab:
    st.subheader("👑 Host Dashboard")

    # Start Round
    question = st.text_input("Enter question for this round:")
    if st.button("Start Round"):
        questions_ws.append_row([question])
        st.session_state["current_question"] = question
        st.success("Question started!")

    # Reveal Answers
    if st.button("Reveal Answers"):
        answers_data = answers_ws.get_all_records()
        df_answers = pd.DataFrame(answers_data) if answers_data else pd.DataFrame(columns=["QUESTION_TEXT", "Player", "Answer"])

        st.markdown("### 📥 Submitted Answers")
        st.dataframe(df_answers)

        if not df_answers.empty:
            counts = Counter(df_answers["Answer"].str.lower())
            max_count = max(counts.values())
            majority = [ans for ans, count in counts.items() if count == max_count]
            st.markdown(f"🧠 **Majority Answer(s):** {majority}")

            # Score update
            score_dict = {row["Player"]: row.get("Score", 0) for row in scores_ws.get_all_records()}
            pink_holder = None

            for _, row in df_answers.iterrows():
                player, answer = row["Player"], row["Answer"].lower()
                if answer in majority and len(majority) == 1:
                    score_dict[player] = score_dict.get(player, 0) + 1
                if counts[answer] == 1 and pink_holder is None:
                    pink_holder = player

            scores_data = [{"Player": p, "Score": s, "Pink Cow": "🐄" if p == pink_holder else ""} for p, s in score_dict.items()]
            scores_ws.clear()
            set_with_dataframe(scores_ws, pd.DataFrame(scores_data))

    # View Scores
    score_records = scores_ws.get_all_records()
    score_df = pd.DataFrame(score_records) if score_records else pd.DataFrame(columns=["Player", "Score", "Pink Cow"])
    st.markdown("### 🏆 Scores")
    st.dataframe(score_df)

    # Reset Button
    if st.button("🔄 Reset Game"):
        answers_ws.clear()
        questions_ws.clear()
        scores_ws.clear()
        answers_ws.append_row(["QUESTION_TEXT", "Player", "Answer"])
        questions_ws.append_row(["QUESTION_TEXT"])
        scores_ws.append_row(["Player", "Score", "Pink Cow"])
        st.success("Game has been reset.")

# --- PLAYER TAB ---
with player_tab:
    st.subheader("🙋 Player View")

    # Remember name across rounds
    if "player_name" not in st.session_state:
        st.session_state["player_name"] = ""

    name = st.text_input("Your Name", value=st.session_state["player_name"])
    st.session_state["player_name"] = name

    latest_qs = questions_ws.get_all_records()
    latest_question = latest_qs[-1]["QUESTION_TEXT"] if latest_qs else None

    if latest_question:
        st.markdown(f"**Current Question:** {latest_question}")
        with st.form("answer_form"):
            answer = st.text_input("Your Answer")
            submitted = st.form_submit_button("Submit")
            if submitted and name.strip() and answer.strip():
                answers_ws.append_row([latest_question, name.strip(), answer.strip()])
                st.success("Answer submitted!")
    else:
        st.info("Waiting for the host to start a round.")

