"""
Prompt templates for SQL generation and result formatting.

This module contains carefully crafted prompts that guide the LLM
to generate accurate SQL queries and format results appropriately.
"""

from typing import List, Dict, Any, Optional


def get_sql_generation_prompt(
    user_query: str,
    schema_context: str,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Generate prompt for SQL query generation.

    This prompt includes:
    - System instructions for SQL generation
    - Database schema context
    - Few-shot examples
    - User's question
    - Conversation history (if available)

    Args:
        user_query: User's natural language question
        schema_context: Database schema information
        conversation_history: Previous conversation turns

    Returns:
        Complete prompt for LLM
    """

    system_instructions = """You are an expert SQL query generator for PostgreSQL databases.

Your task is to convert natural language questions into accurate, efficient SQL queries.

CRITICAL RULES:
1. Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP)
2. Use proper PostgreSQL syntax
3. Always use table aliases for clarity
4. Add appropriate WHERE clauses to filter data
5. Use JOINs when querying multiple tables
6. Include LIMIT clause to prevent returning too many rows (default: 100)
7. Handle NULL values appropriately
8. Use proper date formatting for date queries
9. Generate queries that are safe and performant

OUTPUT FORMAT:
```sql
-- Your SQL query here
SELECT ...
```

Explanation: Brief explanation of what the query does and why you structured it this way.
"""

    few_shot_examples = """
EXAMPLES:

Example 1:
Question: "What are the top 5 highest-rated movies?"
```sql
SELECT m.title, m.release_year, r.imdb_rating
FROM movies m
JOIN ratings r ON m.movie_id = r.movie_id
ORDER BY r.imdb_rating DESC
LIMIT 5;
```
Explanation: This query joins the movies and ratings tables to get movie titles with their ratings, then orders by rating descending and limits to top 5.

Example 2:
Question: "How many movies were released each year in the last decade?"
```sql
SELECT release_year, COUNT(*) as movie_count
FROM movies
WHERE release_year >= EXTRACT(YEAR FROM CURRENT_DATE) - 10
GROUP BY release_year
ORDER BY release_year DESC;
```
Explanation: This query groups movies by year, counts them, and filters for the last 10 years using date arithmetic.

Example 3:
Question: "Show me action movies from 2020 with ratings above 7"
```sql
SELECT m.title, m.release_year, r.imdb_rating
FROM movies m
JOIN movie_genres mg ON m.movie_id = mg.movie_id
JOIN genres g ON mg.genre_id = g.genre_id
JOIN ratings r ON m.movie_id = r.movie_id
WHERE g.genre_name = 'Action'
  AND m.release_year = 2020
  AND r.imdb_rating > 7.0
ORDER BY r.imdb_rating DESC
LIMIT 100;
```
Explanation: This query uses multiple JOINs to connect movies with their genres and ratings, then filters for Action genre, year 2020, and rating > 7.

Example 4:
Question: "What's the average rating by genre?"
```sql
SELECT g.genre_name,
       AVG(r.imdb_rating) as avg_rating,
       COUNT(DISTINCT m.movie_id) as movie_count
FROM genres g
JOIN movie_genres mg ON g.genre_id = mg.genre_id
JOIN movies m ON mg.movie_id = m.movie_id
JOIN ratings r ON m.movie_id = r.movie_id
GROUP BY g.genre_name
HAVING COUNT(DISTINCT m.movie_id) >= 5
ORDER BY avg_rating DESC;
```
Explanation: This query calculates average rating per genre with a minimum of 5 movies, ensuring statistical significance.

Example 5:
Question: "Find movies starring Tom Hanks"
```sql
SELECT m.title, m.release_year, mc.character_name
FROM movies m
JOIN movie_cast mc ON m.movie_id = mc.movie_id
JOIN people p ON mc.person_id = p.person_id
WHERE p.full_name ILIKE '%Tom Hanks%'
ORDER BY m.release_year DESC
LIMIT 100;
```
Explanation: This query uses ILIKE for case-insensitive name matching and joins through the cast table to find movies with Tom Hanks.
"""

    # Build conversation context
    conversation_context = ""
    if conversation_history and len(conversation_history) > 0:
        conversation_context = "\n\nPREVIOUS CONVERSATION:\n"
        for msg in conversation_history[-5:]:  # Last 5 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            conversation_context += f"{role}: {content}\n"

    # Combine all parts
    prompt = f"""{system_instructions}

{few_shot_examples}

DATABASE SCHEMA:
{schema_context}
{conversation_context}

CURRENT QUESTION:
{user_query}

Generate the SQL query following the format above:
"""

    return prompt


def get_result_formatting_prompt(
    user_query: str,
    sql_query: str,
    query_explanation: Optional[str],
    results: List[Dict[str, Any]],
    column_names: List[str]
) -> str:
    """
    Generate prompt for formatting query results.

    This prompt guides the LLM to present query results in a
    user-friendly, natural language format.

    Args:
        user_query: Original user question
        sql_query: SQL query that was executed
        query_explanation: Explanation of the SQL
        results: Query results as list of dictionaries
        column_names: List of column names

    Returns:
        Prompt for result formatting
    """

    # Format results for inclusion in prompt
    if len(results) == 0:
        results_text = "No results found."
    else:
        results_text = f"Found {len(results)} results:\n\n"

        # Show first 10 rows
        for i, row in enumerate(results[:10], 1):
            results_text += f"Row {i}:\n"
            for col in column_names:
                value = row.get(col, "NULL")
                results_text += f"  {col}: {value}\n"
            results_text += "\n"

        if len(results) > 10:
            results_text += f"... and {len(results) - 10} more rows"

    prompt = f"""You are a data analyst explaining query results to a business user.

TASK: Present the query results in a clear, natural language format that answers the user's question.

USER'S QUESTION:
{user_query}

SQL QUERY EXECUTED:
```sql
{sql_query}
```

QUERY RESULTS:
{results_text}

INSTRUCTIONS:
1. Start with a direct answer to the user's question
2. Present key findings clearly (use tables, lists, or prose as appropriate)
3. Highlight interesting insights or patterns
4. Keep language simple and non-technical
5. If there are many results, summarize the most important ones
6. If no results, explain why and suggest alternatives

DO NOT:
- Simply list all rows
- Use technical SQL terminology
- Repeat the entire dataset
- Apologize for technical issues

Generate your response:
"""

    return prompt
