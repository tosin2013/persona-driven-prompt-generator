import logging
import litellm
import json
import re
import os  # Added import for os
from typing import List, Dict, Any

def configure_litellm() -> str:
    """
    Configure LiteLLM with the first valid model configuration found.
    
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

def submit_prompt_to_llm(prompt: str, model: str = None) -> Dict[str, Any]:
    """
    Submit a prompt to the LiteLLM model and return the response.

    Args:
        prompt (str): The prompt to submit to the LLM.
        model (str, optional): The model to use. If None, the default model configured by configure_litellm() will be used.

    Returns:
        Dict[str, Any]: The response from the LLM, including the generated content and other metadata.
    """
    if model is None:
        model = configure_litellm()

    logging.debug(f"Submitting prompt to model: {model}")

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        response_content = response.choices[0].message.content.strip()
        logging.debug(f"Response received: {response_content}")

        return {
            "content": response_content,
            "metadata": {
                "model": model,
                "temperature": 0.7
            }
        }
    except Exception as e:
        logging.error(f"Error submitting prompt to LLM: {e}")
        return {
            "error": str(e)
        }

from agent.enhanced_agents import (
    EnhancedUserProxy, EnhancedAssistant, CodeAssistant, ReviewerAssistant,
    WebResearchAgent, FileSystemAgent, CoordinatedGroupChat, CoordinatedManager,
    create_progress_tracker, monitor_conversation
)

def generate_autogen_workflow(personas: List[Dict[str, Any]], workflow_type: str = "Autonomous (Chat)", agent_types: List[str] = None, task: Dict[str, str] = None, urls: List[str] = None) -> str:
    """Generate an AutoGen workflow with enhanced capabilities."""
    if agent_types is None:
        agent_types = ["Assistant Agent"]
    
    if urls is None:
        urls = []

    task_desc = task.get('task', 'No task description provided') if task else 'No task description provided'
    task_goals = task.get('goals', 'No goals provided') if task else 'No goals provided'

    # Start with imports and task description
    workflow = f"""from agent.enhanced_agents import *
import autogen
import logging
import sys
from typing import Dict, List, Optional, Union
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Task Description
TASK = \"\"\"{task_desc}\"\"\"

# Task Goals
GOALS = \"\"\"{task_goals}\"\"\"

# URLs to analyze
URLS = {urls}

# Configure agents with enhanced settings
config_list = [
    {{
        'model': 'gpt-4',
        'api_key': 'your-api-key',  # Replace with your API key
        'temperature': 0.7,
        'max_tokens': 2000,
        'timeout': TIMEOUT_SECONDS
    }}
]

# Progress tracking
progress = create_progress_tracker()

# URL content cache
url_content_cache = {{}}
"""

    # Add agent definitions based on personas and types
    for i, persona in enumerate(personas):
        agent_name = persona["name"].replace(" ", "_").lower()
        
        if "Web Research Agent" in agent_types:
            workflow += f"""
# Web Research Agent for {persona['name']}
{agent_name}_researcher = WebResearchAgent(
    name="{agent_name}_researcher",
    system_message=\"\"\"Role: Web Content Researcher
Background: {persona['background']}
Knowledge: {persona['knowledge']}
Task: {task_desc}
Objectives: {task_goals}
Responsibilities:
- Analyze web content and URLs
- Extract relevant information
- Identify code snippets
- Summarize findings
- Cache results for efficiency
- Collaborate with other agents to share findings\"\"\",
    llm_config={{"config_list": config_list}}
)

# Initialize URL analysis for {agent_name}_researcher
for url in URLS:
    if url.startswith(('http://', 'https://')):
        analysis = {agent_name}_researcher.analyze_url_content(url)
        url_content_cache[url] = analysis
"""

        if "File System Agent" in agent_types:
            workflow += f"""
# File System Agent for {persona['name']}
{agent_name}_fs = FileSystemAgent(
    name="{agent_name}_fs",
    system_message=\"\"\"Role: File System Handler
Background: {persona['background']}
Knowledge: {persona['knowledge']}
Task: {task_desc}
Objectives: {task_goals}
Responsibilities:
- Read and analyze local files
- Extract file content
- Identify file types
- Cache file contents
- Handle file URLs safely
- Share file content with other agents\"\"\",
    llm_config={{"config_list": config_list}}
)

# Initialize file analysis for {agent_name}_fs
for url in URLS:
    if url.startswith('file:///'):
        content = {agent_name}_fs.read_file_content(url)
        url_content_cache[url] = content
"""

        if "User Proxy Agent" in agent_types:
            workflow += f"""
# User Proxy Agent for {persona['name']}
{agent_name}_proxy = EnhancedUserProxy(
    name="{agent_name}_proxy",
    system_message=\"\"\"Role: {persona['background']}
Goals: {persona['goals']}
Beliefs: {persona['beliefs']}
Task: {task_desc}
Objectives: {task_goals}
Special Instructions: Coordinate with other agents and maintain task focus.
Error Handling: Report any issues and request clarification when needed.\"\"\"
)"""

        if "Assistant Agent" in agent_types:
            workflow += f"""
# Assistant Agent for {persona['name']}
{agent_name}_assistant = EnhancedAssistant(
    name="{agent_name}_assistant",
    system_message=\"\"\"Role: {persona['background']}
Knowledge: {persona['knowledge']}
Communication Style: {persona['communication_style']}
Task: {task_desc}
Objectives: {task_goals}
Collaboration Guidelines: 
- Actively participate in problem-solving
- Share relevant expertise
- Ask for clarification when needed
- Provide detailed explanations
Error Recovery:
- Monitor for inconsistencies
- Suggest alternative approaches
- Report technical issues\"\"\",
    llm_config={{"config_list": config_list}}
)"""

        if "Code Assistant" in agent_types:
            workflow += f"""
# Code Assistant Agent for {persona['name']}
{agent_name}_coder = CodeAssistant(
    name="{agent_name}_coder",
    system_message=\"\"\"Role: Code Implementation Specialist
Background: {persona['background']}
Expertise: {persona['knowledge']}
Task: {task_desc}
Objectives: {task_goals}
Responsibilities:
- Write clean, efficient code
- Implement error handling
- Follow best practices
- Document code thoroughly
- Review and refactor suggestions\"\"\",
    llm_config={{"config_list": config_list}}
)"""

        if "Reviewer Agent" in agent_types:
            workflow += f"""
# Code Review Agent for {persona['name']}
{agent_name}_reviewer = ReviewerAssistant(
    name="{agent_name}_reviewer",
    system_message=\"\"\"Role: Code Quality Reviewer
Background: {persona['background']}
Standards: {persona['knowledge']}
Task: {task_desc}
Review Criteria:
- Code quality and style
- Security best practices
- Performance optimization
- Documentation completeness
- Error handling coverage\"\"\",
    llm_config={{"config_list": config_list}}
)"""

    # Add workflow-specific code based on type
    if workflow_type == "Autonomous (Chat)":
        workflow += """
try:
    # Initialize chat between agents with monitoring
    initiator = user_proxy  # First agent
    receiver = assistant_agent  # Second agent
    chat_history = []
    
    # Start the conversation with task details and URL analysis
    initial_message = f"Let's work on the following task:\\n{TASK}\\n\\nOur goals are:\\n{GOALS}"
    
    # Add URL analysis summary if available
    if url_content_cache:
        initial_message += "\\n\\nURL Analysis Summary:\\n"
        for url, content in url_content_cache.items():
            initial_message += f"\\nURL: {url}\\n"
            if isinstance(content, dict):
                initial_message += f"Domain: {content.get('domain', 'N/A')}\\n"
                initial_message += f"Summary: {content.get('summary', 'No summary available')}\\n"
                if content.get('code_snippets'):
                    initial_message += "Code Snippets Found:\\n"
                    for snippet in content['code_snippets']:
                        initial_message += f"```\\n{snippet}\\n```\\n"
            else:
                initial_message += f"Content: {str(content)[:500]}...\\n"
    
    response = initiator.initiate_chat(
        receiver,
        message=initial_message,
        silent=False
    )
    
    # Monitor and manage the conversation
    while not any(agent.check_termination(msg) for agent, msg in chat_history[-2:] if msg):
        if monitor_conversation(chat_history):
            logging.info("Attempting to redirect conversation...")
            initiator.send(
                receiver,
                "Let's refocus on our main objectives and current progress.",
                silent=False
            )
        chat_history.append(response)
        
except Exception as e:
    logging.error(f"Error in conversation: {str(e)}")
    logging.info("Attempting to recover conversation...")
    initiator.send(
        receiver,
        "Let's resume our discussion from the last stable point.",
        silent=False
    )"""
    
    elif workflow_type == "Sequential":
        workflow += """
try:
    # Create a list of agents in sequence with error handling
    agents = [user_proxy, assistant_agent]  # Add more agents as needed
    
    # Add URL analysis agents if URLs are present
    if URLS:
        if any(url.startswith(('http://', 'https://')) for url in URLS):
            agents.append(web_researcher)
        if any(url.startswith('file:///') for url in URLS):
            agents.append(file_system_agent)

    # Create GroupChat with enhanced monitoring
    groupchat = CoordinatedGroupChat(
        agents=agents,
        messages=[f"Task: {TASK}\\n\\nGoals: {GOALS}\\n\\nURL Analysis: {str(url_content_cache)}"],
        max_round=5,
        speaker_selection_method="auto"
    )

    # Create manager with enhanced monitoring
    manager = CoordinatedManager(
        groupchat=groupchat,
        llm_config={{"config_list": config_list}},
        system_message="Monitor and guide the conversation. Ensure all agents contribute effectively."
    )

    # Start the sequential interaction with progress tracking
    progress["current_phase"] = "Initialization"
    manager.start()
    
except Exception as e:
    logging.error(f"Error in workflow execution: {str(e)}")
    if handle_error(e, "GroupChatManager", groupchat.error_count):
        logging.info("Restarting group chat with recovery...")
        manager.start()"""

    if "GroupChat" in agent_types:
        workflow += """
try:
    # Create coordinated group chat with all agents
    all_agents = [user_proxy, assistant_agent]  # Base agents
    
    # Add specialized agents based on URLs
    if URLS:
        if any(url.startswith(('http://', 'https://')) for url in URLS):
            all_agents.append(web_researcher)
        if any(url.startswith('file:///') for url in URLS):
            all_agents.append(file_system_agent)
    
    # Add other specialized agents
    if coder:
        all_agents.append(coder)
    if reviewer:
        all_agents.append(reviewer)

    coordinated_chat = CoordinatedGroupChat(
        agents=all_agents,
        messages=[f"Task: {TASK}\\n\\nGoals: {GOALS}\\n\\nURL Analysis: {str(url_content_cache)}"],
        max_round=10,
        speaker_selection_method="auto",
        allow_repeat_speaker=False
    )

    # Create coordinated manager
    coordinated_manager = CoordinatedManager(
        groupchat=coordinated_chat,
        llm_config={{"config_list": config_list}}
    )

    # Start the coordinated group chat with phase management
    progress["current_phase"] = "Planning"
    coordinated_manager.start()
    
except Exception as e:
    logging.error(f"Error in coordinated workflow: {str(e)}")
    if handle_error(e, "CoordinatedManager", coordinated_chat.error_count):
        logging.info("Restarting coordinated chat with recovery...")
        coordinated_manager.start()"""

    return workflow

def download_autogen_workflow(workflow: str) -> str:
    """
    Save the generated AutoGen workflow to a Python file.

    Args:
        workflow (str): The generated Python code for the AutoGen workflow

    Returns:
        str: The file path where the workflow is saved
    """
    try:
        file_path = "generated_workflow.py"
        with open(file_path, "w") as f:
            f.write(workflow)
        print(f"Workflow saved to {file_path}")
        return file_path
    except Exception as e:
        print(f"Error saving workflow: {e}")
        logging.error(f"Error saving workflow: {e}")
        return str(e)
