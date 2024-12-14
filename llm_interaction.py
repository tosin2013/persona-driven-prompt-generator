import os
import logging
import litellm
import streamlit as st
import random
import time

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
        litellm.api_key = api_key  # Set the API key directly for OpenAI
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
        litellm.api_key = api_key  # Correctly set the API key for Huggingface
    elif provider == "ollama":
        api_key = os.getenv("OLLAMA_API_KEY")
        if not api_key:
            raise ValueError("OLLAMA_API_KEY environment variable not set")
        # Set the API key directly for OLLAMA
        litellm.api_key = api_key
    elif provider == "mistral":
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable not set")
        # Set the API key directly for Mistral
        litellm.api_key = api_key
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return model

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

def interact_with_llm(prompt: str) -> str:
    """
    Interact with the LLM and return the response.

    Args:
        prompt (str): The prompt to send to the LLM.

    Returns:
        str: The response from the LLM.
    """
    model = configure_litellm()
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

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
        response = litellm.completion(
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
