import streamlit as st
st.title("LLaMAHub")
st.caption("The mishmash of sick study tools!")

st.markdown("""
LLaMAHub is designed to be a study-app for everyone, which a bunch of sick features such as:

- **LLaMA Bytes**: Take a Photo, Upload an Image or Upload a PDF and get a clean summary that explains things in human language.
- **LLaMA Bot** If anything goes above youur head, don't hesitate to ask about anything!
- **LLaMA Tasks** Organize tasks with color coded priority tags, makes it visually easier to see your most important tasks!

A whole hub, a LLaMAHub, all in one place! 
""")

if st.button("Login / Register"):
    st.switch_page("pages/Login.py")