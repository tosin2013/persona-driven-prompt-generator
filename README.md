# Custom Prompt Generator

## Overview
The Custom Prompt Generator is a Python application that leverages Large Language Models (LLMs) and the LiteLLM library to dynamically generate personas, fetch knowledge sources, resolve conflicts, and produce tailored prompts. This application is designed to assist in various software development tasks by providing context-aware prompts based on user input and predefined personas.

## Features
- **Dynamic Persona Generation**: Create realistic personas with human-like names, backgrounds, and expertise.
- **Flexible Persona Count**: Generate 1-10 personas based on your needs.
- **Knowledge Source Fetching**: Fetch relevant knowledge sources using the LiteLLM library.
- **Conflict Resolution**: Resolve conflicts among personas to ensure coherent and fair task execution.
- **Prompt Generation**: Generate tailored prompts based on personas, knowledge sources, and conflict resolutions.
- **AutoGen Integration**:
  - Choose between Autonomous (Chat) and Sequential workflows
  - Configure different agent types (User Proxy, Assistant, GroupChat)
  - Generate executable Python code for AutoGen workflows
- **Export Options**: 
  - Export prompts in Markdown format
  - Copy generated content directly from the UI
  - Download AutoGen workflow as Python file

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
1. Open the application in your browser
2. In the sidebar:
   - Enter the task description and goals
   - Select the number of personas (1-10)
   - Configure AutoGen settings (if using AutoGen)
3. Choose your generation method:
   - "Generate (No AutoGen)" for standard prompts
   - "Generate (With AutoGen)" for AutoGen workflows
4. View and interact with:
   - Generated personas with realistic details
   - Knowledge sources and conflict resolutions
   - Markdown-formatted output
   - AutoGen workflow code
5. Export or copy your generated content as needed

## AutoGen Workflow Types
1. **Autonomous (Chat)**
   - Creates a chat-based interaction between agents
   - Suitable for collaborative problem-solving
   - Includes initiator and receiver agents

2. **Sequential**
   - Creates a step-by-step workflow
   - Agents execute in a predefined order
   - Better for structured tasks

## Agent Types
- **User Proxy Agent**: Represents the user and executes code
- **Assistant Agent**: Plans and generates code to solve tasks
- **GroupChat**: Manages interactions between multiple agents

## File Structure
- `main.py`: Main application with UI and core logic
- `llm_interaction.py`: LLM integration and AutoGen workflow generation
- `persona_management.py`: Persona generation and management
- `database.py`: Database interactions
- `search.py`: Knowledge source fetching
- `utils.py`: Utility functions

## Contributing
Contributions are welcome! Please read our contributing guidelines and submit pull requests for any enhancements.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
