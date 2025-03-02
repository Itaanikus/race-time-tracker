CREATE TABLE members_dim (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT,
    birth_date DATE,
    gender VARCHAR(10)
);

CREATE TABLE race_times_fact (
    id SERIAL PRIMARY KEY,
    runner_id INT NOT NULL,
    race_distance VARCHAR(20) NOT NULL, -- Supports named distances like 'Half Marathon'
    race_time TIME NOT NULL, -- Matches HH:MM:SS format
    race_date DATE NOT NULL,
    FOREIGN KEY (runner_id) REFERENCES members_dim(id) ON DELETE CASCADE
);

CREATE INDEX idx_race_times_fact_runner_id ON race_times_fact(runner_id);