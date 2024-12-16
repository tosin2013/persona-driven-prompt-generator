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

def generate_autogen_workflow(task: str) -> Dict[str, Any]:
    """
    Generate an auto-generated workflow based on the provided task using the LiteLLM library.

    Args:
        task (str): The task description.

    Returns:
        Dict[str, Any]: The auto-generated workflow, including the generated content and other metadata.
    """
    model = configure_litellm()

    logging.debug(f"Generating auto-generated workflow for task: {task}")

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You will be provided with a task. "
                        "Generate an auto-generated workflow in JSON format ONLY, without any additional text or explanations. "
                        "The workflow should include the following fields: steps, description, and metadata."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Task: {task}. Generate an auto-generated workflow for this task. "
                        "Return the workflow as a JSON object ONLY, without any additional text or explanations."
                    )
                }
            ],
            temperature=0.7
        )
        workflow_content = response.choices[0].message.content.strip()
        if not workflow_content:
            raise ValueError("Received empty response from LiteLLM")
        logging.debug(f"Workflow content received: {workflow_content}")

        # Extract JSON object from the response
        json_match = re.search(r'({.*})', workflow_content, re.DOTALL)
        if json_match:
            workflow_json = json.loads(json_match.group(1))
        else:
            raise ValueError("Could not find valid JSON object in response")

        print("Auto-generated workflow generated:")
        print(json.dumps(workflow_json, indent=4))

        return workflow_json
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        logging.error(f"JSON parsing error: {e}")
        return {
            "error": str(e)
        }
    except Exception as e:
        print(f"Error generating auto-generated workflow: {e}")
        logging.error(f"Error generating auto-generated workflow: {e}")
        return {
            "error": str(e)
        }

def download_autogen_workflow(workflow: Dict[str, Any]) -> str:
    """
    Download the auto-generated workflow and save it to a file.

    Args:
        workflow (Dict[str, Any]): The auto-generated workflow.

    Returns:
        str: The file path where the workflow is saved.
    """
    try:
        # Save the workflow to a JSON file
        file_path = "autogen_workflow.json"
        with open(file_path, "w") as file:
            json.dump(workflow, file, indent=4)
        
        print(f"Auto-generated workflow saved to {file_path}")
        return file_path
    except Exception as e:
        print(f"Error saving auto-generated workflow: {e}")
        logging.error(f"Error saving auto-generated workflow: {e}")
        return ""
