import logging
from typing import List, Dict, Any
import litellm
import json
import re
import os

# Get model name from environment variable, default to gpt-3.5-turbo if not set
MODEL_NAME = os.getenv("LITELLM_MODEL", "gpt-3.5-turbo")

def detect_task_domain(task_description: str) -> str:
    """Detect the domain of the task to generate appropriate personas."""
    try:
        response = litellm.completion(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": """Analyze the task description and determine its primary domain. Return ONLY ONE of these domains as a single word:
                    - SOFTWARE (for software development, programming, technical tasks)
                    - MARKETING (for marketing, advertising, branding tasks)
                    - HR (for human resources, recruitment, employee management)
                    - FINANCE (for financial, accounting, investment tasks)
                    - DESIGN (for UI/UX, graphic design, creative tasks)
                    - SALES (for sales, business development tasks)
                    - OPERATIONS (for operations, project management tasks)
                    - LEGAL (for legal, compliance tasks)
                    - RESEARCH (for research, analysis tasks)
                    - EDUCATION (for training, teaching tasks)
                    - CREATIVE (for writing, art, music, performance tasks)
                    - RELIGIOUS (for spiritual, religious, faith-based tasks)
                    - HEALTHCARE (for medical, patient care tasks) 
                    - TECHNOLOGY (for general tech use and troubleshooting)
                    - GOVERNMENT (for policy, politics, and public service tasks) 
                    - GAMING (for game development, esports, and gaming tasks)
                    - SOCIAL (for social impact, activism, and community tasks)  
                    - CULINARY (for culinary, food, and gastronomy tasks)"""
                },
                {
                    "role": "user",
                    "content": f"Task description: {task_description}"
                }
            ],
            temperature=0.3
        )
        domain = response.choices[0].message.content.strip().upper()
        logging.info(f"Detected task domain: {domain}")
        return domain
    except Exception as e:
        logging.error(f"Error detecting task domain: {e}")
        return "SOFTWARE"  # Default fallback

def generate_personas(task_details: Dict[str, Any], persona_count: int = 2) -> List[Dict[str, Any]]:
    """Generate a list of personas based on the task details and domain."""
    logging.debug(f"Generating {persona_count} personas for task: {task_details['task']}")
    
    # Detect the task domain
    domain = detect_task_domain(task_details['task'])
    
    try:
        domain_prompts = {
            "SOFTWARE": """Generate realistic personas for a software development task. Each persona should have software development expertise.""",
            "MARKETING": """Generate realistic personas for a marketing task. Each persona should have marketing, branding, or advertising expertise.""",
            "HR": """Generate realistic personas for a human resources task. Each persona should have HR, recruitment, or employee relations expertise.""",
            "FINANCE": """Generate realistic personas for a financial task. Each persona should have finance, accounting, or investment expertise.""",
            "DESIGN": """Generate realistic personas for a design task. Each persona should have UI/UX, graphic design, or creative expertise.""",
            "SALES": """Generate realistic personas for a sales task. Each persona should have sales, business development, or account management expertise.""",
            "OPERATIONS": """Generate realistic personas for an operations task. Each persona should have operations, project management, or process improvement expertise.""",
            "LEGAL": """Generate realistic personas for a legal task. Each persona should have legal, compliance, or regulatory expertise.""",
            "RESEARCH": """Generate realistic personas for a research task. Each persona should have research, analysis, or data science expertise.""",
            "EDUCATION": """Generate realistic personas for an educational task. Each persona should have teaching, training, or instructional design expertise.""",
            "CREATIVE": """Generate realistic personas for a creative task. Each persona should have expertise in areas like writing, art, music, performance, or other creative fields.""",
            "RELIGIOUS": """Generate realistic personas for a religious or spiritual task. Each persona should have expertise in religious studies, spiritual guidance, faith leadership, or interfaith dialogue.""",
            "HEALTHCARE": """Generate realistic personas for a healthcare task. Each persona should have expertise in medical care, patient care, or healthcare administration.""",
            "TECHNOLOGY": """Generate realistic personas for a technology task. Each persona should have expertise in general tech use, troubleshooting, or software development.""",
            "GOVERNMENT": """Generate realistic personas for a government task. Each persona should have expertise in policy, politics, or public service.""",
            "GAMING": """Generate realistic personas for a gaming task. Each persona should have expertise in game development, esports, or gaming.""",
            "SOCIAL": """Generate realistic personas for a social task. Each persona should have expertise in social impact, activism, or community building.""",
            "CULINARY": """Generate realistic personas for a culinary task. Each persona should have expertise in culinary arts, food preparation, or gastronomy."""
        }
        
        prompt = ""
        try:
            prompt = domain_prompts.get(domain, domain_prompts["SOFTWARE"])
        except Exception as e:
            logging.error(f"Error while selecting domain prompt: {str(e)}")
            prompt = domain_prompts["SOFTWARE"]  # Fallback to software domain if there's an error
        
        response = litellm.completion(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": f"""{prompt}
                    Each persona must have ALL of these fields (no exceptions):
                    1. A realistic full name (first and last name)
                    2. A detailed professional background relevant to the task domain
                    3. Specific goals related to the task
                    4. Clear beliefs about their field
                    5. Relevant domain knowledge and expertise
                    6. A distinct communication style that describes how they interact
                    
                    Return a JSON array of personas with EXACTLY these fields (no more, no less):
                    {{
                        "name": "Full Name",
                        "background": "Professional background",
                        "goals": "Specific goals",
                        "beliefs": "Core beliefs",
                        "knowledge": "Domain expertise",
                        "communication_style": "How they communicate (e.g., direct, diplomatic, analytical)"
                    }}
                    
                    Ensure EVERY persona has ALL fields filled out."""
                },
                {
                    "role": "user",
                    "content": f"Task: {task_details['task']}\nGenerate {persona_count} diverse personas with realistic conflicts and beliefs for this {domain.lower()} task."
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
        # Fallback personas based on domain
        domain_fallbacks = {
            "MARKETING": [
                ("Emily Rodriguez", "Senior Marketing Strategist"),
                ("Marcus Chen", "Digital Marketing Manager")
            ],
            "HR": [
                ("Sarah Thompson", "HR Director"),
                ("Michael Foster", "Talent Acquisition Manager")
            ],
            "FINANCE": [
                ("David Kumar", "Financial Analyst"),
                ("Jennifer Wu", "Investment Advisor")
            ],
            "DESIGN": [
                ("Alex Rivera", "UX Design Lead"),
                ("Sophie Anderson", "Creative Director")
            ],
            "SALES": [
                ("James Wilson", "Sales Director"),
                ("Maria Garcia", "Business Development Manager")
            ],
            "OPERATIONS": [
                ("Robert Taylor", "Operations Manager"),
                ("Lisa Patel", "Project Manager")
            ],
            "LEGAL": [
                ("William Chang", "Legal Counsel"),
                ("Rachel Martinez", "Compliance Officer")
            ],
            "RESEARCH": [
                ("Dr. Amanda Lee", "Research Analyst"),
                ("Dr. Thomas Brown", "Data Scientist")
            ],
            "EDUCATION": [
                ("Patricia Moore", "Instructional Designer"),
                ("Daniel Kim", "Training Specialist")
            ],
            "CREATIVE": [
                ("Isabella Martinez", "Creative Writing Director"),
                ("Nathan Wright", "Art Director"),
                ("Maya Patel", "Music Producer"),
                ("Jordan Lee", "Performance Artist")
            ],
            "RELIGIOUS": [
                ("Rev. David Cohen", "Interfaith Program Director"),
                ("Sister Grace Sullivan", "Spiritual Counselor"),
                ("Imam Ahmad Hassan", "Religious Education Director"),
                ("Rabbi Sarah Goldstein", "Community Outreach Coordinator")
            ],
            "SOFTWARE": [
                ("John Smith", "Senior Software Developer"),
                ("Sarah Johnson", "Technical Lead")
            ]
        }
        
        fallback_personas = domain_fallbacks.get(domain, domain_fallbacks["SOFTWARE"])
        return [
            {
                "name": name,
                "background": f"{title} with {10+i} years of experience",
                "goals": f"Deliver excellent results for {task_details['task']}",
                "beliefs": f"Quality and innovation in {domain.lower()} are essential",
                "knowledge": f"Expert in {domain.lower()} methodologies and best practices",
                "communication_style": "Professional and collaborative"
            } for i, (name, title) in enumerate(fallback_personas[:persona_count])
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
