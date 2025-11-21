"""
Main application entry point for PostgreSQL AI Agent.

This module provides CLI and programmatic interfaces for running the agent.
"""

import sys
import argparse
from typing import Optional

from .agents.graph import run_sql_agent, create_sql_agent_graph
from .config.settings import get_config
from .utils.logger import get_logger, setup_logging
from .database.postgres_client import PostgreSQLClient

logger = get_logger(__name__)


def interactive_mode():
    """
    Run agent in interactive CLI mode.

    Allows users to ask questions and see results in real-time.
    Maintains conversation context across queries.
    """
    print("=" * 70)
    print("PostgreSQL AI Agent - Interactive Mode")
    print("=" * 70)
    print("\nType your questions in natural language.")
    print("Type 'exit' or 'quit' to end the session.")
    print("Type 'help' for usage examples.\n")

    config = get_config()
    thread_id = "interactive_session"

    # Test database connection
    print("Testing database connection...")
    try:
        client = PostgreSQLClient()
        if not client.test_connection():
            print("Failed to connect to database. Please check your configuration.")
            return
        print("Database connection successful\n")
        client.close()
    except Exception as e:
        print(f"Database connection error: {e}")
        print("Please check your .env file and database settings.\n")
        return

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break

            if user_input.lower() == 'help':
                print_help()
                continue

            # Run agent
            print("\nProcessing your query...\n")

            result = run_sql_agent(user_input, thread_id=thread_id)

            # Extract and display response
            if result:
                final_state = list(result.values())[-1]  # Get last state

                # Show SQL query (if enabled)
                if config.enable_query_explanation and final_state.get("sql_query"):
                    print("Generated SQL:")
                    print(f"```sql\n{final_state['sql_query']}\n```\n")

                # Show formatted response
                response = final_state.get("formatted_response", "No response generated")
                print(f"Assistant: {response}\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"\nError: {e}\n")


def query_mode(query: str, thread_id: Optional[str] = None):
    """
    Run agent for a single query.

    Args:
        query: User's natural language question
        thread_id: Optional conversation thread ID
    """
    if not thread_id:
        thread_id = "single_query"

    result = run_sql_agent(query, thread_id=thread_id)

    if result:
        final_state = list(result.values())[-1]

        # Print SQL
        if final_state.get("sql_query"):
            print("Generated SQL:")
            print(f"```sql\n{final_state['sql_query']}\n```\n")

        # Print response
        response = final_state.get("formatted_response", "No response generated")
        print(f"Response:\n{response}")


def print_help():
    """Print help information."""
    help_text = """
USAGE EXAMPLES:

1. Simple queries:
   - "Show me all movies from 2020"
   - "What are the highest-rated movies?"

2. Aggregations:
   - "What's the average rating by genre?"
   - "How many movies were released each year?"

3. Complex queries:
   - "Find movies with Tom Hanks and show their ratings"
   - "Which directors have the highest average movie ratings?"
   - "Compare revenue trends between action and drama genres"

4. Analytical queries:
   - "Rank movies by revenue within each genre"
   - "Show year-over-year growth in movie production"

TIPS:
- Be specific about what data you want
- Mention if you want data sorted or limited
- You can reference previous queries in the same session
    """
    print(help_text)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PostgreSQL AI Agent - Natural Language to SQL"
    )

    parser.add_argument(
        "-q", "--query",
        help="Run a single query and exit",
        type=str
    )

    parser.add_argument(
        "-t", "--thread-id",
        help="Conversation thread ID (for memory)",
        type=str,
        default=None
    )

    parser.add_argument(
        "-i", "--interactive",
        help="Run in interactive mode",
        action="store_true"
    )

    parser.add_argument(
        "--log-level",
        help="Set logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level)

    logger.info("Starting PostgreSQL AI Agent")

    try:
        if args.query:
            # Single query mode
            query_mode(args.query, args.thread_id)
        elif args.interactive or len(sys.argv) == 1:
            # Interactive mode (default)
            interactive_mode()
        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
