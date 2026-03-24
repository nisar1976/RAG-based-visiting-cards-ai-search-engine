-- Note: pgvector extension is optional. This schema uses BYTEA for vector storage
-- which works without the pgvector C extension (useful on Windows)

CREATE TABLE IF NOT EXISTS cards (
    id           INTEGER PRIMARY KEY,
    name         TEXT,
    designation  TEXT,
    company      TEXT,
    country      TEXT,
    phone        TEXT,
    cell         TEXT,
    email        TEXT,
    address      TEXT,
    full_text    TEXT,
    image_path   TEXT UNIQUE,
    embedding    BYTEA NOT NULL,
    created_at   TIMESTAMP DEFAULT NOW()
);
