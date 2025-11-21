"""
Agent nodes for LangGraph workflow.

Each node represents a step in the SQL generation and execution pipeline:
1. Schema Retrieval: Get database schema context
2. SQL Generation: Convert natural language to SQL
3. Query Validation: Validate SQL for security and correctness
4. Query Execution: Execute SQL against database
5. Result Formatting: Format results for user
"""

from typing import Dict, Any
import re
import time
import logging

from ..providers import create_provider
from ..database.postgres_client import PostgreSQLClient
from ..database.query_validator import SQLQueryValidator
from ..database.schema_inspector import SchemaInspector
from ..prompts.templates import (
    get_sql_generation_prompt,
    get_result_formatting_prompt
)
from ..config.settings import get_config
from .state import AgentState

logger = logging.getLogger(__name__)


class AgentNodes:
    """
    Collection of agent nodes for the workflow.

    Each method is a node that processes the state and returns updated state.
    """

    def __init__(self):
        """Initialize agent nodes with required components."""
        self.config = get_config()
        self.llm_provider = create_provider()
        self.db_client = PostgreSQLClient()
        self.validator = SQLQueryValidator()
        self.schema_inspector = SchemaInspector(self.db_client)

        logger.info("Agent nodes initialized")

    def retrieve_schema(self, state: AgentState) -> AgentState:
        """
        Node 1: Retrieve database schema context.

        This node gets the database schema and adds it to the state
        so the SQL generation node has context about available tables,
        columns, and relationships.

        Args:
            state: Current agent state

        Returns:
            Updated state with schema_context
        """
        logger.info("Node: retrieve_schema")

        try:
            # Get schema context (cached after first retrieval)
            schema_context = self.schema_inspector.get_schema_context()

            state["schema_context"] = schema_context
            state["metadata"] = state.get("metadata", {})
            state["metadata"]["schema_retrieved"] = True

            logger.info("Schema context retrieved successfully")

        except Exception as e:
            logger.error(f"Error retrieving schema: {e}")
            state["error"] = f"Failed to retrieve database schema: {str(e)}"

        return state

    def generate_sql(self, state: AgentState) -> AgentState:
        """
        Node 2: Generate SQL query from natural language.

        Uses LLM to convert user's question into a SQL query based on
        the database schema context.

        Args:
            state: Current agent state with user_query and schema_context

        Returns:
            Updated state with sql_query and query_explanation
        """
        logger.info("Node: generate_sql")

        try:
            # Build prompt with schema context and user query
            prompt = get_sql_generation_prompt(
                user_query=state["user_query"],
                schema_context=state.get("schema_context", ""),
                conversation_history=state.get("messages", [])
            )

            logger.debug(f"SQL generation prompt length: {len(prompt)} chars")

            # Generate SQL using LLM
            response = self.llm_provider.generate(
                messages=[{"role": "user", "content": prompt}]
            )

            logger.debug(f"LLM response: {response[:200]}...")

            # Parse response to extract SQL and explanation
            sql_query, explanation = self._parse_sql_response(response)

            state["sql_query"] = sql_query
            state["query_explanation"] = explanation

            logger.info(f"SQL generated: {sql_query[:100]}...")

        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            state["error"] = f"Failed to generate SQL query: {str(e)}"
            state["sql_query"] = None

        return state

    def validate_query(self, state: AgentState) -> AgentState:
        """
        Node 3: Validate SQL query for security and correctness.

        Ensures the generated SQL is safe to execute and follows
        security policies (no DROP, DELETE, etc.).

        Args:
            state: Current agent state with sql_query

        Returns:
            Updated state with query_valid and validation_errors
        """
        logger.info("Node: validate_query")

        sql_query = state.get("sql_query")

        if not sql_query:
            state["query_valid"] = False
            state["validation_errors"] = ["No SQL query to validate"]
            return state

        try:
            # Validate query
            is_valid, errors = self.validator.validate(sql_query)

            state["query_valid"] = is_valid
            state["validation_errors"] = errors if errors else None

            if is_valid:
                logger.info("Query validation passed")
            else:
                logger.warning(f"Query validation failed: {errors}")

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            state["query_valid"] = False
            state["validation_errors"] = [f"Validation error: {str(e)}"]

        return state

    def execute_query(self, state: AgentState) -> AgentState:
        """
        Node 4: Execute SQL query against database.

        Executes the validated SQL query and stores results in state.

        Args:
            state: Current agent state with sql_query

        Returns:
            Updated state with query_results and metadata
        """
        logger.info("Node: execute_query")

        if not state.get("query_valid"):
            logger.warning("Skipping query execution - query invalid")
            state["error"] = "Cannot execute invalid query"
            return state

        sql_query = state["sql_query"]

        try:
            start_time = time.time()

            # Execute query
            results, column_names = self.db_client.execute_query_with_description(
                sql_query
            )

            execution_time = time.time() - start_time

            state["query_results"] = results
            state["column_names"] = column_names

            # Update metadata
            metadata = state.get("metadata", {})
            metadata.update({
                "execution_time": execution_time,
                "row_count": len(results),
                "column_count": len(column_names)
            })
            state["metadata"] = metadata

            logger.info(
                f"Query executed successfully. "
                f"Rows: {len(results)}, Time: {execution_time:.3f}s"
            )

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            state["error"] = f"Query execution failed: {str(e)}"
            state["query_results"] = None

        return state

    def format_response(self, state: AgentState) -> AgentState:
        """
        Node 5: Format results into user-friendly response.

        Converts raw query results into a natural language response
        that answers the user's original question.

        Args:
            state: Current agent state with query_results

        Returns:
            Updated state with formatted_response
        """
        logger.info("Node: format_response")

        try:
            # Check if we have results
            if state.get("error"):
                state["formatted_response"] = self._format_error_response(state)
                return state

            if not state.get("query_results"):
                state["formatted_response"] = "No results found for your query."
                return state

            # Build prompt for result formatting
            prompt = get_result_formatting_prompt(
                user_query=state["user_query"],
                sql_query=state["sql_query"],
                query_explanation=state.get("query_explanation"),
                results=state["query_results"],
                column_names=state.get("column_names", [])
            )

            # Generate formatted response
            response = self.llm_provider.generate(
                messages=[{"role": "user", "content": prompt}]
            )

            # Add metadata footer
            metadata = state.get("metadata", {})
            footer = self._format_metadata_footer(metadata)

            state["formatted_response"] = response + "\n\n" + footer

            logger.info("Response formatted successfully")

        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            state["formatted_response"] = (
                f"I found {len(state.get('query_results', []))} results, "
                f"but encountered an error formatting them: {str(e)}"
            )

        return state

    def _parse_sql_response(self, response: str) -> tuple:
        """
        Parse LLM response to extract SQL query and explanation.

        Expected format:
        ```sql
        SELECT ...
        ```

        Explanation: This query ...

        Args:
            response: LLM response text

        Returns:
            Tuple of (sql_query, explanation)
        """
        # Extract SQL from code block
        sql_match = re.search(r'```sql\n(.*?)\n```', response, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
        else:
            # Fallback: look for SELECT statement
            sql_match = re.search(r'(SELECT.*?);?$', response, re.DOTALL | re.IGNORECASE)
            sql_query = sql_match.group(1).strip() if sql_match else response.strip()

        # Extract explanation (text after SQL)
        explanation_match = re.search(r'Explanation:(.*?)$', response, re.DOTALL | re.IGNORECASE)
        explanation = explanation_match.group(1).strip() if explanation_match else ""

        return sql_query, explanation

    def _format_error_response(self, state: AgentState) -> str:
        """Format error response for user."""
        error = state.get("error", "Unknown error")
        return f"I encountered an error: {error}\n\nPlease try rephrasing your question."

    def _format_metadata_footer(self, metadata: Dict[str, Any]) -> str:
        """Format metadata footer with execution details."""
        parts = []

        if "execution_time" in metadata:
            parts.append(f"Execution time: {metadata['execution_time']:.3f}s")

        if "row_count" in metadata:
            parts.append(f"Rows returned: {metadata['row_count']}")

        return " | ".join(parts) if parts else ""
