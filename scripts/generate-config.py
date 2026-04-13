#!/usr/bin/env python3
#  Copyright (c) 2026, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Generate a config.yml from the current environment variables or a .env file.

Each value in the generated file is annotated with a comment showing whether
it came from an environment variable (``# from ENV_VAR``) or is the built-in
default (``# default``).  Secrets are never included.

Usage::

    python scripts/generate-config.py                          # reads ROOT_DIR/.env → config.yml
    python scripts/generate-config.py --output other.yml       # writes to a different file
    python scripts/generate-config.py --env-file /other/.env   # reads a specific .env file
"""

import argparse
import os
import sys

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from wiki_rag import ROOT_DIR
from wiki_rag.config import (
    _DEFAULT_USER_AGENT,
    _SECRETS,
    _parse_excluded,
    _parse_list,
    _parse_namespaces,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get(env_key: str, default: Any = None) -> tuple[Any, str]:
    """Read a non-secret env var and return (value, source_label).

    Args:
        env_key: Environment variable name.
        default: Value to return when the env var is absent or empty.

    Returns:
        Tuple of (resolved_value, source_label) where source_label is either
        ``"from ENV_VAR"`` or ``"default"``.

    """
    if env_key in _SECRETS:
        msg = f"Refusing to read secret key {env_key!r}"
        raise ValueError(msg)
    raw = os.environ.get(env_key)
    if raw is not None and raw != "":
        return raw, f"from {env_key}"
    return default, "default"


def _cmt(source: str, pad: int = 0) -> str:
    """Format a source comment with optional left-padding spaces.

    Args:
        source: Source label, e.g. ``"from MEDIAWIKI_URL"`` or ``"default"``.
        pad: Number of spaces to prepend before the ``#`` character.

    Returns:
        Formatted comment string, e.g. ``"  # from MEDIAWIKI_URL"``.

    """
    return " " * pad + f"# {source}"


def _fmt_str(val: Any) -> str:
    """Format a value as a quoted YAML string.

    Args:
        val: Value to format.

    Returns:
        Quoted string, e.g. ``'"hello"'``.

    """
    if val is None:
        return '""'
    return f'"{val}"'


def _fmt_bool(val: Any, default: bool = False) -> str:
    """Format a value as a YAML boolean literal.

    Args:
        val: Raw value (string ``"true"``/``"false"`` or native bool).
        default: Fallback when *val* is ``None`` or empty.

    Returns:
        ``"true"`` or ``"false"``.

    """
    if val is None or val == "":
        return "true" if default else "false"
    if isinstance(val, bool):
        return "true" if val else "false"
    return "true" if str(val).strip().lower() == "true" else "false"


def _fmt_int(val: Any, default: int = 0) -> str:
    """Format a value as a YAML integer.

    Args:
        val: Raw value.
        default: Fallback when *val* is ``None`` or empty.

    Returns:
        Integer as a string.

    """
    if val is None or val == "":
        return str(default)
    return str(int(val))


def _fmt_float(val: Any, default: float = 0.0) -> str:
    """Format a value as a YAML float.

    Args:
        val: Raw value.
        default: Fallback when *val* is ``None`` or empty.

    Returns:
        Float as a string.

    """
    if val is None or val == "":
        return str(default)
    return str(float(val))


def _fmt_int_list(val: Any) -> str:
    """Format a namespace-style value as a compact YAML integer list.

    Args:
        val: Raw comma-separated string or Python list.

    Returns:
        YAML inline list, e.g. ``"[0, 4, 12]"``.

    """
    items = _parse_namespaces(val)
    return "[" + ", ".join(str(n) for n in items) + "]"


def _fmt_str_list(val: Any) -> str:
    """Format a comma-separated value or list as a compact YAML string list.

    Args:
        val: Raw comma-separated string or Python list.

    Returns:
        YAML inline list, e.g. ``'["a", "b"]'``.

    """
    items = _parse_list(val)
    if not items:
        return "[]"
    return "[" + ", ".join(f'"{item}"' for item in items) + "]"


def _fmt_excluded(val: Any, indent: str = "    ") -> list[str]:
    """Render exclusion rules as YAML mapping lines.

    Args:
        val: Raw exclusion value (semicolon-format string or dict).
        indent: Indentation prefix for each rendered line.

    Returns:
        List of YAML lines (without trailing newline) for the mapping.

    """
    parsed = _parse_excluded(val)
    if not parsed:
        return [f"{indent}categories: []", f"{indent}wikitext: []"]
    lines = []
    for key, values in sorted(parsed.items()):
        formatted_vals = (
            "[" + ", ".join(f'"{v}"' for v in values) + "]" if values else "[]"
        )
        lines.append(f"{indent}{key}: {formatted_vals}")
    return lines


# ---------------------------------------------------------------------------
# YAML generation
# ---------------------------------------------------------------------------


def _generate_yaml(env_source: Path | None) -> str:
    """Build and return the complete config.yml content as a string.

    Args:
        env_source: Path to the .env file that was loaded, or ``None`` if no
            file was found.  Used only in the file header comment.

    Returns:
        The rendered YAML string.

    """
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    source_note = f"from {env_source}" if env_source else "from environment variables"
    default_ua = _DEFAULT_USER_AGENT

    # Read all non-secret settings.
    mw_url, mw_url_src = _get("MEDIAWIKI_URL", "")
    mw_ns, mw_ns_src = _get("MEDIAWIKI_NAMESPACES", "")
    mw_excl, mw_excl_src = _get("MEDIAWIKI_EXCLUDED", "")
    mw_keep, mw_keep_src = _get("MEDIAWIKI_KEEP_TEMPLATES", "")

    dump_path, dump_path_src = _get("LOADER_DUMP_PATH", "")
    rate_lim, rate_lim_src = _get("ENABLE_RATE_LIMITING", "true")

    coll_name, coll_name_src = _get("COLLECTION_NAME", "your_collection_name")
    index_vendor, index_vendor_src = _get("INDEX_VENDOR", "milvus")

    # General API base URL and model — per-model overrides are YAML-only (no env vars).
    openai_base, openai_base_src = _get("OPENAI_API_BASE", "https://api.openai.com/v1")
    openai_model, openai_model_src = _get("LLM_MODEL", "your_llm_model")

    emb_model, emb_model_src = _get("EMBEDDING_MODEL", "your_embedding_model")
    emb_dims, emb_dims_src = _get("EMBEDDING_DIMENSIONS", "768")

    ctx_model, ctx_model_src = _get("CONTEXTUALISATION_MODEL", "")

    prompt_name, prompt_name_src = _get("SEARCH_PROMPT_NAME", "wiki-rag")
    product, product_src = _get("SEARCH_PRODUCT", "Moodle")
    task_def, task_def_src = _get("SEARCH_TASK_DEF", "Moodle user documentation")
    kb_name, kb_name_src = _get("SEARCH_KB_NAME", "Moodle Docs")
    dist_cutoff, dist_cutoff_src = _get("SEARCH_DISTANCE_CUTOFF", "0.6")
    max_tokens, max_tokens_src = _get("SEARCH_MAX_COMPLETION_TOKENS", "1536")
    temperature, temperature_src = _get("SEARCH_TEMPERATURE", "0.05")
    top_p, top_p_src = _get("SEARCH_TOP_P", "0.85")
    hyde_enabled, hyde_enabled_src = _get("SEARCH_HYDE_ENABLED", "false")
    hyde_passages, hyde_passages_src = _get("SEARCH_HYDE_PASSAGES", "1")

    wrapper_base, wrapper_base_src = _get("WRAPPER_API_BASE", "0.0.0.0:8080")
    wrapper_turns, wrapper_turns_src = _get("WRAPPER_CHAT_MAX_TURNS", "0")
    wrapper_tkns, wrapper_tkns_src = _get("WRAPPER_CHAT_MAX_TOKENS", "0")
    wrapper_model, wrapper_model_src = _get("WRAPPER_MODEL_NAME", "")

    mcp_base, mcp_base_src = _get("MCP_API_BASE", "0.0.0.0:8081")

    milvus_url, milvus_url_src = _get("MILVUS_URL", "http://0.0.0.0:19530")

    ls_tracing, ls_tracing_src = _get("LANGSMITH_TRACING", "false")
    ls_prompts, ls_prompts_src = _get("LANGSMITH_PROMPTS", "false")
    ls_endpoint, ls_endpoint_src = _get(
        "LANGSMITH_ENDPOINT", "https://eu.api.smith.langchain.com"
    )
    ls_prefix, ls_prefix_src = _get("LANGSMITH_PROMPT_PREFIX", "")

    lf_tracing, lf_tracing_src = _get("LANGFUSE_TRACING", "false")
    lf_prompts, lf_prompts_src = _get("LANGFUSE_PROMPTS", "false")
    lf_host, lf_host_src = _get("LANGFUSE_HOST", "https://cloud.langfuse.com")
    lf_prefix, lf_prefix_src = _get("LANGFUSE_PROMPT_PREFIX", "")

    user_agent, user_agent_src = _get("USER_AGENT", default_ua)

    # 6-space indent: 4 spaces for the sites[0] block + 2 more under excluded:
    excl_lines = _fmt_excluded(mw_excl, indent="      ")

    lines: list[str] = []

    # Header.
    lines += [
        f"# config.yml — generated by generate-config.py on {now}",
        f"# Source: {source_note}",
        "#",
        "# Values annotated with  # from ENV_VAR  were set explicitly.",
        "# Values annotated with  # default  were not set and use the built-in default.",
        "# Secrets are NOT included — keep them in .env or real environment variables.",
        "# See dotenv.template for the list of expected secrets.",
        "",
    ]

    # openai
    lines += [
        "# ---------------------------------------------------------------------------",
        "# OpenAI-compatible provider",
        "# ---------------------------------------------------------------------------",
        "openai:",
        f"  api_base: {_fmt_str(openai_base)}{_cmt(openai_base_src, 1)}",
        f"  model: {_fmt_str(openai_model)}{_cmt(openai_model_src, 1)}",
        f"  max_completion_tokens: {_fmt_int(max_tokens, default=1536)}{_cmt(max_tokens_src, 1)}",
        f"  temperature: {_fmt_float(temperature, default=0.05)}{_cmt(temperature_src, 1)}",
        f"  top_p: {_fmt_float(top_p, default=0.85)}{_cmt(top_p_src, 1)}",
        "",
    ]

    # sites
    lines += [
        "# ---------------------------------------------------------------------------",
        "# MediaWiki sources",
        "# ---------------------------------------------------------------------------",
        "sites:",
        f"  - url: {_fmt_str(mw_url)}{_cmt(mw_url_src, 1)}",
        f"    namespaces: {_fmt_int_list(mw_ns)}{_cmt(mw_ns_src, 1)}",
        f"    excluded:{_cmt(mw_excl_src, 1)}",
    ]
    lines += excl_lines
    lines += [
        f"    keep_templates: {_fmt_str_list(mw_keep)}{_cmt(mw_keep_src, 1)}",
        "",
    ]

    # loader
    lines += [
        "# ---------------------------------------------------------------------------",
        "# Loader",
        "# ---------------------------------------------------------------------------",
        "loader:",
        f"  dump_path: {_fmt_str(dump_path)}{_cmt(dump_path_src, 1)}",
        f"  rate_limiting: {_fmt_bool(rate_lim, default=True)}{_cmt(rate_lim_src, 1)}",
        "",
    ]

    # collection
    lines += [
        "# ---------------------------------------------------------------------------",
        "# Collection",
        "# ---------------------------------------------------------------------------",
        "collection:",
        f"  name: {_fmt_str(coll_name)}{_cmt(coll_name_src, 1)}",
        "",
    ]

    # index
    lines += [
        "# ---------------------------------------------------------------------------",
        "# Index / vector store",
        "# ---------------------------------------------------------------------------",
        "index:",
        f"  vendor: {_fmt_str(index_vendor)}{_cmt(index_vendor_src, 1)}",
        "",
    ]

    # embedding
    lines += [
        "# ---------------------------------------------------------------------------",
        "# Embeddings",
        "# ---------------------------------------------------------------------------",
        "embedding:",
        f"  model: {_fmt_str(emb_model)}{_cmt(emb_model_src, 1)}",
        f"  dimensions: {_fmt_int(emb_dims, default=768)}{_cmt(emb_dims_src, 1)}",
        '  # api_base: ""  # YAML-only: optional override for openai.api_base',
        "",
    ]

    # search
    lines += [
        "# ---------------------------------------------------------------------------",
        "# Search / RAG generation",
        "# ---------------------------------------------------------------------------",
        "search:",
        f"  prompt_name: {_fmt_str(prompt_name)}{_cmt(prompt_name_src, 1)}",
        f"  product: {_fmt_str(product)}{_cmt(product_src, 1)}",
        f"  task_def: {_fmt_str(task_def)}{_cmt(task_def_src, 1)}",
        f"  kb_name: {_fmt_str(kb_name)}{_cmt(kb_name_src, 1)}",
        f"  distance_cutoff: {_fmt_float(dist_cutoff, default=0.6)}{_cmt(dist_cutoff_src, 1)}",
        "  contextualisation:",
        f"    model: {_fmt_str(ctx_model)}{_cmt(ctx_model_src, 1)}",
        '    # api_base: ""  # YAML-only: optional override for openai.api_base',
        "  hyde:",
        f"    enabled: {_fmt_bool(hyde_enabled, default=False)}{_cmt(hyde_enabled_src, 1)}",
        f"    passages: {_fmt_int(hyde_passages, default=1)}{_cmt(hyde_passages_src, 1)}",
        '    # model: ""  # YAML-only: optional override for search.contextualisation.model',
        '    # api_base: ""  # YAML-only: optional override for search.contextualisation.api_base',
        "",
    ]

    # wrapper
    lines += [
        "# ---------------------------------------------------------------------------",
        "# OpenAI-compatible HTTP server (wr-server)",
        "# ---------------------------------------------------------------------------",
        "wrapper:",
        f"  api_base: {_fmt_str(wrapper_base)}{_cmt(wrapper_base_src, 1)}",
        f"  chat_max_turns: {_fmt_int(wrapper_turns, default=0)}{_cmt(wrapper_turns_src, 1)}",
        f"  chat_max_tokens: {_fmt_int(wrapper_tkns, default=0)}{_cmt(wrapper_tkns_src, 1)}",
        f"  model_name: {_fmt_str(wrapper_model)}{_cmt(wrapper_model_src, 1)}",
        "",
    ]

    # mcp
    lines += [
        "# ---------------------------------------------------------------------------",
        "# MCP server (wr-mcp)",
        "# ---------------------------------------------------------------------------",
        "mcp:",
        f"  api_base: {_fmt_str(mcp_base)}{_cmt(mcp_base_src, 1)}",
        "",
    ]

    # milvus
    lines += [
        "# ---------------------------------------------------------------------------",
        "# Milvus vector store (non-secret connection settings)",
        "# ---------------------------------------------------------------------------",
        "milvus:",
        f"  url: {_fmt_str(milvus_url)}{_cmt(milvus_url_src, 1)}",
        "",
    ]

    # observability
    lines += [
        "# ---------------------------------------------------------------------------",
        "# Observability",
        "# ---------------------------------------------------------------------------",
        "observability:",
        "  langsmith:",
        f"    tracing: {_fmt_bool(ls_tracing)}{_cmt(ls_tracing_src, 1)}",
        f"    prompts: {_fmt_bool(ls_prompts)}{_cmt(ls_prompts_src, 1)}",
        f"    endpoint: {_fmt_str(ls_endpoint)}{_cmt(ls_endpoint_src, 1)}",
        f"    prompt_prefix: {_fmt_str(ls_prefix)}{_cmt(ls_prefix_src, 1)}",
        "  langfuse:",
        f"    tracing: {_fmt_bool(lf_tracing)}{_cmt(lf_tracing_src, 1)}",
        f"    prompts: {_fmt_bool(lf_prompts)}{_cmt(lf_prompts_src, 1)}",
        f"    host: {_fmt_str(lf_host)}{_cmt(lf_host_src, 1)}",
        f"    prompt_prefix: {_fmt_str(lf_prefix)}{_cmt(lf_prefix_src, 1)}",
        "",
    ]

    # user_agent
    lines += [
        "# ---------------------------------------------------------------------------",
        "# Miscellaneous",
        "# ---------------------------------------------------------------------------",
        f"user_agent: {_fmt_str(user_agent)}{_cmt(user_agent_src, 1)}",
    ]

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse arguments, load env, and emit the generated config.yml."""
    parser = argparse.ArgumentParser(
        prog="generate-config.py",
        description=(
            "Generate a config.yml from an existing .env file or environment variables. "
            "Secrets are never written to the output."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/generate-config.py                           # reads ROOT_DIR/.env → config.yml\n"
            "  python scripts/generate-config.py --output other.yml        # writes to a different file\n"
            "  python scripts/generate-config.py --env-file /other/.env    # reads a specific .env file\n"
        ),
    )
    parser.add_argument(
        "--env-file",
        metavar="PATH",
        type=Path,
        default=None,
        help="Path to the .env file to read (default: ROOT_DIR/.env).",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        type=Path,
        default=Path("config.yml"),
        help="Output path for the generated file (default: config.yml).",
    )
    args = parser.parse_args()

    env_file: Path | None = args.env_file or (ROOT_DIR / ".env")
    assert env_file is not None  # satisfy type checker; always set above

    if env_file.exists():
        load_dotenv(env_file)
        loaded_from: Path | None = env_file
    elif args.env_file:
        # Explicit file was requested but not found — hard error.
        print(f"Error: env file not found: {env_file}", file=sys.stderr)
        sys.exit(1)
    else:
        # Default .env not present — proceed with current environment only.
        loaded_from = None

    yaml_content = _generate_yaml(loaded_from)

    if args.output.exists():
        print(
            f"Error: {args.output} already exists. Remove it or use --output to specify a different path.",
            file=sys.stderr,
        )
        sys.exit(1)
    args.output.write_text(yaml_content, encoding="utf-8")
    print(f"Done. config.yml written to {args.output.resolve()}", file=sys.stderr)
    print(
        "Review the file, then remove any non-secret variables from your .env "
        "(keep only secrets listed in dotenv.template).",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
