BEGIN TRANSACTION;
CREATE TABLE `UserTopic` (
	`id`	integer NOT NULL,
	`user_url`	text NOT NULL,
	`topic`	text NOT NULL,
	PRIMARY KEY(id)
);
CREATE TABLE `UserQuestion` (
	`id`	integer NOT NULL,
	`user_url`	text NOT NULL,
	`question_id`	text NOT NULL,
	PRIMARY KEY(id)
);
CREATE TABLE `User` (
	`id`	integer NOT NULL,
	`user_url`	text NOT NULL UNIQUE,
	`user_id`	text NOT NULL,
	`followee_num`	int NOT NULL,
	`follower_num`	int NOT NULL,
	`answer_num`	int NOT NULL,
	`agree_num`	int NOT NULL,
	`thanks_num`	int NOT NULL,
	`layer`	smallint,
	`is_crawled`	smallint,
	PRIMARY KEY(id)
);
CREATE TABLE `Question` (
	`id`	integer NOT NULL,
	`question_id`	text NOT NULL,
	`topic`	text NOT NULL,
	PRIMARY KEY(id)
);
CREATE TABLE `Following` (
	`id`	integer NOT NULL,
	`user_url`	text NOT NULL,
	`followee_url`	text NOT NULL,
	PRIMARY KEY(id)
);
CREATE UNIQUE INDEX user_question on UserQuestion(user_url, question_id);
CREATE UNIQUE INDEX user_follower on following(user_url, followee_url);
CREATE UNIQUE INDEX question_topic on Question(question_id, topic);
COMMIT;
