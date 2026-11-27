import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock

from ollama import Message

from main import run_agent


class AgentLoopTests(unittest.TestCase):
    def test_unknown_tool_is_rejected_and_loop_is_bounded(self):
        reply = Message(
            role="assistant",
            tool_calls=[{"function": {"name": "shell", "arguments": {"command": "ls"}}}],
        )
        sent = []

        def chat(**request):
            sent.append(list(request["messages"]))
            return SimpleNamespace(message=reply)

        client = Mock()
        client.chat.side_effect = chat
        with redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(RuntimeError, "after 6 model turns"):
                run_agent(client)

        self.assertEqual(len(sent), 6)
        self.assertIs(sent[1][-2], reply)
        self.assertEqual(sent[1][-1]["role"], "tool")
        self.assertIn("Tool is not allowed", sent[1][-1]["content"])
        self.assertNotIn("[PYTHON] Executing", output.getvalue())
