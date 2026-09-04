import unittest
from unittest.mock import MagicMock, patch

import app.clients.llm.gemini_provider as gemini_provider_module
from app.clients.llm.gemini_provider import GeminiProvider


class TestGeminiProviderInit(unittest.TestCase):
    def setUp(self):
        gemini_provider_module._gemini_client = None

    @patch("app.clients.llm.gemini_provider.settings")
    def test_raises_if_api_key_missing(self, mock_settings):
        mock_settings.GEMINI_API_KEY = ""
        with self.assertRaises(ValueError):
            GeminiProvider()

    @patch("app.clients.llm.gemini_provider.genai.Client")
    @patch("app.clients.llm.gemini_provider.settings")
    def test_creates_client_with_api_key(self, mock_settings, mock_client_cls):
        mock_settings.GEMINI_API_KEY = "fake-api-key-for-tests"
        provider = GeminiProvider()
        mock_client_cls.assert_called_once_with(api_key="fake-api-key-for-tests")
        self.assertEqual(provider.model, "gemini-3.6-flash")


class TestGeminiProviderChat(unittest.TestCase):
    def setUp(self):
        gemini_provider_module._gemini_client = None
        self.settings_patcher = patch("app.clients.llm.gemini_provider.settings")
        self.mock_settings = self.settings_patcher.start()
        self.mock_settings.GEMINI_API_KEY = "fake-api-key"

        self.client_patcher = patch("app.clients.llm.gemini_provider.genai.Client")
        self.mock_client_cls = self.client_patcher.start()
        self.mock_client_instance = MagicMock()
        self.mock_client_cls.return_value = self.mock_client_instance

    def tearDown(self):
        self.settings_patcher.stop()
        self.client_patcher.stop()

    def mock_response(self, text_val):
        res = MagicMock()
        res.text = text_val
        self.mock_client_instance.models.generate_content.return_value = res

    def test_returns_stripped_response_text(self):
        self.mock_response("  Hello, I'm a friendly response!  ")
        provider = GeminiProvider()
        result = provider.chat(context="some profile context", history=[], message="hi")
        self.assertEqual(result, "Hello, I'm a friendly response!")

    def test_returns_empty_string_when_response_text_is_none(self):
        self.mock_response(None)
        provider = GeminiProvider()
        result = provider.chat(context="ctx", history=[], message="hi")
        self.assertEqual(result, "")

    def test_calls_generate_content_with_correct_model(self):
        self.mock_response("ok")
        provider = GeminiProvider()
        provider.chat(context="ctx", history=[], message="hi")
        _, kwargs = self.mock_client_instance.models.generate_content.call_args
        self.assertEqual(kwargs["model"], "gemini-3.6-flash")

    def test_system_instruction_includes_context(self):
        self.mock_response("ok")
        provider = GeminiProvider()
        provider.chat(context="Repo: my-cool-project", history=[], message="hi")
        _, kwargs = self.mock_client_instance.models.generate_content.call_args
        self.assertIn(
            "<developer_profile_context>", kwargs["config"].system_instruction
        )

    def test_history_roles_map_assistant_to_model(self):
        self.mock_response("ok")
        history = [
            {"role": "user", "content": "What languages do you use?"},
            {"role": "assistant", "content": "Mostly Python and TypeScript."},
        ]
        provider = GeminiProvider()
        provider.chat(context="ctx", history=history, message="Cool, anything else?")
        _, kwargs = self.mock_client_instance.models.generate_content.call_args
        self.assertEqual(len(kwargs["contents"]), 3)

    def test_current_message_appended_last(self):
        self.mock_response("ok")
        provider = GeminiProvider()
        provider.chat(
            context="ctx",
            history=[{"role": "user", "content": "first message"}],
            message="latest message",
        )
        _, kwargs = self.mock_client_instance.models.generate_content.call_args
        self.assertEqual(kwargs["contents"][-1].parts[0].text, "latest message")

    def test_skips_history_entries_with_empty_content(self):
        self.mock_response("ok")
        history = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "real reply"},
        ]
        provider = GeminiProvider()
        provider.chat(context="ctx", history=history, message="new message")
        _, kwargs = self.mock_client_instance.models.generate_content.call_args
        self.assertEqual(len(kwargs["contents"]), 2)

    def test_defaults_missing_role_to_user(self):
        self.mock_response("ok")
        provider = GeminiProvider()
        provider.chat(
            context="ctx",
            history=[{"content": "message with no role key"}],
            message="hi",
        )
        _, kwargs = self.mock_client_instance.models.generate_content.call_args
        self.assertEqual(kwargs["contents"][0].role, "user")

    def test_temperature_is_low_for_grounded_answers(self):
        self.mock_response("ok")
        provider = GeminiProvider()
        provider.chat(context="ctx", history=[], message="hi")
        _, kwargs = self.mock_client_instance.models.generate_content.call_args
        self.assertEqual(kwargs["config"].temperature, 0.2)


if __name__ == "__main__":
    unittest.main()
