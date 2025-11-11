import chainlit as cl
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_users_from_env():
    """Load users from ALLOWED_USERS environment variable"""
    users = {}
    allowed_users = os.getenv("ALLOWED_USERS", "")
    
    # Parse the format: "username:password;username2:password2"
    user_pairs = allowed_users.split(";")
    for pair in user_pairs:
        if ":" in pair:
            username, password = pair.split(":", 1)  # Split only on first colon
            users[username.strip()] = password.strip()
        else:
            print(f"Warning: Invalid user format '{pair}'. Expected 'username:password'")
    
    print(f"Loaded {len(users)} users from environment variable")
    return users

# Load users from environment variable
USERS = load_users_from_env()

# Simple password authentication
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if username in USERS and USERS[username] == password:
        return cl.User(
            identifier=username,
            metadata={"role": "admin" if username == "admin" else "user"}
        )
    return None

@cl.on_chat_start
async def start():
    user = cl.user_session.get("user")
    await cl.Message(f"Welcome {user.identifier}! You are now authenticated.").send()

@cl.on_message
async def main(message: cl.Message):
    user = cl.user_session.get("user")
    role = user.metadata.get("role", "user")
    await cl.Message(f"Hello {user.identifier} ({role}), you said: {message.content}").send()