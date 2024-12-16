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

def generate_autogen_workflow(personas: List[Dict[str, Any]], workflow_type: str = "Autonomous (Chat)", agent_types: List[str] = None) -> str:
    """
    Generate an AutoGen workflow based on the personas and configuration.

    Args:
        personas (List[Dict[str, Any]]): List of personas to convert into agents
        workflow_type (str): Type of workflow ("Autonomous (Chat)" or "Sequential")
        agent_types (List[str]): List of agent types to include

    Returns:
        str: Generated Python code for the AutoGen workflow
    """
    if agent_types is None:
        agent_types = ["Assistant Agent"]

    # Start with imports
    workflow = """from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import autogen

# Configure agents
config_list = [
    {
        'model': 'gpt-4',
        'api_key': 'your-api-key'  # Replace with your API key
    }
]
"""

    # Add agent definitions based on personas and types
    for i, persona in enumerate(personas):
        agent_name = persona["name"].replace(" ", "_").lower()
        
        if "User Proxy Agent" in agent_types:
            workflow += f"""
# User Proxy Agent for {persona['name']}
{agent_name}_proxy = UserProxyAgent(
    name="{agent_name}_proxy",
    system_message="{persona['background']}\\nGoals: {persona['goals']}\\nBeliefs: {persona['beliefs']}",
    human_input_mode="TERMINATE"
)"""

        if "Assistant Agent" in agent_types:
            workflow += f"""
# Assistant Agent for {persona['name']}
{agent_name}_assistant = AssistantAgent(
    name="{agent_name}_assistant",
    system_message="{persona['background']}\\nKnowledge: {persona['knowledge']}\\nCommunication Style: {persona['communication_style']}",
    llm_config={{"config_list": config_list}}
)"""

    # Add workflow-specific code
    if workflow_type == "Autonomous (Chat)":
        workflow += """

# Initialize chat between agents
initiator = user_proxy  # First agent
receiver = assistant_agent  # Second agent

# Start the conversation
initiator.initiate_chat(
    receiver,
    message="Let's work on the task together."
)"""
    
    elif workflow_type == "Sequential":
        workflow += """

# Create a list of agents in sequence
agents = [user_proxy, assistant_agent]  # Add more agents as needed

# Create GroupChat
groupchat = GroupChat(
    agents=agents,
    messages=[],
    max_round=5
)

# Create manager
manager = GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list})

# Start the sequential interaction
manager.start()"""

    if "GroupChat" in agent_types:
        workflow += """

# Create GroupChat with all agents
all_agents = [user_proxy, assistant_agent]  # Add all agents
groupchat = GroupChat(
    agents=all_agents,
    messages=[],
    max_round=10
)

# Create manager for group chat
manager = GroupChatManager(groupchat=groupchat, llm_config={"config_list": config_list})

# Start the group chat
manager.start()"""

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
