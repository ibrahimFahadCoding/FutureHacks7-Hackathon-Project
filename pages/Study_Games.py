import streamlit as st
import random
import json
import time
from utils.db import load_summaries
from together import Together

# Setup
st.set_page_config(page_title="Quiz Modes", page_icon="🎮")
st.title("🎮 Defuse the Bomb or Chill")

# Get Username and Summaries
username = st.session_state.get("username", "guest")
summaries = load_summaries().get(username, [])

# LLaMA API
llama = Together(api_key="5bd126d37c96a0f67f1e75a0ae0f8f959fcee795b32df2fedd56547e5127b7dd")

def llama_generate_mcqs(summary):
    prompt = f"""
    Generate 10 multiple choice questions based on the following summary. Each question should have:
    - 1 correct answer
    - 3 incorrect but plausible options
    - A format like:
    Q: What is ...?
    A) Option 1
    B) Option 2
    C) Option 3
    D) Option 4
    Answer: A

    Summary:
    {summary}
    """
    response = llama.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content

# Game Mode Choice
mode = st.radio("Choose Your Mode", ["💣 Defuse the Bomb", "😎️ Chill Mode"])

# Pick a summary
if not summaries:
    st.warning("No summaries available. Go generate one first!")
    st.stop()

summary_titles = [s['title'] for s in summaries]
selected_title = st.selectbox("Pick a Summary to Quiz On", summary_titles)
summary_text = next(s['summary'] for s in summaries if s['title'] == selected_title)

# Generate MCQs
if st.button("Start Quiz"):
    with st.spinner("Generating Questions..."):
        try:
            mcqs_raw = llama_generate_mcqs(summary_text)
            questions = []
            blocks = mcqs_raw.strip().split("Q:")
            for block in blocks[1:]:
                q_lines = block.strip().split("\n")
                question = q_lines[0].strip()
                options = [line.split(") ")[1].strip() for line in q_lines[1:5]]
                correct_letter = q_lines[5].split(": ")[1].strip()
                correct_index = ord(correct_letter) - ord('A')
                questions.append({
                    "question": question,
                    "options": options,
                    "correct": correct_index
                })
        except Exception as e:
            st.error(f"Error generating quiz: {e}")
            st.stop()

    # Gameplay
    score = 0
    lives = 1 if mode == "💣 Defuse the Bomb" else 999
    wire_colors = ["red", "blue", "green", "yellow"]
    color_to_code = {"red": "#FF4136", "blue": "#0074D9", "green": "#2ECC40", "yellow": "#FFDC00"}

    for idx, q in enumerate(questions):
        st.subheader(f"Question {idx + 1}")
        st.markdown(f"**{q['question']}**")
        chosen = st.radio("Choose your answer:", q['options'], index=None, key=f"q_{idx}")

        if chosen:
            correct = q['options'][q['correct']]
            if chosen == correct:
                score += 1
                if mode == "💣 Defuse the Bomb":
                    wire_choice = random.choice(wire_colors)
                    wire_text = f"**<span style='color:{color_to_code[wire_choice]}'>Cut the {wire_choice} wire</span>**"
                    st.markdown(wire_text, unsafe_allow_html=True)
                    if random.random() < 0.25:
                        st.error("💥 You chose the wrong wire. Boom!")
                        break
                    else:
                        st.success("✅ Wire cut safely. Moving on!")
                else:
                    st.success("✅ Correct!")
            else:
                st.error(f"❌ Wrong. The correct answer was: {correct}")
                if mode == "💣 Defuse the Bomb":
                    st.error("💥 Boom! Game Over.")
                    break

            time.sleep(1.5)

    st.subheader("Final Score")
    st.markdown(f"**{score} / {len(questions)}**")
