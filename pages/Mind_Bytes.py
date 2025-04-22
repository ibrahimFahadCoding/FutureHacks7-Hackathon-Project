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

# --- Sidebar Games ---
st.sidebar.subheader("🎮 Play a Study Game")

user_summaries = load_summaries().get(username, [])
summary_titles = [s["title"] for s in user_summaries]

selected_title = st.sidebar.selectbox("Choose a Summary", ["None"] + summary_titles)
game_mode = st.sidebar.radio("Choose Game Mode", ["None", "💣 Defuse the Bomb", "🧟 Survival Mode"])

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

# Check if a summary is selected and a game mode is chosen
if selected_title != "None" and game_mode != "None":
    # Check if the selected title has changed or quiz hasn't been generated yet
    if "selected_title" not in st.session_state or st.session_state.selected_title != selected_title:
        selected_summary = next((s for s in user_summaries if s["title"] == selected_title), None)
        if selected_summary:
            with st.spinner("Generating Questions..."):
                quiz = generate_quiz(selected_summary["summary"])
                st.session_state.quiz = quiz
                st.session_state.selected_title = selected_title
                st.session_state.answers = [None] * len(quiz)
                st.session_state.score = 0
                st.session_state.lives = 3
    else:
        quiz = st.session_state.quiz


        if game_mode == "💣 Defuse the Bomb":
            st.subheader("💣 Defuse the Bomb")
            score = 0
            for i, (q, opts, ans) in enumerate(quiz):
                st.markdown(f"**{i+1}. {q}**")
                choice = st.radio("", opts, key=f"bomb_{i}")
                if st.button("Lock Answer", key=f"lock_{i}"):
                    if opts.index(choice) == ans:
                        score += 1
                        st.success("✅ Correct!")
                    else:
                        st.error("💥 Boom! Wrong answer.")
                        break
            st.info(f"Final Score: {score}/{len(quiz)}")

        elif game_mode == "🧟 Survival Mode":
            st.subheader("🧟 Survival Mode")
            lives = st.session_state.lives
            score = st.session_state.score
            for i, (q, opts, ans) in enumerate(quiz):
                st.markdown(f"**{i+1}. {q}**")
                choice = st.radio("", opts, key=f"survival_{i}")
                if st.button("Submit", key=f"submit_{i}"):
                    if opts.index(choice) == ans:
                        st.success("✅ Correct!")
                        score += 1
                    else:
                        st.error("❌ Wrong!")
                        lives -= 1
                        if lives == 0:
                            st.warning("🧟 You didn't survive...")
                            break
                    st.session_state.score = score
                    st.session_state.lives = lives
                    st.info(f"Lives left: {lives}")
            if lives > 0:
                st.success(f"🎉 You survived! Score: {score}/{len(quiz)}")
