import os
import json
import yaml
import logging
import re
from typing import List, Dict, Any
from psycopg2 import connect
from psycopg2.extras import Json
import litellm
import streamlit as st


# Database connection details
DB_NAME = "persona_db"
DB_USER = "persona_user"
DB_PASSWORD = "secure_password"
DB_HOST = "127.0.0.1"  # Ensure this is correct

def create_tables() -> None:
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_memory (
            id SERIAL PRIMARY KEY,
            task TEXT,
            goals TEXT,
            personas JSONB,
            embedding VECTOR,
            reference_urls TEXT[]
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS url_memory (
            id SERIAL PRIMARY KEY,
            persona_name TEXT,
            url TEXT,
            embedding VECTOR
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id SERIAL PRIMARY KEY,
            messages JSONB
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

def fetch_personas_from_db() -> List[Dict[str, Any]]:
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("SELECT personas FROM task_memory ORDER BY id DESC LIMIT 1;")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else []

def store_memory_in_pgvector(task: str, goals: str, personas: List[Dict[str, Any]], embedding: List[float], reference_urls: List[str]) -> None:
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO task_memory (task, goals, personas, embedding, reference_urls)
        VALUES (%s, %s, %s, %s, %s);
    """, (task, goals, Json(personas), embedding, reference_urls))
    conn.commit()
    cursor.close()
    conn.close()

def get_current_task() -> Dict[str, Any]:
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("SELECT task, goals, personas FROM task_memory ORDER BY id DESC LIMIT 1;")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return {"task": result[0], "goals": result[1], "personas": result[2]}
    else:
        return {"error": "No tasks found."}

def configure_litellm() -> str:
    """Configure LiteLLM with the first valid model configuration found.
    
    Checks multiple provider configurations and uses the first valid one found.
    A valid configuration must have both the model name and corresponding API key set.
    
    Returns:
        str: The configured model name
    
    Raises:
        ValueError: If no valid configuration is found
    """
    providers = {
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "huggingface": "HUGGINGFACE_API_KEY",
        "ollama": "OLLAMA_API_KEY",
        "mistral": "MISTRAL_API_KEY"
    }
    
    model = os.getenv("LITELLM_MODEL")
    provider = os.getenv("LITELLM_PROVIDER")
    
    # If specific provider is set, try that first
    if model and provider:
        api_key_var = providers.get(provider.lower())
        if api_key_var:
            api_key = os.getenv(api_key_var)
            if api_key and api_key.strip():
                litellm.api_key = api_key
                logging.debug(f"Using configured provider: {provider} with model: {model}")
                return model
    
    # Try each provider in turn
    for provider, api_key_var in providers.items():
        api_key = os.getenv(api_key_var)
        if api_key and api_key.strip():
            # Set default model for provider if none specified
            if not model:
                model = {
                    "openai": "gpt-3.5-turbo",
                    "groq": "groq/mixtral-8x7b-32768",
                    "deepseek": "deepseek-coder",
                    "huggingface": "huggingface/mistral-7b",
                    "ollama": "ollama/llama2",
                    "mistral": "mistral-medium"
                }.get(provider)
            
            litellm.api_key = api_key
            os.environ["LITELLM_MODEL"] = model
            os.environ["LITELLM_PROVIDER"] = provider
            logging.debug(f"Using available provider: {provider} with model: {model}")
            return model
    
    raise ValueError("No valid LiteLLM configuration found. Please set LITELLM_MODEL, LITELLM_PROVIDER, and corresponding API key in environment variables.")

def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding for the given text.

    Args:
        text (str): The text to generate an embedding for.

    Returns:
        List[float]: The generated embedding.
    """
    # Placeholder function for generating embeddings
    # Replace with actual embedding generation logic
    return [0.0] * 768  # Example embedding

def get_user_input() -> Dict[str, Any]:
    """
    Collect user input for the task, goals, and reference URLs.

    Returns:
        Dict[str, Any]: A dictionary containing the task description, goals, and reference URLs.
    """
    st.sidebar.title("Persona-Driven Prompt Generator")
    task = st.sidebar.text_area("Please describe the task or problem domain:", height=150, key="task_input")
    goals = st.sidebar.text_input("What are the key goals for this task? (e.g., efficiency, creativity):", key="goals_input")
    reference_urls = st.sidebar.text_area("Optional: Provide URLs for reference (one per line):", key="urls_input")
    reference_urls_list = [url.strip() for url in reference_urls.split('\n') if url.strip()]
    
    # Return empty strings if the values are None (this can happen during testing)
    return {
        "task": task if task is not None else "",
        "goals": goals if goals is not None else "",
        "reference_urls": reference_urls_list
    }
