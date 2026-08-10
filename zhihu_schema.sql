BEGIN TRANSACTION;

CREATE TABLE UserTopic (
    id INTEGER PRIMARY KEY,
    user_url TEXT NOT NULL,
    topic TEXT NOT NULL
);

CREATE TABLE UserQuestion (
    id INTEGER PRIMARY KEY,
    user_url TEXT NOT NULL,
    question_id TEXT NOT NULL
);

CREATE TABLE User (
    id INTEGER PRIMARY KEY,
    user_url TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL,
    followee_num INTEGER NOT NULL CHECK (followee_num >= 0),
    follower_num INTEGER NOT NULL CHECK (follower_num >= 0),
    answer_num INTEGER NOT NULL CHECK (answer_num >= 0),
    agree_num INTEGER NOT NULL CHECK (agree_num >= 0),
    thanks_num INTEGER NOT NULL CHECK (thanks_num >= 0),
    layer INTEGER NOT NULL CHECK (layer >= 0),
    is_crawled INTEGER NOT NULL DEFAULT 1 CHECK (is_crawled IN (0, 1))
);

CREATE TABLE Question (
    id INTEGER PRIMARY KEY,
    question_id TEXT NOT NULL,
    topic TEXT NOT NULL
);

CREATE TABLE Following (
    id INTEGER PRIMARY KEY,
    user_url TEXT NOT NULL,
    followee_url TEXT NOT NULL
);

CREATE UNIQUE INDEX user_question_unique
    ON UserQuestion(user_url, question_id);
CREATE UNIQUE INDEX following_unique
    ON Following(user_url, followee_url);
CREATE UNIQUE INDEX question_topic_unique
    ON Question(question_id, topic);
CREATE INDEX user_topic_user ON UserTopic(user_url);
CREATE INDEX following_followee ON Following(followee_url);
CREATE INDEX question_id_lookup ON Question(question_id);

COMMIT;
