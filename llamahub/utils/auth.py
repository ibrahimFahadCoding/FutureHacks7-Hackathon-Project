import json
import os

user_db = "data/users.json"

#Load Users
def load_users():
    if not os.path.exists(user_db):
        return {}
    with open(user_db, 'r') as f:
        return json.load(f)

#Save Users
def save_users(users):
    with open(user_db, 'w') as f:
        json.dump(users, f, indent=4)

#Create User
def create_user(username, password):
    users = load_users()
    if username in users:
        return False

    users[username] = password
    save_users(users)
    return True

#Authenticate User
def authenticate(username, password):
    users = load_users()
    if username in users and users[username] == password:
        return True
    return False
