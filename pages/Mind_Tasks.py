import streamlit as st
from utils.db import get_user_tasks, save_user_tasks
import time

st.title("🗂️ Mind Tasks")
col1, col2, col3 = st.columns([5, 2, 2])
username = st.session_state.get("username", "guest")
st.session_state.tasks = get_user_tasks(username)

# Color dictionary with square representation
priority_dict = {
    "High": '<span style="display:inline-block; width:20px; height:20px; background-color:red;"></span>',
    "Medium": '<span style="display:inline-block; width:20px; height:20px; background-color:orange;"></span>',
    "Low": '<span style="display:inline-block; width:20px; height:20px; background-color:green;"></span>',
}

if not st.session_state.tasks:
    st.info("No Tasks Saved")

task = st.text_input("Enter Task Name")
priority = st.selectbox("Priority", ["Low", "Medium", "High"])
if st.button("Add Task") and task.strip():
    st.session_state.tasks.append({"task": task, "priority": priority, "done": False})
    save_user_tasks(username, st.session_state.tasks)
    st.rerun()

for i, j in enumerate(st.session_state.tasks):
    with col1:
        if j["done"]:
            # Display the task with the color-coded square for completed tasks
            text = f'<span style="font-size: 25px;">{priority_dict[j["priority"]]} Task Completed! </span> <span style="font-size:25px; text-decoration:line-through;"> {j["task"]}</span>'
            st.markdown(text, unsafe_allow_html=True)
        else:
            # Display the task with the color-coded square for tasks that are not completed
            text = f'<span style="font-size: 25px;">{priority_dict[j["priority"]]} {j["task"]}</span>'
            st.markdown(text, unsafe_allow_html=True)

    with col2:
        if st.button("✅", key=f"done_{i}"):
            if not j["done"]:
                j["done"] = True
                st.success("Good Job! Task Completed!")
                time.sleep(1)
                st.rerun()

    with col3:
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.tasks.pop(i)
            save_user_tasks(username, st.session_state.tasks)
            st.rerun()
