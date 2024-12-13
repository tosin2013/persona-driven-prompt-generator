import unittest
from unittest.mock import patch
from persona_testing import (
    create_tables,
    configure_litellm,
    autochat,
    fetch_personas_from_db,
    get_current_task,
    page1,
    duckduckgo_search,
    generate_embedding,
    store_memory_in_pgvector,
    find_similar_tasks,
    generate_initial_conversation,
    edit_persona_tones,
    save_or_copy_conversations,
    store_conversation_history,
    retrieve_conversation_history,
    interact_with_llm,
    submit_prompt_to_llm,
    main,
    upload_urls_to_vector_db
)

class TestPersonaTesting(unittest.TestCase):

    def test_create_tables(self):
        # Test if tables are created successfully
        create_tables()
        # Add assertions to check if tables exist

    def test_configure_litellm(self):
        # Test if LiteLLM is configured correctly
        model = configure_litellm()
        self.assertIsNotNone(model)

    @patch('random.choice')  # Mock random selection
    def test_autochat(self, mock_random_choice):
        # Test autochat function with deterministic behavior
        personas = [{"name": "Persona1", "goals": "Goal1", "emotional_tone": "neutral"}]
        mock_random_choice.return_value = personas[0]  # Always select first persona

        # Capture the generated messages
        messages = []
        with patch('streamlit.session_state', {'messages': messages}):
            autochat(personas, 2)

        # Assert the basic structure
        self.assertIsInstance(messages, list)
        self.assertEqual(len(messages), 2, "Should generate exactly 2 messages")

        # Verify message structure and content
        for message in messages:
            self.assertIn('role', message)
            self.assertIn('content', message)
            self.assertEqual(message['role'], "system")
            self.assertIsInstance(message['content'], str)
            self.assertGreater(len(message['content']), 0)

        # Test with valid sleep_duration
        autochat(personas, 2, sleep_duration=1.0)

        # Test with invalid sleep_duration
        with self.assertRaises(ValueError):
            autochat(personas, 2, sleep_duration=-1.0)

    def test_fetch_personas_from_db(self):
        # Test fetching personas from the database
        personas = fetch_personas_from_db()
        self.assertIsInstance(personas, list)

    def test_get_current_task(self):
        # Test getting the current task
        task = get_current_task()
        self.assertIn("task", task)

    def test_page1(self):
        # Test page1 function
        page1()
        # Add assertions to check if the page is rendered correctly

    def test_duckduckgo_search(self):
        # Test DuckDuckGo search
        results = duckduckgo_search("test query")
        self.assertIsInstance(results, list)

    def test_generate_embedding(self):
        # Test generating embeddings with various inputs
        test_cases = [
            "test text",
            "",  # empty string
            "a" * 1000,  # long text
            "Special chars: !@#$%^&*()",  # special characters
            "Multi\nline\ntext"  # multiline text
        ]

        for text in test_cases:
            with self.subTest(text=text):
                embedding = generate_embedding(text)

                # Check type and structure
                self.assertIsInstance(embedding, list)
                self.assertEqual(len(embedding), 768)  # Expected embedding dimension

                # Check for valid numerical values
                self.assertTrue(all(isinstance(x, float) for x in embedding))

                # Verify not all zeros (real embeddings should have variation)
                self.assertFalse(all(x == 0 for x in embedding))

                # Check for reasonable value range (-1 to 1 is typical for normalized embeddings)
                self.assertTrue(all(-1 <= x <= 1 for x in embedding))

        # Test error handling
        with self.assertRaises(TypeError):
            generate_embedding(None)

        with self.assertRaises(TypeError):
            generate_embedding(123)

    def test_store_memory_in_pgvector(self):
        # Test storing memory in pgvector
        store_memory_in_pgvector("task", "goals", [], [0.0] * 768, [])
        # Add assertions to check if memory is stored correctly

    def test_find_similar_tasks(self):
        # Test finding similar tasks
        similar_tasks = find_similar_tasks([0.0] * 768)
        self.assertIsInstance(similar_tasks, list)

    def test_generate_initial_conversation(self):
        # Test generating initial conversation
        conversation = generate_initial_conversation({"task": "test task", "personas": ["Persona1"]})
        self.assertIsInstance(conversation, list)

    def test_edit_persona_tones(self):
        # Test editing persona tones
        personas = [{"name": "Persona1"}]
        edit_persona_tones(personas)
        self.assertIn("tone", personas[0])

    def test_save_or_copy_conversations(self):
        # Test saving or copying conversations
        save_or_copy_conversations([{"role": "user", "content": "test message"}])
        # Add assertions to check if conversations are saved or copied

    def test_store_conversation_history(self):
        # Test storing conversation history
        store_conversation_history([{"role": "user", "content": "test message"}])
        # Add assertions to check if history is stored correctly

    def test_retrieve_conversation_history(self):
        # Test retrieving conversation history
        history = retrieve_conversation_history()
        self.assertIsInstance(history, list)

    @patch('persona_testing.openai.ChatCompletion.create')  # Adjust import path as needed
    def test_interact_with_llm(self, mock_llm):
        # Setup mock response
        mock_llm.return_value = {'choices': [{'message': {'content': 'mocked response'}}]}

        # Test normal input
        response = interact_with_llm("test prompt")
        self.assertEqual(response, 'mocked response')

        # Test empty input
        with self.assertRaises(ValueError):
            interact_with_llm("")

        # Test long input
        long_prompt = "test " * 1000
        response = interact_with_llm(long_prompt)
        self.assertIsNotNone(response)

        # Test special characters
        special_prompt = "!@#$%^&*()"
        response = interact_with_llm(special_prompt)
        self.assertIsNotNone(response)

        # Test API error handling
        mock_llm.side_effect = Exception("API Error")
        with self.assertRaises(Exception):
            interact_with_llm("test prompt")

    @patch('persona_testing.openai.ChatCompletion.create')  # Adjust import path as needed
    def test_submit_prompt_to_llm(self, mock_llm):
        # Setup mock response
        mock_llm.return_value = {'choices': [{'message': {'content': 'mocked response'}}]}

        # Test normal case
        response = submit_prompt_to_llm("test prompt")
        self.assertEqual(response, 'mocked response')

        # Test input validation
        with self.assertRaises(ValueError):
            submit_prompt_to_llm(None)

        # Test with numeric input
        response = submit_prompt_to_llm("42")
        self.assertIsNotNone(response)

        # Test API timeout
        mock_llm.side_effect = TimeoutError("Request timed out")
        with self.assertRaises(TimeoutError):
            submit_prompt_to_llm("test prompt")

    def test_main(self):
        # Test main function
        main()
        # Add assertions to check if main function runs correctly

    def test_upload_urls_to_vector_db(self):
        # Test uploading URLs to vector database
        upload_urls_to_vector_db([{"name": "Persona1", "reference_urls": ["http://example.com"]}])
        # Add assertions to check if URLs are uploaded correctly

if __name__ == "__main__":
    unittest.main()
