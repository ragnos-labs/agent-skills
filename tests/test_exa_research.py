from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
from types import ModuleType
from typing import Any


def _client_module() -> ModuleType:
    path = (
        Path(__file__).parents[1] / "skills" / "exa-research" / "scripts" / "exa_cli.py"
    )
    spec = importlib.util.spec_from_file_location("exa_research_cli", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeClient:
    def __init__(self, response: object = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def request(self, endpoint: str, data: dict[str, Any]) -> object:
        self.calls.append((endpoint, data))
        if self.error is not None:
            raise self.error
        return self.response


def _run(
    module: ModuleType,
    argv: list[str],
    *,
    environ: dict[str, str] | None = None,
    client: FakeClient | None = None,
) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    factory = (lambda _key: client) if client is not None else module._official_client
    code = module.main(
        argv,
        environ={} if environ is None else environ,
        client_factory=factory,
        stdout=stdout,
        stderr=stderr,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def test_search_emits_normalized_sorted_json_and_fixed_bounded_request() -> None:
    module = _client_module()
    client = FakeClient(
        {
            "requestId": "request-123",
            "resolvedSearchType": "neural",
            "searchTime": 42.5,
            "costDollars": {"total": 0.007},
            "results": [
                {
                    "url": "https://example.com/source",
                    "title": "Example source",
                    "score": 0.9,
                    "publishedDate": "2026-08-17T00:00:00Z",
                    "highlights": ["Relevant evidence."],
                }
            ],
        }
    )
    code, stdout, stderr = _run(
        module,
        [
            "search",
            "bounded query",
            "--num-results",
            "3",
            "--include-domain",
            "EXAMPLE.com",
        ],
        environ={"EXA_API_KEY": "broker-placeholder"},
        client=client,
    )
    assert code == 0
    assert stderr == ""
    assert (
        stdout
        == json.dumps(json.loads(stdout), sort_keys=True, separators=(",", ":")) + "\n"
    )
    document = json.loads(stdout)
    assert document["kind"] == "exa.search"
    assert document["cost_dollars"] == {
        "contents": None,
        "search": None,
        "total": 0.007,
    }
    assert document["request_id"] == "request-123"
    assert document["results"][0]["url"] == "https://example.com/source"
    assert client.calls == [
        (
            "/search",
            {
                "contents": {"highlights": {"maxCharacters": 1200}},
                "includeDomains": ["example.com"],
                "numResults": 3,
                "query": "bounded query",
                "type": "auto",
            },
        )
    ]


def test_missing_credential_and_provider_failure_are_sanitized() -> None:
    module = _client_module()
    code, stdout, stderr = _run(module, ["search", "query"])
    assert code == 2
    assert stdout == ""
    assert json.loads(stderr)["code"] == "credential_unavailable"

    client = FakeClient(error=RuntimeError("private provider response"))
    code, stdout, stderr = _run(
        module,
        ["search", "query"],
        environ={"EXA_API_KEY": "broker-placeholder"},
        client=client,
    )
    assert code == 3
    assert stdout == ""
    assert json.loads(stderr) == {
        "code": "provider_unavailable",
        "exit_code": 3,
        "kind": "exa.error",
        "schema_version": "1.0",
        "status": "failed",
    }
    assert "private provider response" not in stderr


def test_invalid_inputs_and_provider_contract_fail_closed() -> None:
    module = _client_module()
    code, _, stderr = _run(
        module,
        ["search", "query", "--num-results", "21"],
        environ={"EXA_API_KEY": "broker-placeholder"},
        client=FakeClient({"results": []}),
    )
    assert code == 2
    assert json.loads(stderr)["code"] == "invalid_arguments"

    code, _, stderr = _run(
        module,
        ["search", "query"],
        environ={"EXA_API_KEY": "broker-placeholder"},
        client=FakeClient({"results": [{"title": "missing URL"}]}),
    )
    assert code == 3
    assert json.loads(stderr)["code"] == "provider_contract_invalid"

    code, _, stderr = _run(
        module,
        ["search", "query"],
        environ={"EXA_API_KEY": "broker-placeholder"},
        client=FakeClient(
            {
                "costDollars": {"privateFutureField": "raw payload", "total": 0.1},
                "results": [],
            }
        ),
    )
    assert code == 3
    assert json.loads(stderr)["code"] == "provider_contract_invalid"
    assert "privateFutureField" not in stderr

    malformed_responses = (
        {"results": [], "searchTime": float("nan")},
        {"results": [{"url": "https://example.com", "score": float("inf")}]},
        {"costDollars": {"total": float("nan")}, "results": []},
        {
            "costDollars": {
                "search": {"neural": float("inf")},
                "total": 0.1,
            },
            "results": [],
        },
    )
    for response in malformed_responses:
        code, _, stderr = _run(
            module,
            ["search", "query"],
            environ={"EXA_API_KEY": "broker-placeholder"},
            client=FakeClient(response),
        )
        assert code == 3
        assert json.loads(stderr)["code"] == "provider_contract_invalid"
        assert "NaN" not in stderr
        assert "Infinity" not in stderr


def test_doctor_and_version_never_disclose_the_credential(monkeypatch: Any) -> None:
    module = _client_module()
    monkeypatch.setattr(module.importlib.metadata, "version", lambda _name: "2.18.1")
    secret = "credential-value-that-must-not-appear"
    code, stdout, stderr = _run(module, ["doctor"], environ={"EXA_API_KEY": secret})
    assert code == 0
    assert stderr == ""
    assert json.loads(stdout)["credential"] == "available"
    assert secret not in stdout

    code, stdout, stderr = _run(module, ["--version"])
    assert code == 0
    assert stderr == ""
    assert json.loads(stdout)["sdk_version"] == "2.18.1"


def test_help_and_unexpected_failures_are_deterministic_json(monkeypatch: Any) -> None:
    module = _client_module()

    for arguments in (["--help"], ["doctor", "--help"], ["search", "--help"]):
        code, stdout, stderr = _run(module, arguments)
        assert code == 0
        assert stderr == ""
        assert json.loads(stdout)["kind"] == "exa.help"

    monkeypatch.setattr(
        module.importlib.metadata,
        "version",
        lambda _name: (_ for _ in ()).throw(OSError("private local path")),
    )
    code, stdout, stderr = _run(
        module,
        ["doctor"],
        environ={"EXA_API_KEY": "credential-value-that-must-not-appear"},
    )
    assert code == 0
    assert stderr == ""
    assert json.loads(stdout)["sdk_status"] == "unavailable"
    assert "private local path" not in stdout

    monkeypatch.setattr(
        module,
        "_parser",
        lambda: (_ for _ in ()).throw(RuntimeError("private local path")),
    )
    code, stdout, stderr = _run(module, ["doctor"])
    assert code == 4
    assert stdout == ""
    assert json.loads(stderr)["code"] == "internal_error"
    assert "private local path" not in stderr
