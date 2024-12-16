import pytest
from unittest.mock import patch, MagicMock
from llm_interaction import configure_litellm, fetch_knowledge_sources, submit_prompt_to_llm

@pytest.fixture
def mock_litellm():
    with patch('llm_interaction.litellm') as mock:
        yield mock

def test_configure_litellm(mock_litellm):
    mock_litellm.api_key = None
    with patch('os.getenv', side_effect={'LITELLM_MODEL': 'gpt-3.5-turbo', 'OPENAI_API_KEY': 'test_api_key'}.get):
        model = configure_litellm()
        assert model == 'gpt-3.5-turbo'
        assert mock_litellm.api_key == 'test_api_key'

def test_fetch_knowledge_sources(mock_litellm):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '[{"title": "Test Source", "description": "Test Description", "url": "http://test.com"}]'
    mock_litellm.completion.return_value = mock_response

    with patch('os.getenv', side_effect={'LITELLM_MODEL': 'gpt-3.5-turbo', 'OPENAI_API_KEY': 'test_api_key'}.get):
        sources = fetch_knowledge_sources("Test Task")
        assert len(sources) == 1
        assert sources[0]['title'] == 'Test Source'

def test_submit_prompt_to_llm(mock_litellm):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = 'Test Response'
    mock_litellm.completion.return_value = mock_response

    with patch('os.getenv', side_effect={'LITELLM_MODEL': 'gpt-3.5-turbo', 'OPENAI_API_KEY': 'test_api_key'}.get):
        response = submit_prompt_to_llm("Test Prompt")
        assert response['content'] == 'Test Response'
        assert response['metadata']['model'] == 'gpt-3.5-turbo'
        assert response['metadata']['temperature'] == 0.7
