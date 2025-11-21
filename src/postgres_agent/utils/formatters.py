"""
Utilities for formatting query results.
"""

from typing import List, Dict, Any
import json
import io
import csv


def format_as_table(
    results: List[Dict[str, Any]],
    column_names: List[str],
    max_rows: int = 50
) -> str:
    """
    Format results as ASCII table.

    Args:
        results: Query results
        column_names: Column names
        max_rows: Maximum rows to display

    Returns:
        Formatted table string
    """
    if not results:
        return "No results found."

    # Limit rows
    display_results = results[:max_rows]

    # Calculate column widths
    col_widths = {}
    for col in column_names:
        col_widths[col] = max(
            len(str(col)),
            max(len(str(row.get(col, ''))) for row in display_results)
        )

    # Build header
    header = " | ".join(str(col).ljust(col_widths[col]) for col in column_names)
    separator = "-+-".join("-" * col_widths[col] for col in column_names)

    # Build rows
    rows = []
    for row in display_results:
        row_str = " | ".join(
            str(row.get(col, '')).ljust(col_widths[col])
            for col in column_names
        )
        rows.append(row_str)

    # Combine
    table = f"{header}\n{separator}\n" + "\n".join(rows)

    # Add footer if truncated
    if len(results) > max_rows:
        table += f"\n\n... and {len(results) - max_rows} more rows"

    return table


def format_as_json(
    results: List[Dict[str, Any]],
    pretty: bool = True
) -> str:
    """
    Format results as JSON.

    Args:
        results: Query results
        pretty: Whether to pretty-print

    Returns:
        JSON string
    """
    if pretty:
        return json.dumps(results, indent=2, default=str)
    return json.dumps(results, default=str)


def format_as_csv(
    results: List[Dict[str, Any]],
    column_names: List[str]
) -> str:
    """
    Format results as CSV.

    Args:
        results: Query results
        column_names: Column names

    Returns:
        CSV string
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=column_names)

    writer.writeheader()
    for row in results:
        writer.writerow(row)

    return output.getvalue()


def format_as_markdown_table(
    results: List[Dict[str, Any]],
    column_names: List[str],
    max_rows: int = 50
) -> str:
    """
    Format results as Markdown table.

    Args:
        results: Query results
        column_names: Column names
        max_rows: Maximum rows to display

    Returns:
        Markdown table string
    """
    if not results:
        return "No results found."

    # Limit rows
    display_results = results[:max_rows]

    # Build header
    header = "| " + " | ".join(str(col) for col in column_names) + " |"
    separator = "| " + " | ".join("---" for _ in column_names) + " |"

    # Build rows
    rows = []
    for row in display_results:
        row_str = "| " + " | ".join(
            str(row.get(col, '')) for col in column_names
        ) + " |"
        rows.append(row_str)

    # Combine
    table = f"{header}\n{separator}\n" + "\n".join(rows)

    # Add footer if truncated
    if len(results) > max_rows:
        table += f"\n\n*... and {len(results) - max_rows} more rows*"

    return table
