from typing import List, Dict, Any
import os
import sys
import json
import yaml
import logging
import streamlit as st
from psycopg2 import connect
from streamlit_option_menu import option_menu
from utils import create_tables, configure_litellm, fetch_personas_from_db, get_current_task
from settings import page3
from advanced_menu import page2
from homepage import page1, chat_interaction
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST

# Set environment variables with defaults if not already set
os.environ['LITELLM_MODEL'] = os.environ.get('LITELLM_MODEL', 'gpt-4o')
os.environ['LITELLM_PROVIDER'] = os.environ.get('LITELLM_PROVIDER', 'openai') 

# Configure logging at the beginning of the script
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configure the LLM model once at module level
MODEL = configure_litellm()

# Define the pages
def autochat(personas: List[Dict[str, Any]], num_users: int, num_exchanges: int = 10, sleep_duration: float = 1.0) -> None:
    """
    Simulates a chat between the personas using the LLM.

    Args:
        personas (List[Dict[str, Any]]): The list of personas.
        num_users (int): Number of users in the conversation.
        num_exchanges (int, optional): Number of chat exchanges to simulate. Defaults to 10.
        sleep_duration (float, optional): Duration to sleep between responses in seconds. Defaults to 1.0.

    Raises:
        ValueError: If sleep_duration is negative.
    """
    if sleep_duration < 0:
        raise ValueError('sleep_duration must be non-negative')

    for i in range(num_exchanges):  # Simulate exchanges
        for _ in range(num_users):
            persona = random.choice(personas)
            emotional_tone = persona.get('emotional_tone', 'neutral')
            prompt = f"{persona['name']} ({emotional_tone}): {persona['goals']}"
            response = litellm.completion(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            message = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "system", "content": f"{persona['name']}: {message}"})
            
            # Update UI dynamically by appending messages directly
            with st.chat_message("system"):
                st.markdown(f"{persona['name']}: {message}")
            
            time.sleep(sleep_duration)  # Sleep for the specified duration between responses

# Function to get the current task and initialize the prompt if not already set
def main():
    with st.sidebar:
        page = option_menu(
            "Navigation",
            ["Home", "Advanced Menu", "Settings", "Chat Interaction"],
            icons=["house", "gear", "tools", "chat"],
            menu_icon="cast",
            default_index=0,
        )

    if page == "Home":
        page1()  # This is line 54 where page1 is called
    elif page == "Advanced Menu":
        page2()
    elif page == "Settings":
        page3()
    elif page == "Chat Interaction":
        chat_interaction(MODEL)

if __name__ == "__main__":
    create_tables()
    main()
