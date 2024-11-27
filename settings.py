import streamlit as st
from utils import clear_database
import litellm

def page3():
    st.title("Settings")
    
    # Add a 'Clear' button in the settings page
    if st.button("Clear Data and Context"):
        # Clear session state
        st.session_state.clear()
        # Clear the database
        clear_database()
        st.success("Application context and database have been cleared.")

    # Add a 'Clear LLM Context' button in the settings page
    if st.button("Clear LLM Context"):
        # Clear the session state related to LLM prompts and messages
        st.session_state.prompt = None
        st.session_state.messages = []
        st.session_state.chat_log = []
        
        st.success("LLM context has been cleared.")
    
    # Add a button to download all content as markdown
    if st.button("Download All Content as Markdown"):
        content = []
        
        # Add initial conversations
        if "prompt" in st.session_state:
            content.append("### Initial Conversations\n")
            initial_conversations = st.session_state.get("initial_conversations", [])
            for conversation in initial_conversations:
                content.append(conversation)
        
        # Add chat history
        if "messages" in st.session_state:
            content.append("### Chat History\n")
            for message in st.session_state.messages:
                content.append(f"{message['role']}: {message['content']}")
        
        # Combine content into a single markdown string
        markdown_content = "\n\n".join(content)
        
        # Provide a download button
        st.download_button(
            label="Download Markdown",
            data=markdown_content,
            file_name="all_content.md",
            mime="text/markdown"
        )