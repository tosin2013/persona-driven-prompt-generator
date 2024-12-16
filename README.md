# Custom Prompt Generator

## Overview
The Custom Prompt Generator is a Python application that leverages Large Language Models (LLMs) and the LiteLLM library to dynamically generate personas, fetch knowledge sources, resolve conflicts, and produce tailored prompts. This application is designed to assist in various software development tasks by providing context-aware prompts based on user input and predefined personas.

## Features
- **Persona Generation**: Automatically generate personas based on user input and task goals.
- **Knowledge Source Fetching**: Fetch relevant knowledge sources using the LiteLLM library.
- **Conflict Resolution**: Resolve conflicts among personas to ensure coherent and fair task execution.
- **Prompt Generation**: Generate tailored prompts based on personas, knowledge sources, and conflict resolutions.
- **AutoGen Workflow**: Generate and download AutoGen workflow codes for personas, separating them as agents with specific configurations.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/custom-prompt-generator.git
   cd custom-prompt-generator
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the environment variables for LiteLLM:
   ```bash
   export LITELLM_MODEL="your-model-name"
   export LITELLM_PROVIDER="your-provider"
   export OPENAI_API_KEY="your-api-key"
   ```

4. Run the application:
   ```bash
   streamlit run main.py
   ```

## Usage
1. Open the application in your browser.
2. Enter the task description and goals in the sidebar.
3. Optionally, provide URLs for reference.
4. The application will generate personas, fetch knowledge sources, resolve conflicts, and generate a tailored prompt.
5. The generated prompt can be saved to a file in JSON format.
6. The AutoGen workflow codes for the personas can be generated and downloaded.

## File Structure
- `main.py`: The main entry point of the application.
- `llm_interaction.py`: Contains functions for interacting with the LiteLLM library.
- `persona_management.py`: Contains functions for generating and managing personas.
- `database.py`: Contains functions for interacting with the database.
- `search.py`: Contains functions for fetching knowledge sources.
- `utils.py`: Contains utility functions.
- `tests/`: Contains test files for the application.

## Contributing
Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for details on how to contribute to this project.

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments
- Thanks to the LiteLLM team for providing the library.
- Thanks to the Streamlit team for the awesome framework.
