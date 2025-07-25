import streamlit as st
import pandas as pd
from collections import Counter
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import os
import certifi
import json

# Set SSL cert
os.environ['SSL_CERT_FILE'] = certifi.where()

# --- Google Sheets setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Herd Mentality")

answers_ws = sheet.worksheet("answers")
scores_ws = sheet.worksheet("scores")
questions_ws = sheet.worksheet("questions")

# --- Utility: safe Google Sheets loading ---
def safe_load(ws, columns):
    try:
        data = ws.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame(columns=columns)
    except:
        return pd.DataFrame(columns=columns)

# --- App Layout ---
st.set_page_config("🐄 Herd Mentality", layout="centered")
st.title("🐄 Herd Mentality Game")
host_tab, player_tab = st.tabs(["👑 Host", "🙋 Player"])

# --- HOST TAB ---
with host_tab:
    st.subheader("👑 Host Controls")

    # Reset Game
    if st.button("🔄 Reset Game"):
        questions_ws.clear()
        questions_ws.append_row(["QUESTION_TEXT"])
        answers_ws.clear()
        answers_ws.append_row(["QUESTION_TEXT", "Player", "Answer"])
        scores_ws.clear()
        scores_ws.append_row(["Player", "Score", "Pink Cow"])
        st.success("Game reset!")

    # Ask Question
    new_q = st.text_input("New Question")
    if st.button("Start New Round") and new_q.strip():
        questions_ws.append_row([new_q.strip()])
        st.session_state.current_question = new_q.strip()
        st.success("New round started!")

    # Show current question
    q_df = safe_load(questions_ws, ["QUESTION_TEXT"])
    current_q = q_df["QUESTION_TEXT"].iloc[-1] if not q_df.empty else "No question yet"
    st.markdown(f"**Current Question:** {current_q}")

    # Show answers
    df_answers = safe_load(answers_ws, ["QUESTION_TEXT", "Player", "Answer"])
    round_answers = df_answers[df_answers["QUESTION_TEXT"] == current_q]
    st.markdown("### 📥 Submitted Answers")
    st.dataframe(round_answers)

    # Reveal answers and update scores
    if st.button("Reveal Answers and Score"):
        if not round_answers.empty:
            counts = Counter(round_answers["Answer"].str.lower())
            max_count = max(counts.values())
            majority = [ans for ans, count in counts.items() if count == max_count]
            st.markdown(f"🧠 **Majority Answer(s):** {majority}")

            score_df = safe_load(scores_ws, ["Player", "Score", "Pink Cow"])
            score_dict = {row["Player"]: row["Score"] for _, row in score_df.iterrows()}
            pink_holder = None

            for _, row in round_answers.iterrows():
                player, answer = row["Player"], row["Answer"].lower()
                if answer in majority and len(majority) == 1:
                    score_dict[player] = score_dict.get(player, 0) + 1
                if counts[answer] == 1 and pink_holder is None:
                    pink_holder = player

            scores_data = [{"Player": k, "Score": v, "Pink Cow": "🐄" if k == pink_holder else ""} for k, v in score_dict.items()]
            score_df_updated = pd.DataFrame(scores_data)
            scores_ws.clear()
            set_with_dataframe(scores_ws, score_df_updated)

            st.markdown("### 🏆 Scores")
            st.dataframe(score_df_updated)
        else:
            st.warning("No answers submitted yet.")

# --- PLAYER TAB ---
with player_tab:
    st.subheader("🙋 Player View")

    q_df = safe_load(questions_ws, ["QUESTION_TEXT"])
    latest_q = q_df["QUESTION_TEXT"].iloc[-1] if not q_df.empty else None

    if latest_q:
        st.markdown(f"**Current Question:** {latest_q}")

        # Persist player name
        pname = st.text_input("Your Name", key="name_input", value=st.session_state.get("player_name", ""))
        if pname:
            st.session_state["player_name"] = pname

        # Safely initialize answer input
        if "answer_input" not in st.session_state:
            st.session_state["answer_input"] = ""

        # Refresh button (resets only the answer box)
        if st.button("🔃 Refresh Question"):
            st.session_state["answer_input"] = ""

        with st.form("answer_form"):
            pans = st.text_input("Your Answer", key="answer_input", value=st.session_state["answer_input"])
            submit = st.form_submit_button("Submit Answer")
            if submit and pname.strip() and pans.strip():
                answers_ws.append_row([latest_q, pname.strip(), pans.strip().lower()])
                st.success("Answer submitted!", icon="✅")
                st.session_state["answer_input"] = ""
    else:
        st.info("Waiting for host to start the round.")

