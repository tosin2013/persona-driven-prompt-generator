import logging
from psycopg2 import connect
from psycopg2.extras import Json

# Database connection details
DB_NAME = "persona_db"
DB_USER = "persona_user"
DB_PASSWORD = "secure_password"
DB_HOST = "127.0.0.1"  # Ensure this is correct

def create_tables() -> None:
    """Create necessary tables in the database."""
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

def store_memory_in_pgvector(task: str, goals: str, personas: List[Dict[str, Any]], embedding: List[float], reference_urls: List[str]) -> None:
    """Store task memory in the database."""
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

def find_similar_tasks(query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
    """Find similar tasks based on embeddings."""
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task, goals, personas, embedding <=> %s AS similarity
        FROM task_memory
        ORDER BY similarity
        LIMIT %s;
    """, (query_embedding, limit))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return [
        {"task": row[0], "goals": row[1], "personas": row[2], "similarity": row[3]}
        for row in results
    ]

def store_conversation_history(messages: List[Dict[str, str]]) -> None:
    """Store conversation history in the database."""
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversation_history (messages)
        VALUES (%s);
    """, (Json(messages),))
    conn.commit()
    cursor.close()
    conn.close()

def retrieve_conversation_history() -> List[Dict[str, str]]:
    """Retrieve conversation history from the database."""
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("SELECT messages FROM conversation_history ORDER BY id DESC LIMIT 1;")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else []

def upload_urls_to_vector_db(personas: List[Dict[str, Any]]) -> None:
    """Upload URLs associated with personas to the vector database."""
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    for persona in personas:
        for url in persona.get("reference_urls", []):
            embedding = generate_embedding(url)  # Generate embedding for the URL
            cursor.execute("""
                INSERT INTO url_memory (persona_name, url, embedding)
                VALUES (%s, %s, %s);
            """, (persona["name"], url, embedding))
    conn.commit()
    cursor.close()
    conn.close()
