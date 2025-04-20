import json
import os

summary_db = "data/summaries.json"
tasks_db = "data/tasks.json"

os.makedirs(os.path.dirname(tasks_db), exist_ok=True)

#Load Summaries
def load_summaries():
    if not os.path.exists(summary_db):
        return {}
    with open(summary_db, 'r') as f:
        return json.load(f)

#Save Summaries
def save_summaries(data):
    with open(summary_db, 'w') as f:
        json.dump(data, f, indent=4)

#Save New Summary
def save_summary(username, title, summary):
    summaries = load_summaries()
    if username not in summaries:
        summaries[username] = []
    summaries[username].append({
        "title": title,
        "summary": summary
    })
    save_summaries(summaries)

#Get User Summaries
def get_user_summaries(username):
    summaries = load_summaries()
    return summaries.get(username, [])

#Load Tasks
def load_tasks():
    if os.path.exists(tasks_db):
        with open(tasks_db, 'r') as f:
            return json.load(f)

    return []

def save_tasks(tasks):
    with open(tasks_db, 'w') as f:
        json.dump(tasks, f, indent=2)

def get_user_tasks(username):
    tasks = load_tasks()
    return tasks.get(username, [])

def save_user_tasks(username, tasks):
    all_tasks = load_tasks()
    all_tasks[username] = tasks
    save_tasks(all_tasks)
