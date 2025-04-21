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

# Display form to add tasks
task = st.text_input("Enter Task Name")
priority = st.selectbox("Priority", ["Low", "Medium", "High"])
if st.button("Add Task") and task.strip():
    st.session_state.tasks.append({"task": task, "priority": priority, "done": False})
    save_user_tasks(username, st.session_state.tasks)
    st.rerun()

# Separate tasks into pending and completed
pending_tasks = [t for t in st.session_state.tasks if not t["done"]]
completed_tasks = [t for t in st.session_state.tasks if t["done"]]

# Display Pending Tasks
if pending_tasks:
    st.subheader("Pending Tasks")
    for i, task in enumerate(pending_tasks):
        with col1:
            text = f'<span style="font-size: 25px;">{priority_dict[task["priority"]]} {task["task"]}</span>'
            st.markdown(text, unsafe_allow_html=True)

        with col2:
            if st.button("✅", key=f"done_{i}"):
                task["done"] = True
                st.success("Good Job! Task Completed!")
                save_user_tasks(username, st.session_state.tasks)
                time.sleep(5)
                st.rerun()

        with col3:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.tasks.remove(task)
                save_user_tasks(username, st.session_state.tasks)
                st.rerun()

# Display Completed Tasks
if completed_tasks:
    st.subheader("Completed Tasks")
    for i, task in enumerate(completed_tasks):
        with col1:
            text = f'<span style="font-size: 25px;">{priority_dict[task["priority"]]} Task Completed! </span> <span style="font-size:25px; text-decoration:line-through;"> {task["task"]}</span>'
            st.markdown(text, unsafe_allow_html=True)

        with col2:
            if st.button("❌ Undo", key=f"undo_{i}"):
                task["done"] = False
                st.success("Task has been marked as pending!")
                save_user_tasks(username, st.session_state.tasks)
                time.sleep(2)
                st.rerun()

        with col3:
            if st.button("🗑️", key=f"del_completed_{i}"):
                st.session_state.tasks.remove(task)
                save_user_tasks(username, st.session_state.tasks)
                st.rerun()

# If no tasks exist
if not st.session_state.tasks:
    st.info("No Tasks Saved")
