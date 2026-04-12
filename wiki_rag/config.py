#  Copyright (c) 2026, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Centralised configuration loader for wiki-rag.

Configuration loading order:
  1. The ``.env`` file (if present at ``ROOT_DIR/.env``) is loaded into
     ``os.environ`` via ``load_dotenv()``.
  2. ``config.yml`` (optional, at ``ROOT_DIR/config.yml``) is loaded next;
     YAML values **override** env values for every non-secret field.
  3. Built-in defaults are applied when neither source supplies a value.

Secrets are **always** read exclusively from the environment (env file or real
environment variables); any value for a secret key that appears in the YAML
file is silently ignored with a warning.

After loading, the resolved ``Config`` instance is stored in the module-level
singleton :data:`cfg`.  All application code that needs configuration should
either call :func:`load_config` at startup or import ``cfg`` from this module
after startup has completed.

Note on ``LOG_LEVEL``: it is exposed as a module-level constant (read at
import time) because it is referenced by ``@cached`` decorator TTL expressions
in ``search/util.py`` and ``server/util.py``, which are evaluated at class/
function definition time — before ``load_config()`` is ever called.
"""

import dataclasses
import logging
import os
import sys

from pathlib import Path
from typing import Any

import yaml

from dotenv import load_dotenv

from wiki_rag import ROOT_DIR, __version__

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# LOG_LEVEL must be read at import time; it cannot come from .env or
# config.yml because those are loaded later, after module-level decorators
# have already been evaluated.  Set LOG_LEVEL via the real environment only.
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Module-level singleton populated by load_config().
cfg: "Config | None" = None

# Default user agent template (version placeholder resolved at load time).
_DEFAULT_USER_AGENT: str = (
    "Moodle Research Wiki-RAG Crawler/{version} (https://github.com/moodlehq/wiki-rag)"
)

# Environment variable names that must NEVER be read from the YAML file.
_SECRETS: frozenset[str] = frozenset({
    "OPENAI_API_KEY",
    "EMBEDDING_API_KEY",
    "CONTEXTUALISATION_API_KEY",
    "HYDE_API_KEY",
    "LANGSMITH_API_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "AUTH_TOKENS",
    "AUTH_URL",
    "MILVUS_TOKEN",
    "CHROMA_URL",
    "CHROMA_PATH",
})


# ---------------------------------------------------------------------------
# Nested configuration dataclasses
# ---------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class MediawikiConfig:
    """Configuration for a single MediaWiki site."""

    url: str
    namespaces: list[int]
    excluded: dict[str, list[str]]
    keep_templates: list[str]


@dataclasses.dataclass(frozen=True)
class LoaderConfig:
    """Loader / crawler configuration."""

    dump_path: Path
    rate_limiting: bool


@dataclasses.dataclass(frozen=True)
class SearchConfig:
    """Search and RAG generation configuration."""

    prompt_name: str
    product: str
    task_def: str
    kb_name: str
    distance_cutoff: float
    max_completion_tokens: int
    temperature: float
    top_p: float
    hyde_enabled: bool
    hyde_passages: int


@dataclasses.dataclass(frozen=True)
class WrapperConfig:
    """OpenAI-compatible HTTP server configuration."""

    api_base: str
    chat_max_turns: int
    chat_max_tokens: int
    # May be empty string; callers fall back to collection_name at use time.
    model_name: str


@dataclasses.dataclass(frozen=True)
class McpConfig:
    """MCP server configuration."""

    api_base: str


@dataclasses.dataclass(frozen=True)
class MilvusConfig:
    """Milvus vector store connection configuration (non-secret part)."""

    url: str


@dataclasses.dataclass(frozen=True)
class LangsmithConfig:
    """LangSmith tracing and prompt management configuration."""

    tracing: bool
    prompts: bool
    endpoint: str | None
    prompt_prefix: str


@dataclasses.dataclass(frozen=True)
class LangfuseConfig:
    """Langfuse tracing and prompt management configuration."""

    tracing: bool
    prompts: bool
    host: str | None
    prompt_prefix: str


@dataclasses.dataclass(frozen=True)
class Config:
    """Fully resolved configuration for wiki-rag.

    All settings are resolved from the ``.env`` file, ``config.yml``, or
    built-in defaults.  Secret fields (API keys, tokens, passwords) are
    populated exclusively from environment variables; any YAML value for a
    secret field is silently ignored with a warning.

    Multi-site support: ``sites`` holds one :class:`MediawikiConfig` per
    configured MediaWiki instance.  For backward compatibility, the
    :attr:`mediawiki` property returns ``sites[0]``; all existing call sites
    are unaffected.  Currently only the first site is loaded/indexed.
    """

    sites: list[MediawikiConfig]
    loader: LoaderConfig
    collection_name: str
    index_vendor: str
    embedding_model: str
    embedding_dimensions: int
    openai_model: str
    contextualisation_model: str | None
    hyde_model: str | None
    # ------------------------------------------------------------------
    # OpenAI-compatible provider API base URLs and per-model API keys.
    # openai_api_base (env: OPENAI_API_BASE / YAML: openai.api_base) and
    # openai_model (env: LLM_MODEL / YAML: openai.model) are the mandatory
    # general fallbacks; per-model overrides are YAML-only and optional
    # (None means "use the general value").
    # Per-model API keys are env secrets; OPENAI_API_KEY is the env-based
    # general fallback for all clients.
    # ------------------------------------------------------------------
    openai_api_base: str
    embedding_api_base: str | None
    contextualisation_api_base: str | None
    hyde_api_base: str | None
    embedding_api_key: str | None
    contextualisation_api_key: str | None
    hyde_api_key: str | None
    search: SearchConfig
    wrapper: WrapperConfig
    mcp: McpConfig
    milvus: MilvusConfig
    langsmith: LangsmithConfig
    langfuse: LangfuseConfig
    user_agent: str
    log_level: str
    # ------------------------------------------------------------------
    # Secret fields: always from environment only, never from YAML.
    # ------------------------------------------------------------------
    openai_api_key: str | None
    langsmith_api_key: str | None
    langfuse_secret_key: str | None
    langfuse_public_key: str | None
    auth_tokens: list[str]   # parsed from comma-separated env value
    auth_url: str | None
    milvus_token: str | None
    chroma_url: str | None
    chroma_path: str | None

    @property
    def mediawiki(self) -> MediawikiConfig:
        """Backward-compatible accessor for the primary (first) site.

        Returns:
            The first entry in :attr:`sites`.

        """
        return self.sites[0]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _resolve_yaml(yaml_data: dict[str, Any], dotted_path: str) -> Any:
    """Return the value at *dotted_path* inside *yaml_data*, or ``None``.

    Args:
        yaml_data: Parsed top-level YAML mapping.
        dotted_path: Dot-separated key path, e.g. ``"mediawiki.url"``.

    Returns:
        The value at the path, or ``None`` if any intermediate key is absent.

    """
    current: Any = yaml_data
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _parse_namespaces(raw: str | list | None) -> list[int]:
    """Parse MediaWiki namespace IDs from env string or YAML list.

    Args:
        raw: Comma-separated string (from env) or list of ints (from YAML).

    Returns:
        Deduplicated, sorted list of integer namespace IDs.

    """
    if not raw and raw != 0:
        return []
    if isinstance(raw, list):
        return sorted(set(int(n) for n in raw))
    return sorted(set(int(ns.strip()) for ns in str(raw).split(",") if ns.strip()))


def _parse_list(raw: str | list | None) -> list[str]:
    """Parse a comma-separated string or YAML list into a list of strings.

    Args:
        raw: Comma-separated string (from env) or list (from YAML).

    Returns:
        List of stripped, non-empty string values.

    """
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [item.strip() for item in str(raw).split(",") if item.strip()]


def _parse_excluded(raw: str | dict | None) -> dict[str, list[str]]:
    """Parse MediaWiki exclusion rules.

    Accepts either the env-format semicolon-separated string
    (``"categories:A, B;wikitext:regex"``) or a YAML dict
    (``{"categories": ["A", "B"], "wikitext": ["regex"]}``).

    Args:
        raw: Raw exclusion value from env or YAML.

    Returns:
        Mapping of exclusion type to list of values.

    """
    if not raw:
        return {}
    if isinstance(raw, dict):
        return {k: _parse_list(v) for k, v in raw.items()}
    result: dict[str, list[str]] = {}
    for exclusion in str(raw).split(";"):
        if ":" not in exclusion:
            continue
        exclusion_type, exclusion_values = exclusion.split(":", 1)
        result[exclusion_type.strip()] = [v.strip() for v in exclusion_values.split(",") if v.strip()]
    return result


def _parse_bool(raw: str | bool | None, default: bool = False) -> bool:
    """Coerce a string or native bool to Python bool.

    Args:
        raw: String (``"true"``/``"false"``) or native bool from YAML.
        default: Value to return when *raw* is ``None`` or empty.

    Returns:
        Resolved boolean value.

    """
    if raw is None or raw == "":
        return default
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() == "true"


def _parse_int(raw: str | int | None, default: int = 0) -> int:
    """Coerce a string or native int to Python int.

    Args:
        raw: String or int value.
        default: Value to return when *raw* is ``None`` or empty.

    Returns:
        Resolved integer value.

    """
    if raw is None or raw == "":
        return default
    return int(raw)


def _parse_float(raw: str | float | None, default: float = 0.0) -> float:
    """Coerce a string or native float to Python float.

    Args:
        raw: String or float value.
        default: Value to return when *raw* is ``None`` or empty.

    Returns:
        Resolved float value.

    """
    if raw is None or raw == "":
        return default
    return float(raw)


def _get(
    env_key: str,
    yaml_data: dict[str, Any],
    yaml_path: str,
    default: Any = None,
) -> Any:
    """Resolve a single non-secret configuration value.

    YAML value takes precedence over env value; env value takes precedence
    over *default*.

    Args:
        env_key: Environment variable name.
        yaml_data: Top-level parsed YAML mapping.
        yaml_path: Dotted path for the YAML lookup.
        default: Fallback when neither source provides a value.

    Returns:
        Resolved raw value (str, int, bool, list, dict, or None).

    """
    env_val = os.environ.get(env_key)
    yaml_val = _resolve_yaml(yaml_data, yaml_path)
    if yaml_val is not None:
        return yaml_val
    if env_val is not None:
        return env_val
    return default


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config(command: str, config_path: Path | None = None) -> Config:
    """Load and validate configuration for the given command.

    Loading order:
      1. ``.env`` file (if present at ``ROOT_DIR/.env``) via ``load_dotenv()``.
      2. ``config.yml`` (optional; YAML values override env values).
      3. Built-in defaults.

    Secrets are always read from the environment only.

    Args:
        command: Active command; determines which fields are required.
            One of ``"load"``, ``"index"``, ``"search"``, ``"server"``,
            ``"mcp"``.
        config_path: Explicit path to ``config.yml``.  Defaults to
            ``ROOT_DIR/config.yml``.

    Returns:
        Fully populated and validated :class:`Config` instance (also stored
        in the module-level :data:`cfg` singleton).

    Raises:
        SystemExit: When a required setting is missing for the given command.

    """
    global cfg

    # ------------------------------------------------------------------
    # 1. Load .env file if present.
    # ------------------------------------------------------------------
    dotenv_file = ROOT_DIR / ".env"
    if dotenv_file.exists():
        logger.warning("Loading environment variables from %s", dotenv_file)
        logger.warning(
            "Note: .env files are not supposed to be used in production. "
            "Use env secrets instead."
        )
        load_dotenv(dotenv_file)

    # ------------------------------------------------------------------
    # 2. Load config.yml if present.
    # ------------------------------------------------------------------
    yaml_data: dict[str, Any] = {}
    resolved_config_path = config_path or (ROOT_DIR / "config.yml")
    if resolved_config_path.exists():
        logger.info("Loading configuration from %s", resolved_config_path)
        with open(resolved_config_path) as f:
            loaded = yaml.safe_load(f)
            if isinstance(loaded, dict):
                yaml_data = loaded
    elif dotenv_file.exists():
        logger.warning("=" * 72)
        logger.warning(
            "DEPRECATION WARNING: Non-secret configuration via .env is deprecated "
            "and will be removed in a future release. "
            "Please migrate your settings to config.yml."
        )
        logger.warning(
            "Run 'python scripts/generate-config.py' to generate config.yml "
            "from your current .env file."
        )
        logger.warning("=" * 72)

    # Convenience: partial application binding yaml_data.
    def _v(env_key: str, yaml_path: str, default: Any = None) -> Any:
        return _get(env_key, yaml_data, yaml_path, default)

    def _require(value: Any, label: str, env_key: str) -> Any:
        """Exit with error when a required value is absent."""
        if value is None or value == "":
            logger.error("%s (%s) not found in configuration. Exiting.", label, env_key)
            sys.exit(1)
        return value

    # ------------------------------------------------------------------
    # 3. Resolve all settings.
    # ------------------------------------------------------------------

    # --- Core (all commands) ---
    mediawiki_url = _v("MEDIAWIKI_URL", "mediawiki.url")
    mediawiki_namespaces_raw = _v("MEDIAWIKI_NAMESPACES", "mediawiki.namespaces")
    loader_dump_path_raw = _v("LOADER_DUMP_PATH", "loader.dump_path", "")
    collection_name = _v("COLLECTION_NAME", "collection.name")
    index_vendor = _v("INDEX_VENDOR", "index.vendor", "milvus")

    # --- Loader-only ---
    excluded_raw = _v("MEDIAWIKI_EXCLUDED", "mediawiki.excluded")
    keep_templates_raw = _v("MEDIAWIKI_KEEP_TEMPLATES", "mediawiki.keep_templates")
    rate_limiting_raw = _v("ENABLE_RATE_LIMITING", "loader.rate_limiting", "true")

    # --- OpenAI-compatible provider API base URL and model (env var + YAML for defaults) ---
    # Per-model overrides are YAML-only; only the general fields support env vars.
    openai_api_base = _v("OPENAI_API_BASE", "openai.api_base", "") or ""
    embedding_api_base = _resolve_yaml(yaml_data, "embedding.api_base") or None
    contextualisation_api_base = _resolve_yaml(yaml_data, "search.contextualisation.api_base") or None
    hyde_api_base = _resolve_yaml(yaml_data, "search.hyde.api_base") or None

    # --- Per-model API keys (env secrets; OPENAI_API_KEY is the general fallback) ---
    embedding_api_key = os.environ.get("EMBEDDING_API_KEY") or None
    contextualisation_api_key = os.environ.get("CONTEXTUALISATION_API_KEY") or None
    hyde_api_key = os.environ.get("HYDE_API_KEY") or None

    # --- Embedding (index, search, server, mcp) ---
    embedding_model = _v("EMBEDDING_MODEL", "embedding.model")
    embedding_dimensions_raw = _v("EMBEDDING_DIMENSIONS", "embedding.dimensions")

    # --- Models (search, server, mcp) ---
    # openai_model is the general model; env var LLM_MODEL kept for backward compatibility.
    openai_model = _v("LLM_MODEL", "openai.model")
    contextualisation_model = _v("CONTEXTUALISATION_MODEL", "search.contextualisation.model") or None
    hyde_model = _resolve_yaml(yaml_data, "search.hyde.model") or None

    # --- Search (search, server, mcp) ---
    prompt_name = _v("SEARCH_PROMPT_NAME", "search.prompt_name", "wiki-rag")
    product = _v("SEARCH_PRODUCT", "search.product", "Moodle")
    task_def = _v("SEARCH_TASK_DEF", "search.task_def", "Moodle user documentation")
    kb_name = _v("SEARCH_KB_NAME", "search.kb_name", "Moodle Docs")
    distance_cutoff_raw = _v("SEARCH_DISTANCE_CUTOFF", "search.distance_cutoff", "0.6")
    max_completion_tokens_raw = _v("SEARCH_MAX_COMPLETION_TOKENS", "openai.max_completion_tokens", "1536")
    temperature_raw = _v("SEARCH_TEMPERATURE", "openai.temperature", "0.05")
    top_p_raw = _v("SEARCH_TOP_P", "openai.top_p", "0.85")
    hyde_enabled_raw = _v("SEARCH_HYDE_ENABLED", "search.hyde.enabled", "false")
    hyde_passages_raw = _v("SEARCH_HYDE_PASSAGES", "search.hyde.passages", "1")

    # --- Wrapper (server) ---
    wrapper_api_base = _v("WRAPPER_API_BASE", "wrapper.api_base")
    wrapper_chat_max_turns_raw = _v("WRAPPER_CHAT_MAX_TURNS", "wrapper.chat_max_turns", "0")
    wrapper_chat_max_tokens_raw = _v("WRAPPER_CHAT_MAX_TOKENS", "wrapper.chat_max_tokens", "0")
    wrapper_model_name = _v("WRAPPER_MODEL_NAME", "wrapper.model_name", "") or ""

    # --- MCP ---
    mcp_api_base = _v("MCP_API_BASE", "mcp.api_base")

    # --- Milvus (non-secret connection URL) ---
    milvus_url = _v("MILVUS_URL", "milvus.url", "")

    # --- LangSmith (non-secret settings) ---
    langsmith_tracing_raw = _v("LANGSMITH_TRACING", "observability.langsmith.tracing", "false")
    langsmith_prompts_raw = _v("LANGSMITH_PROMPTS", "observability.langsmith.prompts", "false")
    langsmith_endpoint = _v("LANGSMITH_ENDPOINT", "observability.langsmith.endpoint") or None
    langsmith_prompt_prefix = _v("LANGSMITH_PROMPT_PREFIX", "observability.langsmith.prompt_prefix", "") or ""

    # --- Langfuse (non-secret settings) ---
    langfuse_tracing_raw = _v("LANGFUSE_TRACING", "observability.langfuse.tracing", "false")
    langfuse_prompts_raw = _v("LANGFUSE_PROMPTS", "observability.langfuse.prompts", "false")
    langfuse_host = _v("LANGFUSE_HOST", "observability.langfuse.host") or None
    langfuse_prompt_prefix = _v("LANGFUSE_PROMPT_PREFIX", "observability.langfuse.prompt_prefix", "") or ""

    # --- User agent ---
    user_agent_raw = _v("USER_AGENT", "user_agent", _DEFAULT_USER_AGENT)
    user_agent = str(user_agent_raw).format(version=__version__)

    # --- Log level ---
    log_level = (os.environ.get("LOG_LEVEL") or "INFO").upper()

    # --- Secrets (env only) ---
    openai_api_key = os.environ.get("OPENAI_API_KEY") or None
    langsmith_api_key = os.environ.get("LANGSMITH_API_KEY") or None
    langfuse_secret_key = os.environ.get("LANGFUSE_SECRET_KEY") or None
    langfuse_public_key = os.environ.get("LANGFUSE_PUBLIC_KEY") or None
    auth_tokens_raw = os.environ.get("AUTH_TOKENS") or ""
    auth_url = os.environ.get("AUTH_URL") or None
    milvus_token = os.environ.get("MILVUS_TOKEN") or None
    chroma_url = os.environ.get("CHROMA_URL") or None
    chroma_path = os.environ.get("CHROMA_PATH") or None

    # ------------------------------------------------------------------
    # 4. Type coercion.
    # ------------------------------------------------------------------

    # Site-0 (primary) settings from env / mediawiki: YAML section.
    mediawiki_namespaces = _parse_namespaces(mediawiki_namespaces_raw)
    excluded = _parse_excluded(excluded_raw)
    keep_templates = _parse_list(keep_templates_raw)

    # Build the sites list.
    # If 'sites:' is present in YAML it takes precedence; each list item is a
    # per-site dict.  Env vars (MEDIAWIKI_URL etc.) act as defaults for sites[0]
    # only.  For sites[1..n], all fields must be supplied in the YAML.
    # If 'sites:' is absent, fall back to a single-element list built from the
    # mediawiki: YAML section + env vars (backward-compatible behaviour).
    yaml_sites_raw = _resolve_yaml(yaml_data, "sites")
    if yaml_sites_raw and isinstance(yaml_sites_raw, list):
        sites: list[MediawikiConfig] = []
        for i, site_dict in enumerate(yaml_sites_raw):
            if not isinstance(site_dict, dict):
                continue
            if i == 0:
                # Env vars and mediawiki: YAML section fill any omitted fields.
                s_url = site_dict.get("url") or mediawiki_url or ""
                s_ns = _parse_namespaces(site_dict.get("namespaces") or mediawiki_namespaces_raw)
                s_excl = _parse_excluded(site_dict.get("excluded") or excluded_raw)
                s_keep = _parse_list(site_dict.get("keep_templates") or keep_templates_raw)
            else:
                s_url = site_dict.get("url") or ""
                s_ns = _parse_namespaces(site_dict.get("namespaces"))
                s_excl = _parse_excluded(site_dict.get("excluded"))
                s_keep = _parse_list(site_dict.get("keep_templates"))
            sites.append(MediawikiConfig(
                url=str(s_url),
                namespaces=s_ns,
                excluded=s_excl,
                keep_templates=s_keep,
            ))
    else:
        # BC: single site from mediawiki: YAML + env vars.
        sites = [MediawikiConfig(
            url=str(mediawiki_url or ""),
            namespaces=mediawiki_namespaces,
            excluded=excluded,
            keep_templates=keep_templates,
        )]

    rate_limiting = _parse_bool(rate_limiting_raw, default=True)
    embedding_dimensions = _parse_int(embedding_dimensions_raw)
    distance_cutoff = _parse_float(distance_cutoff_raw, default=0.6)
    max_completion_tokens = _parse_int(max_completion_tokens_raw, default=1536)
    temperature = _parse_float(temperature_raw, default=0.05)
    top_p = _parse_float(top_p_raw, default=0.85)
    hyde_enabled = _parse_bool(hyde_enabled_raw, default=False)
    hyde_passages = _parse_int(hyde_passages_raw, default=1)
    wrapper_chat_max_turns = _parse_int(wrapper_chat_max_turns_raw, default=0)
    wrapper_chat_max_tokens = _parse_int(wrapper_chat_max_tokens_raw, default=0)
    langsmith_tracing = _parse_bool(langsmith_tracing_raw, default=False)
    langsmith_prompts = _parse_bool(langsmith_prompts_raw, default=False)
    langfuse_tracing = _parse_bool(langfuse_tracing_raw, default=False)
    langfuse_prompts = _parse_bool(langfuse_prompts_raw, default=False)
    auth_tokens = _parse_list(auth_tokens_raw)

    # Resolve dump path: default to ROOT_DIR/data.
    if loader_dump_path_raw:
        loader_dump_path = Path(str(loader_dump_path_raw))
    else:
        loader_dump_path = ROOT_DIR / "data"

    # Validate rate_limiting string value from env (must be "true" or "false").
    if (
        not isinstance(rate_limiting_raw, bool)
        and str(rate_limiting_raw).strip().lower() not in {"true", "false", ""}
    ):
        logger.error(
            "ENABLE_RATE_LIMITING (loader.rate_limiting) can only be 'true' or 'false'. Exiting."
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # 5. Ensure data directory exists.
    # ------------------------------------------------------------------
    if not loader_dump_path.exists():
        logger.warning("Data directory %s not found. Creating it.", loader_dump_path)
        try:
            loader_dump_path.mkdir(parents=True)
        except Exception:
            logger.error("Could not create data directory %s. Exiting.", loader_dump_path)
            sys.exit(1)

    # ------------------------------------------------------------------
    # 6. Validate required fields per command.
    # ------------------------------------------------------------------
    all_commands = {"load", "index", "search", "server", "mcp"}
    llm_commands = {"search", "server", "mcp"}
    embedding_commands = {"index", "search", "server", "mcp"}

    if command in all_commands:
        if not sites or not sites[0].url:
            logger.error(
                "MediaWiki URL (MEDIAWIKI_URL / sites[0].url) not found in configuration. Exiting."
            )
            sys.exit(1)
        if not sites[0].namespaces:
            logger.error(
                "MediaWiki namespaces (MEDIAWIKI_NAMESPACES / sites[0].namespaces) "
                "not found in configuration. Exiting."
            )
            sys.exit(1)
        _require(collection_name, "Collection name", "COLLECTION_NAME")

    if command in embedding_commands:
        _require(openai_api_base, "OpenAI API base URL", "OPENAI_API_BASE")
        _require(embedding_model, "Embedding model", "EMBEDDING_MODEL")
        _require(embedding_dimensions_raw, "Embedding dimensions", "EMBEDDING_DIMENSIONS")

    if command in llm_commands:
        _require(openai_model, "OpenAI model (LLM_MODEL / openai.model)", "LLM_MODEL")

    if command == "server":
        _require(wrapper_api_base, "Wrapper API base", "WRAPPER_API_BASE")

    if command == "mcp":
        _require(mcp_api_base, "MCP API base", "MCP_API_BASE")

    # ------------------------------------------------------------------
    # 7. Validate observability conditional requirements.
    # ------------------------------------------------------------------
    if command in llm_commands:
        if langsmith_tracing or langsmith_prompts:
            _require(langsmith_endpoint, "LangSmith endpoint", "LANGSMITH_ENDPOINT")
            _require(langsmith_api_key, "LangSmith API key", "LANGSMITH_API_KEY")
        if langfuse_tracing or langfuse_prompts:
            _require(langfuse_host, "Langfuse host", "LANGFUSE_HOST")
            _require(langfuse_public_key, "Langfuse public key", "LANGFUSE_PUBLIC_KEY")
            _require(langfuse_secret_key, "Langfuse secret key", "LANGFUSE_SECRET_KEY")

    # ------------------------------------------------------------------
    # 8. Propagate settings to os.environ for third-party SDK consumption.
    # ------------------------------------------------------------------
    # OPENAI_API_KEY and base_url are now passed explicitly to each model
    # client via api_key= and base_url= respectively.  No implicit write needed.

    # LangSmith SDK reads LANGSMITH_PROJECT and LANGSMITH_PROMPT_PREFIX.
    if langsmith_tracing or langsmith_prompts:
        os.environ["LANGSMITH_PROJECT"] = collection_name or ""
        os.environ["LANGSMITH_PROMPT_PREFIX"] = langsmith_prompt_prefix

    # ------------------------------------------------------------------
    # 9. Assemble Config.
    # ------------------------------------------------------------------
    cfg = Config(
        sites=sites,
        loader=LoaderConfig(
            dump_path=loader_dump_path,
            rate_limiting=rate_limiting,
        ),
        collection_name=str(collection_name or ""),
        index_vendor=str(index_vendor or "milvus"),
        embedding_model=str(embedding_model or ""),
        embedding_dimensions=embedding_dimensions,
        openai_model=str(openai_model or ""),
        contextualisation_model=contextualisation_model,
        hyde_model=hyde_model,
        openai_api_base=openai_api_base,
        embedding_api_base=embedding_api_base,
        contextualisation_api_base=contextualisation_api_base,
        hyde_api_base=hyde_api_base,
        embedding_api_key=embedding_api_key,
        contextualisation_api_key=contextualisation_api_key,
        hyde_api_key=hyde_api_key,
        search=SearchConfig(
            prompt_name=str(prompt_name),
            product=str(product),
            task_def=str(task_def),
            kb_name=str(kb_name),
            distance_cutoff=distance_cutoff,
            max_completion_tokens=max_completion_tokens,
            temperature=temperature,
            top_p=top_p,
            hyde_enabled=hyde_enabled,
            hyde_passages=hyde_passages,
        ),
        wrapper=WrapperConfig(
            api_base=str(wrapper_api_base or ""),
            chat_max_turns=wrapper_chat_max_turns,
            chat_max_tokens=wrapper_chat_max_tokens,
            model_name=wrapper_model_name,
        ),
        mcp=McpConfig(
            api_base=str(mcp_api_base or ""),
        ),
        milvus=MilvusConfig(
            url=str(milvus_url),
        ),
        langsmith=LangsmithConfig(
            tracing=langsmith_tracing,
            prompts=langsmith_prompts,
            endpoint=langsmith_endpoint,
            prompt_prefix=langsmith_prompt_prefix,
        ),
        langfuse=LangfuseConfig(
            tracing=langfuse_tracing,
            prompts=langfuse_prompts,
            host=langfuse_host,
            prompt_prefix=langfuse_prompt_prefix,
        ),
        user_agent=user_agent,
        log_level=log_level,
        openai_api_key=openai_api_key,
        langsmith_api_key=langsmith_api_key,
        langfuse_secret_key=langfuse_secret_key,
        langfuse_public_key=langfuse_public_key,
        auth_tokens=auth_tokens,
        auth_url=auth_url,
        milvus_token=milvus_token,
        chroma_url=chroma_url,
        chroma_path=chroma_path,
    )

    return cfg
