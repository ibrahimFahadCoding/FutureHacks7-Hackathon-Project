import streamlit as st
from utils.db import get_user_tasks, save_user_tasks
import time

st.title("🗂️ Mind Tasks")
col1, col2, col3 = st.columns([5, 2, 2])
username = st.session_state.get("username", "guest")
st.session_state.tasks = get_user_tasks(username)

# Color dictionary with square representation
priority_dict = {
    "High": '<span style="display:inline-block; width:20px; height:20px; background-color:red; border-radius:50%;"></span>',
    "Medium": '<span style="display:inline-block; width:20px; height:20px; background-color:orange; border-radius:50%;"></span>',
    "Low": '<span style="display:inline-block; width:20px; height:20px; background-color:green; border-radius:50%;"></span>',
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
st.subheader("Pending Tasks")
if pending_tasks:
    for i, task in enumerate(pending_tasks):
        with col1:
            text = f'{priority_dict[task["priority"]]} <span style="font-size: 25px;"> {task["task"]}</span>'
            st.markdown(text, unsafe_allow_html=True)

        with col2:
            if st.button("✅", key=f"done_{i}"):
                task["done"] = True
                st.success("Good Job! Task Completed!")
                save_user_tasks(username, st.session_state.tasks)
                time.sleep(1)
                st.rerun()

        with col3:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.tasks.remove(task)
                save_user_tasks(username, st.session_state.tasks)
                st.rerun()
else:
    st.info("No pending tasks.")

# Display Completed Tasks
st.subheader("Completed Tasks")
if completed_tasks:
    for i, task in enumerate(completed_tasks):
        with col1:
            text = f'{priority_dict[task["priority"]]} <span style="font-size: 25px; text-decoration:line-through;"> {task["task"]}</span>'
            st.markdown(text, unsafe_allow_html=True)

        with col2:
            if st.button("❌ Undo", key=f"undo_{i}"):
                task["done"] = False
                st.success("Task has been marked as pending!")
                save_user_tasks(username, st.session_state.tasks)
                time.sleep(1)
                st.rerun()

        with col3:
            if st.button("🗑️", key=f"del_completed_{i}"):
                st.session_state.tasks.remove(task)
                save_user_tasks(username, st.session_state.tasks)
                st.rerun()
else:
    st.info("No completed tasks.")
