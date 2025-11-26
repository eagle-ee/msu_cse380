DROP TABLE IF EXISTS test;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS password_history;

CREATE TABLE test (col1 INTEGER);
INSERT INTO test VALUES (43);

CREATE TABLE users(user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, first_name TEXT, last_name TEXT, email_address TEXT UNIQUE, password TEXT, salt TEXT);
CREATE TABLE password_history(user_id INTEGER, password TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id));