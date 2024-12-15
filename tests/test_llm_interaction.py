import unittest
from unittest.mock import patch, MagicMock
import os
from llm_interaction import configure_litellm, autochat, interact_with_llm, submit_prompt_to_llm, generate_persona_prompt, update_ui_with_message
import litellm

class TestLLMInteraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment variables."""
        os.environ["LITELLM_MODEL"] = "gpt-3.5-turbo"
        os.environ["LITELLM_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test_api_key"

    def setUp(self):
        """Set up test fixtures."""
        # Mock streamlit session state
        self.mock_session_state = MagicMock()
        self.mock_session_state.messages = []
        self.patcher = patch('streamlit.session_state', self.mock_session_state)
        self.patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.patcher.stop()

    def test_configure_litellm(self):
        """Test the configure_litellm function."""
        model = configure_litellm()
        self.assertEqual(model, "gpt-3.5-turbo")

    @patch('litellm.completion')
    def test_autochat(self, mock_completion):
        """Test the autochat function."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_completion.return_value = mock_response

        personas = [
            {"name": "Persona1", "emotional_tone": "neutral", "goals": "Test goal"}
        ]
        autochat(personas, 1)

        mock_completion.assert_called()

    @patch('litellm.completion')
    def test_interact_with_llm(self, mock_completion):
        """Test the interact_with_llm function."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        mock_completion.return_value = mock_response

        response = interact_with_llm("Test prompt")
        self.assertEqual(response, "Test response")

    @patch('litellm.completion')
    def test_submit_prompt_to_llm(self, mock_completion):
        """Test the submit_prompt_to_llm function."""
        mock_completion.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }

        response = submit_prompt_to_llm("Test prompt")
        self.assertEqual(response, "Test response")

    def test_generate_persona_prompt(self):
        """Test the generate_persona_prompt function."""
        persona = {
            "name": "Persona1",
            "emotional_tone": "neutral",
            "goals": "Test goal"
        }
        prompt = generate_persona_prompt(persona)
        self.assertEqual(prompt, "Persona1 (neutral): Test goal")

    def test_update_ui_with_message(self):
        """Test the update_ui_with_message function."""
        update_ui_with_message("Persona1", "Test message")
        self.assertEqual(
            self.mock_session_state.messages[-1],
            {"role": "system", "content": "Persona1: Test message"}
        )

    @patch('litellm.completion')
    def test_submit_prompt_to_llm_api_error(self, mock_completion):
        """Test the submit_prompt_to_llm function with an API error."""
        mock_completion.side_effect = litellm.exceptions.APIError(
            message="API Error",
            llm_provider="openai",
            model="gpt-3.5-turbo",
            status_code=500
        )

        response = submit_prompt_to_llm("Test prompt")
        self.assertEqual(response, "An API error occurred: litellm.APIError: API Error")

    @patch('litellm.completion')
    def test_submit_prompt_to_llm_authentication_error(self, mock_completion):
        """Test the submit_prompt_to_llm function with an authentication error."""
        mock_completion.side_effect = litellm.exceptions.AuthenticationError(
            message="Authentication Error",
            llm_provider="openai",
            model="gpt-3.5-turbo"
        )

        response = submit_prompt_to_llm("Test prompt")
        self.assertEqual(response, "An authentication error occurred: litellm.AuthenticationError: Authentication Error")

    @patch('litellm.completion')
    def test_submit_prompt_to_llm_rate_limit_error(self, mock_completion):
        """Test the submit_prompt_to_llm function with a rate limit error."""
        mock_completion.side_effect = litellm.exceptions.RateLimitError(
            message="Rate Limit Error",
            llm_provider="openai",
            model="gpt-3.5-turbo"
        )

        response = submit_prompt_to_llm("Test prompt")
        self.assertEqual(response, "A rate limit error occurred: litellm.RateLimitError: Rate Limit Error")

    @patch('litellm.completion')
    def test_submit_prompt_to_llm_unexpected_error(self, mock_completion):
        """Test the submit_prompt_to_llm function with an unexpected error."""
        mock_completion.side_effect = Exception("Unexpected Error")

        response = submit_prompt_to_llm("Test prompt")
        self.assertEqual(response, "An unexpected error occurred: Unexpected Error")

if __name__ == '__main__':
    unittest.main()
