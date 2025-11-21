-- PostgreSQL Movie Database Schema
-- Optimized for AI Agent queries with proper indexing

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS awards CASCADE;
DROP TABLE IF EXISTS movie_studios CASCADE;
DROP TABLE IF EXISTS studios CASCADE;
DROP TABLE IF EXISTS ratings CASCADE;
DROP TABLE IF EXISTS movie_crew CASCADE;
DROP TABLE IF EXISTS movie_cast CASCADE;
DROP TABLE IF EXISTS people CASCADE;
DROP TABLE IF EXISTS movie_genres CASCADE;
DROP TABLE IF EXISTS genres CASCADE;
DROP TABLE IF EXISTS movies CASCADE;

-- Movies table (main entity)
CREATE TABLE movies (
    movie_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_year INTEGER,
    runtime_minutes INTEGER,
    plot_summary TEXT,
    poster_url VARCHAR(500),
    budget_usd BIGINT,
    revenue_usd BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_year CHECK (release_year >= 1800 AND release_year <= 2100),
    CONSTRAINT chk_runtime CHECK (runtime_minutes > 0),
    CONSTRAINT chk_budget CHECK (budget_usd >= 0),
    CONSTRAINT chk_revenue CHECK (revenue_usd >= 0)
);

-- Genres table
CREATE TABLE genres (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(50) UNIQUE NOT NULL
);

-- Junction table for movie-genre (many-to-many)
CREATE TABLE movie_genres (
    movie_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
);

-- People table (actors, directors, writers, etc.)
CREATE TABLE people (
    person_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    birth_date DATE,
    biography TEXT,
    profile_url VARCHAR(500)
);

-- Movie cast (actors)
CREATE TABLE movie_cast (
    movie_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    character_name VARCHAR(255),
    cast_order INTEGER,
    PRIMARY KEY (movie_id, person_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES people(person_id) ON DELETE CASCADE
);

-- Movie crew (directors, writers, producers, etc.)
CREATE TABLE movie_crew (
    movie_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL,
    PRIMARY KEY (movie_id, person_id, role),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES people(person_id) ON DELETE CASCADE
);

-- Ratings table
CREATE TABLE ratings (
    rating_id SERIAL PRIMARY KEY,
    movie_id INTEGER UNIQUE NOT NULL,
    imdb_rating DECIMAL(3,1),
    imdb_votes INTEGER,
    rotten_tomatoes_rating INTEGER,
    metacritic_rating INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    CONSTRAINT chk_imdb_rating CHECK (imdb_rating >= 0 AND imdb_rating <= 10),
    CONSTRAINT chk_rt_rating CHECK (rotten_tomatoes_rating >= 0 AND rotten_tomatoes_rating <= 100),
    CONSTRAINT chk_mc_rating CHECK (metacritic_rating >= 0 AND metacritic_rating <= 100)
);

-- Studios table
CREATE TABLE studios (
    studio_id SERIAL PRIMARY KEY,
    studio_name VARCHAR(255) UNIQUE NOT NULL,
    country VARCHAR(100),
    founded_year INTEGER
);

-- Junction table for movie-studio (many-to-many)
CREATE TABLE movie_studios (
    movie_id INTEGER NOT NULL,
    studio_id INTEGER NOT NULL,
    PRIMARY KEY (movie_id, studio_id),
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE,
    FOREIGN KEY (studio_id) REFERENCES studios(studio_id) ON DELETE CASCADE
);

-- Awards table
CREATE TABLE awards (
    award_id SERIAL PRIMARY KEY,
    movie_id INTEGER NOT NULL,
    award_name VARCHAR(255) NOT NULL,
    category VARCHAR(255),
    year INTEGER NOT NULL,
    won BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_movies_year ON movies(release_year);
CREATE INDEX idx_movies_title ON movies(title);
CREATE INDEX idx_ratings_imdb ON ratings(imdb_rating DESC);
CREATE INDEX idx_ratings_movie ON ratings(movie_id);
CREATE INDEX idx_awards_year ON awards(year);
CREATE INDEX idx_awards_movie ON awards(movie_id);
CREATE INDEX idx_people_name ON people(full_name);
CREATE INDEX idx_movie_genres_movie ON movie_genres(movie_id);
CREATE INDEX idx_movie_genres_genre ON movie_genres(genre_id);
CREATE INDEX idx_movie_cast_movie ON movie_cast(movie_id);
CREATE INDEX idx_movie_cast_person ON movie_cast(person_id);
CREATE INDEX idx_movie_crew_movie ON movie_crew(movie_id);
CREATE INDEX idx_movie_crew_person ON movie_crew(person_id);

-- Create update trigger for movies updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_movies_updated_at BEFORE UPDATE
    ON movies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW movie_details AS
SELECT
    m.movie_id,
    m.title,
    m.release_year,
    m.runtime_minutes,
    m.budget_usd,
    m.revenue_usd,
    r.imdb_rating,
    r.imdb_votes,
    STRING_AGG(DISTINCT g.genre_name, ', ' ORDER BY g.genre_name) as genres
FROM movies m
LEFT JOIN ratings r ON m.movie_id = r.movie_id
LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
LEFT JOIN genres g ON mg.genre_id = g.genre_id
GROUP BY m.movie_id, m.title, m.release_year, m.runtime_minutes,
         m.budget_usd, m.revenue_usd, r.imdb_rating, r.imdb_votes;

COMMENT ON VIEW movie_details IS 'Consolidated view of movie information with ratings and genres';
