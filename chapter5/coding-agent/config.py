"""
Configuration for the coding agent
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the coding agent"""
    
    # API Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    
    # Provider selection (anthropic, openai, or openrouter)
    PROVIDER = os.getenv("PROVIDER", "anthropic").lower()
    
    # Default model
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "claude-sonnet-5")
    
    # OpenRouter configuration
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    
    # Agent configuration
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "50"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))
    
    # System configuration
    WORKING_DIRECTORY = os.getenv("WORKING_DIRECTORY", os.getcwd())
    
    @classmethod
    def get_provider(cls) -> str:
        """Get the configured provider"""
        return cls.PROVIDER
    
    @classmethod
    def get_api_key(cls, provider: str = None) -> str:
        """Get API key for specified provider (or configured provider if not specified)"""
        if provider is None:
            provider = cls.PROVIDER
        
        if provider == "anthropic":
            if not cls.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set in .env file")
            return cls.ANTHROPIC_API_KEY
        elif provider == "openai":
            if not cls.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set in .env file")
            return cls.OPENAI_API_KEY
        elif provider == "openrouter":
            if not cls.OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY not set in .env file")
            return cls.OPENROUTER_API_KEY
        else:
            raise ValueError(f"Unknown provider: {provider}. Must be one of: anthropic, openai, openrouter")
    
    @classmethod
    def get_base_url(cls) -> str:
        """Get base URL for the configured provider"""
        if cls.PROVIDER == "openrouter":
            return cls.OPENROUTER_BASE_URL
        return None  # Use default for anthropic/openai

    @staticmethod
    def map_model_to_openrouter(model: str) -> str:
        """Map a native (anthropic/openai) model id to an OpenRouter model id.

        Used by the OpenRouter fallback so a user with ONLY an OPENROUTER_API_KEY
        can still run a task written for a direct provider.

          - already-prefixed ids (contain "/") are passed through unchanged
          - claude-sonnet-* -> anthropic/claude-sonnet-4.6
          - claude-haiku-*  -> anthropic/claude-haiku-4.5
          - claude-opus-*   -> anthropic/claude-opus-4.8
          - any other claude-* -> anthropic/claude-opus-4.8
          - gpt-* / o1-*    -> openai/<model>
          - anything else   -> returned unchanged (best effort)
        """
        if "/" in model:
            return model  # already an OpenRouter id
        m = model.lower()
        if m.startswith("claude"):
            if "haiku" in m:
                return "anthropic/claude-haiku-4.5"
            if "sonnet" in m:
                return "anthropic/claude-sonnet-4.6"
            # opus, or any other/unknown Claude tier -> latest Opus
            return "anthropic/claude-opus-4.8"
        if m.startswith("gpt-") or m.startswith("o1"):
            return f"openai/{model}"
        return model

    @classmethod
    def resolve(cls) -> dict:
        """Resolve the effective (provider, api_key, base_url, model).

        Applies the OpenRouter universal fallback: if the requested direct
        provider (anthropic/openai) has no API key configured, but an
        OPENROUTER_API_KEY is available, transparently route through OpenRouter
        (OpenAI-compatible SDK + prefixed model id). Default behavior is
        unchanged whenever the requested provider's own key is present.

        Returns a dict: {provider, api_key, base_url, model,
                         requested_provider, fell_back}.
        """
        requested = cls.PROVIDER
        model = cls.DEFAULT_MODEL

        # Explicit OpenRouter selection: use as configured (no mapping).
        if requested == "openrouter":
            return {
                "provider": "openrouter",
                "api_key": cls.get_api_key("openrouter"),
                "base_url": cls.OPENROUTER_BASE_URL,
                "model": model,
                "requested_provider": requested,
                "fell_back": False,
            }

        if requested in ("anthropic", "openai"):
            direct_key = cls.ANTHROPIC_API_KEY if requested == "anthropic" else cls.OPENAI_API_KEY
            if direct_key:
                # Direct provider key present -> behave exactly as before.
                return {
                    "provider": requested,
                    "api_key": direct_key,
                    "base_url": None,
                    "model": model,
                    "requested_provider": requested,
                    "fell_back": False,
                }
            # No direct key -> fall back to OpenRouter if we have that key.
            if cls.OPENROUTER_API_KEY:
                return {
                    "provider": "openrouter",
                    "api_key": cls.OPENROUTER_API_KEY,
                    "base_url": cls.OPENROUTER_BASE_URL,
                    "model": cls.map_model_to_openrouter(model),
                    "requested_provider": requested,
                    "fell_back": True,
                }
            key_name = "ANTHROPIC_API_KEY" if requested == "anthropic" else "OPENAI_API_KEY"
            raise ValueError(
                f"No {key_name} set and no OPENROUTER_API_KEY available for fallback. "
                f"Set {key_name} for direct access, or set OPENROUTER_API_KEY to route "
                f"'{requested}' models through OpenRouter."
            )

        raise ValueError(f"Unknown provider: {requested}. Must be one of: anthropic, openai, openrouter")

    @classmethod
    def validate(cls):
        """Validate configuration (fallback-aware)."""
        # resolve() raises a clear error if neither the direct key nor the
        # OpenRouter fallback key is available.
        resolved = cls.resolve()
        provider = cls.get_provider()

        # Validate model name only when using the direct provider path; when we
        # fall back to OpenRouter the model id is remapped/prefixed, so the
        # native naming rules no longer apply.
        if not resolved["fell_back"]:
            if provider == "anthropic" and not cls.DEFAULT_MODEL.startswith("claude"):
                raise ValueError(f"Model '{cls.DEFAULT_MODEL}' is not valid for Anthropic. Use a model starting with 'claude-'")
            elif provider == "openai" and not any(cls.DEFAULT_MODEL.startswith(p) for p in ["gpt-", "o1-"]):
                raise ValueError(f"Model '{cls.DEFAULT_MODEL}' is not valid for OpenAI. Use a model starting with 'gpt-' or 'o1-'")
        # OpenRouter accepts any model name, so no validation needed

