import logging
import streamlit as st
import os
import json
from typing import List, Dict, Any
from psycopg2 import connect
from psycopg2.extras import Json
from database import create_tables, store_memory_in_pgvector, find_similar_tasks
from llm_interaction import configure_litellm, submit_prompt_to_llm
from persona_management import generate_personas, generate_initial_conversation, edit_persona_tones
from search import duckduckgo_search
from utils import generate_embedding

# Database connection details
DB_NAME = "persona_db"
DB_USER = "persona_user"
DB_PASSWORD = "secure_password"
DB_HOST = "127.0.0.1"  # Ensure this is correct

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

    # Step 2: Generate Personas
    def generate_personas_wrapper(task_details: Dict[str, Any], persona_count: int = 2) -> List[Dict[str, Any]]:
        return generate_personas(task_details, persona_count)

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
            file_contents = yaml.dump(prompt, default_
