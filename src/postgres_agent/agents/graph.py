"""
LangGraph graph definition for SQL agent workflow.

This module defines the agent workflow as a state graph with nodes
and conditional edges that determine the flow of execution.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
import logging

from .state import AgentState
from .nodes import AgentNodes
from ..config.settings import get_config

logger = logging.getLogger(__name__)


def create_sql_agent_graph():
    """
    Create LangGraph workflow for SQL agent.

    The workflow follows this pattern:

    START -> retrieve_schema -> generate_sql -> validate_query ->
    (if valid) -> execute_query -> format_response -> END
    (if invalid) -> format_response -> END

    Returns:
        Compiled LangGraph StateGraph
    """
    logger.info("Creating SQL agent graph")

    # Initialize nodes
    nodes = AgentNodes()

    # Create state graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("retrieve_schema", nodes.retrieve_schema)
    workflow.add_node("generate_sql", nodes.generate_sql)
    workflow.add_node("validate_query", nodes.validate_query)
    workflow.add_node("execute_query", nodes.execute_query)
    workflow.add_node("format_response", nodes.format_response)

    # Define edges
    # Start with schema retrieval
    workflow.set_entry_point("retrieve_schema")

    # After schema retrieval, generate SQL
    workflow.add_edge("retrieve_schema", "generate_sql")

    # After SQL generation, validate it
    workflow.add_edge("generate_sql", "validate_query")

    # After validation, conditionally execute or format error
    workflow.add_conditional_edges(
        "validate_query",
        lambda state: "execute" if state.get("query_valid") else "format",
        {
            "execute": "execute_query",
            "format": "format_response"
        }
    )

    # After execution, format response
    workflow.add_edge("execute_query", "format_response")

    # End after formatting
    workflow.add_edge("format_response", END)

    # Setup checkpointer for memory
    config = get_config()

    if config.checkpointer.type == "sqlite":
        try:
            checkpointer = SqliteSaver.from_conn_string(config.checkpointer.sqlite_path)
        except Exception as e:
            logger.warning(f"Failed to create SQLite checkpointer: {e}. Using memory.")
            checkpointer = MemorySaver()
    else:
        checkpointer = MemorySaver()

    # Compile graph
    app = workflow.compile(checkpointer=checkpointer)

    logger.info("SQL agent graph created successfully")

    return app


def run_sql_agent(user_query: str, thread_id: str = "default") -> dict:
    """
    Run SQL agent on a user query.

    Args:
        user_query: User's natural language question
        thread_id: Conversation thread ID for memory

    Returns:
        Final state with formatted response
    """
    logger.info(f"Running SQL agent for query: {user_query[:100]}...")

    # Create initial state
    initial_state = {
        "messages": [],
        "user_query": user_query,
        "sql_query": None,
        "query_explanation": None,
        "query_valid": False,
        "validation_errors": None,
        "query_results": None,
        "column_names": None,
        "formatted_response": None,
        "schema_context": None,
        "error": None,
        "metadata": {}
    }

    # Create graph
    app = create_sql_agent_graph()

    # Run graph with checkpointing
    config = {"configurable": {"thread_id": thread_id}}

    final_state = None
    for state in app.stream(initial_state, config):
        final_state = state

    logger.info("SQL agent execution complete")

    return final_state
