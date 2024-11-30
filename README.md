# Persona-Driven Prompt Generator

Welcome to the **Persona-Driven Prompt Generator**! This application allows you to create customized prompts by generating personas and knowledge sources based on a task description and goals you provide. It leverages Large Language Models (LLMs) via the [LiteLLM](https://github.com/litellm/litellm) library to dynamically generate personas, fetch relevant knowledge sources, resolve conflicts among personas, and produce a comprehensive prompt tailored to your needs.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
  - [Using the Streamlit Interface](#using-the-streamlit-interface)
- [Saving the Generated Prompt](#saving-the-generated-prompt)
- [Example](#example)
- [Supported LLM Providers](#supported-llm-providers)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Dynamic Persona Generation**: Create diverse personas based on your task description.
- **Knowledge Source Fetching**: Generate a list of relevant knowledge sources.
- **Conflict Resolution**: Automatically resolve conflicts among personas.
- **Prompt Generation**: Compile all inputs into a comprehensive prompt.
- **Streamlit Interface**: User-friendly web interface for easy interaction.
- **Flexible Output**: Save the generated prompt in JSON or YAML format.

## Prerequisites

- Python 3.7 or higher
- An API key from one of the supported LLM providers (e.g., OpenAI, Groq, DeepSeek, Hugging Face)
- Internet connection (to interact with the LLM APIs)

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/tosin2013/persona-driven-prompt-generator.git
   cd persona-driven-prompt-generator
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Required Packages**

   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Vector Database**
   ```bash
   ./setup_database.sh
   ```

## Configuration

To configure LiteLLM effectively, you need to set specific environment variables tailored to your chosen LLM provider. Below are examples for each supported provider:

### OpenAI Example

```bash
export LITELLM_MODEL="gpt-3.5-turbo"
export LITELLM_PROVIDER="openai"
export OPENAI_API_KEY="your-openai-api-key"
```

In this configuration, `LITELLM_MODEL` specifies the model name, `LITELLM_PROVIDER` indicates the provider, and `OPENAI_API_KEY` is your unique API key for authentication.

### Groq Example

```bash
export LITELLM_MODEL="groq-model-name"
export LITELLM_PROVIDER="groq"
export GROQ_API_KEY="your-groq-api-key"
```

Replace `groq-model-name` with the specific model you intend to use and `your-groq-api-key` with your Groq API key.

### DeepSeek Example

```bash
export LITELLM_MODEL="deepseek-model-name"
export LITELLM_PROVIDER="deepseek"
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

Ensure you replace `deepseek-model-name` with your chosen model and `your-deepseek-api-key` with the appropriate API key.

### Hugging Face Example

```bash
export LITELLM_MODEL="huggingface/transformer-model"
export LITELLM_PROVIDER="huggingface"
export HUGGINGFACE_API_KEY="your-huggingface-api-key"
```

Here, `huggingface/transformer-model` should be replaced with the specific model from Hugging Face, and `your-huggingface-api-key` with your API key.

### Ollama Example

```bash
export LITELLM_MODEL="ollama/llama2"
export LITELLM_PROVIDER="ollama"
export LITELLM_API_BASE="http://localhost:11434"
export OLLAMA_API_KEY="your-ollama-api-key"
```

For Ollama, set `LITELLM_API_BASE` to the base URL where the Ollama service is running, typically `http://localhost:11434`, and provide your Ollama API key.

**Note:** Replace placeholder values (e.g., `your-openai-api-key`) with your actual API keys. For enhanced security, consider using a `.env` file to manage these variables. Ensure that the `LITELLM_MODEL` corresponds to a model supported by your specified provider.

For more detailed information, refer to the [LiteLLM documentation](https://docs.litellm.ai/docs/). 

---

## Usage

### Running the Application

Start the Streamlit application by running:

```bash
streamlit run persona_testing.py
```

> **Note**: Ensure that the filename `persona_testing.py` matches the name of your Python script containing the code.

### Using the Streamlit Interface

Once the application is running, it will open in your default web browser at `http://localhost:8501`. You can also access it on any other machine on the same network using `http://your-ip-address:8501`.

#### Steps:

1. **Describe the Task**

   - Enter a detailed description of the task or problem domain you want to generate a prompt for.

2. **Specify Key Goals**

   - Input the key goals for this task (e.g., efficiency, creativity).

3. **Select LLM Provider**

   - Choose your preferred LLM provider from the dropdown menu (`openai`, `groq`, `deepseek`, `huggingface`).

4. **Enter Model Name**

   - Provide the name of the model you wish to use (e.g., `gpt-3.5-turbo` for OpenAI).

5. **Enter API Key**

   - Input your API key associated with the selected LLM provider.

6. **Select Number of Personas**

   - Use the slider to select how many personas you would like to include (1 to 5).

7. **Generate Prompt**

   - Click the "Generate Prompt" button to start the process.

8. **View Generated Prompt**

   - The generated prompt will be displayed in the "Generated Prompt" section.

9. **Save the Prompt (Optional)**

   - If you wish to save the prompt, check the "Save the prompt to a file" option.
   - Select the desired file format (`json` or `yaml`).
   - The prompt will be saved to the corresponding file in the application directory.

---

## Saving the Generated Prompt

The application allows you to save the generated prompt in either JSON or YAML format.

1. **Enable Saving**

   - Check the "Save the prompt to a file" checkbox in the Streamlit interface.

2. **Select File Format**

   - Choose between `json` or `yaml` from the dropdown menu.

3. **Save Location**

   - The prompt will be saved in the application directory as `generated_prompt.json` or `generated_prompt.yaml`.

---

## Example

### Scenario

You want to generate a prompt for a task that involves developing a marketing strategy for a new eco-friendly product, focusing on creativity and audience engagement.

### Steps

1. **Task Description**

   - "Develop a marketing strategy for a new eco-friendly product."

2. **Key Goals**

   - "Creativity, audience engagement."

3. **LLM Provider**

   - Select `openai`.

4. **Model Name**

   - Enter `gpt-3.5-turbo`.

5. **API Key**

   - Enter your OpenAI API key.

6. **Number of Personas**

   - Select `3`.

7. **Generate Prompt**

   - Click "Generate Prompt".

### Output

```json
{
  "task": "Develop a marketing strategy for a new eco-friendly product.",
  "personas": ["Alex", "Jordan", "Taylor"],
  "knowledge_sources": ["Green Marketing Strategies", "Consumer Engagement Techniques", "Creative Advertising Case Studies"],
  "conflict_resolution": "Prioritize environmental impact and consumer connection by balancing innovative ideas with proven engagement methods.",
  "instructions": "Generate outputs for the task 'Develop a marketing strategy for a new eco-friendly product.' by incorporating the perspectives of Alex, Jordan, Taylor. Use knowledge from Green Marketing Strategies, Consumer Engagement Techniques, Creative Advertising Case Studies, and resolve conflicts using Prioritize environmental impact and consumer connection by balancing innovative ideas with proven engagement methods."
}
```

---

## Supported LLM Providers

The application supports the following LLM providers via LiteLLM:

- **OpenAI**
  - Requires `OPENAI_API_KEY`.
- **Groq**
  - Requires `GROQ_API_KEY`.
- **DeepSeek**
  - Requires `DEEPSEEK_API_KEY`.
- **Hugging Face**
  - Requires `HUGGINGFACE_API_KEY`.

> **Note**: Ensure you have valid API keys and necessary permissions to use the services.

---

## Troubleshooting

- **Empty Responses from LiteLLM**

  - If you receive empty responses or errors during persona or knowledge source generation, check your API key and network connection.
  - Ensure that your environment variables are correctly set.

- **Unsupported Provider**

  - If you select an unsupported provider, the application will display an error message.
  - Refer to the [Supported LLM Providers](#supported-llm-providers) section for valid options.

- **JSON Parsing Errors**

  - Occasionally, the LLM may return malformed JSON.
  - If this occurs, try increasing the `temperature` parameter or adjusting your input.

- **Environment Variables Not Set**

  - Ensure all required environment variables are set before running the application.
  - Missing variables will result in `ValueError` exceptions.

---

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**

   - Click the "Fork" button at the top right corner of the repository page.

2. **Create a New Branch**

   - Create a new branch for your feature or bug fix:

     ```bash
     git checkout -b feature/your-feature-name
     ```

3. **Make Changes**

   - Implement your feature or bug fix.

4. **Commit Changes**

   - Commit your changes with a descriptive message:

     ```bash
     git commit -am "Add new feature for XYZ"
     ```

5. **Push to Your Fork**

   - Push your changes to your forked repository:

     ```bash
     git push origin feature/your-feature-name
     ```

6. **Submit a Pull Request**

   - Open a pull request against the main repository.

---

## License

This project is licensed under the MIT License.

---

Thank you for using the Persona-Driven Prompt Generator! If you encounter any issues or have suggestions, please feel free to open an issue or submit a pull request.