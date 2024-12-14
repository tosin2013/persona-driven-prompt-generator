from typing import List, Dict, Any
import json
import logging
import litellm
import re
from utils import configure_litellm

def enhance_task_description(task: str, goals: str) -> Dict[str, str]:
    """
    Enhance the task description and goals using LLM to make them more detailed and structured.
    
    Args:
        task (str): Original task description
        goals (str): Original goals
        
    Returns:
        Dict[str, str]: Enhanced task description and goals
    """
    model = configure_litellm()
    
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert in task analysis and requirements engineering. "
                    "Your role is to enhance and structure task descriptions to make them more comprehensive and actionable. "
                    "For each task, you should:\n"
                    "1. Clarify any ambiguous points\n"
                    "2. Add specific, measurable objectives\n"
                    "3. Identify key requirements and constraints\n"
                    "4. Break down complex tasks into manageable components\n"
                    "5. Add success criteria\n"
                    "Return the enhanced description in JSON format with 'enhanced_task' and 'enhanced_goals' fields."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Task Description: {task}\n"
                    f"Goals: {goals}\n\n"
                    "Please enhance this task description and goals to make them more detailed and actionable. "
                    "Return ONLY a JSON object with 'enhanced_task' and 'enhanced_goals' fields."
                )
            }
        ]
        
        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=0.7
        )
        
        enhanced_content = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'(\{.*\})', enhanced_content, re.DOTALL)
        if json_match:
            enhanced_json = json.loads(json_match.group(1))
            return {
                "task": enhanced_json.get("enhanced_task", task),
                "goals": enhanced_json.get("enhanced_goals", goals)
            }
        else:
            logging.warning("Could not parse LLM response as JSON, using original task")
            return {"task": task, "goals": goals}
            
    except Exception as e:
        logging.error(f"Error enhancing task description: {e}")
        return {"task": task, "goals": goals}

def generate_personas(task_details: Dict[str, Any], persona_count: int = 2) -> List[Dict[str, Any]]:
    """
    Generate a list of personas with diverse perspectives for a given task.
    
    Args:
        task_details (Dict[str, Any]): Dictionary containing task information
        persona_count (int, optional): Number of personas to generate. Defaults to 2.
    
    Returns:
        List[Dict[str, Any]]: List of generated personas
    """
    print("\nGenerating personas dynamically...")
    task = task_details["task"]
    reference_urls = task_details.get("reference_urls", [])
    goals = task_details.get("goals", "No specific goals provided.")

    # Enhance task description and goals
    enhanced_task_details = enhance_task_description(task, goals)
    task = enhanced_task_details["task"]
    goals = enhanced_task_details["goals"]

    model = configure_litellm()
    logging.debug(f"Generating {persona_count} personas for task: {task} with reference URLs: {reference_urls}")

    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert in creating diverse and well-defined personas for collaborative tasks. "
                    "Your goal is to generate personas that will work together effectively while maintaining unique perspectives. "
                    "Each persona should be distinct and contribute meaningfully to the task at hand. "
                    "Generate the personas in JSON format ONLY, without any additional text or explanations.\n\n"
                    "Each persona must include:\n"
                    "- name: A distinctive, professional name\n"
                    "- background: Relevant expertise and experience\n"
                    "- goals: Personal and professional objectives\n"
                    "- beliefs: Core values and principles\n"
                    "- knowledge: Specific areas of expertise\n"
                    "- communication_style: How they interact with others\n"
                    "- role: Their primary function in the task\n"
                    "- strengths: Key capabilities\n"
                    "- challenges: Areas they might struggle with"
                )
            },
            {
                "role": "user",
                "content": (
                    f"Task Description: {task}\n"
                    f"Goals: {goals}\n"
                    f"Number of Personas: {persona_count}\n\n"
                    "Generate personas that:\n"
                    "1. Have complementary skills and knowledge\n"
                    "2. Represent different perspectives and approaches\n"
                    "3. Can effectively collaborate while maintaining their unique viewpoints\n"
                    "4. Have realistic strengths and challenges\n"
                    "Return ONLY a JSON array of personas."
                )
            }
        ]

        # Add context from reference URLs if available
        if reference_urls:
            for url in reference_urls:
                messages.append({
                    "role": "user",
                    "content": f"Consider information from this source: {url}"
                })

        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=0.7
        )
        personas_content = response.choices[0].message.content.strip()
        logging.debug(f"Personas content received: {personas_content}")

        if not personas_content:
            raise ValueError("Received empty response from LiteLLM")

        # Extract JSON array from the response
        json_match = re.search(r'(\[.*\])', personas_content, re.DOTALL)
        if json_match:
            personas_json = json.loads(json_match.group(1))
            logging.debug(f"Parsed personas JSON: {personas_json}")
            
            # Validate persona structure
            required_fields = {"name", "background", "goals", "beliefs", "knowledge", "communication_style", "role", "strengths", "challenges"}
            for persona in personas_json:
                missing_fields = required_fields - set(persona.keys())
                if missing_fields:
                    logging.warning(f"Persona {persona.get('name', 'Unknown')} missing fields: {missing_fields}")
                    # Add default values for missing fields
                    for field in missing_fields:
                        persona[field] = f"Default {field}"
            
            return personas_json
        else:
            raise ValueError("Could not find valid JSON array in response")

    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error: {e}")
        return generate_default_personas(persona_count)
    except Exception as e:
        logging.error(f"Error generating personas: {e}")
        return generate_default_personas(persona_count)

def generate_default_personas(count: int) -> List[Dict[str, Any]]:
    """Generate default personas if the main generation fails."""
    return [
        {
            "name": f"Persona_{i}",
            "background": "General professional background",
            "goals": "Contribute to the task effectively",
            "beliefs": "Collaborative problem-solving",
            "knowledge": "General domain knowledge",
            "communication_style": "Professional and clear",
            "role": "Team member",
            "strengths": "Adaptability and cooperation",
            "challenges": "Managing complex situations"
        } for i in range(count)
    ]

def generate_prompt(task_details: Dict[str, str], personas: List[Dict[str, Any]], 
                   knowledge_sources: List[Dict[str, str]], conflict_strategy: str, 
                   prior_decisions: List[str]) -> Dict[str, Any]:
    model = configure_litellm()
    agent_configs = {}
    
    # Generate agent configuration for each persona
    for persona in personas:
        try:
            # Generate agent configuration using LLM
            response = litellm.completion(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are tasked with generating an agent configuration based on a persona's attributes. "
                            "The configuration should reflect the persona's unique characteristics and approach to the task."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Task: {task_details['task']}\n"
                            f"Persona:\n"
                            f"- Name: {persona['name']}\n"
                            f"- Background: {persona['background']}\n"
                            f"- Goals: {persona['goals']}\n"
                            f"- Beliefs: {persona['beliefs']}\n"
                            f"- Knowledge: {persona['knowledge']}\n"
                            f"- Communication Style: {persona['communication_style']}\n"
                            "Generate a configuration for this agent that reflects their unique attributes."
                        )
                    }
                ],
                temperature=0.7
            )
            
            agent_config = json.loads(response.choices[0].message.content.strip())
            agent_configs[persona['name']] = agent_config
            
        except Exception as e:
            logging.error(f"Error generating agent configuration for {persona['name']}: {e}")
            agent_configs[persona['name']] = {}
    
    # Generate workflow configuration
    try:
        workflow_response = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate a workflow configuration that orchestrates the interaction between multiple agents. "
                        "The workflow should define how agents collaborate and resolve conflicts."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Task: {task_details['task']}\n"
                        f"Agents: {list(agent_configs.keys())}\n"
                        f"Conflict Strategy: {conflict_strategy}\n"
                        "Generate a workflow configuration that defines how these agents should interact."
                    )
                }
            ],
            temperature=0.7
        )
        
        workflow_config = json.loads(workflow_response.choices[0].message.content.strip())
        
    except Exception as e:
        logging.error(f"Error generating workflow configuration: {e}")
        workflow_config = {}
    
    # Construct the final output
    output = {
        "agent_configs": agent_configs,
        "workflow_config": workflow_config,
        "task": task_details["task"],
        "knowledge_sources": [
            {"title": source["title"], "url": source["url"]}
            for source in knowledge_sources
        ],
        "conflict_resolution": conflict_strategy,
        "memory": {
            "personas": [p["name"] for p in personas],
            "task_goals": task_details.get("goals", "No specific goals provided."),
            "prior_decisions": prior_decisions
        }
    }
    
    # Print the constructed output
    print("\nGenerated Configuration:")
    print(json.dumps(output, indent=4))
    
    return output
