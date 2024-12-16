import logging
import streamlit as st
import os
import json
from typing import List, Dict, Any
from psycopg2 import connect
from psycopg2.extras import Json
from database import create_tables, store_memory_in_pgvector, find_similar_tasks
from llm_interaction import configure_litellm, submit_prompt_to_llm, generate_autogen_workflow, download_autogen_workflow
from persona_management import generate_personas, generate_initial_conversation, edit_persona_tones, generate_personas_wrapper
from search import duckduckgo_search
from utils import generate_embedding, get_user_input
import litellm  # Add this import
import yaml
import re

# Database connection details
DB_NAME = "persona_db"
DB_USER = "persona_user"
DB_PASSWORD = "secure_password"
DB_HOST = "127.0.0.1"  # Ensure this is correct

def fetch_knowledge_sources(task: str) -> List[Dict[str, str]]:
    """
    Fetch knowledge sources relevant to the task using the LiteLLM library.

    Args:
        task (str): The task description.

    Returns:
        List[Dict[str, str]]: A list of knowledge sources with details such as title, description, and URL.
    """
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

def resolve_conflicts(personas_text: str, task_details: Dict[str, str]) -> str:
    """
    Resolve conflicts among personas by prioritizing fairness, knowledge, and relevance to task goals.

    Args:
        personas_text (str): Text representation of the personas.
        task_details (Dict[str, str]): Details of the task including task description and goals.

    Returns:
        str: Conflict resolution strategy.
    """
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

def generate_prompt(task_details: Dict[str, str], personas: List[Dict[str, Any]], knowledge_sources: List[Dict[str, str]], conflict_strategy: str, prior_decisions: List[str], additional_context: str) -> Dict[str, Any]:
    """
    Generate a prompt based on the task details, personas, knowledge sources, and conflict resolution strategy.

    Args:
        task_details (Dict[str, str]): Details of the task including task description and goals.
        personas (List[Dict[str, Any]]): List of personas.
        knowledge_sources (List[Dict[str, str]]): List of knowledge sources.
        conflict_strategy (str): Conflict resolution strategy.
        prior_decisions (List[str]): List of prior decisions.
        additional_context (str): Additional context or instructions for the prompt generation.

    Returns:
        Dict[str, Any]: A dictionary representing the generated prompt.
    """
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
            f"### Additional Context ###\n"
            f"{additional_context}\n\n"
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

def save_prompt_to_file(prompt: Dict[str, Any], file_format: str, output_path: str = None) -> None:
    """
    Save the generated prompt to a file in the specified format.

    Args:
        prompt (Dict[str, Any]): The generated prompt.
        file_format (str): The file format to save the prompt in (e.g., "json", "yaml").
        output_path (str, optional): Custom output path for the file. If not provided,
                                   defaults to "generated_prompt.[format]".
    """
    if output_path is None:
        output_path = f"generated_prompt.{file_format}"

    try:
        with open(output_path, 'w') as f:
            if file_format.lower() == "json":
                json.dump(prompt, f)
            elif file_format.lower() == "yaml":
                yaml.dump(prompt, f)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
        print(f"Prompt saved to {output_path}")
    except Exception as e:
        print(f"Error saving prompt to file: {e}")

def generate_and_download_autogen_workflow(personas: List[Dict[str, Any]]) -> None:
    """
    Generate and download an AutoGen workflow based on the personas.

    Args:
        personas (List[Dict[str, Any]]): List of personas.
    """
    workflow_code = generate_autogen_workflow(personas)
    download_autogen_workflow(workflow_code)

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
    user_input = get_user_input()

    # Step 2: Generate Personas
    personas = generate_personas_wrapper(user_input)

    # Step 3: Generate Knowledge Sources via API
    knowledge_sources = fetch_knowledge_sources(user_input["task"])

    # Step 4: Resolve Persona Conflicts
    conflict_resolution = resolve_conflicts(json.dumps(personas, indent=4), user_input)

    # Step 5: Generate the Prompt
    additional_context = "This is additional context for the prompt generation."
    prompt = generate_prompt(user_input, personas, knowledge_sources, conflict_resolution, [], additional_context)

    # Step 6: Save Prompt to File
    save_prompt_to_file(prompt, "json")

    # Step 7: Generate and Download AutoGen Workflow
    generate_and_download_autogen_workflow(personas)

if __name__ == "__main__":
    page1()
