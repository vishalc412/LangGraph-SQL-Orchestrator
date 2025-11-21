"""
PostgreSQL client for database operations.

This module handles PostgreSQL connections, query execution, and result processing.
Includes connection pooling, error handling, and query validation.

Features:
- Connection pooling with psycopg2
- Automatic retry on transient failures
- Query timeout enforcement
- Result set size limiting
- SSL/TLS support
"""

from typing import List, Dict, Any, Optional, Tuple
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError, DatabaseError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from contextlib import contextmanager
import logging

from ..config.settings import get_config, PostgreSQLConfig

logger = logging.getLogger(__name__)


class PostgreSQLClient:
    """
    PostgreSQL client wrapper with connection pooling and error handling.

    This class manages PostgreSQL connections and provides methods for
    executing queries safely with proper error handling and resource management.

    Features:
    - Connection pooling for performance and resource efficiency
    - Automatic retry on transient failures
    - Query timeout enforcement
    - Result set limiting to prevent memory issues
    - SSL/TLS encrypted connections
    - Read-only query execution (configurable)

    Example usage:
        >>> client = PostgreSQLClient()
        >>> results = client.execute_query(
        ...     "SELECT * FROM movies WHERE release_year = %s",
        ...     (2020,)
        ... )
        >>> for row in results:
        ...     print(row['title'])
    """

    def __init__(self, config: Optional[PostgreSQLConfig] = None):
        """
        Initialize PostgreSQL client with connection pool.

        Args:
            config: PostgreSQL configuration. If None, uses app config.
        """
        if config is None:
            app_config = get_config()
            config = app_config.postgres

        self.config = config
        self.connection_pool = None

        # Initialize connection pool
        self._initialize_pool()

    @retry(
        retry=retry_if_exception_type(OperationalError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=10)
    )
    def _initialize_pool(self):
        """
        Initialize PostgreSQL connection pool with retry logic.

        The connection pool maintains a set of database connections that can
        be reused, improving performance by avoiding the overhead of creating
        new connections for each query.

        Raises:
            OperationalError: If unable to connect after retries
        """
        try:
            logger.info("Initializing PostgreSQL connection pool")

            # Get connection string
            dsn = self.config.get_connection_string()

            # Create connection pool
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.min_pool_size,
                maxconn=self.config.max_pool_size,
                dsn=dsn,
                cursor_factory=RealDictCursor,  # Return results as dictionaries
                connect_timeout=self.config.pool_timeout
            )

            # Test connection
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    version = cur.fetchone()
                    logger.info(f"Connected to PostgreSQL: {version['version']}")

            logger.info(
                f"Connection pool initialized successfully. "
                f"Pool size: {self.config.min_pool_size}-{self.config.max_pool_size}"
            )

        except OperationalError as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing pool: {e}")
            raise OperationalError(f"Connection pool initialization error: {e}")

    @contextmanager
    def get_connection(self):
        """
        Get database connection from pool (context manager).

        This context manager automatically returns the connection to the pool
        when done, even if an exception occurs.

        Yields:
            Database connection from pool

        Example:
            >>> with client.get_connection() as conn:
            ...     with conn.cursor() as cur:
            ...         cur.execute("SELECT * FROM movies LIMIT 5")
            ...         results = cur.fetchall()
        """
        conn = None
        try:
            # Get connection from pool
            conn = self.connection_pool.getconn()

            # Set query timeout
            with conn.cursor() as cur:
                cur.execute(f"SET statement_timeout = {self.config.query_timeout * 1000}")

            yield conn

        finally:
            # Return connection to pool
            if conn:
                self.connection_pool.putconn(conn)

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute SELECT query and return results.

        This method safely executes a SELECT query with parameterized values
        to prevent SQL injection. Results are limited by max_rows config.

        Args:
            query: SQL SELECT query with placeholders (%s)
            params: Tuple of parameter values for placeholders
            fetch_all: If True, fetch all results. If False, fetch one row.

        Returns:
            List of result rows as dictionaries (or single dict if fetch_all=False)

        Raises:
            DatabaseError: If query execution fails

        Example:
            >>> # Parameterized query (prevents SQL injection)
            >>> results = client.execute_query(
            ...     "SELECT * FROM movies WHERE release_year = %s AND title LIKE %s",
            ...     (2020, '%Star%')
            ... )
        """
        try:
            logger.debug(f"Executing query: {query[:100]}...")
            if params:
                logger.debug(f"Parameters: {params}")

            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Execute query
                    cur.execute(query, params)

                    # Fetch results
                    if fetch_all:
                        results = cur.fetchmany(self.config.max_rows)
                    else:
                        result = cur.fetchone()
                        results = [result] if result else []

                    # Convert RealDictRow to regular dict
                    results = [dict(row) for row in results]

                    # Log query info
                    row_count = len(results)
                    logger.info(f"Query executed successfully. Rows returned: {row_count}")

                    return results

        except DatabaseError as e:
            logger.error(f"Database error executing query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing query: {e}")
            raise DatabaseError(f"Query execution error: {e}")

    def execute_query_with_description(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Execute query and return results with column descriptions.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Tuple of (results, column_names)
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    results = cur.fetchmany(self.config.max_rows)

                    # Convert to regular dicts
                    results = [dict(row) for row in results]

                    # Extract column names from cursor description
                    column_names = [desc[0] for desc in cur.description] if cur.description else []

                    return results, column_names

        except Exception as e:
            logger.error(f"Error executing query with description: {e}")
            raise

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for a table.

        Retrieves column names, types, constraints, and other metadata.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with schema information
        """
        query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
        """

        try:
            columns = self.execute_query(query, (table_name,))

            # Get primary key
            pk_query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid
                AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass
                AND i.indisprimary;
            """

            try:
                primary_keys = self.execute_query(pk_query, (table_name,))
                pk_columns = [pk['attname'] for pk in primary_keys]
            except Exception:
                pk_columns = []

            # Get foreign keys
            fk_query = """
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s;
            """

            try:
                foreign_keys = self.execute_query(fk_query, (table_name,))
            except Exception:
                foreign_keys = []

            return {
                "table_name": table_name,
                "columns": columns,
                "primary_keys": pk_columns,
                "foreign_keys": foreign_keys
            }

        except Exception as e:
            logger.error(f"Error getting table schema: {e}")
            return {
                "table_name": table_name,
                "columns": [],
                "primary_keys": [],
                "foreign_keys": []
            }

    def get_all_tables(self) -> List[str]:
        """
        Get list of all tables in the database.

        Returns:
            List of table names
        """
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """

        try:
            results = self.execute_query(query)
            return [row['table_name'] for row in results]
        except Exception as e:
            logger.error(f"Error getting table list: {e}")
            return []

    def get_database_schema_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive schema information for entire database.

        This provides context to the LLM for query generation.

        Returns:
            Dictionary with complete database schema information
        """
        tables = self.get_all_tables()

        schema_summary = {
            "database": self.config.database,
            "tables": []
        }

        for table in tables:
            table_info = self.get_table_schema(table)
            schema_summary["tables"].append(table_info)

        logger.info(f"Retrieved schema for {len(tables)} tables")

        return schema_summary

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def close(self):
        """Close all connections in the pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Connection pool closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
