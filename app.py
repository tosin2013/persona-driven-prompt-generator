import streamlit as st
from llm_interaction import generate_autogen_workflow, download_autogen_workflow

def main():
    st.title("Custom Prompt Generator")
    personas = [
        {"name": "User Proxy Agent", "type": "User Proxy Agent", "configuration": {"executes_code": True}},
        {"name": "Assistant Agent", "type": "Assistant Agent", "configuration": {"plans_and_generates_code": True}},
        {"name": "GroupChat", "type": "GroupChat", "configuration": {"manages_group_chat": True}}
    ]
    workflow_code = generate_autogen_workflow(personas)
    download_autogen_workflow(workflow_code)

if __name__ == "__main__":
    main()
