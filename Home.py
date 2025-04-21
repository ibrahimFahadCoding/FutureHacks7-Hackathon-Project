import streamlit as st
st.set_page_config(page_title="Home", page_icon="🏠")
st.title("Mindframe")
st.caption("The mishmash of sick study tools!")

st.markdown("""
Mindframe is designed to be a study-app for everyone, which a bunch of sick features such as:

- **Mind Bytes**: Take a Photo, Upload an Image or Upload a PDF and get a clean summary that explains things in human language.
- **Mind Bot** If anything goes above youur head, don't hesitate to ask about anything!
- **Mind Tasks** Organize tasks with color coded priority tags, makes it visually easier to see your most important tasks!

A whole hub, all in one place! 
""")

if st.button("Login / Register"):
    st.switch_page("pages/Login.py")