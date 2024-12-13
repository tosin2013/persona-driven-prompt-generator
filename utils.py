import os
import json
import yaml
import logging
import re
from typing import List, Dict, Any
from psycopg2 import connect
from psycopg2.extras import Json
import litellm


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
    model = os.getenv("LITELLM_MODEL")
    provider = os.getenv("LITELLM_PROVIDER")
    if not model or not provider:
        raise ValueError("LITELLM_MODEL and LITELLM_PROVIDER environment variables must be set")
    logging.debug(f"Configuring LiteLLM with model='{model}', provider='{provider}'")
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key.strip() == "":
            raise ValueError("OPENAI_API_KEY environment variable not set or empty")
        litellm.api_key = api_key
    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key.strip() == "":
            raise ValueError("GROQ_API_KEY environment variable not set or empty")
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key or api_key.strip() == "":
            raise ValueError("DEEPSEEK_API_KEY environment variable not set or empty")
        litellm.api_key = api_key
    elif provider == "huggingface":
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key or api_key.strip() == "":
            raise ValueError("HUGGINGFACE_API_KEY environment variable not set or empty")
        litellm.api_key = api_key
    elif provider == "ollama":
        api_key = os.getenv("OLLAMA_API_KEY")
        if not api_key or api_key.strip() == "":
            raise ValueError("OLLAMA_API_KEY environment variable not set or empty")
        litellm.api_key = api_key
    elif provider == "mistral":
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key or api_key.strip() == "":
            raise ValueError("MISTRAL_API_KEY environment variable not set or empty")
        litellm.api_key = api_key
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    return model

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
