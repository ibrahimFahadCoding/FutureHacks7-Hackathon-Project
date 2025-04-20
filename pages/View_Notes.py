import streamlit as st
from utils.db import load_summaries
import json
import os

#Page Setup
st.set_page_config(page_title="My Notes", page_icon="📚")
st.title("📚 Saved Notes")


#Get Credentials
username = st.session_state.get("username", "guest")
summaries = load_summaries().get(username, [])

if not summaries:
    st.info("No Notes Saved Yet.")
else:
    for idx, s in enumerate(summaries):
        with st.expander(f"{s["title"]}"):
            st.markdown(s["summary"])
            if st.button("Delete", key=f"del_{idx}"):
                summaries.pop(idx)
                st.success("Summary Deleted!")
                os.makedirs("data", exist_ok=True)
                with open("data/summaries.json", "w") as f:
                    json.dump({username: summaries}, f, indent=2)
                st.rerun()

