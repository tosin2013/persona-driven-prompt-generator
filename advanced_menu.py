import streamlit as st
from psycopg2 import connect
from psycopg2.extras import Json
from typing import List, Dict, Any
from streamlit_option_menu import option_menu
from page1 import page1

# Database connection details
DB_NAME = "persona_db"
DB_USER = "persona_user"
DB_PASSWORD = "secure_password"
DB_HOST = "127.0.0.1"  # Ensure this is correct

def fetch_personas_from_db() -> List[Dict[str, Any]]:
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("SELECT personas FROM task_memory ORDER BY id DESC LIMIT 1;")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else []

def update_persona_in_db(personas: List[Dict[str, Any]]) -> None:
    conn = connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    cursor = conn.cursor()
    cursor.execute("UPDATE task_memory SET personas = %s WHERE id = (SELECT id FROM task_memory ORDER BY id DESC LIMIT 1);", (Json(personas),))
    conn.commit()
    cursor.close()
    conn.close()

def fetch_emotional_tones() -> List[str]:
    # Predefined list of emotional tones
    tones = [
        "focused", "inspired", "excited", "determined", "collaborative", 
        "urgent", "motivated", "ambitious", "curious", "reflective", 
        "frustrated", "anxious", "overwhelmed", "apprehensive", 
        "disappointed", "elated", "proud", "happy", "sad", "angry", 
        "afraid", "surprised", "neutral"
    ]
    return tones

def generate_emotional_tone(goal: str) -> str:
    """
    Generates an emotional tone based on the goal.

    Args:
        goal (str): The goal to generate an emotional tone for.

    Returns:
        str: The generated emotional tone.
    """

    # Define a dictionary to map goal keywords to emotional tones
    tone_map = {
        "efficiency": "focused",
        "creativity": "inspired",
        "innovation": "excited",
        "problem-solving": "determined",
        "teamwork": "collaborative",
        "deadline": "urgent",
        "challenge": "motivated",
        "growth": "ambitious",
        "learning": "curious",
        "improvement": "reflective"
    }

    # Define a dictionary to map goal keywords to complex emotional tones
    complex_tone_map = {
        "conflict": "frustrated",
        "uncertainty": "anxious",
        "pressure": "overwhelmed",
        "change": "apprehensive",
        "failure": "disappointed",
        "success": "elated",
        "achievement": "proud"
    }

    # Define a dictionary to map goal keywords to non-complex emotional tones
    non_complex_tone_map = {
        "happiness": "happy",
        "sadness": "sad",
        "anger": "angry",
        "fear": "afraid",
        "surprise": "surprised"
    }

    # Convert the goal to lowercase for case-insensitive matching
    goal = goal.lower()

    # Check if the goal matches any keywords in the tone maps
    for keyword, tone in tone_map.items():
        if keyword in goal:
            return tone

    for keyword, tone in complex_tone_map.items():
        if keyword in goal:
            return tone

    for keyword, tone in non_complex_tone_map.items():
        if keyword in goal:
            return tone

    # If no match is found, return a neutral tone
    return "neutral"

def calculate_emotional_tone_score(personas: List[Dict[str, Any]]) -> int:
    """
    Calculates an emotional tone score based on the personas' emotional tones.

    Args:
        personas (List[Dict[str, Any]]): The list of personas.

    Returns:
        int: The calculated emotional tone score.
    """
    tone_weights = {
        "focused": 10, "inspired": 9, "excited": 8, "determined": 7, "collaborative": 6, 
        "urgent": 5, "motivated": 4, "ambitious": 3, "curious": 2, "reflective": 1, 
        "frustrated": -1, "anxious": -2, "overwhelmed": -3, "apprehensive": -4, 
        "disappointed": -5, "elated": 10, "proud": 9, "happy": 8, "sad": -6, "angry": -7, 
        "afraid": -8, "surprised": 0, "neutral": 0
    }
    score = sum(tone_weights.get(persona.get("emotional_tone", "neutral"), 0) for persona in personas)
    return score

def predict_project_success(score: int) -> str:
    """
    Predicts the project's success based on the emotional tone score.

    Args:
        score (int): The emotional tone score.

    Returns:
        str: The prediction of the project's success.
    """
    if score > 50:
        return "High chance of success"
    elif score > 20:
        return "Moderate chance of success"
    elif score > 0:
        return "Low chance of success"
    else:
        return "High risk of failure"

def improve_emotional_tone(personas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Attempts to improve the emotional tone of the personas for better project success.

    Args:
        personas (List[Dict[str, Any]]): The list of personas.

    Returns:
        List[Dict[str, Any]]: The updated list of personas with improved emotional tones.
    """
    positive_tones = ["focused", "inspired", "excited", "determined", "collaborative", 
                      "urgent", "motivated", "ambitious", "curious", "reflective", 
                      "elated", "proud", "happy"]
    for persona in personas:
        if persona.get("emotional_tone") not in positive_tones:
            persona["emotional_tone"] = "motivated"  # Default to a positive tone
    return personas

def autochat(personas: List[Dict[str, Any]]) -> None:
    """
    Simulates a chat between the personas.

    Args:
        personas (List[Dict[str, Any]]): The list of personas.
    """
    st.session_state.chat_log = []
    for persona in personas:
        message = f"{persona['name']} ({persona['emotional_tone']}): {persona['goals']}"
        st.session_state.chat_log.append(message)

def page2():
    st.title("Advanced Menu")

    personas = fetch_personas_from_db()
    if not personas:
        st.warning("No personas found in the database.")
        return

    score = calculate_emotional_tone_score(personas)
    prediction = predict_project_success(score)
    st.markdown(f"### Emotional Tone Score: {score}")
    st.markdown(f"### Project Success Prediction: {prediction}")

    if st.button("Improve Emotional Tone"):
        personas = improve_emotional_tone(personas)
        update_persona_in_db(personas)  # Save the updated tones to the database
        score = calculate_emotional_tone_score(personas)
        prediction = predict_project_success(score)
        st.markdown(f"### Improved Emotional Tone Score: {score}")
        st.markdown(f"### Improved Project Success Prediction: {prediction}")

    st.markdown("### Edit Personas")
    emotional_tones = fetch_emotional_tones()
    for persona in personas:
        st.markdown(f"#### {persona['name']}")
        persona["background"] = st.text_input(f"Background for {persona['name']}", value=persona.get("background", ""))
        persona["goals"] = st.text_input(f"Goals for {persona['name']}", value=persona.get("goals", ""))
        persona["beliefs"] = st.text_input(f"Beliefs for {persona['name']}", value=persona.get("beliefs", ""))
        persona["knowledge"] = st.text_input(f"Knowledge for {persona['name']}", value=persona.get("knowledge", ""))
        persona["communication_style"] = st.text_input(f"Communication Style for {persona['name']}", value=persona.get("communication_style", ""))
        persona["emotional_tone"] = st.selectbox(f"Emotional Tone for {persona['name']}", options=emotional_tones, index=emotional_tones.index(persona.get("emotional_tone", "neutral")))

    if st.button("Save Changes"):
        update_persona_in_db(personas)
        st.success("Personas updated successfully!")

    st.markdown("### Initial Conversation Settings")
    conversation_length = st.number_input("Default length of initial conversation", min_value=1, max_value=500, value=10)
    if st.button("Save Conversation Settings"):
        st.session_state.conversation_length = conversation_length
        st.success("Conversation length updated successfully!")

    st.markdown("### Autochat")
    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []

    if st.button("Start Autochat"):
        autochat(personas)
        st.session_state.autochat_active = True

    if st.button("Stop Autochat"):
        st.session_state.autochat_active = False

    if st.session_state.get("autochat_active", False):
        st.markdown("#### Chat Log")
        for message in st.session_state.chat_log:
            st.markdown(message)

def main():
    with st.sidebar:
        page = option_menu(
            "Navigation",
            ["Home", "Advanced Menu", "Settings"],
            icons=["house", "gear", "tools"],
            menu_icon="cast",
            default_index=0,
        )

    if page == "Home":
        page1()
    elif page == "Advanced Menu":
        page2()
    elif page == "Settings":
        page3()

if __name__ == "__main__":
    main()