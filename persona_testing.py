import json
import yaml
import requests
from pathlib import Path
import os
import sys
import litellm
import logging
import streamlit as st
import re
from typing import List, Dict, Any
from psycopg2 import connect
from psycopg2.extras import Json
import subprocess
from advanced_menu import page2
from settings import page3
from utils import clear_database
import time
import random

# Configure logging at the beginning of the script
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Database connection details
DB_NAME = "persona_db"
DB_USER = "persona_user"
DB_PASSWORD = "secure_password"
DB_HOST = "127.0.0.1"  # Ensure this is correct

# Remove the advanced_mode checkbox
# advanced_mode = st.sidebar.checkbox("Enable Advanced Settings", value=False)

# Add a new function to create necessary tables
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

def configure_litellm() -> str:
    """Configure LiteLLM based on environment variables."""
    model = os.getenv("LITELLM_MODEL")
    provider = os.getenv("LITELLM_PROVIDER")

    if not model or not provider:
        raise ValueError("LITELLM_MODEL and LITELLM_PROVIDER environment variables must be set")

    logging.debug(f"Configuring LiteLLM with model='{model}', provider='{provider}'")

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        litellm.OpenAIConfig(api_key=api_key)
    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        # No specific configuration class for Groq; ensure the API key is set as an environment variable
    elif provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")
        # Set the API key directly for Deepseek
        litellm.api_key = api_key
    elif provider == "huggingface":
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError("HUGGINGFACE_API_KEY environment variable not set")
        litellm.HuggingfaceConfig(api_key=api_key)
    elif provider == "ollama":
        api_key = os.getenv("OLLAMA_API_KEY")
        if not api_key:
            raise ValueError("OLLAMA_API_KEY environment variable not set")
        # Set the API key directly for OLLAMA
        litellm.api_key = api_key
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return model

# Define the pages
def autochat(personas: List[Dict[str, Any]], num_users: int) -> None:
    """
    Simulates a chat between the personas using the LLM.

    Args:
        personas (List[Dict[str, Any]]): The list of personas.
        num_users (int): Number of users in the conversation.
    """
    model = configure_litellm()

    for i in range(10):  # Simulate 10 exchanges
        for _ in range(num_users):
            persona = random.choice(personas)
            emotional_tone = persona.get('emotional_tone', 'neutral')
            prompt = f"{persona['name']} ({emotional_tone}): {persona['goals']}"
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            message = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "system", "content": f"{persona['name']}: {message}"})
            
            # Update UI dynamically by appending messages directly
            with st.chat_message("system"):
                st.markdown(f"{persona['name']}: {message}")
            
            time.sleep(1)  # Sleep for 1 second between responses

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

# Function to get the current task and initialize the prompt if not already set
def get_current_task() -> Dict[str, Any]:
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST  # Add host parameter
    )
    cursor = conn.cursor()  # Create cursor after connection

    # Get the most recent task
    cursor.execute("SELECT task, goals, personas FROM task_memory ORDER BY id DESC LIMIT 1;")
    result = cursor.fetchone()

    cursor.close()  # Close the cursor
    conn.close()

    if result:
        task_details = {"task": result[0], "goals": result[1], "personas": result[2]}
        if st.session_state.prompt is None:
            # Initialize the prompt if not already set
            st.session_state.prompt = generate_prompt(task_details, task_details["personas"], [], "", [])
            st.session_state.prompt["model"] = os.getenv("LITELLM_MODEL")
        return task_details
    else:
        return {"error": "No tasks found."}

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

    # Step 1: Collect User Input
    def get_user_input() -> Dict[str, Any]:
        st.sidebar.title("Persona-Driven Prompt Generator")
        task = st.sidebar.text_area("Please describe the task or problem domain:", height=150)
        goals = st.sidebar.text_input("What are the key goals for this task? (e.g., efficiency, creativity):")
        reference_urls = st.sidebar.text_area("Optional: Provide URLs for reference (one per line):")
        reference_urls_list = [url.strip() for url in reference_urls.split('\n') if url.strip()]
        logging.debug(f"User input received: task='{task}', goals='{goals}', reference_urls='{reference_urls_list}'")
        return {"task": task, "goals": goals, "reference_urls": reference_urls_list}

    # Function to create a ShellGPT role
    def create_shellgpt_role(role_name: str, persona: Dict[str, Any]) -> None:
        description = (
            f"Role for persona {persona['name']}.\n"
            f"Background: {persona['background']}\n"
            f"Goals: {persona['goals']}\n"
            f"Beliefs: {persona['beliefs']}\n"
            f"Knowledge: {persona['knowledge']}\n"
            f"Communication Style: {persona['communication_style']}\n"
            "APPLY MARKDOWN"
        )
        try:
            result = subprocess.run(
                ["sgpt", "--create-role", role_name],
                input=description,
                text=True,
                capture_output=True,
                check=True
            )
            if "already exists" in result.stderr:
                overwrite = input(f"Role '{role_name}' already exists, overwrite it? [y/N]: ")
                if overwrite.lower() == 'y':
                    subprocess.run(
                        ["sgpt", "--create-role", role_name, "--overwrite"],
                        input=description,
                        text=True,
                        check=True
                    )
                    logging.info(f"ShellGPT role '{role_name}' overwritten successfully.")
                else:
                    logging.info(f"Aborted overwriting ShellGPT role '{role_name}'.")
            else:
                logging.info(f"ShellGPT role '{role_name}' created successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to create ShellGPT role '{role_name}': {e.stderr.strip()}")
        except Exception as e:
            logging.error(f"Unexpected error occurred while creating ShellGPT role '{role_name}': {e}")

    # Function to delete a ShellGPT role by removing the role file
    def delete_shellgpt_role(role_name: str) -> None:
        role_file_path = Path.home() / ".config" / "shell_gpt" / "roles" / f"{role_name}.json"
        try:
            if role_file_path.exists():
                role_file_path.unlink()
                logging.info(f"ShellGPT role '{role_name}' deleted successfully.")
            else:
                logging.warning(f"ShellGPT role '{role_name}' does not exist.")
        except Exception as e:
            logging.error(f"Unexpected error occurred while deleting ShellGPT role '{role_name}': {e}")

    # Function to generate a ShellGPT role for each persona
    def generate_shellgpt_roles(personas: List[Dict[str, Any]]) -> None:
        roles_dir = Path.home() / ".config" / "shell_gpt" / "roles"
        existing_roles = [role.stem for role in roles_dir.glob("*.json")]

        persona_role_names = [persona["name"].replace(" ", "_").lower() for persona in personas]

        # Delete roles that do not match current personas
        for role in existing_roles:
            if role not in persona_role_names:
                delete_shellgpt_role(role)

        # Create or update roles for current personas
        for persona in personas:
            role_name = persona["name"].replace(" ", "_").lower()
            create_shellgpt_role(role_name, persona)

    # Step 2: Generate Personas
    def generate_personas(task_details: Dict[str, Any], persona_count: int = 2) -> List[Dict[str, Any]]:
        print("\nGenerating personas dynamically...")
        task = task_details["task"]
        reference_urls = task_details.get("reference_urls", [])

        model = configure_litellm()

        logging.debug(f"Generating {persona_count} personas for task: {task} with reference URLs: {reference_urls}")

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an observer tasked with analyzing and managing interactions between multiple personas. "
                        "Your goal is to ensure the task is addressed effectively by balancing the perspectives of the personas. "
                        "As an observer, you must maintain a memory of the personas' attributes and prior decisions. "
                        "You will be provided with a task and asked to generate personas in JSON format ONLY, without any additional text or explanations. "
                        "Each persona should include the following fields: name, background, goals, beliefs, knowledge, and communication_style."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Task: {task}. Generate {persona_count} personas with diverse perspectives. "
                        "Return the personas as a JSON array ONLY, without any additional text or explanations."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "As the observer, track the following memory state:\n"
                        "- Personas and their attributes\n"
                        "- Task goals\n"
                        "- Prior decisions\n"
                        "Ensure that each generated output reflects and updates the memory state."
                    )
                }
            ]

            if reference_urls:
                for url in reference_urls:
                    messages.append({
                        "role": "user",
                        "content": f"Please take into account the information from the following URL: {url}"
                    })

            response = litellm.completion(
                model=model,
                messages=messages,
                temperature=0.7
            )
            personas_content = response.choices[0].message.content.strip()
            logging.debug(f"Personas content received: {personas_content}")

            if not personas_content:
                raise ValueError("Received empty response from LiteLLM")

            # Extract JSON array from the response
            json_match = re.search(r'(\[.*\])', personas_content, re.DOTALL)
            if json_match:
                personas_json = json.loads(json_match.group(1))
                logging.debug(f"Parsed personas JSON: {personas_json}")
            else:
                raise ValueError("Could not find valid JSON array in response")

            print(f"\nGenerated Personas:\n{personas_json}")
            return personas_json
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            logging.error(f"JSON parsing error: {e}")
            return []
        except Exception as e:
            print(f"Error generating personas: {e}")
            logging.error(f"Error generating personas: {e}")
            return []

    # Step 3: Generate Knowledge Sources via API
    def fetch_knowledge_sources(task: str) -> List[Dict[str, str]]:
        print("\nGenerating knowledge sources dynamically...")

        model = configure_litellm()

        logging.debug(f"Fetching knowledge sources for task: {task}")

        try:
            response = litellm.completion(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You will be provided with a task. "
                            "Generate a list of knowledge sources in JSON format ONLY, without any additional text or explanations. "
                            "Each knowledge source should include the following fields: title, description, and url."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Task: {task}. Generate a list of knowledge sources relevant to this task. "
                            "Return the knowledge sources as a JSON array ONLY, without any additional text or explanations."
                        )
                    }
                ],
                temperature=0.7
            )
            knowledge_sources_content = response.choices[0].message.content.strip()
            if not knowledge_sources_content:
                raise ValueError("Received empty response from LiteLLM")
            logging.debug(f"Knowledge sources content received: {knowledge_sources_content}")

            # Extract JSON array from the response
            json_match = re.search(r'(\[.*\])', knowledge_sources_content, re.DOTALL)
            if json_match:
                knowledge_sources_json = json.loads(json_match.group(1))
            else:
                raise ValueError("Could not find valid JSON array in response")

            print("Knowledge sources generated:")
            print(json.dumps(knowledge_sources_json, indent=4))

            # Print any URLs found in the knowledge sources
            for source in knowledge_sources_json:
                if "url" in source:
                    print(f"URL: {source['url']}")

            return knowledge_sources_json
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            logging.error(f"JSON parsing error: {e}")
            return []
        except Exception as e:
            print(f"Error generating knowledge sources: {e}")
            logging.error(f"Error generating knowledge sources: {e}")
            return []

    # Step 4: Resolve Persona Conflicts
    def resolve_conflicts(personas_text: str, task_details: Dict[str, str]) -> str:
        print("\nResolving conflicts among personas...")
        task = task_details["task"]

        model = configure_litellm()

        logging.debug("Resolving conflicts among personas")

        try:
            response = litellm.completion(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Resolve conflicts between personas by prioritizing fairness, knowledge, and relevance to task goals."
                    },
                    {
                        "role": "user",
                        "content": f"Task: {task}\n\nPersonas:\n{personas_text}\n\nIdentify conflicts and propose resolutions."
                    }
                ],
                temperature=0.7
            )
            conflict_resolution = response.choices[0].message.content.strip()
            if not conflict_resolution:
                raise ValueError("Received empty response from LiteLLM")
            logging.debug(f"Conflict resolution received: {conflict_resolution}")
            print(f"\nConflict Resolution:\n{conflict_resolution}")
            return conflict_resolution
        except Exception as e:
            print(f"Error resolving conflicts: {e}")
            logging.error(f"Error resolving conflicts: {e}")
            # Prompt user for manual conflict resolution
            print("Unable to resolve conflicts automatically. Please provide guidance.")
            user_input = input("Enter your conflict resolution strategy: ")
            return user_input

    # Step 5: Generate the Prompt
    def generate_prompt(task_details: Dict[str, str], personas: List[Dict[str, Any]], knowledge_sources: List[Dict[str, str]], conflict_strategy: str, prior_decisions: List[str]) -> Dict[str, Any]:
        # Construct the memory section
        memory_personas = "\n".join([
            f"- {persona['name']}:\n"
            f"    - Background: {persona['background']}\n"
            f"    - Goals: {persona['goals']}\n"
            f"    - Beliefs: {persona['beliefs']}\n"
            f"    - Knowledge: {persona['knowledge']}\n"
            f"    - Communication Style: {persona['communication_style']}"
            for persona in personas
        ])
        
        memory_prior_decisions = "\n".join([
            f"- {decision}" for decision in prior_decisions
        ])

        # Construct the prompt
        prompt = {
            "task": task_details["task"],
            "personas": [persona["name"] for persona in personas],
            "knowledge_sources": [
                {"title": source["title"], "url": source["url"]}
                for source in knowledge_sources
            ],
            "conflict_resolution": conflict_strategy,
            "memory": {
                "personas": memory_personas,
                "task_goals": task_details.get("goals", "No specific goals provided."),
                "prior_decisions": memory_prior_decisions
            },
            "instructions": (
                f"### Task ###\n"
                f"{task_details['task']}\n\n"
                f"### Memory: Personas ###\n"
                f"{memory_personas}\n\n"
                f"### Memory: Task Goals ###\n"
                f"{task_details.get('goals', 'No specific goals provided.')}\n\n"
                f"### Memory: Prior Decisions ###\n"
                f"{memory_prior_decisions}\n\n"
                f"### Instructions ###\n"
                f"Generate outputs for the task '{task_details['task']}' by incorporating the perspectives of "
                f"{', '.join([p['name'] for p in personas])}. Use knowledge from "
                f"{', '.join([source['title'] for source in knowledge_sources])}, and resolve conflicts using "
                f"{conflict_strategy}. Update the memory with significant decisions or outputs generated."
            )
        }

        # Print the constructed prompt
        print("\nGenerated Prompt:")
        print(json.dumps(prompt, indent=4))
        
        return prompt

    # Step 6: Save Prompt to File
    def save_prompt_to_file(prompt: Dict[str, Any], file_format: str) -> None:
        if file_format == "yaml":
            file_contents = yaml.dump(prompt, default_flow_style=False, sort_keys=False)
            file_name = "generated_prompt.yaml"
        elif file_format == "json":
            file_contents = json.dumps(prompt, indent=4)
            file_name = "generated_prompt.json"
        else:
            st.error("Invalid file format selected.")
            return

        # Provide a download button
        st.download_button(
            label="Download Prompt",
            data=file_contents,
            file_name=file_name,
            mime="text/plain"
        )

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

    # Function to perform DuckDuckGo search
    def duckduckgo_search(query: str) -> List[Dict[str, Any]]:
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            try:
                data = response.json()
                results = data.get("RelatedTopics", [])
                top_results = results[:5]  # Get top 5 results
                return top_results
            except json.JSONDecodeError as e:
                logging.error(f"JSON decoding error: {e}")
                return []
        else:
            logging.error(f"Failed to fetch data from DuckDuckGo. Status code: {response.status_code}")
            return []

    # Function to generate embeddings
    def generate_embedding(text: str) -> List[float]:
        # Placeholder function for generating embeddings
        # Replace with actual embedding generation logic
        return [0.0] * 768  # Example embedding

    # Function to store memory in pgvector
    def store_memory_in_pgvector(task: str, goals: str, personas: List[Dict[str, Any]], embedding: List[float], reference_urls: List[str]) -> None:
        conn = connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST  # Add host parameter
        )
        cursor = conn.cursor()  # Create cursor after connection

        # Insert task memory into PostgreSQL
        cursor.execute("""
            INSERT INTO task_memory (task, goals, personas, embedding, reference_urls)
            VALUES (%s, %s, %s, %s, %s);
        """, (task, goals, Json(personas), embedding, reference_urls))

        conn.commit()
        cursor.close()  # Close the cursor
        conn.close()

    # Function to get the current task
    def get_current_task() -> Dict[str, Any]:
        conn = connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST  # Add host parameter
        )
        cursor = conn.cursor()  # Create cursor after connection

        # Get the most recent task
        cursor.execute("SELECT task, goals, personas FROM task_memory ORDER BY id DESC LIMIT 1;")
        result = cursor.fetchone()

        cursor.close()  # Close the cursorues
        conn.close()

        if result:
            return {"task": result[0], "goals": result[1], "personas": result[2]}
        else:
            return {"error": "No tasks found."}

    # Function to find similar tasks
    def find_similar_tasks(query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        conn = connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST  # Add host parameter
        )
        cursor = conn.cursor()  # Create cursor after connection

        # Semantic similarity query
        cursor.execute("""
            SELECT task, goals, personas, embedding <=> %s AS similarity
            FROM task_memory
            ORDER BY similarity
            LIMIT %s;
        """, (query_embedding, limit))

        results = cursor.fetchall()

        cursor.close()  # Close the cursor
        conn.close()

        return [
            {"task": row[0], "goals": row[1], "personas": row[2], "similarity": row[3]}
            for row in results
        ]

    def generate_initial_conversation(prompt: Dict[str, Any], conversation_length: int = 10) -> List[Dict[str, str]]:
        """Generate initial conversation between personas about the task."""
        model = configure_litellm()
        
        try:
            response = litellm.completion(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate a natural conversation between the personas discussing "
                            "their approach to the task. The conversation should highlight "
                            "their different perspectives, how they plan to work together, and "
                            "incorporate their knowledge. Limit the conversation to "
                            f"{conversation_length} exchanges."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Task: {prompt['task']}\n"
                            f"Personas: {', '.join(prompt['personas'])}\n"
                            f"Goals: {prompt['memory']['task_goals']}\n"
                            "Generate a conversation between these personas discussing "
                            "their initial thoughts and approach to the task."
                        )
                    }
                ],
                temperature=0.7
            )
            
            conversation = response.choices[0].message.content.strip()
            messages = [{"role": "system", "content": "Initial conversation generated:"}]
            
            # Split conversation into messages and note the persona that was talking
            dialog_lines = conversation.split('\n')
            for line in dialog_lines:
                if line.strip():
                    speaker = line.split(':')[0].strip() if ':' in line else "system"
                    content = line.split(':', 1)[1].strip() if ':' in line else line
                    messages.append({"role": speaker.lower(), "content": content})
            
            # Pass the initial conversation to sgpt
            subprocess.run(
                ["sgpt", "--chat", "conversation_1", conversation],
                text=True,
                check=True
            )
            
            return messages
        except Exception as e:
            logging.error(f"Error generating initial conversation: {e}")
            return [{"role": "system", "content": "Failed to generate initial conversation."}]

    # Function to edit persona tones
    def edit_persona_tones(personas: List[Dict[str, Any]]) -> None:
        st.markdown("### Edit Persona Tones")
        for persona in personas:
            persona_name = persona["name"]
            persona["tone"] = st.text_input(f"Tone for {persona_name}", value=persona.get("tone", "default tone"))

    # Function to save or copy all conversations
    def save_or_copy_conversations(messages: List[Dict[str, str]]) -> None:
        st.markdown("### Save or Copy Conversations")
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        if st.button("Save Conversations"):
            with open("conversations.txt", "w") as file:
                file.write(conversation_text)
            st.success("Conversations saved to conversations.txt")
        
        if st.button("Copy Conversations"):
            st.code(conversation_text)
            st.success("Conversations copied to clipboard")

    # Function to store conversation history
    def store_conversation_history(messages: List[Dict[str, str]]) -> None:
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

    # Function to retrieve conversation history
    def retrieve_conversation_history() -> List[Dict[str, str]]:
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

    # Modify the function to interact with LLM
    def interact_with_llm(prompt: str) -> str:
        # Retrieve conversation history
        history = retrieve_conversation_history()
        
        # Include history in the messages
        messages = history + [{"role": "user", "content": prompt}]
        
        response = litellm.completion(
            model=st.session_state.prompt["model"],
            messages=messages,
            temperature=0.7
        )
        reply = response.choices[0].message['content'].strip()  # Ensure correct access to the message content
        
        # Store the updated conversation history
        messages.append({"role": "system", "content": reply})
        store_conversation_history(messages)
        
        return reply

    # Initialize session state variables
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'show_modal' not in st.session_state:
        st.session_state['show_modal'] = False
    if 'prompt' not in st.session_state:
        st.session_state['prompt'] = None
    if 'autochat_active' not in st.session_state:
        st.session_state['autochat_active'] = False
    if 'chat_log' not in st.session_state:
        st.session_state['chat_log'] = []

    # Define callback functions
    def handle_chat_input():
        prompt = st.session_state['user_input']
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Waiting for response..."):
            if st.session_state.prompt:
                reply = interact_with_llm(prompt)
                st.session_state.messages.append({"role": "system", "content": reply})
            else:
                st.session_state.messages.append({"role": "system", "content": "Prompt is not initialized. Please initialize the prompt first by clicking 'Initialize and Load Prompt for Chat'."})

    # Main Function with API Selection and Persona Tuner
    from litellm import completion

    def submit_prompt_to_llm(prompt: str, api_key: str = None, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """
        Submit a formatted prompt to LiteLLM and return the response.

        Args:
            prompt (str): The formatted prompt to send to LiteLLM.
            api_key (str): Optional API key for accessing the LLM. Can also use default in LiteLLM config.
            temperature (float): Sampling temperature to control randomness.
            max_tokens (int): Maximum number of tokens to include in the response.

        Returns:
            str: The response generated by the LLM.
        """
        model_name = os.getenv("LITELLM_MODEL", "gpt-3.5-turbo")  # Use environment variable or default to "gpt-3.5-turbo"
        
        # If using API keys dynamically
        config = {}
        if api_key:
            config["api_key"] = api_key

        try:
            logging.debug(f"Submitting prompt to LiteLLM with model='{model_name}', temperature={temperature}, max_tokens={max_tokens}")
            logging.debug(f"Prompt: {prompt}")
            # Submit the prompt to LiteLLM
            response = completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **config,
            )
            logging.debug(f"Response: {response}")

            # Extract the content from the response
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            logging.error(f"Error submitting prompt to LiteLLM: {e}")
            return f"An error occurred: {e}"

    def main() -> None:
        logging.debug("Program started")
        create_tables()  # Ensure tables are created
        task_details = get_user_input()
        
        if not task_details["task"] or not task_details["goals"]:
            st.error("Please provide both the task description and goals.")
            return
        
        # Ensure environment variables for LiteLLM are set
        if not os.getenv("LITELLM_MODEL") or not os.getenv("LITELLM_PROVIDER"):
            st.error("Error: LITELLM_MODEL and LITELLM_PROVIDER environment variables must be set.")
            sys.exit("Terminating program due to missing environment variables.")
        
        # Display the current model in use
        st.sidebar.write(f"Current model in use: {os.getenv('LITELLM_MODEL')}")
        
        # Persona Tuner
        persona_count = st.sidebar.slider("How many personas would you like to include?", 1, 20, 2)
        
        if st.sidebar.button("Submit"):
            with st.spinner("Generating personas and prompt..."):
                personas = generate_personas(task_details, persona_count=persona_count)
                
                # Generate ShellGPT roles for each persona
                generate_shellgpt_roles(personas)
                
                # Knowledge Sources
                knowledge_sources = fetch_knowledge_sources(task_details["task"])
                
                # Conflict Resolution
                conflict_strategy = resolve_conflicts(personas, task_details)
                
                # Generate Prompt
                prompt = generate_prompt(task_details, personas, knowledge_sources, conflict_strategy, prior_decisions=[])
                
                # Generate and store prompt
                combined_text = f"Task: {task_details['task']}. Goals: {task_details['goals']}. Personas: {json.dumps(personas)}"
                embedding = generate_embedding(combined_text)  # Function for generating embeddings
                store_memory_in_pgvector(task_details["task"], task_details["goals"], personas, embedding, task_details["reference_urls"])

                # Upload URLs to vector database
                upload_urls_to_vector_db(personas)

                st.success("Task and personas saved!")
                
                # Store the model in the session state
                st.session_state.prompt = prompt
                st.session_state.prompt["model"] = os.getenv("LITELLM_MODEL")
                st.session_state.show_modal = True
                
                # Add generated personas to chat
                st.session_state.messages.append({"role": "system", "content": f"Generated Personas: {json.dumps(personas, indent=4)}"})
                
                # Perform DuckDuckGo search for each persona
                for persona in personas:
                    query = f"{persona['name']} {', '.join([source['title'] for source in knowledge_sources])}"
                    search_results = duckduckgo_search(query)
                    persona["search_results"] = search_results
                    st.table(search_results)
                
                # Update memory with search results
                st.session_state.prompt["memory"]["personas"] = "\n".join([
                    f"- {persona['name']}:\n"
                    f"    - Background: {persona['background']}\n"
                    f"    - Goals: {persona['goals']}\n"
                    f"    - Beliefs: {persona['beliefs']}\n"
                    f"    - Knowledge: {persona['knowledge']}\n"
                    f"    - Communication Style: {persona['communication_style']}\n"
                    f"    - Search Results: {json.dumps(persona['search_results'], indent=4)}"
                    for persona in personas
                ])
            
            # Display status overview
            st.markdown("### Status Overview")
            st.markdown(f"**Task:** {task_details['task']}")
            st.markdown(f"**Goals:** {task_details['goals']}")
            st.markdown(f"**Personas:** {', '.join([persona['name'] for persona in personas])}")
            
            # Recommendations for next steps
            st.markdown("### Recommendations for Next Steps")
            st.markdown("- Review the generated personas and their attributes.")
            st.markdown("- Analyze the knowledge sources and incorporate relevant information.")
            st.markdown("- Use the conflict resolution strategy to address any persona conflicts.")
            st.markdown("- Generate initial conversations to simulate interactions between personas.")
            st.markdown("- Save or copy the generated conversations for further analysis.")

        # Add button for generating initial conversation
        if "prompt" in st.session_state:
            if st.sidebar.button("Generate Initial Conversation"):
                with st.spinner("Generating initial conversation..."):
                    initial_messages = generate_initial_conversation(st.session_state.prompt)
                    st.session_state.messages.extend(initial_messages)
                    st.success("Initial conversation generated!")
        
        if "show_modal" in st.session_state and st.session_state.show_modal:
            display_prompt(st.session_state.prompt)
            
            logging.debug("Program completed successfully")
        
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        st.chat_input("What is up?", key='user_input', on_submit=handle_chat_input)

        # Function to format the prompt for the LLM in a role-based format
        def format_prompt_for_llm(task_details: Dict[str, Any], personas: List[Dict[str, Any]]) -> str:
            # Define the instruction section
            prompt = "### Instruction ###\n"
            prompt += (
                "You are to simulate a collaborative discussion between multiple personas.\n"
                "Each persona will share their perspective, align their efforts, and suggest actionable steps for the given task.\n"
                "Ensure the personas maintain their unique attributes while working towards the shared goal.\n\n"
            )
            
            # Add context about the task
            prompt += "### Context ###\n"
            prompt += f"**Task:** {task_details['task']}\n"
            prompt += f"**Goals:** {task_details['goals']}\n\n"
            
            # Define personas and their attributes
            prompt += "### Personas ###\n"
            for persona in personas:
                prompt += f"**Persona Name:** {persona['name']}\n"
                prompt += f"- **Background:** {persona['background']}\n"
                prompt += f"- **Goals:** {persona['goals']}\n"
                prompt += f"- **Beliefs:** {persona['beliefs']}\n"
                prompt += f"- **Knowledge:** {persona['knowledge']}\n"
                prompt += f"- **Communication Style:** {persona['communication_style']}\n\n"
            
            # Specify the task for the personas
            prompt += "### Task ###\n"
            prompt += (
                "Generate a collaborative discussion between the personas about the task above. "
                "Ensure each persona maintains their unique perspective and style, but collectively works towards the shared goals.\n"
                "Highlight:\n"
                "- Each persona's approach to the task.\n"
                "- How their perspectives complement or challenge each other.\n"
                "- How they resolve conflicts or disagreements.\n"
                "- Their final actionable plan for completing the task.\n\n"
            )
            
            return prompt


        # Display current task and initialize the prompt for the chat if not already set
        if st.sidebar.button("Initialize and Load Prompt for Chat"):
            current_task = get_current_task()
            if "error" not in current_task:
                formatted_prompt = format_prompt_for_llm(current_task, current_task["personas"])
                #st.session_state.prompt = {"model": os.getenv("LITELLM_MODEL"), "content": formatted_prompt}
                #st.session_state.messages.append({"role": "system", "content": formatted_prompt})
                #st.success("Prompt initialized and loaded for chat.")
                
                # Submit the prompt to the LLM
                api_key = os.getenv("LITELLM_API_KEY")
                llm_response = submit_prompt_to_llm(formatted_prompt, api_key=api_key)
                st.session_state.messages.append({"role": "system", "content": llm_response})
                st.success("Chat is ready. You can start interacting with the personas.")
            else:
                st.warning(current_task["error"])

        # Autochat functionality
        st.sidebar.markdown("### Autochat")
        num_users = st.sidebar.slider("Number of users in conversation", 1, 20, 2)

        if st.sidebar.button("Start Autochat"):
            personas = fetch_personas_from_db()
            autochat(personas, num_users)
            st.session_state.autochat_active = True

        if st.sidebar.button("Stop Autochat"):
            st.session_state.autochat_active = False

        if st.session_state.get("autochat_active", False):
            st.markdown("#### Chat Log")
            for message in st.session_state.messages:
                st.markdown(message)

    def upload_urls_to_vector_db(personas: List[Dict[str, Any]]) -> None:
        """
        Upload URLs associated with personas to the vector database.
        
        Args:
            personas (List[Dict[str, Any]]): The list of personas.
        """
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

    if __name__ == "__main__":
        main()

# Navigation menu
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Advanced Menu", "Settings"])

# Display the selected page
if page == "Home":
    page1()
elif page == "Advanced Menu":
    page2()
elif page == "Settings":
    page3()


