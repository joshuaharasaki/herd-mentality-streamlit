import streamlit as st
import pandas as pd
from collections import Counter

# Initialize session state
if "answers" not in st.session_state:
    st.session_state.answers = []
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "pink_cow" not in st.session_state:
    st.session_state.pink_cow = None
if "question" not in st.session_state:
    st.session_state.question = ""

# Page layout
st.set_page_config(page_title="🐄 Herd Mentality", layout="centered")
st.title("🐄 Herd Mentality Game")

# Tabs for Host and Player
host_tab, player_tab = st.tabs(["👑 Host", "🙋 Player"])

# --- HOST VIEW ---
with host_tab:
    st.subheader("👑 Host Dashboard")
    
    # Set question
    question = st.text_input("Enter question for this round:", st.session_state.question)
    if question:
        st.session_state.question = question

    with st.form("host_answer_form"):
        name = st.text_input("Player Name")
        answer = st.text_input("Answer")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.answers.append((name.strip(), answer.strip().lower()))
            st.success(f"Answer submitted for {name}.")

    # Reveal answers
    if st.button("📤 Reveal Answers"):
        st.markdown(f"### ❓ Question: {st.session_state.question}")
        df = pd.DataFrame(st.session_state.answers, columns=["Player", "Answer"])
        st.dataframe(df)

        # Count answers
        counts = Counter([a[1] for a in st.session_state.answers])
        max_count = max(counts.values(), default=0)
        majority = [ans for ans, count in counts.items() if count == max_count]

        st.markdown(f"🧠 **Majority Answer(s):** {majority}")

        # Update scores
        for name, ans in st.session_state.answers:
            if ans in majority and len(majority) == 1:
                st.session_state.scores[name] = st.session_state.scores.get(name, 0) + 1

        # Assign Pink Cow
        pink_holder = None
        for name, ans in st.session_state.answers:
            if counts[ans] == 1:
                pink_holder = name
                break
        st.session_state.pink_cow = pink_holder
        if pink_holder:
            st.markdown(f"🐄 **Pink Cow goes to:** {pink_holder}")

        # Show scores
        if st.session_state.scores:
            score_df = pd.DataFrame(list(st.session_state.scores.items()), columns=["Player", "Score"])
            if st.session_state.pink_cow:
                score_df["Pink Cow"] = score_df["Player"].apply(lambda x: "🐄" if x == st.session_state.pink_cow else "")
            st.markdown("### 🏆 Scores")
            st.dataframe(score_df.sort_values("Score", ascending=False))

    # Reset for next round
    if st.button("🔄 Next Round (Clear Answers)"):
        st.session_state.answers = []

# --- PLAYER VIEW ---
with player_tab:
    st.subheader("🙋 Player View")
    if st.session_state.question:
        st.markdown(f"**Current Question:** {st.session_state.question}")
        with st.form("player_submission_form"):
            pname = st.text_input("Your Name")
            pans = st.text_input("Your Answer")
            psubmit = st.form_submit_button("Submit Answer")
            if psubmit:
                st.session_state.answers.append((pname.strip(), pans.strip().lower()))
                st.success("Answer submitted!")
    else:
        st.info("Waiting for host to set a question.")
