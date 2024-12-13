import streamlit as st
import json
from typing import Dict, Any

def page1():
    st.title("Persona-Driven Prompt Generator")
    st.markdown("""
        <style>
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    # Function to display the generated prompt in a dialog
    def display_prompt(prompt: Dict[str, Any]) -> None:
        st.markdown("### Generated Prompt")
        st.markdown(f"**Task:** {prompt['task']}")
        st.markdown(f"**Personas:** {', '.join(prompt['personas'])}")
        
        # Format knowledge sources with titles and URLs
        knowledge_sources_formatted = "\n".join([
            f"- [{source['title']}]({source['url']})"
            for source in prompt['knowledge_sources']
        ])
        st.markdown(f"**Knowledge Sources:**\n{knowledge_sources_formatted}")
        
        st.markdown(f"**Conflict Resolution:** {prompt['conflict_resolution']}")
        st.markdown(f"**Instructions:** {prompt['instructions']}")

        if st.button("Copy to Clipboard"):
            st.code(json.dumps(prompt, indent=4), language='json')
            st.success("Copied to clipboard!")

        # Allow user to select file format and save the prompt
        file_format = st.selectbox("Choose file format to download:", ["json", "yaml"])
        save_prompt_to_file(prompt, file_format)

        if st.button("Close"):
            st.session_state.show_modal = False
            st.experimental_rerun()
