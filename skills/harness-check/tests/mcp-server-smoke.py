#!/usr/bin/env python3
"""Protocol smoke test for the bundled MCP fixture server.

This drives the protocol directly, which is fine HERE: it tests the fixture
itself, and never counts as harness telemetry coverage.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SERVER = Path(__file__).resolve().parent.parent / "assets" / "mcp-server.py"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "methods.log"
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "harness_echo",
                        "arguments": {"text": "smoke-marker"}}},
            {"jsonrpc": "2.0", "id": 4, "method": "resources/list"},
            {"jsonrpc": "2.0", "id": 5, "method": "resources/read",
             "params": {"uri": "harness-check://fixture/resource"}},
            {"jsonrpc": "2.0", "id": 6, "method": "prompts/list"},
            {"jsonrpc": "2.0", "id": 7, "method": "prompts/get",
             "params": {"name": "harness-check-prompt"}},
            {"jsonrpc": "2.0", "id": 8, "method": "no/such/method"},
        ]
        stdin = "".join(json.dumps(r) + "\n" for r in requests)
        proc = subprocess.run(
            [sys.executable, str(SERVER), "--log", str(log)],
            input=stdin, capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, proc.stderr

        by_id, notifications = {}, []
        for line in proc.stdout.splitlines():
            msg = json.loads(line)
            if "id" in msg and msg["id"] is not None:
                by_id[msg["id"]] = msg
            else:
                notifications.append(msg)

        assert by_id[1]["result"]["serverInfo"]["name"] == "harness-check"
        tools = [t["name"] for t in by_id[2]["result"]["tools"]]
        assert tools == ["harness_echo"], tools
        assert by_id[3]["result"]["content"][0]["text"] == "smoke-marker"
        assert by_id[4]["result"]["resources"][0]["uri"] == \
            "harness-check://fixture/resource"
        assert by_id[5]["result"]["contents"][0]["text"] == \
            "harness-check-resource-read"
        assert by_id[6]["result"]["prompts"][0]["name"] == \
            "harness-check-prompt"
        assert by_id[7]["result"]["messages"][0]["content"]["text"] == \
            "harness-check-prompt-get"
        assert by_id[8]["error"]["code"] == -32601

        sent = {n["method"] for n in notifications}
        for changed in ("tools", "resources", "prompts"):
            assert f"notifications/{changed}/list_changed" in sent, sent

        logged = log.read_text().splitlines()
        assert "initialize" in logged
        assert "tools/call\tharness_echo\tsmoke-marker" in logged, logged

    print("mcp-server smoke test: OK")


if __name__ == "__main__":
    main()
