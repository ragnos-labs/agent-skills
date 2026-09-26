#!/usr/bin/env python3
"""Credential-safe JSON CLI for Exa's official Python SDK."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol

API_ORIGIN = "https://api.exa.ai"
CLI_VERSION = "0.2.0"
SDK_DISTRIBUTION = "exa-py"
SDK_VERSION = "2.18.1"
SCHEMA_VERSION = "1.0"
USER_AGENT = f"ragnos-agent-skills/exa-research/{CLI_VERSION}"

_DOMAIN = re.compile(
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", re.IGNORECASE
)
_SEARCH_TYPES = (
    "auto",
    "deep",
    "deep-lite",
    "deep-reasoning",
    "fast",
    "instant",
    "neural",
)


class ExaClient(Protocol):
    def request(
        self,
        endpoint: str,
        data: Mapping[str, Any] | None = None,
        method: str = "POST",
    ) -> Mapping[str, Any]: ...


class CliFailure(Exception):
    def __init__(self, code: str, exit_code: int) -> None:
        super().__init__(code)
        self.code = code
        self.exit_code = exit_code


class ProviderContractFailure(Exception):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise CliFailure("invalid_arguments", 2)


def _write(document: Mapping[str, Any], stream: Any) -> None:
    stream.write(
        json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def _error(code: str, exit_code: int) -> dict[str, Any]:
    return {
        "code": code,
        "exit_code": exit_code,
        "kind": "exa.error",
        "schema_version": SCHEMA_VERSION,
        "status": "failed",
    }


def _credential(environ: Mapping[str, str]) -> str:
    value = environ.get("EXA_API_KEY")
    if (
        value is None
        or not value
        or value != value.strip()
        or any(char.isspace() for char in value)
    ):
        raise CliFailure("credential_unavailable", 2)
    return value


def _official_client(api_key: str) -> ExaClient:
    try:
        from exa_py import Exa
    except ImportError as exc:
        raise CliFailure("official_sdk_unavailable", 2) from exc
    try:
        installed_version = importlib.metadata.version(SDK_DISTRIBUTION)
    except importlib.metadata.PackageNotFoundError as exc:
        raise CliFailure("official_sdk_unavailable", 2) from exc
    if installed_version != SDK_VERSION:
        raise CliFailure("official_sdk_version_mismatch", 2)
    return Exa(api_key=api_key, base_url=API_ORIGIN, user_agent=USER_AGENT)


def _domain(value: str) -> str:
    normalized = value.lower().rstrip(".")
    if _DOMAIN.fullmatch(normalized) is None:
        raise argparse.ArgumentTypeError("invalid domain")
    return normalized


def _parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(prog="exa", add_help=False)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "doctor",
        add_help=False,
        help="Check the installed client without a network call",
    )
    search = subparsers.add_parser(
        "search", add_help=False, help="Search Exa and return normalized JSON"
    )
    search.add_argument("query")
    search.add_argument("--num-results", type=int, default=5)
    search.add_argument(
        "--type", dest="search_type", choices=_SEARCH_TYPES, default="auto"
    )
    search.add_argument("--include-domain", action="append", default=[], type=_domain)
    search.add_argument("--exclude-domain", action="append", default=[], type=_domain)
    search.add_argument("--max-highlight-characters", type=int, default=1200)
    api = subparsers.add_parser("api", add_help=False)
    api.add_argument("endpoint")
    api.add_argument("--method", choices=("GET", "POST", "PATCH", "PUT", "DELETE"), default="POST")
    api.add_argument("--data", help="JSON object, @file, or - for stdin")
    api.add_argument("--params", help="JSON query parameters")
    api.add_argument("--stream", action="store_true")
    api.add_argument("--timeout", type=int, default=300)
    return parser


def _version_document() -> dict[str, Any]:
    return {
        "api_origin": API_ORIGIN,
        "client": "exa-research",
        "client_version": CLI_VERSION,
        "kind": "exa.version",
        "schema_version": SCHEMA_VERSION,
        "sdk": SDK_DISTRIBUTION,
        "sdk_version": SDK_VERSION,
        "status": "ready",
    }


def _help_document(command: str | None = None) -> dict[str, Any]:
    commands: dict[str, Any] = {
        "api": {
            "arguments": ["endpoint"],
            "options": ["--method", "--data", "--params", "--stream", "--timeout"],
            "purpose": "full research API JSON or SSE, fixed api.exa.ai origin",
            "data": "JSON object, @file, or - for stdin; query parameters via --params",
            "roots": ["search", "contents", "findSimilar", "answer", "research", "agent", "monitors", "batches", "websets"],
        },
        "doctor": {"network": "not_checked", "purpose": "check local readiness"},
        "search": {
            "arguments": ["query"],
            "options": [
                "--num-results",
                "--type",
                "--include-domain",
                "--exclude-domain",
                "--max-highlight-characters",
            ],
            "purpose": "run one bounded Exa search",
        },
    }
    return {
        "client": "exa-research",
        "command": command,
        "commands": commands if command is None else {command: commands[command]},
        "kind": "exa.help",
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
    }


def _doctor(environ: Mapping[str, str]) -> dict[str, Any]:
    credential = "available"
    try:
        _credential(environ)
    except CliFailure:
        credential = "unavailable"
    try:
        installed_version = importlib.metadata.version(SDK_DISTRIBUTION)
    except Exception:
        installed_version = None
    sdk_status = "ready" if installed_version == SDK_VERSION else "unavailable"
    return {
        **_version_document(),
        "credential": credential,
        "installed_sdk_version": installed_version,
        "kind": "exa.doctor",
        "network": "not_checked",
        "sdk_status": sdk_status,
        "status": "ready"
        if credential == "available" and sdk_status == "ready"
        else "degraded",
    }


def _result(document: object) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ProviderContractFailure
    url = document.get("url")
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        raise ProviderContractFailure
    highlights = document.get("highlights")
    if highlights is not None and (
        not isinstance(highlights, list)
        or any(not isinstance(item, str) for item in highlights)
    ):
        raise ProviderContractFailure
    score = document.get("score")
    if score is not None and (
        not isinstance(score, (int, float))
        or isinstance(score, bool)
        or not math.isfinite(score)
    ):
        raise ProviderContractFailure
    return {
        "author": document.get("author")
        if isinstance(document.get("author"), str)
        else None,
        "crawl_date": (
            document.get("crawlDate")
            if isinstance(document.get("crawlDate"), str)
            else None
        ),
        "highlights": highlights,
        "published_date": (
            document.get("publishedDate")
            if isinstance(document.get("publishedDate"), str)
            else None
        ),
        "score": score
        if isinstance(score, (int, float)) and not isinstance(score, bool)
        else None,
        "title": document.get("title")
        if isinstance(document.get("title"), str)
        else None,
        "url": url,
    }


def _optional_number(document: Mapping[str, Any], name: str) -> int | float | None:
    value = document.get(name)
    if value is None:
        return None
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        raise ProviderContractFailure
    return value


def _numeric_mapping(
    value: object, *, allowed_keys: frozenset[str]
) -> dict[str, int | float] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or not set(value).issubset(allowed_keys):
        raise ProviderContractFailure
    if any(
        not isinstance(item, (int, float))
        or isinstance(item, bool)
        or not math.isfinite(item)
        for item in value.values()
    ):
        raise ProviderContractFailure
    return {key: value[key] for key in sorted(value)}


def _cost_dollars(value: object) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or not set(value).issubset(
        {"contents", "search", "total"}
    ):
        raise ProviderContractFailure
    total = value.get("total")
    if (
        not isinstance(total, (int, float))
        or isinstance(total, bool)
        or not math.isfinite(total)
    ):
        raise ProviderContractFailure
    return {
        "contents": _numeric_mapping(
            value.get("contents"), allowed_keys=frozenset({"summary", "text"})
        ),
        "search": _numeric_mapping(
            value.get("search"), allowed_keys=frozenset({"keyword", "neural"})
        ),
        "total": total,
    }


def _normalize_search_response(
    response: object, *, query: str, requested_results: int, search_type: str
) -> dict[str, Any]:
    if not isinstance(response, dict) or not isinstance(response.get("results"), list):
        raise ProviderContractFailure
    request_id = response.get("requestId")
    if request_id is not None and not isinstance(request_id, str):
        raise ProviderContractFailure
    cost = _cost_dollars(response.get("costDollars"))
    return {
        "client": "exa-research",
        "client_version": CLI_VERSION,
        "cost_dollars": cost,
        "kind": "exa.search",
        "provider": "exa",
        "query": query,
        "request_id": request_id,
        "requested_results": requested_results,
        "resolved_search_type": (
            response.get("resolvedSearchType")
            if isinstance(response.get("resolvedSearchType"), str)
            and response.get("resolvedSearchType")
            else None
        ),
        "results": [_result(item) for item in response["results"]],
        "schema_version": SCHEMA_VERSION,
        "sdk": SDK_DISTRIBUTION,
        "sdk_version": SDK_VERSION,
        "search_time_ms": _optional_number(response, "searchTime"),
        "search_type": search_type,
        "status": "succeeded",
    }


def _search(
    args: argparse.Namespace,
    *,
    environ: Mapping[str, str],
    client_factory: Callable[[str], ExaClient],
) -> dict[str, Any]:
    query = args.query.strip()
    if not query or len(query) > 2000:
        raise CliFailure("invalid_arguments", 2)
    if not 1 <= args.num_results <= 20:
        raise CliFailure("invalid_arguments", 2)
    if not 200 <= args.max_highlight_characters <= 4000:
        raise CliFailure("invalid_arguments", 2)
    include_domains = tuple(dict.fromkeys(args.include_domain))
    exclude_domains = tuple(dict.fromkeys(args.exclude_domain))
    if set(include_domains).intersection(exclude_domains):
        raise CliFailure("invalid_arguments", 2)
    payload: dict[str, Any] = {
        "contents": {"highlights": {"maxCharacters": args.max_highlight_characters}},
        "numResults": args.num_results,
        "query": query,
        "type": args.search_type,
    }
    if include_domains:
        payload["includeDomains"] = list(include_domains)
    if exclude_domains:
        payload["excludeDomains"] = list(exclude_domains)
    try:
        client = client_factory(_credential(environ))
        response = client.request("/search", payload)
    except CliFailure:
        raise
    except Exception as exc:
        raise CliFailure("provider_unavailable", 3) from exc
    try:
        return _normalize_search_response(
            response,
            query=query,
            requested_results=args.num_results,
            search_type=args.search_type,
        )
    except ProviderContractFailure as exc:
        raise CliFailure("provider_contract_invalid", 3) from exc


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        # Never forward provider credentials to a redirect destination.
        return None


def _json_object(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        raw = sys.stdin.read() if value == "-" else (
            Path(value[1:]).read_text(encoding="utf-8") if value.startswith("@") else value
        )
        document = json.loads(raw)
        if not isinstance(document, dict):
            raise ValueError
        json.dumps(document, allow_nan=False)
        return document
    except (OSError, ValueError, UnicodeError) as exc:
        raise CliFailure("invalid_json_object", 2) from exc


def _api(args: argparse.Namespace, environ: Mapping[str, str], stdout: Any) -> None:
    endpoint = args.endpoint
    roots = {"search", "contents", "findSimilar", "answer", "research", "agent",
             "monitors", "batches", "websets"}
    if (not re.fullmatch(r"/[A-Za-z0-9_/-]+", endpoint)
            or "//" in endpoint or endpoint.split("/")[1] not in roots):
        raise CliFailure("invalid_research_endpoint", 2)
    if not 1 <= args.timeout <= 3600:
        raise CliFailure("invalid_timeout", 2)
    payload = _json_object(args.data)
    params = _json_object(args.params)
    if args.method == "GET" and payload is not None:
        raise CliFailure("get_requires_params_not_data", 2)
    if params is not None:
        for key, value in params.items():
            items = value if isinstance(value, list) else [value]
            if any(not isinstance(item, (str, int, float, bool)) for item in items):
                raise CliFailure("invalid_query_parameters", 2)
            encoded = [str(item).lower() if isinstance(item, bool) else item for item in items]
            params[key] = encoded if isinstance(value, list) else encoded[0]
    if payload and payload.get("stream") and not args.stream:
        raise CliFailure("stream_requires_stream_flag", 2)
    url = API_ORIGIN + endpoint
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    request = urllib.request.Request(
        url, method=args.method,
        data=json.dumps(payload, allow_nan=False).encode() if payload is not None else None,
        headers={"x-api-key": _credential(environ), "Content-Type": "application/json",
                 "User-Agent": USER_AGENT,
                 "Accept": "text/event-stream" if args.stream else "application/json"},
    )
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=args.timeout) as response:
            if args.stream:
                for line in response:
                    stdout.write(line.decode("utf-8"))
                    stdout.flush()
            else:
                raw = response.read()
                document = json.loads(raw) if raw else {}
                # Validate before writing so malformed responses cannot produce partial JSON.
                rendered = json.dumps(document, allow_nan=False, ensure_ascii=False, sort_keys=True)
                stdout.write(rendered + "\n")
    except urllib.error.HTTPError as exc:
        raise CliFailure(f"provider_http_{exc.code}", 3) from exc
    except (ValueError, UnicodeError) as exc:
        raise CliFailure("provider_contract_invalid", 3) from exc
    except (OSError, urllib.error.URLError) as exc:
        raise CliFailure("provider_unavailable", 3) from exc


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    client_factory: Callable[[str], ExaClient] = _official_client,
    stdout: Any = sys.stdout,
    stderr: Any = sys.stderr,
) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    values = os.environ if environ is None else environ
    if arguments == ("--version",):
        _write(_version_document(), stdout)
        return 0
    help_commands = {
        ("api", "--help"): "api",
        ("api", "-h"): "api",
        ("--help",): None,
        ("-h",): None,
        ("doctor", "--help"): "doctor",
        ("doctor", "-h"): "doctor",
        ("search", "--help"): "search",
        ("search", "-h"): "search",
    }
    if arguments in help_commands:
        _write(_help_document(help_commands[arguments]), stdout)
        return 0
    try:
        args = _parser().parse_args(arguments)
        if args.command == "api":
            _api(args, values, stdout)
            return 0
        document = (
            _doctor(values)
            if args.command == "doctor"
            else _search(args, environ=values, client_factory=client_factory)
        )
        _write(document, stdout)
        return 0
    except CliFailure as exc:
        _write(_error(exc.code, exc.exit_code), stderr)
        return exc.exit_code
    except Exception:
        _write(_error("internal_error", 4), stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
