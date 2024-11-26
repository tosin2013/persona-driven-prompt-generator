import json
import yaml
import requests
from pathlib import Path
import os
import sys
import litellm
import logging
import streamlit as st

# Configure logging at the beginning of the script
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Step 1: Collect User Input
def get_user_input():
    st.sidebar.title("Persona-Driven Prompt Generator")
    task = st.sidebar.text_area("Please describe the task or problem domain:", height=150)
    goals = st.sidebar.text_input("What are the key goals for this task? (e.g., efficiency, creativity):")
    logging.debug(f"User input received: task='{task}', goals='{goals}'")
    return {"task": task, "goals": goals}

def configure_litellm():
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
        litellm.DeepseekConfig(api_key=api_key)
    elif provider == "huggingface":
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError("HUGGINGFACE_API_KEY environment variable not set")
        litellm.HuggingfaceConfig(api_key=api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return model

# Step 2: Generate Personas
def generate_personas(task_details, persona_count=2):
    print("\nGenerating personas dynamically...")
    task = task_details["task"]

    model = configure_litellm()

    logging.debug(f"Generating {persona_count} personas for task: {task}")

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You will be provided with a task. "
                        "Generate personas in JSON format ONLY, without any additional text or explanations. "
                        "Each persona should include the following fields: name, background, goals, beliefs, knowledge, and communication_style."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Task: {task}. Generate {persona_count} personas with diverse perspectives. "
                        "Return the personas as a JSON array ONLY, without any additional text or explanations."
                    )
                }
            ],
            temperature=0.7
        )
        personas_content = response.choices[0].message.content.strip()
        if not personas_content:
            raise ValueError("Received empty response from LiteLLM")
        logging.debug(f"Personas content received: {personas_content}")

        # Extract JSON array from the response
        import re
        json_match = re.search(r'(\[.*\])', personas_content, re.DOTALL)
        if json_match:
            personas_json = json.loads(json_match.group(1))
        else:
            raise ValueError("Could not find valid JSON array in response")

        print(f"\nGenerated Personas:\n{personas_json}")
        return personas_json
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        sys.exit("Terminating program due to failure in persona generation.")
    except Exception as e:
        print(f"Error generating personas: {e}")
        sys.exit("Terminating program due to failure in persona generation.")

# Step 3: Generate Knowledge Sources via API
def fetch_knowledge_sources(task):
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
        import re
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
        sys.exit("Terminating program due to failure in knowledge source generation.")
    except Exception as e:
        print(f"Error generating knowledge sources: {e}")
        sys.exit("Terminating program due to failure in knowledge source generation.")

# Step 4: Resolve Persona Conflicts4

# Save and Load State Functions
def save_state_to_file(state, filename="decision_tree_state.json"):
    with open(filename, "w") as file:
        json.dump(state, file, indent=4)
    print(f"State saved to {filename}")

def load_state_from_file(filename="decision_tree_state.json"):
    try:
        with open(filename, "r") as file:
            state = json.load(file)
        print("State loaded successfully.")
        return state
    except FileNotFoundError:
        print("State file not found. Starting fresh.")
        return {}

# Adjusted resolve_conflicts Function
def resolve_conflicts(personas_text, task_details):
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
        # Prompt user for manual conflict resolution
        print("Unable to resolve conflicts automatically. Please provide guidance.")
        user_input = input("Enter your conflict resolution strategy: ")
        return user_input

# Step 5: Generate the Prompt
def generate_prompt(task_details, personas, knowledge_sources, conflict_strategy):
    prompt = {
        "task": task_details["task"],
        "personas": [persona["name"] for persona in personas],
        # Correctly extract knowledge source titles
        "knowledge_sources": [source["title"] for source in knowledge_sources],
        "conflict_resolution": conflict_strategy,
        "instructions": f"Generate outputs for the task '{task_details['task']}' by incorporating the perspectives of {', '.join([p['name'] for p in personas])}. Use knowledge from {', '.join([source['title'] for source in knowledge_sources])}, and resolve conflicts using {conflict_strategy}."
    }
    logging.debug("Generating the final prompt")
    print("\nGenerated Prompt:")
    print(json.dumps(prompt, indent=4))
    return prompt

# Step 6: Save Prompt to File
def save_prompt_to_file(prompt):
    print("\nWould you like to save the prompt to a file? (yes/no):")
    if input().lower() == "yes":
        file_format = input("Enter file format ('json' or 'yaml'): ").strip().lower()
        if file_format == "yaml":
            file_path = Path("generated_prompt.yaml")
            with file_path.open("w") as file:
                yaml.dump(prompt, file, default_flow_style=False, sort_keys=False)
            print(f"Prompt saved to {file_path}")
        elif file_format == "json":
            file_path = Path("generated_prompt.json")
            with file_path.open("w") as file:
                json.dump(prompt, file, indent=4)
            print(f"Prompt saved to {file_path}")
        else:
            print("Invalid format. Please choose 'json' or 'yaml'.")
    logging.debug("Prompt saved to file")

# Function to display the generated prompt in a dialog
def display_prompt(prompt):
    st.markdown("### Generated Prompt")
    st.markdown(f"**Task:** {prompt['task']}")
    st.markdown(f"**Personas:** {', '.join(prompt['personas'])}")
    st.markdown(f"**Knowledge Sources:** {', '.join(prompt['knowledge_sources'])}")
    st.markdown(f"**Conflict Resolution:** {prompt['conflict_resolution']}")
    st.markdown(f"**Instructions:** {prompt['instructions']}")
    if st.button("Copy to Clipboard"):
        st.code(json.dumps(prompt, indent=4), language='json')
        st.success("Copied to clipboard!")
    if st.button("Save to File"):
        save_prompt_to_file(prompt)
        st.success("Prompt saved to file.")
    if st.button("Close"):
        st.session_state.show_modal = False
        st.experimental_rerun()

# Main Function with API Selection and Persona Tuner
def main():
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
        prompt = generate_prompt(task_details, personas, knowledge_sources, conflict_strategy)
        
        # Store the model in the session state
        st.session_state.prompt = prompt
        st.session_state.prompt["model"] = os.getenv("LITELLM_MODEL")
        st.session_state.show_modal = True
        
        # Add generated personas to chat
        st.session_state.messages.append({"role": "system", "content": f"Generated Personas: {json.dumps(personas, indent=4)}"})
    
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

if __name__ == "__main__":
    main()
