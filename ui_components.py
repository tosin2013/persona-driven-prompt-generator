"""
UI Components Module for the Persona-Driven Prompt Generator.

This module contains reusable UI components and helper functions for the Streamlit interface.
"""

from typing import Dict, Any, List, Optional
import streamlit as st
import json
import yaml
from dataclasses import dataclass

@dataclass
class UIConfig:
    """Configuration class for UI elements."""
    button_counter: int = 0
    default_file_format: str = "json"
    supported_formats: List[str] = None

    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ["json", "yaml"]

def create_download_buttons(
    prompt: Dict[str, Any],
    markdown_content: str,
    button_counter: int,
    col1: st.columns,
    col2: st.columns
) -> None:
    """
    Creates download buttons for different file formats.
    
    Args:
        prompt (Dict[str, Any]): The prompt data to be downloaded
        markdown_content (str): The markdown content to be downloaded
        button_counter (int): Counter for generating unique keys
        col1 (st.columns): First column for buttons
        col2 (st.columns): Second column for buttons
    """
    # Column 1: Copy to Markdown
    with col1:
        st.download_button(
            label="Copy to Markdown",
            data=markdown_content,
            file_name="prompt.md",
            mime="text/markdown",
            help="Click to copy the content in markdown format",
            key=f"download_markdown_{button_counter}"
        )
        with st.expander("View Markdown"):
            st.code(markdown_content, language="markdown")

    # Column 2: Download options
    with col2:
        file_format = st.selectbox(
            "Choose file format:", 
            ["json", "yaml"],
            key=f"file_format_selectbox_{button_counter}"
        )
        if file_format == "json":
            st.download_button(
                label="Download JSON",
                data=json.dumps(prompt, indent=4),
                file_name="prompt.json",
                mime="application/json",
                key=f"download_json_{button_counter}"
            )
        else:
            yaml_content = yaml.dump(prompt, default_flow_style=False)
            st.download_button(
                label="Copy to YAML",
                data=yaml_content,
                file_name="prompt.yaml",
                mime="text/yaml",
                key=f"download_yaml_{button_counter}"
            )

def display_persona_details(
    persona: Dict[str, Any],
    expanded: bool = True
) -> None:
    """
    Displays detailed information about a persona in an expander.
    
    Args:
        persona (Dict[str, Any]): The persona data to display
        expanded (bool, optional): Whether the expander should be initially expanded. Defaults to True.
    """
    with st.expander(f" {persona['name']}", expanded=expanded):
        st.markdown(f"**Background:** {persona['background']}")
        st.markdown(f"**Goals:** {persona['goals']}")
        st.markdown(f"**Beliefs:** {persona['beliefs']}")
        st.markdown(f"**Knowledge:** {persona['knowledge']}")
        st.markdown(f"**Communication Style:** {persona['communication_style']}")
        st.markdown(f"**Role:** {persona['role']}")
        st.markdown(f"**Strengths:** {persona['strengths']}")
        st.markdown(f"**Challenges:** {persona['challenges']}")

def display_knowledge_sources(
    knowledge_sources: List[Dict[str, str]]
) -> str:
    """
    Formats and displays knowledge sources.
    
    Args:
        knowledge_sources (List[Dict[str, str]]): List of knowledge sources to display
        
    Returns:
        str: Formatted markdown string of knowledge sources
    """
    formatted_sources = "\n".join([
        f"- [{source['title']}]({source['url']})"
        for source in knowledge_sources
    ])
    st.markdown("### Knowledge Sources")
    st.markdown(formatted_sources if formatted_sources else "No knowledge sources provided")
    return formatted_sources

def create_markdown_content(
    prompt: Dict[str, Any],
    personas: List[Dict[str, Any]],
    knowledge_sources: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Creates markdown content from prompt data.
    
    Args:
        prompt (Dict[str, Any]): The prompt data
        personas (List[Dict[str, Any]]): List of personas
        knowledge_sources (Optional[List[Dict[str, str]]]): List of knowledge sources
        
    Returns:
        str: Generated markdown content
    """
    content = [
        "# Generated Prompt\n",
        "## Original Task Details\n",
        f"**Task:** {prompt.get('original_task', 'N/A')}\n",
        f"**Goals:** {prompt.get('original_goals', 'N/A')}\n\n",
        "## Enhanced Task Details\n",
        f"**Task:** {prompt['task']}\n",
        f"**Goals:** {prompt['goals']}\n\n",
        "## Personas\n"
    ]
    
    for persona in personas:
        content.extend([
            f"### {persona['name']}\n",
            f"- **Background:** {persona['background']}\n",
            f"- **Goals:** {persona['goals']}\n",
            f"- **Beliefs:** {persona['beliefs']}\n",
            f"- **Knowledge:** {persona['knowledge']}\n",
            f"- **Communication Style:** {persona['communication_style']}\n",
            f"- **Role:** {persona['role']}\n",
            f"- **Strengths:** {persona['strengths']}\n",
            f"- **Challenges:** {persona['challenges']}\n\n"
        ])
    
    if knowledge_sources:
        content.append("## Knowledge Sources\n")
        for source in knowledge_sources:
            content.append(f"- [{source['title']}]({source['url']})\n")
    
    content.extend([
        f"\n## Conflict Resolution Strategy\n{prompt['conflict_resolution']}\n",
        f"\n## Instructions\n{prompt['instructions']}\n"
    ])
    
    return "".join(content)
