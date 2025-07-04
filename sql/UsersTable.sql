CREATE TABLE IF NOT EXISTS users (
  id             SERIAL         PRIMARY KEY,
  name           VARCHAR(255)   UNIQUE NOT NULL,
  password_hash  VARCHAR(255)   NOT NULL,
  created_at     TIMESTAMPTZ    NOT NULL DEFAULT now()
);