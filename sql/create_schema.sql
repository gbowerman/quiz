
CREATE TABLE IF NOT EXISTS titles(
    title_id SMALLSERIAL PRIMARY KEY,
    title VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS questions(
    title_id INT,
    question VARCHAR(512),
    answer VARCHAR(512),
    num_answers INT,
    CONSTRAINT fk_title
        FOREIGN KEY(title_id)
            REFERENCES titles(title_id)
);

CREATE TABLE IF NOT EXISTS sessions(
    session_id UUID PRIMARY KEY,
    session_start TIMESTAMP,
    title_id INT,
    score INT,
    q_count INT
);

CREATE TABLE IF NOT EXISTS session_qs(
    q_id SERIAL PRIMARY KEY,    
    session_id UUID,
    question VARCHAR(512),
    answer VARCHAR(512),
    num_answers INT,
    CONSTRAINT fk_session
        FOREIGN KEY(session_id)
            REFERENCES sessions(session_id)
);
GRANT ALL PRIVILEGES ON DATABASE quiz_db TO quizzer;
GRANT USAGE ON SCHEMA public TO quizzer;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO quizzer;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO quizzer;

