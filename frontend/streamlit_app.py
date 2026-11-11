"""Streamlit chat client for the CanFinRAG API."""

import os

import requests
import streamlit as st


st.set_page_config(page_title="CanFinRAG", page_icon="📚")
st.title("CanFinRAG")
st.caption("Answers are grounded in the indexed documents and include source pages.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask a question about the financial documents")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    try:
        response = requests.post(
            f"{os.getenv('CANFINRAG_API_URL', 'http://localhost:8000')}/query",
            json={"question": question},
            timeout=180,
        )
        response.raise_for_status()
        result = response.json()
        answer = result["answer"]
        citations = "\n\nSources:\n" + "\n".join(
            f"- {item['document']}, page {item['page']}" for item in result["citations"]
        )
    except requests.RequestException as error:
        answer = f"API request failed: {error}"
        citations = ""
    with st.chat_message("assistant"):
        st.markdown(answer + citations)
    st.session_state.messages.append(
        {"role": "assistant", "content": answer + citations}
    )
