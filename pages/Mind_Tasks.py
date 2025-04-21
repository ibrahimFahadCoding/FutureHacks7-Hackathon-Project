import streamlit as st
from utils.db import get_user_tasks, save_user_tasks
import time

st.title("🗂️ Mind Tasks")

username = st.session_state.get("username", "guest")
if "tasks" not in st.session_state:
    st.session_state.tasks = get_user_tasks(username)

colors = {"High": "red", "Medium": "orange", "Low": "green"}

# Task Input
task = st.text_input("Enter Task Name")
priority = st.selectbox("Priority", ["Low", "Medium", "High"])
if st.button("Add Task") and task.strip():
    st.session_state.tasks.append({"task": task, "priority": priority, "done": False})
    save_user_tasks(username, st.session_state.tasks)
    st.rerun()

# Split tasks
pending_tasks = [t for t in st.session_state.tasks if not t["done"]]
completed_tasks = [t for t in st.session_state.tasks if t["done"]]

# --- Pending Tasks ---
st.subheader("🕒 Pending Tasks")
if not pending_tasks:
    st.info("No pending tasks.")
else:
    for i, j in enumerate(pending_tasks):
        col1, col2, col3 = st.columns([5, 2, 2])
        with col1:
            text = f'<span style="font-size: 25px; color:{colors[j["priority"]]};">[{j["priority"]}]</span> <span style="font-size:25px;"> {j["task"]}</span>'
            st.markdown(text, unsafe_allow_html=True)
        with col2:
            if st.button("✅", key=f"done_{i}"):
                j["done"] = True
                save_user_tasks(username, st.session_state.tasks)
                st.success("Good Job! Task Completed!")
                time.sleep(1)
                st.rerun()
        with col3:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.tasks.remove(j)
                save_user_tasks(username, st.session_state.tasks)
                st.rerun()

# --- Completed Tasks ---
st.subheader("✅ Completed Tasks")
if not completed_tasks:
    st.info("No tasks completed yet.")
else:
    for i, j in enumerate(completed_tasks):
        col1, col2 = st.columns([7, 2])
        with col1:
            text = f'<span style="font-size: 25px; color:{colors[j["priority"]]};">[* ✅] [{j["priority"]}]</span> <span style="font-size:25px;"> {j["task"]}</span>'
            st.markdown(text, unsafe_allow_html=True)
        with col2:
            if st.button("🗑️", key=f"del_done_{i}"):
                st.session_state.tasks.remove(j)
                save_user_tasks(username, st.session_state.tasks)
                st.rerun()
