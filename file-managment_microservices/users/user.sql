DROP TABLE IF EXiSTS users;
DROP TABLE IF EXISTS password_history;

CREATE TABLE users(user_id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, first_name TEXT, last_name TEXT, email_address TEXT UNIQUE, group_name TEXT, password TEXT, salt TEXT);
CREATE TABLE password_history(user_id INTEGER, password TEXT, FOREIGN KEY (user_id) REFERENCES users(user_id));