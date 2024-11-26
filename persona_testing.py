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

# Configure logging at the beginning of the script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Database connection details
DB_NAME = "persona_db"
DB_USER = "persona_user"
DB_PASSWORD = "secure_password"
DB_HOST = "127.0.0.1"  # Ensure this is correct

# Function to clear the database
def clear_database():
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("DELETE FROM task_memory;")
    conn.commit()
    cursor.close()
    conn.close()

# Sidebar for toggle
advanced_mode = st.sidebar.checkbox("Enable Advanced Settings", value=False)

# Add a 'Clear' button in the sidebar
if st.sidebar.button("Clear Data and Context"):
    # Clear session state
    st.session_state.clear()
    # Clear the database
    clear_database()
    st.success("Application context and database have been cleared.")

# Add a 'Clear LLM Context' button in the sidebar
if st.sidebar.button("Clear LLM Context"):
    # Clear the session state related to LLM prompts and messages
    st.session_state.prompt = {}
    st.session_state.messages = []
    st.success("LLM context has been cleared.")

# Step 1: Collect User Input
def get_user_input() -> Dict[str, Any]:
    st.sidebar.title("Persona-Driven Prompt Generator")
    task = st.sidebar.text_area("Please describe the task or problem domain:", height=150)
    goals = st.sidebar.text_input("What are the key goals for this task? (e.g., efficiency, creativity):")
    reference_urls = st.sidebar.text_area("Optional: Provide URLs for reference (one per line):")
    reference_urls_list = [url.strip() for url in reference_urls.split('\n') if url.strip()]
    logging.debug(f"User input received: task='{task}', goals='{goals}', reference_urls='{reference_urls_list}'")
    return {"task": task, "goals": goals, "reference_urls": reference_urls_list}

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
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return model

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

# Main Function with API Selection and Persona Tuner
def main() -> None:
    logging.debug("Program started")
    task_details = get_user_input()
    
    # Ensure environment variables for LiteLLM are set
    if not os.getenv("LITELLM_MODEL") or not os.getenv("LITELLM_PROVIDER"):
        st.error("Error: LITELLM_MODEL and LITELLM_PROVIDER environment variables must be set.")
        sys.exit("Terminating program due to missing environment variables.")
    
    # Display the current model in use
    st.sidebar.write(f"Current model in use: {os.getenv('LITELLM_MODEL')}")
    
    # Persona Tuner
    persona_count = st.sidebar.slider("How many personas would you like to include?", 1, 20, 2)
    
    if st.sidebar.button("Submit"):
        personas = generate_personas(task_details, persona_count=persona_count)
        
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
    
    if "show_modal" in st.session_state and st.session_state.show_modal:
        display_prompt(st.session_state.prompt)
        
        logging.debug("Program completed successfully")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("What is up?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Interact with the generated prompt
        if "prompt" in st.session_state:
            response = litellm.completion(
                model=st.session_state.prompt["model"],
                messages=[
                    {"role": "system", "content": "You are interacting with the generated prompt."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "system", "content": reply})
            with st.chat_message("system"):
                st.markdown(reply.replace("\n", "\n\n"))

    # Display current task
    if st.sidebar.button("What is the current prompt?"):
        current_task = get_current_task()
        if "error" not in current_task:
            st.write(f"**Task:** {current_task['task']}")
            st.write(f"**Goals:** {current_task['goals']}")
            st.write(f"**Personas:** {current_task['personas']}")
        else:
            st.warning(current_task["error"])

if __name__ == "__main__":
    main()

