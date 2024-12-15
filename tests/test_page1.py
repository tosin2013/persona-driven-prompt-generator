import os
import json
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from page1 import create_agent_config_file, create_workflow_file, create_output_zip

@pytest.fixture
def mock_generate_prompt():
    with patch('page1.generate_prompt') as mock:
        yield mock

def test_create_agent_config_file():
    agent_name = "test_agent"
    persona_name = "test_persona"
    agent_config = {"key": "value"}
    base_path = Path(".")

    config_file = create_agent_config_file(agent_name, persona_name, agent_config, base_path)

    assert config_file.exists()
    with open(config_file, "r") as f:
        data = json.load(f)
    assert data == agent_config
    os.remove(config_file)

def test_create_workflow_file():
    workflow_config = {"workflow": "test"}
    base_path = Path(".")

    workflow_file = create_workflow_file(workflow_config, base_path)

    assert workflow_file.exists()
    with open(workflow_file, "r") as f:
        data = json.load(f)
    assert data == workflow_config
    os.remove(workflow_file)

def test_create_output_zip(mock_generate_prompt):
    task_details = {"task": "test", "goals": "test"}
    personas = ["persona1", "persona2"]
    knowledge_sources = ["source1", "source2"]
    conflict_strategy = "consensus"
    prior_decisions = []

    mock_generate_prompt.return_value = (
        {"persona1": {"key": "value1"}, "persona2": {"key": "value2"}},
        {"workflow": "test"},
        "test_agent"
    )

    zip_path = create_output_zip(
        task_details,
        personas,
        knowledge_sources,
        conflict_strategy,
        prior_decisions
    )

    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert len(zipf.namelist()) == 3  # 2 agent configs + 1 workflow
    os.remove(zip_path)
