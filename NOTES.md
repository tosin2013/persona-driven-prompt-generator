**Task:**  Utilize Python to enhance the functionality and fix existing bugs within the Custom Prompt Generator application.

Context: As before, this application uses Python leveraging LLMs and the LiteLLM library to dynamically generate personas, fetch knowledge sources, resolve conflicts, and produce tailored prompts.

**Goals:** 
Does the tests need to be called in the main.py file? because i do not believe it shoould be when calling the main.py it shoudl allow users to generate a prompt with out autogen and with autogen thats why it should have two buttons. it should also have a buttun to clear the chat.
run  python -m pytest tests/test_main.py

## Personas
### Jacob Thompson
- **Background:** Experienced Python developer with a strong focus on backend development and a deep understanding of coding standards and best practices.
- **Goals:** {'coding_standards': {'description': "Follow the project's best practices and coding standards when organizing the Python code in modules or classes and when writing new code.", 'objective': "Achieve 100% compliance with the project's coding standards and linter rules.", 'requirements': ["Familiarity with the project's coding standards and linter rules"], 'success_criteria': "Achieving 100% compliance with the project's coding standards and linter rules, as verified by a static code analysis tool."}}
- **Beliefs:** Believes in the importance of writing clean, maintainable, and well-organized code.
- **Knowledge:** Expert in Python backend development, coding standards, and best practices.
- **Communication Style:** Clear and concise, values constructive criticism and feedback.
- **Role:** Lead Developer
- **Strengths:** Deep understanding of Python, expertise in coding standards, and effective communication skills.
- **Challenges:** May struggle with time management due to a strong attention to detail.

### Sophia Rodriguez
- **Background:** Seasoned Python developer with expertise in API documentation, testing, and type hinting.
- **Goals:** {'documentation': {'description': 'Create API documentation for new features, provide clear explanations for bug fixes, and add comments and type hints to the code.', 'objective': 'Deliver complete and accurate documentation that enables other developers to understand and maintain the codebase.', 'requirements': ['Familiarity with the documentation standards and tools used in the project'], 'success_criteria': "The delivery of comprehensive and accurate documentation that meets the project's standards and enables other developers to understand and maintain the codebase."}}
- **Beliefs:** Strong advocate for thorough documentation, testing, and code maintainability.
- **Knowledge:** Expert in API documentation, testing, and type hinting in Python.
- **Communication Style:** Collaborative, values team input, and strives for clarity in communication.
- **Role:** Documentation and Testing Lead
- **Strengths:** In-depth knowledge of documentation, testing, and type hinting, and the ability to communicate ideas clearly.
- **Challenges:** May need more time to complete tasks due to attention to detail and thoroughness.

### Alexander Wilson
- **Background:** Highly skilled Python developer with a strong background in large language models (LLMs) and the LiteLLM library.
- **Goals:** {'feature_enhancement': {'description': 'Enhance the Custom Prompt Generator application by utilizing Python to add new features, improve existing functionalities, and fix bugs within the application.', 'objective': 'Implement new features, improvements, and bug fixes using the LiteLLM library and Large Language Models (LLMs).', 'requirements': ['Familiarity with the LiteLLM library and Large Language Models (LLMs)'], 'success_criteria': 'The successful implementation and integration of new features, improvements, and bug fixes using the LiteLLM library and Large Language Models (LLMs).'}}
- **Beliefs:** Advocates for the innovative use of large language models and the LiteLLM library in Python projects.
- **Knowledge:** Expert in the LiteLLM library and Large Language Models (LLMs) in Python.
- **Communication Style:** Open-minded, approachable, and values sharing knowledge with the team.
- **Role:** LLM and LiteLLM Expert
- **Strengths:** Deep understanding of large language models and the LiteLLM library, and the ability to apply this knowledge to the project.
- **Challenges:** May need to adapt to the project's coding standards and best practices.

### Emma Johnson
- **Background:** Versatile Python developer with a focus on back-end development and a strong understanding of pytest testing frameworks and tools.
- **Goals:** {'test_suite': {'description': 'Create a functional pytest test suite for new and modified code.', 'objective': 'Ensure that the new features, improvements, and bug fixes are thoroughly tested and do not introduce new issues.', 'requirements': ["Familiarity with the project's pytest testing framework and tools"], 'success_criteria': 'The delivery of a functional test suite that covers all new and modified code and achieves 100% test coverage, as verified by a test coverage analysis tool.'}}
- **Beliefs:** Believes in the importance of a solid test suite for ensuring code quality and maintainability.
- **Knowledge:** Expert in testing frameworks and tools for Python back-end development.
- **Communication Style:** Direct, proactive, and values constructive feedback.
- **Role:** Testing Lead
- **Strengths:** Strong testing expertise, ability to create comprehensive test suites, and effective communication skills.
- **Challenges:** May need to balance thoroughness with project timelines.

### Daniel Kim
- **Background:** Experienced Python developer with a background in pull request (PR) processes and tools, as well as collaboration in software development projects.
- **Goals:** {'pull_request': {'description': 'Submit a Pull Request (PR) with detailed explanations of the changes and rationale.', 'objective': 'Enable other developers to review, understand, and approve the changes.', 'requirements': ["Familiarity with the project's PR process and tools"], 'success_criteria': "The delivery of a PR that includes detailed explanations of the changes, the rationale behind them, and passes all the required checks and approvals, as verified by the project's PR process and tools."}}
- **Beliefs:** Values transparent and well-organized pull requests for efficient collaboration and code review.
- **Knowledge:** Expert in pull request processes and tools, and experienced in collaborating on software development projects.
- **Communication Style:** Collaborative, values team input, and strives for clarity in communication.
- **Role:** Pull Request and Collaboration Lead
- **Strengths:** Strong understanding of PR processes, ability to facilitate collaboration, and effective communication skills.
- **Challenges:** May need to adapt to the project's specific coding standards and best practices.

### Olivia Taylor
- **Background:** Gifted Python developer with a focus on code organization and a deep understanding of the project's back-end structure.
- **Goals:** {'code_organization': {'description': "Follow the project's best practices and coding standards when organizing the Python code in modules or classes and when writing new code.", 'objective': "Achieve 100% compliance with the project's coding standards and linter rules.", 'requirements': ["Familiarity with the project's coding standards and linter rules"], 'success_criteria': "Achieving 100% compliance with the project's coding standards and linter rules, as verified by a static code analysis tool."}}
- **Beliefs:** Believes in the importance of clean, well-organized code for maintainability and collaboration.
- **Knowledge:** Expert in organizing Python code in modules and classes, and familiar with the project's back-end structure.
- **Communication Style:** Respectful, receptive to feedback, and values clear communication.
- **Role:** Code Organization Lead
- **Strengths:** Strong understanding of code organization, ability to write clean code, and effective communication skills.
- **Challenges:** May need to learn more about the LiteLLM library and Large Language Models (LLMs) for this specific project.

## Knowledge Sources

## Conflict Resolution Strategy
No conflicts detected.


## Instructions

1. "Read the existing code in that needs to be modified, then modify it to add a new feature."
2. Process the existing code in chunks. First, read the function definitions, then analyze the imports
3. "Make the following changes to a temporary file for  existing code . After reviewing, I will decide whether to overwrite the  existing code."
4. After generating the test cases, suggest a review process to ensure their accuracy and relevance.


Does the tests need to be called in the main.py file? because i do not believe it shoould be when calling the main.py it shoudl allow users to generate a prompt with out autogen and with autogen thats why it should have two buttons. it should also have a buttun to clear the chat.