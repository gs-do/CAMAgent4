import chainlit as cl
import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

# Load environment variables from .env file
load_dotenv()

project_endpoint = os.getenv("AIPROJECT_ENDPOINT")
agent_id = os.getenv("AGENT_ID")

def get_azure_credential():
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        print("Using ManagedIdentityCredential for production environment")
        # You can specify a specific managed identity client ID if needed
        managed_identity_client_id = os.getenv("MANAGED_IDENTITY_CLIENT_ID")
        if managed_identity_client_id:
            return ManagedIdentityCredential(client_id=managed_identity_client_id)
        else:
            return ManagedIdentityCredential()
    else:
        print("Using DefaultAzureCredential for local development")
        return DefaultAzureCredential()

# Create AIProjectClient with environment-based credential
credential = get_azure_credential()
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=credential,
)

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
async def on_chat_start():
    # Create a thread for the agent
    if not cl.user_session.get("thread_id"):
        thread = project_client.agents.threads.create()

        cl.user_session.set("thread_id", thread.id)
        print(f"New Thread ID: {thread.id}")

@cl.on_message
async def on_message(message: cl.Message):
    thread_id = cl.user_session.get("thread_id")
    
    try:
        # Show thinking message to user
        msg = await cl.Message("thinking...", author="agent").send()

        project_client.agents.messages.create(
            thread_id=thread_id,
            role="user",
            content=message.content,
        )
        
        # Run the agent to process tne message in the thread
        run = project_client.agents.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)
        print(f"Run finished with status: {run.status}")

        # Check if you got "Rate limit is exceeded.", then you want to increase the token limit
        if run.status == "failed":
            raise Exception(run.last_error)

        response_text = "No response from agent"  # Default value
        if run.status == "failed":
            response_text = f"Run failed: {run.last_error}"
        else:
            messages = project_client.agents.messages.list(thread_id=thread_id)
            for msg1 in messages:
                if msg1.text_messages:
                    last_text = msg1.text_messages[-1]
                    if str(msg1.role).lower() == "messagerole.agent":
                        response_text = last_text.text.value
                        break
    
        msg.content = response_text
        await msg.update()

    except Exception as e:
        await cl.Message(content=f"Error: {str(e)}").send()