import streamlit as st
from utils.auth import create_user, authenticate

#Page Setup
st.set_page_config(page_title="Login/Register", layout="centered")
st.title("Welcome to LLaMA Bytes")
st.caption("Create a User or Login!")

#Check if User is Logged in
if 'username' in st.session_state:
    st.success(f"Welcome back, {st.session_state["username"]}!")
    st.button("Log Out", on_click=lambda: st.session_state.pop('username', None))
else:
    #Page Select (Login/Register)
    page = st.radio("Select a Page:", ("Login", "Register"))
    if page == "Register":
        st.subheader("Create New User")

        #Create User Inputs
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Create User"):
            if new_password != confirm_password:
                st.error("Passwords Do Not Match!")
            elif create_user(new_username, new_password):
                st.success(f"User Created for {new_username} Successfully!")
                st.session_state["username"] = new_username
            else:

                st.error("Username Already Taken!")

    elif page == "Login":
        st.subheader("Login to your Account")
        #Login Inputs
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Log In"):
            if authenticate(username, password):
                st.success(f"Welcome back, {username}")
                st.session_state["username"] = username
            else:
                st.error("Invalid Username or Password!")
