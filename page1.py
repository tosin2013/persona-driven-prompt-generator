import os
import json
import zipfile
from pathlib import Path
from shared_functions import generate_prompt

def create_agent_config_file(agent_name: str, persona_name: str, agent_config: dict, base_path: Path) -> Path:
    """
    Create an agent config file in the agents directory.

    Args:
        agent_name (str): The name of the agent.
        persona_name (str): The name of the persona.
        agent_config (dict): The configuration data for the agent.
        base_path (Path): The base directory path where the agent directory will be created.

    Returns:
        Path: The path to the created agent config file.
    """
    agent_dir = base_path / "agent" / agent_name
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    config_file = agent_dir / f"agent_config_{persona_name}.json"
    with open(config_file, "w") as f:
        json.dump(agent_config, f, indent=4)
    return config_file

def create_workflow_file(workflow_config: dict, base_path: Path) -> Path:
    """
    Create the workflow.json file.

    Args:
        workflow_config (dict): The configuration data for the workflow.
        base_path (Path): The base directory path where the workflow file will be created.

    Returns:
        Path: The path to the created workflow file.
    """
    workflow_file = base_path / "agent" / "workflow.json"
    with open(workflow_file, "w") as f:
        json.dump(workflow_config, f, indent=4)
    return workflow_file

def create_output_zip(task_details: dict, personas: list, knowledge_sources: list, 
                     conflict_strategy: str, prior_decisions: list) -> Path:
    """
    Generate agent configs and workflow, save them to appropriate directory structure,
    and create a zip file containing all outputs.

    Args:
        task_details (dict): Details of the task.
        personas (list): List of personas.
        knowledge_sources (list): List of knowledge sources.
        conflict_strategy (str): Strategy for resolving conflicts.
        prior_decisions (list): List of prior decisions.

    Returns:
        Path: The path to the created zip file.
    """
    # Get configurations from generate_prompt
    agent_configs, workflow_config, agent_name = generate_prompt(
        task_details=task_details,
        personas=personas,
        knowledge_sources=knowledge_sources,
        conflict_strategy=conflict_strategy,
        prior_decisions=prior_decisions
    )
    
    # Create base directory for outputs
    base_path = Path(".")
    
    # Create agent config files
    config_files = []
    for persona_name, agent_config in agent_configs.items():
        config_file = create_agent_config_file(
            agent_name,
            persona_name,
            agent_config,
            base_path
        )
        config_files.append(config_file)
    
    # Create workflow config file
    workflow_file = create_workflow_file(workflow_config, base_path)
    
    # Create zip file
    zip_path = base_path / f"{agent_name}_output.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        # Add agent config files
        for config_file in config_files:
            arcname = config_file.relative_to(base_path)
            zipf.write(config_file, arcname=arcname)
        
        # Add workflow config file
        arcname = workflow_file.relative_to(base_path)
        zipf.write(workflow_file, arcname=arcname)
    
    return zip_path
    

if __name__ == "__main__":
    # Example usage
    task_details = {
        "task": "Example task",
        "goals": "Example goals"
    }
    personas = []  # Add your personas here
    knowledge_sources = []  # Add your knowledge sources here
    conflict_strategy = "consensus"
    prior_decisions = []
    
    zip_path = create_output_zip(
        task_details,
        personas,
        knowledge_sources,
        conflict_strategy,
        prior_decisions
    )
    print(f"Created zip file at: {zip_path}")
