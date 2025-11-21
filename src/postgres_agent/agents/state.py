"""
Agent state management for LangGraph workflow.

This module defines the state structure that flows through the agent graph.
State includes conversation history, current query, generated SQL, results, etc.
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add


class AgentState(TypedDict):
    """
    State object that flows through the agent graph.

    This state is passed between nodes and accumulates information
    as the agent processes the user's request.

    Attributes:
        messages: Conversation history (user and assistant messages)
        user_query: Current user's natural language question
        sql_query: Generated SQL query
        query_explanation: Explanation of what the SQL does
        query_valid: Whether SQL passed validation
        validation_errors: List of validation errors (if any)
        query_results: Results from executing SQL
        formatted_response: Final formatted response for user
        schema_context: Database schema information
        error: Error message if something went wrong
        metadata: Additional metadata (execution time, row count, etc.)
    """
    # Conversation context
    messages: Annotated[List[Dict[str, str]], add]  # Accumulated list of messages
    user_query: str

    # SQL generation
    sql_query: Optional[str]
    query_explanation: Optional[str]

    # Validation
    query_valid: bool
    validation_errors: Optional[List[str]]

    # Execution
    query_results: Optional[List[Dict[str, Any]]]
    column_names: Optional[List[str]]

    # Response
    formatted_response: Optional[str]

    # Context
    schema_context: Optional[str]

    # Error handling
    error: Optional[str]

    # Metadata
    metadata: Optional[Dict[str, Any]]
