import streamlit as st
from mistralai import Mistral

#Page Config with Together API Setup
st.set_page_config(page_title="Nerd Bot", layout="centered", page_icon="💬")
st.title("💬 Nerd Bot")

mistral = Mistral(api_key="CxXUpnz9TPqQvH2yDayDDNb97yH4BVbt")

#Initialize Chat History
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": """You are a helpful, friendly AI whos job is to answer questions about anything. 
        Feel free to add in a tiny bit humor. But don't be cringey. Also your name is Nerd!"""}
    ]

for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🙂"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🤓"):
            st.markdown(msg["content"])

#Chat Input
user_input = st.chat_input("Ask me anything...")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🙂"):
        st.markdown(user_input)

    #Generate AI Response
    with st.chat_message("assistant", avatar="🤓"):
        with st.spinner("Thinking..."):
            try:
                response = mistral.chat.complete(
                    model="mistral-large-latest",
                    messages=st.session_state.chat_history,
                    temperature=0.7
                ).choices[0].message.content
            except Exception as e:
                response = f"Error: {e}"
        st.markdown(response)

    st.session_state.chat_history.append({"role": "assistant", "content": response})