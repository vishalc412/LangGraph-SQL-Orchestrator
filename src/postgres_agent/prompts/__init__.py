"""
Prompts package for SQL generation and result formatting.

This package contains prompt templates and examples for the LLM.
"""

from .templates import get_sql_generation_prompt, get_result_formatting_prompt
from .examples import (
    WINDOW_FUNCTION_EXAMPLES,
    CTE_EXAMPLES,
    SUBQUERY_EXAMPLES,
    ANALYTICAL_EXAMPLES
)

__all__ = [
    "get_sql_generation_prompt",
    "get_result_formatting_prompt",
    "WINDOW_FUNCTION_EXAMPLES",
    "CTE_EXAMPLES",
    "SUBQUERY_EXAMPLES",
    "ANALYTICAL_EXAMPLES"
]
