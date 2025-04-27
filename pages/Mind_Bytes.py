import streamlit as st
from google.cloud import vision
from mistralai import Mistral
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
client = Mistral(api_key="CxXUpnz9TPqQvH2yDayDDNb97yH4BVbt")
googlecreds = dict(st.secrets["google_credentials"])
creds = service_account.Credentials.from_service_account_info(googlecreds)

# Username from session (fallback = guest)
username = st.session_state.get("username", "guest")

# LLaMA Function
def mistral_chat(prompt, system=None):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    response = client.chat.complete(
        model="mistral-large-latest",
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

# Chunking Function (No tiktoken)
def split_text_into_chunks(text, max_words=2000):  # ~2000 words ≈ 6000 tokens
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_words:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# Word count check
def count_words(text):
    return len(text.split())

# Maximum word count threshold to trigger re-summarization
MAX_WORD_COUNT = 1000

# Input Option
photo_option = st.radio("Choose how you'd like to capture the text: ", ["Upload an Image", "Take Live Photo", "Upload PDF", "Paste Text"])

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

elif photo_option == "Paste Text":
    extracted_text = st.text_input(label='marhaba', label_visibility="hidden", placeholder="Enter Text Here...")

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
        info_msg = st.info("")
        with st.spinner("Generating Summary..."):
            try:
                chunks = split_text_into_chunks(extracted_text, max_words=2000)
                summaries = []
                for i, chunk in enumerate(chunks):
                    info_msg.info(f"Summarizing chunk {i + 1}/{len(chunks)}...")
                    # Adjusting the prompt to focus on high-level summaries
                    summary_prompt = f"""
                    You are an expert educational assistant that helps students learn by summarizing complex information into clear, organized, and engaging study notes.

                    Summarize the following text using the following format:
                    - Use **clear, student-friendly language**.
                    - Organize the summary with **meaningful subheadings**.
                    - Present ideas in **concise bullet points**, grouped logically under the subheadings.
                    - Where appropriate, use **nested bullets** to break down more detailed ideas simply.
                    - **Avoid copying the text verbatim**—rephrase and explain for clarity and better retention.
                    - **Avoid vague or overly technical language** unless necessary—and if needed, define it briefly and clearly.
                    - **If the text is very long**:
                        - Create a **high-level overview** only.
                        - **Include 5-7 bullet points per section**.
                        - Focus on the **very important concepts** and **include smaller details ONLY if possible**.
                        - Keep it under 600 words.
                        - Avoid repetition
                        - Include examples for each topic using a nested bullet point.
                    - Focus on **summarizing only the most important concepts**, avoid detailed descriptions unless necessary.

                    Text chunk ({i+1}/{len(chunks)}):
                    {chunk}
                    """
                    summaries.append(mistral_chat(summary_prompt))

                # Combine all summaries
                final_summary_md = "\n\n---\n\n".join(summaries)
                st.session_state["summary_md"] = final_summary_md

                # Check word count of the final summary
                if count_words(final_summary_md) > MAX_WORD_COUNT:
                    #st.warning(f"Summary is over {MAX_WORD_COUNT} words. Re-summarizing to make it more concise...")
                    # Re-summarize if the summary is too long
                    re_summary_prompt = f"""
                    You are an expert educational assistant that helps students learn by summarizing complex information into clear, organized, and engaging study notes.

                    The following summary is too long. Please condense it to make it more concise while retaining the very important ideas. 
                    The new summary should not exceed 500 words.

                    Current summary:
                    {final_summary_md}
                    """
                    final_summary_md = mistral_chat(re_summary_prompt)

                # Displaying AI-generated summary (after possible re-summarizing)
                st.subheader("AI Generated Summary")
                st.markdown(final_summary_md)

                # Generate a concise title
                title_prompt = f"""Give a short and clear title (max 6 words) for this summary. No punctuation.
                Summary: {final_summary_md}"""
                raw_title = mistral_chat(title_prompt).strip()
                st.session_state["summary_title"] = raw_title

                # Save to database
                save_summary(username, raw_title, final_summary_md)

                # Create and serve PDF
                safe_title = re.sub(r'\W+', '_', raw_title.lower())[:40]
                pdf_filename = f"summary_{safe_title}.pdf"
                pdf_path = save_markdown_pdf(final_summary_md, raw_title, pdf_filename)

                st.success(f"PDF Generated: `{pdf_filename}`")
                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", data=f, file_name=pdf_filename, mime="application/pdf")


            except Exception as e:

                error_message = str(e)

                if "inputs tokens + max_new_tokens must be" in error_message:
                    raise ValueError("Too many tokens in file. Try summarizing a smaller portion or a smaller file.")

                raise RuntimeError(f"Unexpected error from Together API: {error_message}")
