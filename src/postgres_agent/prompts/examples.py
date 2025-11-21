"""
Additional few-shot examples for complex SQL patterns.

This module contains more advanced examples that can be included
in prompts for specific query types.
"""

# Window function examples
WINDOW_FUNCTION_EXAMPLES = """
Example: Rank movies by revenue within each genre
```sql
WITH ranked_movies AS (
    SELECT
        m.title,
        g.genre_name,
        m.revenue_usd,
        ROW_NUMBER() OVER (PARTITION BY g.genre_name ORDER BY m.revenue_usd DESC) as rank
    FROM movies m
    JOIN movie_genres mg ON m.movie_id = mg.movie_id
    JOIN genres g ON mg.genre_id = g.genre_id
    WHERE m.revenue_usd IS NOT NULL
)
SELECT title, genre_name, revenue_usd, rank
FROM ranked_movies
WHERE rank <= 5
ORDER BY genre_name, rank;
```

Example: Calculate year-over-year growth in movie production
```sql
SELECT
    release_year,
    COUNT(*) as movie_count,
    LAG(COUNT(*)) OVER (ORDER BY release_year) as prev_year_count,
    ROUND(
        (COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY release_year)) * 100.0 /
        LAG(COUNT(*)) OVER (ORDER BY release_year),
        2
    ) as yoy_growth_pct
FROM movies
GROUP BY release_year
ORDER BY release_year DESC;
```
"""

# CTE (Common Table Expression) examples
CTE_EXAMPLES = """
Example: Find actors who worked with multiple award-winning directors
```sql
WITH award_winning_directors AS (
    SELECT DISTINCT p.person_id, p.full_name
    FROM people p
    JOIN movie_crew mc ON p.person_id = mc.person_id
    JOIN awards a ON mc.movie_id = a.movie_id
    WHERE mc.role = 'Director' AND a.won = TRUE
),
actor_director_pairs AS (
    SELECT
        actor.person_id as actor_id,
        actor.full_name as actor_name,
        dir.person_id as director_id,
        dir.full_name as director_name
    FROM people actor
    JOIN movie_cast mc ON actor.person_id = mc.person_id
    JOIN movie_crew crew ON mc.movie_id = crew.movie_id
    JOIN award_winning_directors dir ON crew.person_id = dir.person_id
    WHERE crew.role = 'Director'
)
SELECT
    actor_name,
    COUNT(DISTINCT director_id) as num_award_winning_directors,
    STRING_AGG(DISTINCT director_name, ', ') as directors
FROM actor_director_pairs
GROUP BY actor_id, actor_name
HAVING COUNT(DISTINCT director_id) >= 2
ORDER BY num_award_winning_directors DESC
LIMIT 20;
```
"""

# Subquery examples
SUBQUERY_EXAMPLES = """
Example: Find movies that performed better than the average in their genre
```sql
SELECT
    m.title,
    g.genre_name,
    m.revenue_usd,
    genre_avg.avg_revenue
FROM movies m
JOIN movie_genres mg ON m.movie_id = mg.movie_id
JOIN genres g ON mg.genre_id = g.genre_id
JOIN (
    SELECT
        g.genre_id,
        AVG(m.revenue_usd) as avg_revenue
    FROM movies m
    JOIN movie_genres mg ON m.movie_id = mg.movie_id
    JOIN genres g ON mg.genre_id = g.genre_id
    WHERE m.revenue_usd IS NOT NULL
    GROUP BY g.genre_id
) genre_avg ON g.genre_id = genre_avg.genre_id
WHERE m.revenue_usd > genre_avg.avg_revenue
ORDER BY (m.revenue_usd - genre_avg.avg_revenue) DESC
LIMIT 50;
```
"""

# Analytical query examples
ANALYTICAL_EXAMPLES = """
Example: Calculate budget-to-revenue ratio and identify high-performers
```sql
SELECT
    m.title,
    m.release_year,
    m.budget_usd,
    m.revenue_usd,
    ROUND(m.revenue_usd::numeric / NULLIF(m.budget_usd, 0), 2) as revenue_multiple,
    CASE
        WHEN m.revenue_usd > m.budget_usd * 3 THEN 'High Performer'
        WHEN m.revenue_usd > m.budget_usd THEN 'Profitable'
        ELSE 'Under-performed'
    END as performance_category
FROM movies m
WHERE m.budget_usd IS NOT NULL
  AND m.revenue_usd IS NOT NULL
  AND m.budget_usd > 0
ORDER BY revenue_multiple DESC
LIMIT 100;
```

Example: Find correlations between runtime and ratings
```sql
SELECT
    CASE
        WHEN runtime_minutes < 90 THEN 'Short (<90 min)'
        WHEN runtime_minutes < 120 THEN 'Medium (90-120 min)'
        WHEN runtime_minutes < 150 THEN 'Long (120-150 min)'
        ELSE 'Very Long (>150 min)'
    END as runtime_category,
    COUNT(*) as movie_count,
    ROUND(AVG(r.imdb_rating), 2) as avg_rating,
    ROUND(AVG(r.imdb_votes), 0) as avg_votes,
    MIN(r.imdb_rating) as min_rating,
    MAX(r.imdb_rating) as max_rating
FROM movies m
JOIN ratings r ON m.movie_id = r.movie_id
WHERE m.runtime_minutes IS NOT NULL
  AND r.imdb_rating IS NOT NULL
GROUP BY runtime_category
ORDER BY
    CASE runtime_category
        WHEN 'Short (<90 min)' THEN 1
        WHEN 'Medium (90-120 min)' THEN 2
        WHEN 'Long (120-150 min)' THEN 3
        ELSE 4
    END;
```
"""
