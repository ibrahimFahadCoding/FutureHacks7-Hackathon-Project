import streamlit as st
from google.cloud import vision
from together import Together
from PIL import Image
import os
from pathlib import Path
import markdown
from weasyprint import HTML
import re
from utils.db import save_summary
import PyPDF2 as pypdf
from dotenv import load_dotenv
from google.oauth2 import service_account
import random

#Page Config with Env Variables
st.set_page_config(page_title="Mind Bytes", layout="centered", page_icon="📝")
st.title("Mind Bytes")
st.caption("""Gimme whatever it is you don't understand and get back a summary! 📝""")

together_client = Together(api_key="5bd126d37c96a0f67f1e75a0ae0f8f959fcee795b32df2fedd56547e5127b7dd")

googlecreds = dict(st.secrets["google_credentials"])
creds = service_account.Credentials.from_service_account_info(googlecreds)



#Initialize LLaMA
def llama_chat(prompt, system=None):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})

    llama_response = together_client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=msgs,
        temperature=0.4
    )
    return llama_response.choices[0].message.content

#Get Summary + PDF
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

    downloads_path = "/tmp/"
    full_path = os.path.join(downloads_path, filename)
    HTML(string=styled_html).write_pdf(full_path)
    return full_path

#Get Photo
photo_option = st.radio("Choose how you'd like to capture the text: ", ["Upload an Image", "Take Live Photo", "Upload PDF"])

image_bytes = None
extracted_text = ""

if photo_option == "Upload an Image":
    uploaded_file = st.file_uploader("Upload Image ", type=["jpg","jpeg","png"])
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
        extracted_text = ""
        reader = pypdf.PdfReader(uploaded_pdf)
        for page in reader.pages:
            extracted_text += page.extract_text() or ""
        st.text_area("Extracted Text from PDF", extracted_text, height=200)



#Extract Text with Google Vision API
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

if 'extracted_text' in locals() and extracted_text:
    if st.button("Generate Summary with LLaMA 3"):
        with st.spinner("Generating Summary..."):
            try:
                summary_prompt = f"""You are a helpful AI that summarizes educational content for students. 
                Here is the block of text {extracted_text}. Summarize the key concepts in 
                **bullet point format** using clear, student-friendly language, so basically make a summary for 
                dummies. Explain things fully and concisely. Try to use just subheaders and nested bullet points
                so that its not just a wall of text."""

                summary_md = llama_chat(summary_prompt)
                st.subheader("AI Generated Summary")
                st.markdown(summary_md)

                title_prompt = f"""Give a short and clear title (max 6 words) for the 
                following study summary. Avoid Quotation marks or punctuation. 
                Summary: {summary_md}"""

                raw_title = llama_chat(title_prompt)
                clean_title = re.sub(r'\W+', '_', raw_title.strip().lower())[:40]
                pdf_filename = f"summary_{clean_title}.pdf"

                #Save to DB
                username = st.session_state.get("username", "guest")
                save_summary(username, raw_title.strip(), summary_md)

                pdf_path = save_markdown_pdf(summary_md, raw_title.strip(), pdf_filename)

                st.success(f"PDF Generated as `{pdf_filename}`!")
                with open(pdf_path, "rb") as f:
                    st.download_button("Download PDF", data=f, file_name=pdf_filename, mime="application/pdf")
            except Exception as e:
                st.error(f"Error Generating Summary: {e}")

# Check if a summary is available
if "summary_md" in st.session_state and st.session_state.summary_md:
    st.sidebar.subheader("🎮 Play a Study Game")

    game_mode = st.sidebar.radio("Choose Game Mode", ["None", "💣 Defuse the Bomb", "🧟 Survival Mode"])


    def generate_quiz(summary):
        quiz_prompt = f"""Based on this summary, create 10 multiple choice questions. 
        Each question should have 1 correct answer and 3 incorrect options. 
        Format it like this:

        Q: Question here?
        A) Option 1
        B) Option 2
        C) Option 3
        D) Option 4
        Answer: B
        ---
        Summary:
        {summary}
        """

        response = llama_chat(quiz_prompt)
        pattern = r"Q: (.*?)\n(A\) .*?)\n(B\) .*?)\n(C\) .*?)\n(D\) .*?)\nAnswer: ([A-D])"
        matches = re.findall(pattern, response, re.DOTALL)
        quiz = []
        for match in matches:
            question = match[0]
            options = [match[1][3:], match[2][3:], match[3][3:], match[4][3:]]
            answer = "ABCD".index(match[5])
            quiz.append((question, options, answer))
        return quiz


    if game_mode != "None":
        with st.spinner("Loading questions..."):
            quiz = generate_quiz(st.session_state.summary_md)

        if game_mode == "💣 Defuse the Bomb":
            st.subheader("💣 Defuse the Bomb")
            score = 0
            for i, (question, options, answer) in enumerate(quiz):
                st.markdown(f"**{i + 1}. {question}**")
                choice = st.radio("", options, key=f"bomb_{i}")
                if st.button("Lock Answer", key=f"lock_{i}"):
                    if options.index(choice) == answer:
                        score += 1
                        st.success("✅ Correct! Bomb defused!")
                    else:
                        st.error("💥 Boom! Wrong answer.")
                        break
            st.info(f"Final Score: {score}/{len(quiz)}")

        elif game_mode == "🧟 Survival Mode":
            st.subheader("🧟 Survival Mode")
            lives = 3
            score = 0
            for i, (question, options, answer) in enumerate(quiz):
                st.markdown(f"**{i + 1}. {question}**")
                choice = st.radio("", options, key=f"survival_{i}")
                if st.button("Submit", key=f"submit_{i}"):
                    if options.index(choice) == answer:
                        st.success("✅ Correct!")
                        score += 1
                    else:
                        st.error("❌ Wrong!")
                        lives -= 1
                        if lives == 0:
                            st.warning("🧟 You didn't survive...")
                            break
                    st.info(f"Lives left: {lives}")
            if lives > 0:
                st.success(f"🎉 You survived! Score: {score}/{len(quiz)}")