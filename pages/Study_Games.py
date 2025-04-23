import streamlit as st
import random
import json
import time
from utils.db import load_summaries
from together import Together

# Setup
st.set_page_config(page_title="Quiz Games", page_icon="🎮")
st.title("🎮 Quiz Games")

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
mode = st.radio("Choose Your Mode", ["💣 Defuse the Bomb", "😎 Chill Mode"])

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

        choice_placeholder = st.empty()
        chosen = choice_placeholder.radio("", q['options'], index=None, key=f"q_{idx}")

        if chosen:
            choice_placeholder.empty()
            correct = q['options'][q['correct']]
            if chosen == correct:
                score += 1
                if mode == "💣 Defuse the Bomb":
                    wire_choices = random.sample(wire_colors, 4)
                    correct_wire = random.choice(wire_choices)
                    st.markdown("**Pick the correct wire to defuse:**")
                    wire_placeholder = st.empty()

                    start_time = time.time()
                    picked_wire = wire_placeholder.radio(
                        "",
                        [f"<span style='color:{color_to_code[c]}'>{c.capitalize()} Wire</span>" for c in wire_choices],
                        format_func=lambda x: x,
                        key=f"wire_{idx}",
                        label_visibility="collapsed",
                        index=None,
                    )

                    if picked_wire:
                        wire_placeholder.empty()
                        picked_color = re.search(r"color:(#[0-9A-Fa-f]+)", picked_wire)
                        if picked_color:
                            picked_color = picked_color.group(1)
                            if color_to_code[correct_wire] != picked_color:
                                st.error("💥 Wrong wire! Boom!")
                                break
                            else:
                                st.success("✅ Wire cut successfully!")
                        else:
                            st.error("🚩 Couldn't detect color. Game error.")
                            break
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
