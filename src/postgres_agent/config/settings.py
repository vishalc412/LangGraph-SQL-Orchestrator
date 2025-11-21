"""
Configuration management for PostgreSQL AI Agent system.

This module uses Pydantic Settings for type-safe configuration management.
All settings can be overridden via environment variables.

Author: AI Agent Development Team
Date: 2025
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal, Optional, List
from pathlib import Path


class OpenAIConfig(BaseSettings):
    """
    OpenAI-specific configuration settings.

    Environment variables should be prefixed with OPENAI_
    Example: OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
    """
    api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4o-mini", description="Model name for SQL generation")
    temperature: float = Field(default=0, ge=0, le=2, description="Sampling temperature (0 for deterministic)")
    max_tokens: int = Field(default=2500, gt=0, description="Maximum tokens in response")
    timeout: int = Field(default=60, description="API timeout in seconds")

    class Config:
        env_prefix = "OPENAI_"


class OllamaConfig(BaseSettings):
    """
    Ollama-specific configuration for local LLM deployment.

    Environment variables should be prefixed with OLLAMA_
    """
    host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    model: str = Field(default="llama3.1", description="Model name (must be pulled first)")
    temperature: float = Field(default=0, ge=0, le=2, description="Sampling temperature")
    timeout: int = Field(default=120, description="API timeout in seconds")

    class Config:
        env_prefix = "OLLAMA_"


class PostgreSQLConfig(BaseSettings):
    """
    PostgreSQL connection configuration.

    Supports both connection string and individual parameter configuration.
    """
    # Connection string (preferred)
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL connection URL (postgresql://user:pass@host:port/db)"
    )

    # Individual connection parameters (fallback)
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(default="movies_db", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="", description="Database password")

    # Connection pool settings
    min_pool_size: int = Field(default=2, description="Minimum connection pool size")
    max_pool_size: int = Field(default=10, description="Maximum connection pool size")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")

    # Query settings
    query_timeout: int = Field(default=30, description="Query execution timeout in seconds")
    max_rows: int = Field(default=1000, description="Maximum rows to return")

    # SSL settings
    ssl_mode: Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"] = Field(
        default="prefer",
        description="SSL mode for connection"
    )

    class Config:
        env_prefix = "POSTGRES_"

    def get_connection_string(self) -> str:
        """
        Get PostgreSQL connection string.

        Returns:
            Complete connection string for psycopg2/SQLAlchemy
        """
        if self.database_url:
            return self.database_url

        # Build connection string from components
        password_part = f":{self.password}" if self.password else ""
        return (
            f"postgresql://{self.user}{password_part}@"
            f"{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.ssl_mode}"
        )


class CheckpointerConfig(BaseSettings):
    """
    Configuration for LangGraph memory checkpointing.

    Supports multiple backend types for state persistence.
    """
    type: Literal["memory", "sqlite", "postgres"] = Field(
        default="sqlite",
        description="Checkpointer backend type"
    )
    sqlite_path: str = Field(
        default="./data/checkpoints.db",
        description="SQLite database path"
    )
    postgres_table: str = Field(
        default="conversation_checkpoints",
        description="PostgreSQL table name for checkpoints"
    )

    class Config:
        env_prefix = "CHECKPOINTER_"


class SecurityConfig(BaseSettings):
    """
    Security-related configuration.
    """
    enable_sql_validation: bool = Field(
        default=True,
        description="Enable SQL query validation before execution"
    )
    allowed_operations: List[str] = Field(
        default=["SELECT"],
        description="Allowed SQL operations"
    )
    blocked_keywords: List[str] = Field(
        default=["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER"],
        description="Blocked SQL keywords"
    )
    enable_audit_log: bool = Field(
        default=True,
        description="Enable audit logging of all queries"
    )
    audit_log_path: str = Field(
        default="./logs/audit.log",
        description="Path to audit log file"
    )

    class Config:
        env_prefix = "SECURITY_"


class AppConfig(BaseSettings):
    """
    Main application configuration combining all sub-configs.

    This is the primary configuration class used throughout the application.
    """
    # Application settings
    app_name: str = Field(default="PostgreSQL AI Agent", description="Application name")
    environment: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # LLM Provider selection
    default_llm_provider: Literal["openai", "ollama"] = Field(
        default="openai",
        description="Default LLM provider"
    )

    # Sub-configurations
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    postgres: PostgreSQLConfig = Field(default_factory=PostgreSQLConfig)
    checkpointer: CheckpointerConfig = Field(default_factory=CheckpointerConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    # Agent settings
    max_conversation_turns: int = Field(
        default=10,
        description="Maximum conversation turns to keep in memory"
    )
    enable_streaming: bool = Field(default=True, description="Enable response streaming")
    enable_query_explanation: bool = Field(
        default=True,
        description="Provide explanations for generated SQL queries"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_llm_config(self, provider: Optional[str] = None):
        """
        Get LLM configuration for specified provider.

        Args:
            provider: LLM provider name ("openai" or "ollama").
                     If None, uses default_llm_provider.

        Returns:
            Configuration object for the specified provider.
        """
        provider = provider or self.default_llm_provider
        if provider == "openai":
            return self.openai
        elif provider == "ollama":
            return self.ollama
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")


# Global configuration instance
# This is initialized once and used throughout the application
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get global configuration instance (singleton pattern).

    Returns:
        AppConfig instance with all settings loaded.
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config():
    """Force reload of configuration (useful for testing)."""
    global _config
    _config = AppConfig()
    return _config
