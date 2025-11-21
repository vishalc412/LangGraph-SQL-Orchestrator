"""
Database schema inspector for providing context to LLM.

This module extracts and formats database schema information in a way
that's optimized for LLM consumption, enabling accurate SQL generation.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class SchemaInspector:
    """
    Inspector for database schema to provide context for SQL generation.

    This class extracts schema information and formats it for LLM consumption.
    Includes tables, columns, relationships, sample values, and statistics.

    Example usage:
        >>> inspector = SchemaInspector()
        >>> schema_context = inspector.get_schema_context()
        >>> # Pass schema_context to LLM prompt for SQL generation
    """

    def __init__(self, client=None):
        """
        Initialize schema inspector.

        Args:
            client: PostgreSQL client. If None, creates new client.
        """
        # Lazy import to avoid circular dependency
        if client is None:
            from .postgres_client import PostgreSQLClient
            client = PostgreSQLClient()

        self.client = client
        self._schema_cache: Optional[str] = None

    def get_schema_context(self, refresh: bool = False) -> str:
        """
        Get formatted schema context for LLM.

        Returns schema information as a formatted string that can be
        included in LLM prompts.

        Args:
            refresh: If True, refresh cached schema information

        Returns:
            Formatted schema context string
        """
        if self._schema_cache is None or refresh:
            self._schema_cache = self._build_schema_context()

        return self._schema_cache

    def _build_schema_context(self) -> str:
        """
        Build comprehensive schema context string.

        Returns:
            Formatted schema context
        """
        logger.info("Building schema context")

        # Get all tables
        tables = self.client.get_all_tables()

        context_parts = [
            "# Database Schema\n",
            f"Database: {self.client.config.database}\n",
            f"Tables: {len(tables)}\n\n"
        ]

        # Add detailed information for each table
        for table_name in tables:
            table_info = self._get_table_context(table_name)
            context_parts.append(table_info)
            context_parts.append("\n")

        # Add relationship information
        relationships = self._get_relationships_context(tables)
        if relationships:
            context_parts.append("\n## Table Relationships\n")
            context_parts.append(relationships)

        context = "".join(context_parts)
        logger.info(f"Schema context built: {len(context)} characters")

        return context

    def _get_table_context(self, table_name: str) -> str:
        """
        Get formatted context for a single table.

        Args:
            table_name: Name of the table

        Returns:
            Formatted table context
        """
        schema_info = self.client.get_table_schema(table_name)

        parts = [f"## Table: {table_name}\n"]

        # Add columns
        parts.append("### Columns:\n")
        for col in schema_info['columns']:
            col_line = f"- {col['column_name']} ({col['data_type']})"

            if col['is_nullable'] == 'NO':
                col_line += " NOT NULL"

            if col['column_name'] in schema_info['primary_keys']:
                col_line += " PRIMARY KEY"

            if col['column_default']:
                col_line += f" DEFAULT {col['column_default']}"

            parts.append(col_line + "\n")

        # Add foreign keys
        if schema_info['foreign_keys']:
            parts.append("\n### Foreign Keys:\n")
            for fk in schema_info['foreign_keys']:
                parts.append(
                    f"- {fk['column_name']} -> "
                    f"{fk['foreign_table_name']}({fk['foreign_column_name']})\n"
                )

        # Add sample values
        sample_query = f"SELECT * FROM {table_name} LIMIT 3"
        try:
            samples = self.client.execute_query(sample_query)
            if samples:
                parts.append("\n### Sample Data:\n")
                for i, row in enumerate(samples, 1):
                    parts.append(f"Row {i}: {dict(row)}\n")
        except Exception as e:
            logger.warning(f"Could not fetch sample data for {table_name}: {e}")

        return "".join(parts)

    def _get_relationships_context(self, tables: List[str]) -> str:
        """
        Get formatted context for table relationships.

        Args:
            tables: List of table names

        Returns:
            Formatted relationships context
        """
        relationships = []

        for table in tables:
            schema_info = self.client.get_table_schema(table)

            for fk in schema_info['foreign_keys']:
                rel = (
                    f"{table}.{fk['column_name']} -> "
                    f"{fk['foreign_table_name']}.{fk['foreign_column_name']}"
                )
                relationships.append(rel)

        if not relationships:
            return ""

        return "\n".join(f"- {rel}" for rel in relationships)

    def get_table_summary(self, table_name: str) -> Dict[str, Any]:
        """
        Get summary statistics for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with summary statistics
        """
        try:
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = self.client.execute_query(count_query, fetch_all=False)
            row_count = result[0]['count'] if result else 0

            # Get table size
            size_query = """
            SELECT pg_size_pretty(pg_total_relation_size(%s)) as size
            """
            size_result = self.client.execute_query(size_query, (table_name,), fetch_all=False)
            table_size = size_result[0]['size'] if size_result else "Unknown"

            return {
                "table_name": table_name,
                "row_count": row_count,
                "size": table_size
            }

        except Exception as e:
            logger.error(f"Error getting table summary: {e}")
            return {
                "table_name": table_name,
                "row_count": 0,
                "size": "Unknown"
            }
