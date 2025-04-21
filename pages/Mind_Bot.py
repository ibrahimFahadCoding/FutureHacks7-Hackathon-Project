import streamlit as st
from together import Together

#Page Config with Together API Setup
st.set_page_config(page_title="Mind Bot", layout="centered")
st.title("💬 Mind Chatbot")

together_client = Together(api_key="5bd126d37c96a0f67f1e75a0ae0f8f959fcee795b32df2fedd56547e5127b7dd")

#Initialize Chat History
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": """You are a helpful, friendly AI whos job is to answer questions about anything. 
        Feel free to add in a little humor. Explain concepts and provide examples in math, science, and 
        coding problems."""}
    ]

for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🙂"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(msg["content"])

#Chat Input
user_input = st.chat_input("Ask me anything...")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🙂"):
        st.markdown(user_input)

    #Generate AI Response
    with st.chat_message("assistant", avatar="🧠"):
        with st.spinner("Thinking..."):
            try:
                response = together_client.chat.completions.create(
                    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                    messages=st.session_state.chat_history,
                    temperature=0.7
                ).choices[0].message.content
            except Exception as e:
                response = f"Error: {e}"
        st.markdown(response)

    st.session_state.chat_history.append({"role": "assistant", "content": response})