import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from typing import Any, cast
from unittest.mock import MagicMock, patch

from dana.core.cli.config_manager import ConfigurationManager


def make_models_resp(models_count: int, status: int = 200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"data": [{} for _ in range(models_count)]}
    return resp


class TestLocalLLMWizard(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        for key in ["LOCAL_BASE_URL", "LOCAL_API_KEY", "HTTP_PROXY", "HTTPS_PROXY"]:
            os.environ.pop(key, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)

    @patch("requests.get")
    def test_detection_prefill_and_skip_api_key(self, mock_get: MagicMock):
        # Quick probes succeed for 127.0.0.1:11434
        mock_get.return_value = make_models_resp(2, 200)

        manager = ConfigurationManager(output_file=".env", debug=False)

        # Inputs:
        # 1) Accept detected endpoint (Enter)
        # 2) Accept default URL (Enter)
        inputs = ["", ""]
        with patch("builtins.input", side_effect=inputs):
            result = manager._configure_local_provider()

        # Should configure without asking for API key (defaults to not-needed)
        self.assertIsInstance(result, dict)
        result_dict = cast(dict[str, Any], result)
        self.assertEqual(result_dict["LOCAL_BASE_URL"], "http://127.0.0.1:11434/v1")
        self.assertEqual(result_dict["LOCAL_API_KEY"], "not-needed")

    @patch("requests.get")
    def test_failure_message_contains_url_and_tips(self, mock_get: MagicMock):
        # Simulate connectivity failure
        mock_get.side_effect = Exception("Connection refused")

        manager = ConfigurationManager(output_file=".env", debug=False)

        # Inputs:
        # 1) No detected endpoint, provide Enter for default
        # 2) At retry prompt, choose 'n'
        inputs = ["", "n"]
        buf = io.StringIO()
        with redirect_stdout(buf):
            with patch("builtins.input", side_effect=inputs):
                result = manager._configure_local_provider()

        out = buf.getvalue()
        self.assertIsNone(result)
        # Actionable, connectivity-centric messaging
        self.assertIn("Could not reach your Local LLM at:", out)
        self.assertIn("Prefer 127.0.0.1 over localhost", out)
        self.assertIn("Include the /v1 path in the URL", out)
        self.assertIn("unset HTTP_PROXY HTTPS_PROXY", out)

    @patch("requests.get")
    def test_fallback_to_openai_provider_on_200_no_models(self, mock_get: MagicMock):
        # First quick probe may fail (no detection), then validation returns 200 with empty data
        def side_effect(url, timeout):
            if url.endswith("/models"):
                resp = MagicMock()
                resp.status_code = 200
                resp.json.return_value = {"data": []}  # No models
                return resp
            raise AssertionError("Unexpected URL")

        mock_get.side_effect = side_effect

        manager = ConfigurationManager(output_file=".env", debug=False)

        # Inputs:
        # 1) Provide base URL explicitly
        # 2) At retry prompt, choose 'n'
        # 3) Accept fallback to OpenAI pointing at BASE_URL
        inputs = ["http://127.0.0.1:8000/v1", "n", "y"]
        with patch("builtins.input", side_effect=inputs):
            result = manager._configure_local_provider()

        self.assertIsInstance(result, dict)
        result_dict = cast(dict[str, Any], result)
        self.assertEqual(result_dict["OPENAI_BASE_URL"], "http://127.0.0.1:8000/v1")
        self.assertEqual(result_dict["OPENAI_API_KEY"], "not-needed")


if __name__ == "__main__":
    unittest.main()


