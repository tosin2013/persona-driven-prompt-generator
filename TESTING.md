# Testing Guide

This document explains how to run tests for the Persona-Driven Prompt Generator project.

## Prerequisites

Before running the tests, make sure you have:

1. Python 3.9+ installed
2. The following environment variables set:
   ```bash
   LITELLM_MODEL=gpt-3.5-turbo
   LITELLM_PROVIDER=openai
   OPENAI_API_KEY=your_api_key
   ```

## Installing Test Dependencies

Install the required test dependencies:

```bash
pip install pytest pytest-cov
```

## Running Tests

### Run All Tests

To run all tests:

```bash
python -m pytest
```

### Run Tests with Verbosity

For more detailed test output:

```bash
python -m pytest -v
```

### Run Specific Test Files

To run tests from a specific file:

```bash
python -m pytest tests/test_llm_interaction.py
python -m pytest tests/test_main.py
python -m pytest tests/test_page1.py
```

### Run Tests with Coverage Report

To generate a test coverage report:

```bash
python -m pytest --cov=.
```

For a more detailed coverage report:

```bash
python -m pytest --cov=. --cov-report=html
```

This will create a `htmlcov` directory with an HTML coverage report.

## Test Structure

The test suite is organized as follows:

- `tests/test_llm_interaction.py`: Tests for LLM interaction functionality
  - Tests basic LLM configuration
  - Tests prompt generation and submission
  - Tests error handling (API errors, authentication, rate limits)
  - Tests UI message updates

## Writing New Tests

When adding new tests:

1. Create test files in the `tests` directory
2. Follow the naming convention: `test_*.py`
3. Use descriptive test names that explain what is being tested
4. Include appropriate assertions and error cases
5. Mock external dependencies (e.g., LiteLLM, Streamlit)

Example test structure:

```python
class TestYourFeature(unittest.TestCase):
    def setUp(self):
        # Set up test environment
        pass

    def test_specific_functionality(self):
        # Test implementation
        pass

    def tearDown(self):
        # Clean up after tests
        pass
```

## Troubleshooting

Common issues and solutions:

1. **Missing Environment Variables**
   - Ensure all required environment variables are set
   - Use a `.env` file for local development

2. **Import Errors**
   - Make sure all dependencies are installed
   - Check your Python path includes the project root

3. **Mock Objects**
   - Verify mock objects match the expected interface
   - Include all required parameters in mock responses

## Continuous Integration

Tests are automatically run on:
- Pull request creation
- Push to main branch
- Daily scheduled runs

For CI/CD related issues, check the GitHub Actions workflow logs.
