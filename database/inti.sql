CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR,                     -- Add name column
    username VARCHAR UNIQUE,
    email VARCHAR UNIQUE,
    password_hash VARCHAR,
    api_key VARCHAR UNIQUE,
    profile_photo VARCHAR,
    is_premium BOOLEAN DEFAULT FALSE,
    storage_limit BIGINT DEFAULT 1073741824, -- 1GB
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE uploads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR, -- text, image, video, document
    file_url VARCHAR,
    content TEXT,
    share_token VARCHAR,
    share_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR, -- upload, api_call, etc.
    details TEXT, -- JSON string
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
