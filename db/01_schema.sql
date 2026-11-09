CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recipes (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    minutes INT,
    description TEXT,
    ingredients JSONB,
    steps JSONB,
    ingredient_ids INT[],
    like_count INT NOT NULL DEFAULT 0,
    embedding vector(128)
);

CREATE TABLE IF NOT EXISTS user_recipe_interactions (
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, recipe_id)
);