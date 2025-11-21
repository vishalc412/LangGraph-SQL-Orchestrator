"""
Unit tests for SQL query validator.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.postgres_agent.database.query_validator import (
    SQLQueryValidator,
    SQLValidationError
)


class TestSQLQueryValidator:
    """Test cases for SQLQueryValidator."""

    def setup_method(self):
        """Setup test fixtures."""
        self.validator = SQLQueryValidator()

    def test_valid_select_query(self):
        """Test that valid SELECT queries pass validation."""
        query = "SELECT * FROM movies WHERE release_year = 2020"
        is_valid, errors = self.validator.validate(query)

        assert is_valid is True
        assert len(errors) == 0

    def test_valid_complex_query(self):
        """Test that valid complex SELECT queries pass validation."""
        query = """
        SELECT m.title, r.imdb_rating
        FROM movies m
        JOIN ratings r ON m.movie_id = r.movie_id
        WHERE r.imdb_rating > 8.0
        ORDER BY r.imdb_rating DESC
        LIMIT 10
        """
        is_valid, errors = self.validator.validate(query)

        assert is_valid is True
        assert len(errors) == 0

    def test_blocked_drop_keyword(self):
        """Test that DROP keyword is blocked."""
        query = "DROP TABLE movies"
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert any("DROP" in error for error in errors)

    def test_blocked_delete_keyword(self):
        """Test that DELETE keyword is blocked."""
        query = "DELETE FROM movies WHERE id = 1"
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert any("DELETE" in error for error in errors)

    def test_blocked_update_keyword(self):
        """Test that UPDATE keyword is blocked."""
        query = "UPDATE movies SET title = 'New Title' WHERE id = 1"
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert any("UPDATE" in error for error in errors)

    def test_blocked_insert_keyword(self):
        """Test that INSERT keyword is blocked."""
        query = "INSERT INTO movies (title) VALUES ('New Movie')"
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert any("INSERT" in error for error in errors)

    def test_blocked_truncate_keyword(self):
        """Test that TRUNCATE keyword is blocked."""
        query = "TRUNCATE TABLE movies"
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert any("TRUNCATE" in error for error in errors)

    def test_sql_injection_or_1_equals_1(self):
        """Test that OR 1=1 injection pattern is detected."""
        query = "SELECT * FROM movies WHERE id = 1 OR 1=1"
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert any("injection" in error.lower() for error in errors)

    def test_sql_injection_string_equals(self):
        """Test that string equality injection is detected."""
        query = "SELECT * FROM movies WHERE name = 'a' OR 'a'='a'"
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert any("injection" in error.lower() for error in errors)

    def test_multiple_statements_blocked(self):
        """Test that multiple statements are blocked."""
        query = "SELECT * FROM movies; DROP TABLE movies;"
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert any("Multiple statements" in error for error in errors)

    def test_empty_query(self):
        """Test that empty queries are invalid."""
        query = ""
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert len(errors) > 0

    def test_whitespace_only_query(self):
        """Test that whitespace-only queries are invalid."""
        query = "   \n\t   "
        is_valid, errors = self.validator.validate(query)

        assert is_valid is False
        assert len(errors) > 0

    def test_comment_removal(self):
        """Test that comments are removed before validation."""
        query = "SELECT * FROM movies -- DROP TABLE users"
        is_valid, errors = self.validator.validate(query)

        # The query should be valid because the comment is removed
        assert is_valid is True

    def test_validate_and_raise_valid(self):
        """Test validate_and_raise with valid query."""
        query = "SELECT * FROM movies LIMIT 10"
        # Should not raise
        self.validator.validate_and_raise(query)

    def test_validate_and_raise_invalid(self):
        """Test validate_and_raise with invalid query."""
        query = "DROP TABLE movies"
        with pytest.raises(SQLValidationError):
            self.validator.validate_and_raise(query)

    def test_case_insensitive_blocking(self):
        """Test that blocked keywords work case-insensitively."""
        queries = [
            "drop table movies",
            "DROP TABLE movies",
            "Drop Table Movies",
            "DroP TablE Movies"
        ]

        for query in queries:
            is_valid, errors = self.validator.validate(query)
            assert is_valid is False, f"Query should be blocked: {query}"


class TestSQLValidationError:
    """Test cases for SQLValidationError exception."""

    def test_exception_message(self):
        """Test that SQLValidationError has correct message."""
        error = SQLValidationError("Test error message")
        assert str(error) == "Test error message"
