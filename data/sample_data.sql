-- Insert sample genres
INSERT INTO genres (genre_name) VALUES
    ('Action'),
    ('Adventure'),
    ('Comedy'),
    ('Drama'),
    ('Sci-Fi'),
    ('Thriller'),
    ('Romance'),
    ('Horror'),
    ('Animation'),
    ('Documentary');

-- Insert sample studios
INSERT INTO studios (studio_name, country, founded_year) VALUES
    ('Warner Bros', 'USA', 1923),
    ('Universal Pictures', 'USA', 1912),
    ('Paramount Pictures', 'USA', 1912),
    ('20th Century Studios', 'USA', 1935),
    ('Sony Pictures', 'USA', 1924),
    ('Walt Disney Studios', 'USA', 1923),
    ('Lionsgate', 'USA', 1997),
    ('Columbia Pictures', 'USA', 1924);

-- Insert sample people (actors, directors)
INSERT INTO people (full_name, birth_date, biography) VALUES
    ('Christopher Nolan', '1970-07-30', 'British-American filmmaker known for complex narratives'),
    ('Tom Hanks', '1956-07-09', 'American actor and filmmaker'),
    ('Scarlett Johansson', '1984-11-22', 'American actress and singer'),
    ('Leonardo DiCaprio', '1974-11-11', 'American actor and producer'),
    ('Emma Stone', '1988-11-06', 'American actress'),
    ('Ryan Gosling', '1980-11-12', 'Canadian actor and musician'),
    ('Meryl Streep', '1949-06-22', 'American actress'),
    ('Denzel Washington', '1954-12-28', 'American actor, director, and producer'),
    ('Greta Gerwig', '1983-08-04', 'American actress and filmmaker'),
    ('Quentin Tarantino', '1963-03-27', 'American filmmaker and actor');

-- Insert sample movies
INSERT INTO movies (title, release_year, runtime_minutes, plot_summary, budget_usd, revenue_usd) VALUES
    ('Inception', 2010, 148, 'A thief who steals corporate secrets through dream-sharing technology', 160000000, 829895144),
    ('The Dark Knight', 2008, 152, 'Batman faces the Joker in Gotham City', 185000000, 1004558444),
    ('Interstellar', 2014, 169, 'A team of explorers travel through a wormhole in space', 165000000, 677471339),
    ('La La Land', 2016, 128, 'A jazz musician and an actress fall in love in Los Angeles', 30000000, 446092357),
    ('Forrest Gump', 1994, 142, 'The life story of a simple man with low IQ', 55000000, 678226465),
    ('The Shawshank Redemption', 1994, 142, 'Two imprisoned men bond over years', 25000000, 28341469),
    ('Pulp Fiction', 1994, 154, 'Various interconnected stories of crime in Los Angeles', 8000000, 213928762),
    ('The Matrix', 1999, 136, 'A computer hacker learns about the true nature of reality', 63000000, 465343787),
    ('Avatar', 2009, 162, 'A marine on an alien planet torn between two worlds', 237000000, 2923706026),
    ('Titanic', 1997, 195, 'A love story aboard the ill-fated ship', 200000000, 2264743305),
    ('Avengers: Endgame', 2019, 181, 'The Avengers assemble once more', 356000000, 2797501328),
    ('Joker', 2019, 122, 'The origin story of Batmans nemesis', 55000000, 1074251311),
    ('Parasite', 2019, 132, 'A poor family schemes to work for a wealthy family', 11400000, 262538016),
    ('1917', 2019, 119, 'Two British soldiers on a mission during WWI', 95000000, 384882596),
    ('Dunkirk', 2017, 106, 'Allied soldiers surrounded by enemy forces', 100000000, 526940665);

-- Insert ratings
INSERT INTO ratings (movie_id, imdb_rating, imdb_votes, rotten_tomatoes_rating, metacritic_rating) VALUES
    (1, 8.8, 2400000, 87, 74),
    (2, 9.0, 2700000, 94, 84),
    (3, 8.6, 1900000, 72, 74),
    (4, 8.0, 600000, 91, 93),
    (5, 8.8, 2100000, 71, 82),
    (6, 9.3, 2700000, 91, 82),
    (7, 8.9, 2100000, 92, 94),
    (8, 8.7, 1900000, 88, 73),
    (9, 7.9, 1300000, 82, 83),
    (10, 7.9, 1200000, 88, 75),
    (11, 8.4, 1100000, 94, 78),
    (12, 8.4, 1300000, 68, 59),
    (13, 8.5, 900000, 98, 96),
    (14, 8.3, 600000, 89, 78),
    (15, 7.8, 700000, 92, 94);

-- Link movies to genres
INSERT INTO movie_genres (movie_id, genre_id) VALUES
    -- Inception: Action, Sci-Fi, Thriller
    (1, 1), (1, 5), (1, 6),
    -- The Dark Knight: Action, Drama, Thriller
    (2, 1), (2, 4), (2, 6),
    -- Interstellar: Adventure, Drama, Sci-Fi
    (3, 2), (3, 4), (3, 5),
    -- La La Land: Comedy, Drama, Romance
    (4, 3), (4, 4), (4, 7),
    -- Forrest Gump: Drama, Romance
    (5, 4), (5, 7),
    -- The Shawshank Redemption: Drama
    (6, 4),
    -- Pulp Fiction: Drama, Thriller
    (7, 4), (7, 6),
    -- The Matrix: Action, Sci-Fi
    (8, 1), (8, 5),
    -- Avatar: Action, Adventure, Sci-Fi
    (9, 1), (9, 2), (9, 5),
    -- Titanic: Drama, Romance
    (10, 4), (10, 7),
    -- Avengers: Endgame: Action, Adventure, Sci-Fi
    (11, 1), (11, 2), (11, 5),
    -- Joker: Drama, Thriller
    (12, 4), (12, 6),
    -- Parasite: Drama, Thriller
    (13, 4), (13, 6),
    -- 1917: Action, Drama
    (14, 1), (14, 4),
    -- Dunkirk: Action, Drama, Thriller
    (15, 1), (15, 4), (15, 6);

-- Link movies to studios
INSERT INTO movie_studios (movie_id, studio_id) VALUES
    (1, 1), -- Inception - Warner Bros
    (2, 1), -- The Dark Knight - Warner Bros
    (3, 4), -- Interstellar - Paramount
    (4, 7), -- La La Land - Lionsgate
    (5, 3), -- Forrest Gump - Paramount
    (6, 8), -- The Shawshank Redemption - Columbia
    (7, 5), -- Pulp Fiction - Sony
    (8, 1), -- The Matrix - Warner Bros
    (9, 4), -- Avatar - 20th Century
    (10, 3), -- Titanic - Paramount
    (11, 6), -- Avengers - Disney
    (12, 1), -- Joker - Warner Bros
    (13, 2), -- Parasite - Universal
    (14, 2), -- 1917 - Universal
    (15, 1); -- Dunkirk - Warner Bros

-- Link crew members (directors)
INSERT INTO movie_crew (movie_id, person_id, role) VALUES
    (1, 1, 'Director'),  -- Inception - Nolan
    (2, 1, 'Director'),  -- Dark Knight - Nolan
    (3, 1, 'Director'),  -- Interstellar - Nolan
    (4, 9, 'Director'),  -- La La Land - Gerwig (placeholder)
    (7, 10, 'Director'), -- Pulp Fiction - Tarantino
    (15, 1, 'Director'); -- Dunkirk - Nolan

-- Link cast members
INSERT INTO movie_cast (movie_id, person_id, character_name, cast_order) VALUES
    (1, 4, 'Dom Cobb', 1),
    (1, 3, 'Mal Cobb', 2),
    (5, 2, 'Forrest Gump', 1),
    (4, 5, 'Mia', 1),
    (4, 6, 'Sebastian', 2),
    (11, 3, 'Black Widow', 3);

-- Insert sample awards
INSERT INTO awards (movie_id, award_name, category, year, won) VALUES
    (4, 'Academy Awards', 'Best Director', 2017, TRUE),
    (4, 'Academy Awards', 'Best Actress', 2017, TRUE),
    (4, 'Academy Awards', 'Best Picture', 2017, FALSE),
    (6, 'Academy Awards', 'Best Picture', 1995, FALSE),
    (7, 'Academy Awards', 'Best Original Screenplay', 1995, TRUE),
    (13, 'Academy Awards', 'Best Picture', 2020, TRUE),
    (13, 'Academy Awards', 'Best Director', 2020, TRUE);
