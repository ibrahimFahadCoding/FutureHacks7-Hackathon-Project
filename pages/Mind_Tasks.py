import streamlit as st
from utils.db import get_user_tasks, save_user_tasks
import time

st.title("🗂️ Task Manager")
username = st.session_state.get("username", "guest")
st.session_state.tasks = get_user_tasks(username)

colors = {"High": "red", "Medium": "orange", "Low": "green"}

if not st.session_state.tasks:
    st.info("No Tasks Saved")

task = st.text_input("Enter Task Name")
priority = st.selectbox("Priority", ["Low", "Medium", "High"])
if st.button("Add Task") and task.strip():
    st.session_state.tasks.append({"task": task, "priority": priority, "done": False})
    save_user_tasks(username, st.session_state.tasks)
    st.rerun()
for i, j in enumerate(st.session_state.tasks):
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        text = f'<span style="font-size: 20px; color:{colors[j["priority"]]};">[{j["priority"]}]</span> <span style="font-size:20px;">{j["task"]}</span>'
        st.markdown(text, unsafe_allow_html=True)
    with col2:
        if st.button("✅", key=f"done_{i}"):
            if not j["done"]:
                j["done"] = True
                st.session_state.tasks.pop(i)
                save_user_tasks(username, st.session_state.tasks)
                st.success("Good Job! Task Completed!")
                time.sleep(5)
                st.rerun()
    with col3:
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.tasks.pop(i)
            save_user_tasks(username, st.session_state.tasks)
            st.rerun()