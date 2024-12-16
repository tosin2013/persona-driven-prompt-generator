import logging
from typing import List, Dict, Any
import litellm
import json

def generate_personas(task_details: Dict[str, Any], persona_count: int = 2) -> List[Dict[str, Any]]:
    """Generate a list of personas based on the task details."""
    logging.debug(f"Generating {persona_count} personas for task: {task_details['task']}")
    
    try:
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """Generate realistic personas for a software development task. Each persona must have:
                    1. A realistic full name (first and last name)
                    2. A detailed professional background in tech/software
                    3. Specific goals related to the task
                    4. Clear beliefs about software development
                    5. Relevant technical knowledge
                    6. A distinct communication style
                    
                    Return ONLY a JSON array of personas with these exact fields:
                    {
                        "name": "Full Name",
                        "background": "Professional background",
                        "goals": "Specific goals",
                        "beliefs": "Core beliefs",
                        "knowledge": "Technical expertise",
                        "communication_style": "Communication style"
                    }"""
                },
                {
                    "role": "user",
                    "content": f"Task: {task_details['task']}\nGenerate {persona_count} distinct personas with realistic characteristics."
                }
            ],
            temperature=0.7
        )
        
        personas_content = response.choices[0].message.content.strip()
        # Extract JSON array if wrapped in other text
        json_start = personas_content.find('[')
        json_end = personas_content.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            personas_content = personas_content[json_start:json_end]
        
        personas = json.loads(personas_content)
        return personas
    except Exception as e:
        logging.error(f"Error generating personas: {e}")
        # Fallback to basic persona generation with realistic names
        return [
            {
                "name": f"{'John Smith' if i == 0 else 'Sarah Johnson' if i == 1 else f'Developer {i+1}'}",
                "background": f"Senior Software Developer with {10+i} years of experience",
                "goals": f"Deliver high-quality solutions for {task_details['task']}",
                "beliefs": "Code quality and maintainability are paramount",
                "knowledge": f"Expert in relevant technologies for task {i+1}",
                "communication_style": "Professional and detailed"
            } for i in range(persona_count)
        ]

def generate_initial_conversation(personas: List[Dict[str, Any]]) -> str:
    """
    Generate an initial conversation based on the personas.

    Args:
        personas (List[Dict[str, Any]]): List of personas.

    Returns:
        str: Initial conversation text.
    """
    logging.debug("Generating initial conversation for personas")
    conversation = "\n".join([
        f"{persona['name']}: Hello, I am {persona['name']}. My background is {persona['background']}. I aim to achieve {persona['goals']}."
        for persona in personas
    ])
    return conversation

def edit_persona_tones(personas: List[Dict[str, Any]], tone_adjustments: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Edit the tones of the personas based on the provided adjustments.

    Args:
        personas (List[Dict[str, Any]]): List of personas.
        tone_adjustments (Dict[str, str]): Adjustments to the tones of the personas.

    Returns:
        List[Dict[str, Any]]: Updated list of personas with adjusted tones.
    """
    logging.debug("Editing persona tones based on adjustments")
    for persona in personas:
        if persona['name'] in tone_adjustments:
            persona['communication_style'] = tone_adjustments[persona['name']]
    return personas

def generate_personas_wrapper(task_details: Dict[str, Any], persona_count: int = 2) -> List[Dict[str, Any]]:
    """
    Wrapper function to generate personas based on task details.

    Args:
        task_details (Dict[str, Any]): Details of the task including task description, goals, and reference URLs.
        persona_count (int): Number of personas to generate.

    Returns:
        List[Dict[str, Any]]: A list of personas with details such as background, goals, beliefs, knowledge, and communication style.
    """
    return generate_personas(task_details, persona_count)
