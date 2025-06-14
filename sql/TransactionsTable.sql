CREATE TABLE transactions (
  id           SERIAL        PRIMARY KEY,
  user_id      INTEGER       NOT NULL REFERENCES users(id),
  date_time    TIMESTAMP     NOT NULL,
  amount       NUMERIC(10,2) NOT NULL,
  description  TEXT,
  created_at   TIMESTAMPTZ   NOT NULL DEFAULT now()
);