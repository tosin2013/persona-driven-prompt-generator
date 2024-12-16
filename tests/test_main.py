import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from main import generate_personas_wrapper, fetch_knowledge_sources, resolve_conflicts, generate_prompt, save_prompt_to_file
from utils import get_user_input
import os
import json

# Mock data for testing
mock_task_details = {
    "task": "Test task",
    "goals": "Test goals",
    "reference_urls": ["http://example.com"]
}

mock_personas = [
    {
        "name": "Persona 1",
        "background": "Background for Persona 1",
        "goals": "Goals for Persona 1",
        "beliefs": "Beliefs for Persona 1",
        "knowledge": "Knowledge for Persona 1",
        "communication_style": "Communication style for Persona 1"
    }
]

mock_knowledge_sources = [
    {
        "title": "Test Source",
        "description": "Test description",
        "url": "http://test.com"
    }
]

mock_conflict_resolution = "Test conflict resolution"

@patch('streamlit.sidebar.text_area')
@patch('streamlit.sidebar.text_input')
def test_get_user_input(mock_text_input, mock_text_area):
    """
    Test the get_user_input function with proper Streamlit component mocking.
    """
    # Mock the Streamlit components
    mock_text_area.side_effect = ["Test task", "http://example.com\n"]
    mock_text_input.return_value = "Test goals"
    
    # Call the function
    user_input = get_user_input()
    
    # Verify the result
    assert user_input["task"] == "Test task"
    assert user_input["goals"] == "Test goals"
    assert user_input["reference_urls"] == ["http://example.com"]

@patch('main.configure_litellm')
def test_generate_personas_wrapper(mock_configure_litellm):
    """
    Test the generate_personas_wrapper function.
    """
    mock_configure_litellm.return_value = "dummy_model"
    personas = generate_personas_wrapper(mock_task_details)
    assert len(personas) == 2
    assert "name" in personas[0]

@patch('main.configure_litellm')
def test_fetch_knowledge_sources(mock_configure_litellm):
    """
    Test the fetch_knowledge_sources function.
    """
    mock_configure_litellm.return_value = "dummy_model"
    knowledge_sources = fetch_knowledge_sources(mock_task_details["task"])
    assert isinstance(knowledge_sources, list)

@patch('main.configure_litellm')
@patch('main.litellm.completion')
def test_resolve_conflicts(mock_completion, mock_configure_litellm):
    """
    Test the resolve_conflicts function.
    """
    mock_configure_litellm.return_value = "dummy_model"
    mock_completion.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="Test conflict resolution"))])
    conflict_resolution = resolve_conflicts(str(mock_personas), mock_task_details)
    assert conflict_resolution == "Test conflict resolution"

@patch('main.configure_litellm')
def test_generate_prompt(mock_configure_litellm):
    """
    Test the generate_prompt function.
    """
    mock_configure_litellm.return_value = "dummy_model"
    additional_context = "Additional test context"
    prompt = generate_prompt(
        mock_task_details,
        mock_personas,
        mock_knowledge_sources,
        mock_conflict_resolution,
        [],
        additional_context
    )
    assert "task" in prompt
    assert "personas" in prompt
    assert "knowledge_sources" in prompt
    assert "conflict_resolution" in prompt
    assert "memory" in prompt
    assert "instructions" in prompt

@patch('main.configure_litellm')
def test_save_prompt_to_file(mock_configure_litellm, tmp_path):
    """
    Test the save_prompt_to_file function using pytest's tmp_path fixture.
    """
    mock_configure_litellm.return_value = "dummy_model"
    file_format = "json"
    test_file = os.path.join(tmp_path, "test_prompt.json")
    
    # Save the prompt to a temporary file
    save_prompt_to_file(mock_task_details, file_format, output_path=test_file)
    
    # Read and verify the file contents
    with open(test_file, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data == mock_task_details
