import streamlit as st
import random
import json
import time
from utils.db import load_summaries
from together import Together

# Setup
st.set_page_config(page_title="😎 Quiz Modes", page_icon="😎")
st.title("😎 Defuse the Bomb or Chill")

# Get Username and Summaries
username = st.session_state.get("username", "guest")
summaries = load_summaries().get(username, [])

# LLaMA API
llama = Together(api_key="YOUR_TOGETHER_API_KEY")

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
mode = st.radio("Choose Your Mode", ["💣 Defuse the Bomb", "😎 Chill Mode"])

# Pick a summary
if not summaries:
    st.warning("No summaries available. Go generate one first!")
    st.stop()

summary_titles = [s['title'] for s in summaries]
selected_title = st.selectbox("Pick a Summary to Quiz On", summary_titles)
summary_text = next(s['summary'] for s in summaries if s['title'] == selected_title)

# Generate MCQs
if 'questions' not in st.session_state and st.button("Start Quiz"):
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
            st.session_state.questions = questions
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.lives = 1 if mode == "💣 Defuse the Bomb" else 999
        except Exception as e:
            st.error(f"Error generating quiz: {e}")
            st.stop()

if 'questions' in st.session_state:
    questions = st.session_state.questions
    q_idx = st.session_state.current_q
    score = st.session_state.score
    lives = st.session_state.lives

    if q_idx < len(questions) and lives > 0:
        q = questions[q_idx]
        st.subheader(f"Question {q_idx + 1}")
        st.markdown(f"**{q['question']}**")

        timer_placeholder = st.empty()
        choice_placeholder = st.empty()
        wire_placeholder = st.empty()
        result_placeholder = st.empty()

        start_time = time.time()
        answered = False

        while time.time() - start_time < 10 and not answered:
            remaining = int(10 - (time.time() - start_time))
            timer_placeholder.markdown(f"⏱️ Time left: {remaining}s")
            chosen = choice_placeholder.radio("", q['options'], index=None, key=f"q_{q_idx}")
            if chosen:
                answered = True
                correct = q['options'][q['correct']]
                if chosen == correct:
                    st.session_state.score += 1
                    if mode == "💣 Defuse the Bomb":
                        wire_colors = ["red", "blue", "green", "yellow"]
                        color_to_code = {
                            "red": "#FF4136",
                            "blue": "#0074D9",
                            "green": "#2ECC40",
                            "yellow": "#FFDC00"
                        }
                        correct_wire = random.choice(wire_colors)
                        chosen_wire = st.radio("Which wire do you want to cut?", wire_colors, format_func=lambda x: f"{x.capitalize()} wire", key=f"wire_{q_idx}")
                        wire_color_text = f"<span style='color:{color_to_code[chosen_wire]}; font-weight:bold;'>{chosen_wire.capitalize()} wire</span>"
                        wire_placeholder.markdown(f"You chose to cut the {wire_color_text}.", unsafe_allow_html=True)

                        if chosen_wire != correct_wire:
                            result_placeholder.error("💥 Wrong wire! Boom!")
                            st.session_state.lives = 0
                            break
                        else:
                            result_placeholder.success("✅ Safe wire! Moving on!")
                    else:
                        result_placeholder.success("✅ Correct!")
                else:
                    result_placeholder.error(f"❌ Wrong. The correct answer was: {correct}")
                    if mode == "💣 Defuse the Bomb":
                        result_placeholder.error("💥 Boom! Game Over.")
                        st.session_state.lives = 0
                        break
            time.sleep(0.25)

        if not answered:
            result_placeholder.error("⏰ Time's up! Boom!")
            st.session_state.lives = 0

        st.session_state.current_q += 1

    if st.session_state.lives > 0 and st.session_state.current_q >= len(st.session_state.questions):
        st.subheader("Final Score")
        st.markdown(f"**{st.session_state.score} / {len(st.session_state.questions)}**")
        del st.session_state.questions
        del st.session_state.current_q
        del st.session_state.score
        del st.session_state.lives

    if st.session_state.lives <= 0:
        st.subheader("💀 Game Over")
        st.markdown(f"**Final Score: {st.session_state.score} / {len(st.session_state.questions)}**")
        del st.session_state.questions
        del st.session_state.current_q
        del st.session_state.score
        del st.session_state.lives
