import streamlit as st
import json
from typing import Dict, Any
import litellm
import threading
import time
from shared_functions import generate_prompt, generate_personas

def page1():
    st.title("Persona-Driven Prompt Generator - wok")
    st.markdown("""
        <style>
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
        }
        .stButton>button {
            width: 100%;
            padding: 0.5rem 1rem;
            font-size: 1rem;
            font-weight: 500;
            border-radius: 8px;
            transition: all 0.2s;
        }
        .stButton>button:first-child {
            background-color: #4CAF50;
            color: white;
        }
        .stButton>button:first-child:hover {
            background-color: #45a049;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stButton>button[data-testid="baseButton-secondary"] {
            background-color: #f44336;
            color: white;
            border: none;
        }
        .stButton>button[data-testid="baseButton-secondary"]:hover {
            background-color: #da190b;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        /* Custom styling for text areas */
        .stTextArea textarea {
            min-height: 150px !important;
            font-size: 1rem !important;
            line-height: 1.5 !important;
            padding: 12px !important;
            border-radius: 8px !important;
        }
        .task-description textarea {
            min-height: 200px !important;
            font-family: 'Arial', sans-serif !important;
            background-color: #f8f9fa !important;
            border: 2px solid #e9ecef !important;
        }
        .task-description textarea:focus {
            border-color: #4CAF50 !important;
            box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar setup for workflow type selection and AutoGen workflow enabling
    workflow_type = st.sidebar.selectbox(
        "AutoGen Workflow Type", ["Autonomous (Chat)", "Sequential"]
    )
    num_personas = st.sidebar.slider(
        "Number of Personas",
        min_value=1,
        max_value=50,
        value=2,  # default value
        help="Select the number of personas to generate (1-50)"
    )
    autogen_workflow = st.sidebar.checkbox("Enable AutoGen Workflow", value=False)

    # Function to display the generated prompt in a dialog
    def display_prompt(prompt: Dict[str, Any]) -> None:
        st.markdown("### Generated Prompt")
        
        # Display original and enhanced task information
        with st.expander("📝 Task Details", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original Task:**")
                st.markdown(prompt.get('original_task', 'N/A'))
                st.markdown("**Original Goals:**")
                st.markdown(prompt.get('original_goals', 'N/A'))
            with col2:
                st.markdown("**Enhanced Task:**")
                st.markdown(prompt['task'])
                st.markdown("**Enhanced Goals:**")
                st.markdown(prompt['goals'])
        
        # Create markdown content for copying
        markdown_content = [
            "# Generated Prompt\n",
            "## Original Task Details\n",
            f"**Task:** {prompt.get('original_task', 'N/A')}\n",
            f"**Goals:** {prompt.get('original_goals', 'N/A')}\n\n",
            "## Enhanced Task Details\n",
            f"**Task:** {prompt['task']}\n",
            f"**Goals:** {prompt['goals']}\n\n",
            "## Personas\n"
        ]
        
        # Display detailed persona information
        st.markdown("### Personas")
        for persona in prompt['full_personas']:
            # Display in UI
            with st.expander(f" {persona['name']}"):
                st.markdown(f"**Background:** {persona['background']}")
                st.markdown(f"**Goals:** {persona['goals']}")
                st.markdown(f"**Beliefs:** {persona['beliefs']}")
                st.markdown(f"**Knowledge:** {persona['knowledge']}")
                st.markdown(f"**Communication Style:** {persona['communication_style']}")
                st.markdown(f"**Role:** {persona['role']}")
                st.markdown(f"**Strengths:** {persona['strengths']}")
                st.markdown(f"**Challenges:** {persona['challenges']}")
            
            # Add to markdown content
            markdown_content.extend([
                f"### {persona['name']}\n",
                f"- **Background:** {persona['background']}\n",
                f"- **Goals:** {persona['goals']}\n",
                f"- **Beliefs:** {persona['beliefs']}\n",
                f"- **Knowledge:** {persona['knowledge']}\n",
                f"- **Communication Style:** {persona['communication_style']}\n",
                f"- **Role:** {persona['role']}\n",
                f"- **Strengths:** {persona['strengths']}\n",
                f"- **Challenges:** {persona['challenges']}\n\n"
            ])
        
        # Format and display knowledge sources
        st.markdown("### Knowledge Sources")
        knowledge_sources_formatted = "\n".join([
            f"- [{source['title']}]({source['url']})"
            for source in prompt['knowledge_sources']
        ])
        st.markdown(knowledge_sources_formatted if knowledge_sources_formatted else "No knowledge sources provided")
        
        # Add knowledge sources to markdown content
        markdown_content.append("## Knowledge Sources\n")
        for source in prompt['knowledge_sources']:
            markdown_content.append(f"- [{source['title']}]({source['url']})\n")
        
        st.markdown(f"**Conflict Resolution Strategy:** {prompt['conflict_resolution']}")
        st.markdown(f"**Instructions:** {prompt['instructions']}")
        
        # Add remaining sections to markdown content
        markdown_content.extend([
            f"\n## Conflict Resolution Strategy\n{prompt['conflict_resolution']}\n",
            f"\n## Instructions\n{prompt['instructions']}\n"
        ])

        # Combine all markdown content
        full_markdown = "".join(markdown_content)

        # Create columns for the buttons
        col1, col2 = st.columns(2)
        
        # Column 1: Copy to Markdown
        with col1:
            st.download_button(
                label="Copy to Markdown",
                data=full_markdown,
                file_name="prompt.md",
                mime="text/markdown",
                help="Click to copy the content in markdown format",
                key="download_markdown"
            )
            # Also display the markdown content in a collapsible section
            with st.expander("View Markdown"):
                st.code(full_markdown, language="markdown")

        # Column 2: Download options
        with col2:
            file_format = st.selectbox("Choose file format:", ["json", "yaml"])
            if file_format == "json":
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(prompt, indent=4),
                    file_name="prompt.json",
                    mime="application/json"
                )
            else:
                import yaml
                yaml_content = yaml.dump(prompt, default_flow_style=False)
                st.download_button(
                    label="Copy to YAML",
                    data=yaml_content,
                    file_name="prompt.yaml",
                    mime="text/yaml",
                    key="download_yaml"
                )

    # Initialize session state for clearing
    if 'clear_form' not in st.session_state:
        st.session_state.clear_form = False

    # Collect user input for task description, goals, and reference URLs
    st.markdown("### Task Description")
    st.markdown("Describe your task in detail. Include any specific requirements, constraints, or preferences.")
    task_description = st.text_area(
        "Task Description",
        value="" if st.session_state.clear_form else None,
        height=200,
        help="Enter a detailed description of your task",
        key="task_description",
        label_visibility="collapsed"
    )

    st.markdown("### Task Goals")
    st.markdown("What are the specific goals or outcomes you want to achieve?")
    goals = st.text_area(
        "Goals",
        value="" if st.session_state.clear_form else None,
        height=150,
        help="Enter the goals or desired outcomes",
        key="goals"
    )

    st.markdown("### Reference URLs")
    st.markdown("Add any relevant URLs that provide context or examples (one per line)")
    reference_urls = st.text_area(
        "Reference URLs",
        value="" if st.session_state.clear_form else None,
        height=100,
        help="Enter each URL on a new line",
        key="urls"
    )

    # Add some spacing
    st.markdown("<br>", unsafe_allow_html=True)

    # Create a row for the buttons using columns
    col1, col2, col3 = st.columns([1, 1, 2])
    
    def clear_form():
        st.session_state.clear_form = True
        if 'current_prompt' in st.session_state:
            del st.session_state.current_prompt
        st.rerun()
    
    with col1:
        if st.button("Generate Prompt", type="primary"):
            st.session_state.clear_form = False  # Reset clear form flag
            # Process URLs: strip whitespace and filter out empty lines
            urls = [url.strip() for url in (reference_urls or "").splitlines() if url.strip()]
            
            # Generate personas, knowledge sources, and resolve conflicts
            task_details = {
                "task": task_description or "",
                "goals": goals or "",
                "reference_urls": urls
            }
            personas = generate_personas(task_details, num_personas)
            knowledge_sources = [{"title": url.split('/')[-1], "url": url} for url in task_details["reference_urls"]]
            conflict_resolution = resolve_conflicts(personas)
            instructions = generate_instructions(task_description, goals, knowledge_sources)

            prompt = {
                "original_task": task_description,
                "original_goals": goals,
                "task": task_details.get("enhanced_task", task_description),
                "goals": task_details.get("enhanced_goals", goals),
                "personas": [persona['name'] for persona in personas],
                "knowledge_sources": knowledge_sources,
                "conflict_resolution": conflict_resolution,
                "instructions": instructions,
                "full_personas": personas
            }

            # Store the prompt in session state
            st.session_state.current_prompt = prompt
            # Display the prompt
            display_prompt(prompt)

    with col2:
        if st.button("Clear All", type="secondary", on_click=clear_form):
            pass  # The actual clearing is handled in the clear_form callback

    # Reset clear form flag after rerun
    if st.session_state.clear_form:
        st.session_state.clear_form = False

    # Display the current prompt if it exists in session state
    if 'current_prompt' in st.session_state:
        display_prompt(st.session_state.current_prompt)

def resolve_conflicts(personas: list) -> str:
    # Placeholder function to resolve conflicts between personas
    return "No conflicts detected."

def generate_instructions(task_description: str, goals: str, knowledge_sources: list) -> str:
    # Placeholder function to generate instructions based on task description, goals, and knowledge sources
    return f"Complete the task: {task_description} with the following goals: {goals} and refer to the provided knowledge sources."

def save_prompt_to_file(prompt: Dict[str, Any], file_format: str) -> None:
    # Placeholder function to save the prompt to a file in the selected format
    file_name = f"prompt.{file_format}"
    with open(file_name, 'w') as file:
        if file_format == "json":
            json.dump(prompt, file, indent=4)
        elif file_format == "yaml":
            import yaml
            yaml.dump(prompt, file)
    st.success(f"Prompt saved to {file_name}")

def chat_interaction(MODEL):
    st.title("Chat Interaction with LLM")
    st.markdown("Interact with the LLM in a chat-like interface.")

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'personas' not in st.session_state:
        st.session_state.personas = []
    if 'workflow_config' not in st.session_state:
        st.session_state.workflow_config = {}

    # Sidebar for chat configuration
    with st.sidebar:
        num_personas = st.slider(
            "Number of Personas",
            min_value=1,
            max_value=50,
            value=2,
            help="Select the number of personas to generate (1-50)"
        )
        
        if st.button("Generate New Personas"):
            # Example task details
            task_details = {
                "task": "Engage in a collaborative discussion",
                "goals": "Generate creative and diverse perspectives"
            }
            
            # Example personas (you can modify this based on your needs)
            personas = [
                {
                    "name": f"Persona_{i}",
                    "background": f"Expert in field {i}",
                    "goals": "Contribute unique insights",
                    "beliefs": "Values collaboration",
                    "knowledge": f"Specialized in area {i}",
                    "communication_style": "Professional and clear"
                } for i in range(num_personas)
            ]
            
            # Generate prompt with configurations
            config = generate_prompt(
                task_details=task_details,
                personas=personas,
                knowledge_sources=[{"title": "General Knowledge", "url": ""}],
                conflict_strategy="Collaborative resolution",
                prior_decisions=[]
            )
            
            st.session_state.personas = config["agent_configs"]
            st.session_state.workflow_config = config["workflow_config"]
            st.success(f"Generated {num_personas} personas!")

    # Display current personas
    if st.session_state.personas:
        with st.expander("Current Personas"):
            st.json(st.session_state.personas)

    # Chat interface
    user_input = st.text_input("You:", key="user_input")
    if st.button("Send"):
        if user_input:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # If we have personas, use them in the conversation
            if st.session_state.personas:
                # Create a context-aware prompt that includes persona information
                messages = [
                    {
                        "role": "system",
                        "content": f"You are orchestrating a conversation between multiple personas: {', '.join(st.session_state.personas.keys())}. Use their unique characteristics and the workflow configuration to generate responses."
                    }
                ] + st.session_state.messages
            else:
                messages = st.session_state.messages

            # Get response from LLM
            response = litellm.completion(
                model=MODEL,
                messages=messages,
                temperature=0.7
            )
            message = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": message})

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Auto chat feature
    def auto_chat():
        while True:
            time.sleep(10)
            if st.session_state.personas:
                # Use personas in auto-chat
                auto_message = "Continuing the conversation with our personas..."
            else:
                auto_message = "Auto message"
                
            st.session_state.messages.append({"role": "user", "content": auto_message})
            response = litellm.completion(
                model=MODEL,
                messages=st.session_state.messages,
                temperature=0.7
            )
            message = response.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": message})

    if st.sidebar.checkbox("Enable Auto Chat"):
        auto_chat_thread = threading.Thread(target=auto_chat)
        auto_chat_thread.start()
