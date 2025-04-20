import streamlit as st
st.title("LockIn")

if st.button("Login/Register"):
    st.switch_page("pages/Login.py")

