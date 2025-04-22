import streamlit as st
from google.cloud import vision
from together import Together
from PIL import Image
import os
from pathlib import Path
import markdown
from weasyprint import HTML
import re
from utils.db import save_summary, load_summaries
import PyPDF2 as pypdf
from dotenv import load_dotenv
from google.oauth2 import service_account
import random
import json
import time

# Page Config
st.set_page_config(page_title="Mind Bytes", layout="centered", page_icon="📝")
st.title("Mind Bytes")
st.caption("""Gimme whatever it is you don't understand and get back a summary! 📝""")

# API Clients
together_client = Together(api_key="5bd126d37c96a0f67f1e75a0ae0f8f959fcee795b32df2fedd56547e5127b7dd")
googlecreds = dict(st.secrets["google_credentials"])
creds = service_account.Credentials.from_service_account_info(googlecreds)

# Username from session (fallback = guest)
username = st.session_state.get("username", "guest")

# LLaMA Function
def llama_chat(prompt, system=None):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    response = together_client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=msgs,
        temperature=0.4
    )
    return response.choices[0].message.content

# Save PDF
def save_markdown_pdf(md_text, title, filename):
    html = markdown.markdown(md_text, extensions=["fenced_code", "tables"])
    styled_html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 2em;
                line-height: 1.6;
            }}
            h1 {{
                font-size: 24px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        {html}
    </body>
    </html>
    """
    path = "/tmp/"
    full_path = os.path.join(path, filename)
    HTML(string=styled_html).write_pdf(full_path)
    return full_path

# Input Option
photo_option = st.radio("Choose how you'd like to capture the text: ", ["Upload an Image", "Take Live Photo", "Upload PDF"])

image_bytes = None
extracted_text = ""

if photo_option == "Upload an Image":
    uploaded_file = st.file_uploader("Upload Image ", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        image_bytes = uploaded_file.read()

elif photo_option == "Take Live Photo":
    cam_input = st.camera_input("Snap a Pic with the Camera")
    if cam_input:
        st.image(cam_input, caption="Captured Image", use_container_width=True)
        image_bytes = cam_input.getvalue()

elif photo_option == "Upload PDF":
    uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded_pdf:
        reader = pypdf.PdfReader(uploaded_pdf)
        for page in reader.pages:
            extracted_text += page.extract_text() or ""
        st.text_area("Extracted Text from PDF", extracted_text, height=200)

# Google Vision for Images
if image_bytes:
    image = vision.Image(content=image_bytes)
    st.subheader("Extracting Text...")
    try:
        client = vision.ImageAnnotatorClient(credentials=creds)
        response = client.document_text_detection(image=image)
        texts = response.text_annotations
        if texts:
            extracted_text = texts[0].description
            st.text_area("Extracted Text", extracted_text, height=200)
        else:
            st.error("No Text Found")
            st.stop()
    except Exception as e:
        st.error(f"Google Vision Error: {e}")
        st.stop()

# Generate Summary Button
if extracted_text:
    if st.button("Generate Summary with LLaMA 3"):
        with st.spinner("Generating Summary..."):
            try:
                summary_prompt = f"""You are a helpful AI that summarizes educational content for students. 
                Here is the block of text {extracted_text}. Summarize the key concepts in 
                **bullet point format** using clear, student-friendly language. Use subheaders and nested bullets."""

                summary_md = llama_chat(summary_prompt)
                st.session_state["summary_md"] = summary_md

                st.subheader("AI Generated Summary")
                st.markdown(summary_md)

                title_prompt = f"""Give a short and clear title (max 6 words) for this summary. No punctuation.
                Summary: {summary_md}"""
                raw_title = llama_chat(title_prompt).strip()
                st.session_state["summary_title"] = raw_title

                # Save to DB
                save_summary(username, raw_title, summary_md)

                pdf_filename = f"summary_{re.sub(r'\\W+', '_', raw_title.lower())[:40]}.pdf"
                pdf_path = save_markdown_pdf(summary_md, raw_title, pdf_filename)

                st.success(f"PDF Generated: `{pdf_filename}`")
                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", data=f, file_name=pdf_filename, mime="application/pdf")
            except Exception as e:
                st.error(f"Error Generating Summary: {e}")

# --- Sidebar Setup ---
st.sidebar.subheader("🎮 Play a Study Game")

user_summaries = load_summaries().get(username, [])
summary_titles = [s["title"] for s in user_summaries]

selected_title = st.sidebar.selectbox("Choose a Summary", ["None"] + summary_titles)
game_mode = st.sidebar.radio("Choose Game Mode", ["None", "💣 Defuse the Bomb", "😎 Chill Mode"])

# --- Game Setup ---
def generate_quiz(summary):
    quiz_prompt = f"""Based on this summary, create 10 multiple choice questions. 
Each question must have 1 correct answer and 3 incorrect answers. Format:

Q: What is...?
A) ...
B) ...
C) ...
D) ...
Answer: B
---
Summary:
{summary}"""
    response = llama_chat(quiz_prompt)
    pattern = r"Q: (.*?)\nA\) (.*?)\nB\) (.*?)\nC\) (.*?)\nD\) (.*?)\nAnswer: ([A-D])"
    matches = re.findall(pattern, response, re.DOTALL)
    quiz = []
    for m in matches:
        q = m[0]
        opts = [m[1], m[2], m[3], m[4]]
        ans = "ABCD".index(m[5])
        quiz.append((q, opts, ans))
    return quiz

if selected_title != "None" and game_mode != "None":
    selected_summary = next((s for s in user_summaries if s["title"] == selected_title), None)

    if selected_summary:
        if "quiz_id" not in st.session_state or st.session_state.quiz_id != f"{selected_title}_{game_mode}":
            with st.spinner("Generating Questions..."):
                quiz = generate_quiz(selected_summary["summary"])
                st.session_state.quiz = quiz
                st.session_state.quiz_id = f"{selected_title}_{game_mode}"
                st.session_state.current_q = 0
                st.session_state.score = 0
                st.session_state.lives = 3

        quiz = st.session_state.quiz
        curr = st.session_state.current_q
        total = len(quiz)

        # 💣 DEFUSE THE BOMB MODE
        if game_mode == "💣 Defuse the Bomb":
            st.subheader("💣 Defuse the Bomb")

            if curr < total and st.session_state.lives > 0:
                q, opts, ans = quiz[curr]
                st.markdown(f"### Question {curr + 1} of {total}")
                st.markdown(f"**{q}**")
                choice = st.radio("Pick your answer:", opts, key=f"bomb_q_{curr}")

                timer_placeholder = st.empty()
                locked_key = f"locked_{curr}"
                start_time = time.time()

                for i in range(10, 0, -1):
                    if locked_key in st.session_state:
                        break
                    timer_placeholder.warning(f"⏱️ Time Left: {i} seconds")
                    time.sleep(1)

                if st.button("Lock Answer", key=f"lock_{curr}"):
                    st.session_state[locked_key] = True
                    if opts.index(choice) == ans:
                        st.success("✅ Correct! Bomb defused.")
                        st.session_state.score += 1
                    else:
                        st.error(f"💥 Boom! Wrong answer. Correct: **{opts[ans]}**")
                        st.session_state.lives = 0
                    st.session_state.current_q += 1
                    st.rerun()

                elif time.time() - start_time >= 10 and locked_key not in st.session_state:
                    st.warning("⏰ Time's up!")
                    st.session_state.lives = 0
                    st.session_state.current_q += 1
                    st.rerun()

                st.warning(f"💣 Lives left: {st.session_state.lives}")

            else:
                if st.session_state.lives <= 0:
                    st.error("Game Over! The bomb exploded 💥")
                else:
                    st.success(f"🎉 You defused all bombs! Score: {st.session_state.score}/{total}")

        # 😎 CHILL MODE
        elif game_mode == "😎 Chill Mode":
            st.subheader("😎 Chill Mode")

            if curr < total:
                q, opts, ans = quiz[curr]
                st.markdown(f"### Question {curr + 1} of {total}")
                st.markdown(f"**{q}**")
                choice = st.radio("Pick your answer:", opts, key=f"chill_q_{curr}")

                if st.button("Submit Answer", key=f"submit_{curr}"):
                    if opts.index(choice) == ans:
                        st.success("✅ Correct!")
                        st.session_state.score += 1
                    else:
                        st.error(f"❌ Oops! Correct answer: **{opts[ans]}**")
                    st.session_state.current_q += 1
                    st.rerun()
            else:
                st.success(f"😎 Done! Final Score: {st.session_state.score}/{total}")
