#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Util functions to serve langgraph behind an OpenAI API wrapper."""

import logging
import time
import uuid

from typing import TypedDict

import requests
import tiktoken

from cachetools import TTLCache, cached
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_community.adapters import openai
from langchain_core.messages import BaseMessage
from pydantic import UUID4, BaseModel, Field

import wiki_rag.config as _config_module

from wiki_rag import server
from wiki_rag.config import LOG_LEVEL

logger = logging.getLogger(__name__)


def _default_wrapper_model_name() -> str:
    assert server.context is not None
    return server.context["wrapper_model_name"]


def _default_kb_name() -> str:
    assert server.context is not None
    return server.context["kb_name"]


class Message(TypedDict):
    """Base message class. Simple but enough for OpenAI."""

    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """Chat completion request model. Includes the messages history and the model to use."""

    max_tokens: int | None = 1536  # Max tokens to generate (not all models support this). Deprecated.
    max_completion_tokens: int | None = 1536  # Max tokens to generate (not all models support this).
    temperature: float | None = 0.05  # Temperature for sampling (0.0, deterministic to 2.0, creative).
    top_p: float | None = 0.85  # Which probability (0.0 - 1.0) is used to consider the next token (0.85 default).
    model: str = Field(default_factory=_default_wrapper_model_name)
    messages: list[Message] = [Message(role="user", content="Hello!")]
    stream: bool | None = False


class ChoiceResponse(BaseModel):
    """Choice response model. Includes the completion and the model used."""

    index: int = 0
    message: Message = Message(role="assistant", content="Hello!")


class ChatCompletionResponse(BaseModel):
    """Chat completion response model. Includes the completion and the model used."""

    id: UUID4 = uuid.uuid4()
    object: str = "chat.completion"
    created: int = int(time.time())
    model: str = Field(default_factory=_default_wrapper_model_name)
    choices: list[ChoiceResponse] = [ChoiceResponse()]


class ModelResponse(BaseModel):
    """Information about a LLM model."""

    id: str = Field(default_factory=_default_wrapper_model_name)
    object: str = "model"
    created: int = int(time.time())
    owned_by: str = Field(default_factory=_default_kb_name)


class ModelsListResponse(BaseModel):
    """Information about the available models."""

    object: str = "list"
    data: list[ModelResponse]


def filter_completions_history(
        history: list[Message],
        max_turns_allowed: int,
        max_tokens_allowed: int,
        remove_system_messages: bool) -> list[Message]:
    """Filter the history of completions based on the number of turns and tokens.

    This is used to avoid the model to receive too much history (some clients are
    always sending the whole conversation history)
    """
    # Remove system messages.
    if remove_system_messages:
        history = [msg for msg in history if (msg["role"] != "system" and msg["role"] != "developer")]

    # Filter turns.
    if max_turns_allowed > 0:
        current_turns = _count_turns(history)
        if current_turns > max_turns_allowed:
            keep_messages = max_turns_allowed * 2 + 1
            history = history[-keep_messages:]

    # Filter tokens.
    if max_tokens_allowed > 0:
        current_tokens = _count_tokens(history)
        if current_tokens > max_tokens_allowed:
            # Calculate the start and end pointers to keep.
            end = len(history) - 2  # The last message isn't ever deleted (it's the actual request).
            start = 0
            while start < len(history) and (history[start]["role"] == "assistant" or start + 1 > end):
                start += 1

            # Go calculating start and end until the number of tokens is less than the max.
            while start <= end:
                # The first remaining message cannot be assistant ever.
                if history[start]["role"] == "assistant":
                    current_tokens -= _count_tokens([history[start]])
                    start += 1
                    continue

                # Still too many tokens, remove the first user message.
                if history[start]["role"] == "user":
                    if current_tokens > max_tokens_allowed:
                        current_tokens -= _count_tokens([history[start]])
                        start += 1
                        continue
                    else:
                        break  # We are done, user message is within the allowed tokens.

            history = history[start:]

    return history


def _count_turns(messages: list[Message]) -> int:
    """Count how many "turns" are in the message history."""
    return (len(messages) - 1) // 2


def _count_tokens(messages: list[Message]) -> int:
    """Count how many tokens are in the message history."""
    encoder = tiktoken.get_encoding("gpt2")  # Model is not very important here, differences are minimal.
    return sum([len(encoder.encode(msg["content"])) for msg in messages])


def convert_from_openai_to_langchain(history: list[Message]) -> list[BaseMessage]:
    """Convert the messages to the format expected by langgraph."""
    return [
        openai.convert_dict_to_message(message) for message in history
    ]


async def validate_authentication(auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))):
    """Validate the authentication of the request.

    Requires and Authorization header with a valid token. Two possible methods to validate
    the token are provided:
    - local: If the token is in AUTH_TOKENS environment variable (comma separated list).
    - remote: The token, forwarded with the same Authorization header, is validated against
              a remote service (AUTH_URL) that returns 200 if valid.

    When wrapper.auth_required is false, all requests are allowed through without any token check.
    """
    assert _config_module.cfg is not None, "load_config() must be called before validate_authentication()"
    if not _config_module.cfg.wrapper.auth_required:
        return

    # Ensure that the token is present and is a bearer token.
    if not auth or auth.scheme.lower() != "bearer" or not auth.credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )

    auth_token = auth.credentials

    # Check if the token is in the local list (AUTH_TOKENS env variable).
    authorised = check_token_with_local_env(auth_token)

    # If not authorised yet, check the remote service (AUTH_URL env variable).
    if not authorised:
        authorised = check_token_with_service(auth_token)

    # Arrived here, not authorised, raise an exception.
    if not authorised:
        raise HTTPException(
            status_code=403,
            detail="Invalid authentication credentials"
        )


@cached(cache=TTLCache(maxsize=64, ttl=0 if LOG_LEVEL == "DEBUG" else 300))
def check_token_with_local_env(token: str) -> bool:
    """Check the configured token list to validate the bearer token."""
    assert _config_module.cfg is not None, "load_config() must be called before check_token_with_local_env()"
    allowed_tokens = _config_module.cfg.auth_tokens
    if not allowed_tokens:
        return False

    logger.info("Checking token against configured AUTH_TOKENS list.")
    return token in allowed_tokens


@cached(cache=TTLCache(maxsize=64, ttl=0 if LOG_LEVEL == "DEBUG" else 300))
def check_token_with_service(token: str) -> bool:
    """Check the remote service to validate the token.

    Cached for 5 minutes to avoid hitting the service too often.
    """
    assert _config_module.cfg is not None, "load_config() must be called before check_token_with_service()"
    auth_url = _config_module.cfg.auth_url
    if not auth_url:
        return False

    logger.info(f"Checking token with service: {auth_url}")
    status_code = 500
    try:
        status_code = requests.get(auth_url, headers={"Authorization": f"Bearer {token}"}).status_code
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Error checking token with service {auth_url}: {e}")

    return status_code == 200
