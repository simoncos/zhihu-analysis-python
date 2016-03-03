CREATE TABLE `Summoner` (
	`id`	integer NOT NULL,
	`summoner_id`	text NOT NULL UNIQUE, /*key*/
	`summoner_name`	text NOT NULL,
	`is_crawled`	integer,
	PRIMARY KEY(id)
);
CREATE TABLE `Match` (
	`id`	integer NOT NULL,
	`match_id`	text NOT NULL UNIQUE, /*key*/
	`version` text NOT NULL,	
	`duration` real NOT NULL,
	`is_crawled`	integer,
	PRIMARY KEY(id)
);
CREATE TABLE `Team` (
	`id`	integer NOT NULL,
	`match_id`	text NOT NULL, /*key*/
	`side`	text NOT NULL, /*key*/
	`win`	integer NOT NULL,
	`bans` text NOT NULL, /*tuple*/
	`dragon_kills` integer NOT NULL,
	`baron_kills` integer NOT NULL,
	PRIMARY KEY(id)
);
CREATE TABLE `Participant` (
	`id`	integer NOT NULL,
	`summoner_id`	text NOT NULL, /*key*/
	`match_id`	text NOT NULL, /*key*/
	`side`	text NOT NULL, 
	`champion`	text NOT NULL,
	`previous_season_tier`	text,
	`kda` real NOT NULL,
	`kills` integer NOT NULL,
	`deaths` integer NOT NULL,
	`assists` integer NOT NULL,
	`champion_level` integer NOT NULL,
	`gold_earned` integer NOT NULL,
	`gold_spent` integer NOT NULL,
	`magic_damage_dealt` integer NOT NULL,
	`magic_damage_dealt_to_champions` integer NOT NULL,
	`magic_damage_taken` integer NOT NULL,
	`physical_damage_dealt` integer NOT NULL,
	`physical_damage_dealt_to_champions` integer NOT NULL,
	`physical_damage_taken` integer NOT NULL,
	`true_damage_dealt` integer NOT NULL,
	`true_damage_dealt_to_champions` integer NOT NULL,
	`true_damage_taken` integer NOT NULL,
	`damage_dealt` integer NOT NULL,
	`damage_dealt_to_champions` integer NOT NULL,
	`damage_taken` integer NOT NULL,
	`healing_done` integer NOT NULL,
	`crowd_control_dealt` integer NOT NULL,
	`ward_kills` integer NOT NULL,
	`wards_placed` integer NOT NULL,
	`turret_kills` integer NOT NULL,
	`participant_win` integer NOT NULL,

	PRIMARY KEY(id)
);
CREATE TABLE `ParticipantTimeline` (
	`id`	integer NOT NULL,
	`summoner_id`	text NOT NULL, /*key*/
	`match_id`	text NOT NULL, /*key*/
	`delta` text NOT NULL, /*key*/
	`participant_role` text NOT NULL,
	`participant_lane` text NOT NULL,
	`participant_gold_per_min_delta` real,
	`participant_xp_diff_per_min_delta` real,
	`participant_xp_per_min_delta` real,
	`participant_damage_taken_diff_per_min_delta` real,
	`participant_damage_taken_per_min_delta` real,
	PRIMARY KEY(id)
);
CREATE TABLE `FrameKillEvent` (
	`id`	integer NOT NULL,
	`match_id`	text NOT NULL, /*key*/
	`frame_number`	text NOT NULL, /*key*/
	`event_number`	text NOT NULL, /*key*/
	`killer_id` text NOT NULL,
	`victim_id` text NOT NULL,
	`assist_ids` text, /*tuple*/
	PRIMARY KEY(id)
);
