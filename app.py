import chainlit as cl
    
@cl.on_message
async def main(message: cl.Message):
    await cl.Message(f"You said: {message.content}").send()