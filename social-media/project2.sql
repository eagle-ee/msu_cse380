DROP TABLE IF EXISTS test;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS password_history;
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS follows;
DROP TABLE IF EXISTS likes;

CREATE TABLE test (col1 INTEGER);
INSERT INTO test VALUES (43);

CREATE TABLE users(
    user_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    username TEXT UNIQUE, 
    first_name TEXT, 
    last_name TEXT, 
    email_address TEXT UNIQUE, 
    password TEXT, 
    moderator INTEGER, 
    salt TEXT);
CREATE TABLE posts(
    post_id INTEGER PRIMARY KEY, 
    user_id INTEGER, 
    title TEXT, 
    body TEXT, 
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE);
CREATE TABLE tags(
    post_id INTEGER, 
    tag TEXT, 
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE);
CREATE TABLE follows(
    follower_id INTEGER, 
    followed_id INTEGER, 
    FOREIGN KEY (follower_id) REFERENCES users(user_id) ON DELETE CASCADE, 
    FOREIGN KEY (followed_id) REFERENCES users(user_id) ON DELETE CASCADE,
    PRIMARY KEY (follower_id, followed_id));
CREATE TABLE likes(
    user_id INTEGER, 
    post_id INTEGER, 
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE, 
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    PRIMARY KEY(user_id, post_id));
CREATE TABLE password_history(
    user_id INTEGER, 
    password TEXT, 
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE);
