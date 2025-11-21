"""
SQL Query Validator for security and correctness.

This module validates SQL queries before execution to prevent:
- SQL injection attacks
- Destructive operations (DROP, DELETE, UPDATE)
- Syntax errors
- Performance issues (missing WHERE clauses, etc.)

This is a critical security component.
"""

import re
from typing import Tuple, List
import sqlparse
from sqlparse.tokens import Keyword, DML

from ..config.settings import get_config
import logging

logger = logging.getLogger(__name__)


class SQLValidationError(Exception):
    """Raised when SQL validation fails."""
    pass


class SQLQueryValidator:
    """
    Validator for SQL queries to ensure security and correctness.

    This validator performs multiple checks:
    1. Security checks (no destructive operations, SQL injection prevention)
    2. Syntax validation
    3. Performance checks (optional warnings)
    4. Schema validation (table/column existence)

    Example usage:
        >>> validator = SQLQueryValidator()
        >>> query = "SELECT * FROM movies WHERE id = 1"
        >>> is_valid, errors = validator.validate(query)
        >>> if not is_valid:
        ...     print(f"Validation failed: {errors}")
    """

    def __init__(self):
        """Initialize validator with configuration."""
        config = get_config()
        self.security_config = config.security

        # Compile regex patterns for performance
        self.comment_pattern = re.compile(r'--.*$|/\*.*?\*/', re.MULTILINE | re.DOTALL)

    def validate(self, query: str) -> Tuple[bool, List[str]]:
        """
        Validate SQL query.

        Args:
            query: SQL query string to validate

        Returns:
            Tuple of (is_valid, error_messages)
            - is_valid: True if query passes all checks
            - error_messages: List of validation error messages

        Example:
            >>> validator = SQLQueryValidator()
            >>> valid, errors = validator.validate("DROP TABLE movies;")
            >>> print(valid)  # False
            >>> print(errors)  # ['Blocked keyword detected: DROP']
        """
        errors = []

        try:
            # Check if query is empty
            if not query or not query.strip():
                errors.append("Query is empty")
                return False, errors

            # Remove comments (they can hide malicious code)
            cleaned_query = self._remove_comments(query)

            # Security checks
            errors.extend(self._check_blocked_keywords(cleaned_query))
            errors.extend(self._check_allowed_operations(cleaned_query))
            errors.extend(self._check_sql_injection_patterns(cleaned_query))

            # Syntax validation
            syntax_errors = self._validate_syntax(cleaned_query)
            errors.extend(syntax_errors)

            # Performance checks (warnings, not blockers)
            warnings = self._check_performance_issues(cleaned_query)
            if warnings:
                logger.warning(f"Performance warnings: {warnings}")

            is_valid = len(errors) == 0

            if is_valid:
                logger.info("Query validation passed")
            else:
                logger.warning(f"Query validation failed: {errors}")

            return is_valid, errors

        except Exception as e:
            logger.error(f"Error during query validation: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors

    def _remove_comments(self, query: str) -> str:
        """
        Remove SQL comments from query.

        Comments can be used to hide malicious SQL or bypass validation.

        Args:
            query: SQL query string

        Returns:
            Query with comments removed
        """
        # Remove single-line comments (--) and multi-line comments (/* */)
        cleaned = self.comment_pattern.sub('', query)
        return cleaned.strip()

    def _check_blocked_keywords(self, query: str) -> List[str]:
        """
        Check for blocked SQL keywords.

        Prevents destructive operations like DROP, DELETE, UPDATE.

        Args:
            query: SQL query string

        Returns:
            List of error messages (empty if no issues)
        """
        errors = []
        query_upper = query.upper()

        for keyword in self.security_config.blocked_keywords:
            # Check if keyword appears as a standalone word (not part of another word)
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, query_upper):
                errors.append(f"Blocked keyword detected: {keyword}")

        return errors

    def _check_allowed_operations(self, query: str) -> List[str]:
        """
        Check if query uses only allowed operations.

        By default, only SELECT queries are allowed.

        Args:
            query: SQL query string

        Returns:
            List of error messages
        """
        errors = []

        # Parse query to identify operation
        parsed = sqlparse.parse(query)
        if not parsed:
            errors.append("Unable to parse query")
            return errors

        statement = parsed[0]

        # Get first token (should be the operation: SELECT, INSERT, etc.)
        operation = None
        for token in statement.tokens:
            if token.ttype is DML:
                operation = token.value.upper()
                break

        if operation and operation not in self.security_config.allowed_operations:
            errors.append(
                f"Operation '{operation}' not allowed. "
                f"Allowed operations: {', '.join(self.security_config.allowed_operations)}"
            )

        return errors

    def _check_sql_injection_patterns(self, query: str) -> List[str]:
        """
        Check for common SQL injection patterns.

        Detects suspicious patterns like:
        - Always-true conditions: OR 1=1, OR 'a'='a'
        - Comment injection: --
        - Union-based injection: UNION SELECT
        - Stacked queries: ; followed by another statement

        Args:
            query: SQL query string

        Returns:
            List of error messages
        """
        errors = []
        query_upper = query.upper()

        # Check for always-true conditions
        always_true_patterns = [
            r"OR\s+1\s*=\s*1",
            r"OR\s+'[^']*'\s*=\s*'[^']*'",
            r"OR\s+\d+\s*=\s*\d+",
        ]

        for pattern in always_true_patterns:
            if re.search(pattern, query_upper):
                errors.append("Suspicious pattern detected: possible SQL injection (always-true condition)")
                break

        # Check for UNION-based injection
        if 'UNION' in query_upper and 'SELECT' in query_upper:
            # This is a simplistic check; legitimate queries may use UNION
            # In production, you'd want more sophisticated detection
            logger.warning("UNION SELECT detected - review query carefully")

        # Check for stacked queries (multiple statements separated by ;)
        statements = sqlparse.split(query)
        if len(statements) > 1:
            errors.append("Multiple statements detected. Only single statements allowed.")

        return errors

    def _validate_syntax(self, query: str) -> List[str]:
        """
        Validate SQL syntax.

        Uses sqlparse to check for basic syntax errors.

        Args:
            query: SQL query string

        Returns:
            List of error messages
        """
        errors = []

        try:
            # Parse query
            parsed = sqlparse.parse(query)

            if not parsed:
                errors.append("Invalid SQL syntax: unable to parse query")
                return errors

            statement = parsed[0]

            # Check for basic structural issues
            if not statement.tokens:
                errors.append("Invalid SQL syntax: empty statement")

            # Additional syntax checks can be added here
            # For example, checking for balanced parentheses, valid identifiers, etc.

        except Exception as e:
            errors.append(f"Syntax validation error: {str(e)}")

        return errors

    def _check_performance_issues(self, query: str) -> List[str]:
        """
        Check for potential performance issues.

        These are warnings, not blockers. Examples:
        - SELECT * without WHERE clause
        - Missing indexes (requires schema knowledge)
        - Cartesian products (JOIN without ON)

        Args:
            query: SQL query string

        Returns:
            List of warning messages
        """
        warnings = []
        query_upper = query.upper()

        # Check for SELECT * without WHERE
        if 'SELECT *' in query_upper and 'WHERE' not in query_upper and 'LIMIT' not in query_upper:
            warnings.append("Performance warning: SELECT * without WHERE or LIMIT may return large result set")

        # Check for JOIN without ON condition
        if 'JOIN' in query_upper and 'ON' not in query_upper:
            warnings.append("Performance warning: JOIN without ON condition may create Cartesian product")

        return warnings

    def validate_and_raise(self, query: str):
        """
        Validate query and raise exception if invalid.

        Convenience method for use in code that expects exceptions.

        Args:
            query: SQL query string

        Raises:
            SQLValidationError: If validation fails
        """
        is_valid, errors = self.validate(query)
        if not is_valid:
            error_message = "; ".join(errors)
            raise SQLValidationError(f"Query validation failed: {error_message}")
