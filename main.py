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
import litellm
import yaml
import re

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = None
if 'personas' not in st.session_state:
    st.session_state.personas = None
if 'knowledge_sources' not in st.session_state:
    st.session_state.knowledge_sources = None
if 'conflict_resolution' not in st.session_state:
    st.session_state.conflict_resolution = None
if 'persona_count' not in st.session_state:
    st.session_state.persona_count = 2  # Default number of personas

def fetch_knowledge_sources(task: str) -> List[Dict[str, str]]:
    """Fetch knowledge sources relevant to the task using the LiteLLM library."""
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
        
        json_match = re.search(r'(\[.*\])', knowledge_sources_content, re.DOTALL)
        if json_match:
            knowledge_sources_json = json.loads(json_match.group(1))
        else:
            raise ValueError("Could not find valid JSON array in response")

        return knowledge_sources_json
    except Exception as e:
        logging.error(f"Error generating knowledge sources: {e}")
        return []

def resolve_conflicts(personas_text: str, task_details: Dict[str, str]) -> str:
    """Resolve conflicts among personas."""
    print("\nResolving conflicts among personas...")
    model = configure_litellm()
    
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
                    "content": f"Task: {task_details['task']}\n\nPersonas:\n{personas_text}\n\nIdentify conflicts and propose resolutions."
                }
            ],
            temperature=0.7
        )
        conflict_resolution = response.choices[0].message.content.strip()
        if not conflict_resolution:
            raise ValueError("Received empty response from LiteLLM")
        return conflict_resolution
    except Exception as e:
        logging.error(f"Error resolving conflicts: {e}")
        return "No conflicts detected."

def generate_prompt(task_details: Dict[str, str], personas: List[Dict[str, Any]], 
                   knowledge_sources: List[Dict[str, str]], conflict_strategy: str, 
                   prior_decisions: List[str], additional_context: str, use_autogen: bool = False) -> Dict[str, Any]:
    """Generate a prompt based on the inputs."""
    memory_personas = "\n".join([
        f"- {persona['name']}:\n"
        f"    - Background: {persona['background']}\n"
        f"    - Goals: {persona['goals']}\n"
        f"    - Beliefs: {persona['beliefs']}\n"
        f"    - Knowledge: {persona['knowledge']}\n"
        f"    - Communication Style: {persona['communication_style']}"
        for persona in personas
    ])
    
    memory_prior_decisions = "\n".join([f"- {decision}" for decision in prior_decisions])

    prompt = {
        "task": task_details["task"],
        "personas": [persona["name"] for persona in personas],
        "knowledge_sources": [
            {"title": source["title"], "url": source["url"]}
            for source in knowledge_sources
        ],
        "conflict_resolution": conflict_strategy,
        "use_autogen": use_autogen,
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
            f"the provided strategy. Update the memory with significant decisions or outputs generated."
        )
    }
    
    return prompt

def clear_chat():
    """Clear the chat history and reset session state."""
    st.session_state.chat_history = []
    st.session_state.current_prompt = None
    st.session_state.personas = None
    st.session_state.knowledge_sources = None
    st.session_state.conflict_resolution = None

def generate_markdown_output(prompt: Dict[str, Any]) -> str:
    """Generate a markdown formatted output of the prompt."""
    markdown = f"""# Task: {prompt['task']}

## Personas
{prompt['memory']['personas']}

## Knowledge Sources
"""
    for source in prompt['knowledge_sources']:
        markdown += f"- [{source['title']}]({source.get('url', '#')})\n"
    
    markdown += f"""
## Conflict Resolution Strategy
{prompt['conflict_resolution']}

## Task Goals
{prompt['memory']['task_goals']}

## Prior Decisions
{prompt['memory']['prior_decisions']}

## Instructions
{prompt['instructions']}
"""
    return markdown

def main():
    st.title("Persona-Driven Prompt Generator")
    
    # Apply custom styling
    st.markdown("""
        <style>
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            width: 100%;
            margin: 5px 0;
            padding: 10px;
            border-radius: 5px;
        }
        .chat-message {
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            white-space: pre-wrap;
            font-family: monospace;
        }
        .system-message {
            background-color: #f0f2f6;
        }
        .user-message {
            background-color: #e3f2fd;
        }
        .persona-card {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar for user input
    with st.sidebar:
        st.header("Input Configuration")
        
        # Add persona count slider
        st.session_state.persona_count = st.slider(
            "Number of Personas",
            min_value=1,
            max_value=10,
            value=st.session_state.persona_count,
            help="Select the number of personas to generate"
        )
        
        # AutoGen Configuration
        st.subheader("AutoGen Configuration")
        
        workflow_type = st.radio(
            "Select Workflow Type",
            options=["Autonomous (Chat)", "Sequential"],
            help="""
            Autonomous: Includes an initiator and receiver for chat-based interactions.
            Sequential: Includes a list of agents in a given order for step-by-step execution.
            """
        )
        
        st.subheader("Agent Configuration")
        agent_types = st.multiselect(
            "Select Agent Types",
            options=["User Proxy Agent", "Assistant Agent", "GroupChat"],
            default=["Assistant Agent"],
            help="""
            User Proxy Agent: Represents the user and executes code
            Assistant Agent: Plans and generates code to solve tasks
            GroupChat: Manages group chat interactions
            """
        )
        
        user_input = get_user_input()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Generate\n(No AutoGen)"):
                with st.spinner("Generating prompt..."):
                    # Generate content
                    st.session_state.personas = generate_personas_wrapper(
                        user_input,
                        persona_count=st.session_state.persona_count
                    )
                    st.session_state.knowledge_sources = fetch_knowledge_sources(user_input["task"])
                    st.session_state.conflict_resolution = resolve_conflicts(
                        json.dumps(st.session_state.personas, indent=4), 
                        user_input
                    )
                    
                    st.session_state.current_prompt = generate_prompt(
                        user_input,
                        st.session_state.personas,
                        st.session_state.knowledge_sources,
                        st.session_state.conflict_resolution,
                        [],
                        "Standard prompt generation without AutoGen.",
                        use_autogen=False
                    )
                    
                    # Generate markdown
                    markdown_output = generate_markdown_output(st.session_state.current_prompt)
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "role": "system",
                        "content": "Generated prompt without AutoGen:",
                        "markdown": markdown_output
                    })
        
        with col2:
            if st.button("Generate\n(With AutoGen)"):
                with st.spinner("Generating prompt with AutoGen..."):
                    # Generate content
                    st.session_state.personas = generate_personas_wrapper(
                        user_input,
                        persona_count=st.session_state.persona_count
                    )
                    st.session_state.knowledge_sources = fetch_knowledge_sources(user_input["task"])
                    st.session_state.conflict_resolution = resolve_conflicts(
                        json.dumps(st.session_state.personas, indent=4), 
                        user_input
                    )
                    
                    # Add AutoGen configuration to the prompt
                    autogen_config = {
                        "workflow_type": workflow_type,
                        "agent_types": agent_types
                    }
                    
                    st.session_state.current_prompt = generate_prompt(
                        user_input,
                        st.session_state.personas,
                        st.session_state.knowledge_sources,
                        st.session_state.conflict_resolution,
                        [],
                        f"Enhanced prompt generation with AutoGen workflow.\nWorkflow Type: {workflow_type}\nAgent Types: {', '.join(agent_types)}",
                        use_autogen=True
                    )
                    
                    # Generate markdown
                    markdown_output = generate_markdown_output(st.session_state.current_prompt)
                    
                    # Generate AutoGen workflow with configuration
                    workflow_code = generate_autogen_workflow(
                        st.session_state.personas,
                        workflow_type=workflow_type,
                        agent_types=agent_types,
                        task=user_input
                    )
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "role": "system",
                        "content": "Generated prompt with AutoGen:",
                        "markdown": markdown_output
                    })
                    st.session_state.chat_history.append({
                        "role": "system",
                        "content": f"AutoGen Workflow ({workflow_type}):",
                        "code": workflow_code
                    })
        
        with col3:
            if st.button("Clear Chat"):
                clear_chat()
                st.rerun()

    # Main area for displaying content
    if st.session_state.personas:
        st.header("Generated Personas")
        cols = st.columns(2)
        for idx, persona in enumerate(st.session_state.personas):
            with cols[idx % 2]:
                with st.container():
                    st.markdown(f"""
                    <div class="persona-card">
                        <h3>{persona['name']}</h3>
                        <p><strong>Background:</strong> {persona['background']}</p>
                        <p><strong>Goals:</strong> {persona['goals']}</p>
                        <p><strong>Beliefs:</strong> {persona['beliefs']}</p>
                        <p><strong>Knowledge:</strong> {persona['knowledge']}</p>
                        <p><strong>Communication Style:</strong> {persona['communication_style']}</p>
                    </div>
                    """, unsafe_allow_html=True)

    # Display chat history with markdown support
    st.header("Generated Content")
    for message in st.session_state.chat_history:
        with st.expander(message["content"], expanded=True):
            if "markdown" in message:
                st.markdown(message["markdown"])
                # Add copy button for markdown
                if st.button(f"Copy as Markdown", key=f"copy_{hash(message['markdown'])}"):
                    st.code(message["markdown"], language="markdown")
            elif "code" in message:
                st.code(message["code"], language="python")
            else:
                st.markdown(f'<div class="chat-message">{message["content"]}</div>', 
                          unsafe_allow_html=True)

    # Display current prompt if available
    if st.session_state.current_prompt:
        with st.expander("Current Prompt (JSON)", expanded=False):
            st.json(st.session_state.current_prompt)

if __name__ == "__main__":
    main()
