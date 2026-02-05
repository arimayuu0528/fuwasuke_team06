DROP DATABASE IF EXISTS huwasuke_db;
CREATE DATABASE huwasuke_db DEFAULT CHARACTER SET utf8mb4;
USE huwasuke_db;

-- ==========================================
-- 1. CREATE TABLE 文（一括）
-- ==========================================

-- ユーザー
CREATE TABLE t_users (
    user_id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    password CHAR(10) NOT NULL,
    wakeup_time TIME NOT NULL DEFAULT '07:00:00',
    sleep_time TIME NOT NULL DEFAULT '23:30:00',
    user_name VARCHAR(8) NOT NULL,
    PRIMARY KEY (user_id)
);

-- 優先度
CREATE TABLE t_priorities (
    priority_id INT NOT NULL AUTO_INCREMENT,
    priority_name VARCHAR(10) NOT NULL,
    PRIMARY KEY (priority_id)
);

-- しんどさレベル
CREATE TABLE t_fatigue_levels (
    fatigue_id INT NOT NULL AUTO_INCREMENT,
    fatigue_name VARCHAR(4) NOT NULL,
    PRIMARY KEY (fatigue_id)
);

-- タスク
CREATE TABLE t_tasks (
    task_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    task_name VARCHAR(50) NOT NULL,
    priority_id INT NOT NULL,
    fatigue_id INT NOT NULL,
    deadline DATE NOT NULL,
    duration_min INT NOT NULL,
    created_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    category_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (task_id),
    FOREIGN KEY (user_id) REFERENCES t_users(user_id),
    FOREIGN KEY (priority_id) REFERENCES t_priorities(priority_id),
    FOREIGN KEY (fatigue_id) REFERENCES t_fatigue_levels(fatigue_id)
);

-- タスク評価
CREATE TABLE t_task_reviews (
    evaluation_id INT NOT NULL AUTO_INCREMENT,
    task_id INT NOT NULL,
    evaluation INT NOT NULL,
    comment VARCHAR(255),
    evaluation_day DATE NOT NULL,
    PRIMARY KEY (evaluation_id),
    FOREIGN KEY (task_id) REFERENCES t_tasks(task_id)
);

-- 固定予定マスター
CREATE TABLE t_fixed_schedule_masters (
    master_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(50) NOT NULL,
    duration_min INT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    repeat_type VARCHAR(5) NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    location VARCHAR(100) NOT NULL,
    tag VARCHAR(30) NOT NULL,
    memo VARCHAR(100) NOT NULL,
    PRIMARY KEY (master_id),
    FOREIGN KEY (user_id) REFERENCES t_users(user_id)
);

-- 固定予定インスタンス
CREATE TABLE t_fixed_schedule_instances (
    instance_id INT NOT NULL AUTO_INCREMENT,
    master_id INT NOT NULL,
    schedule_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_cancelled BOOLEAN NOT NULL,
    PRIMARY KEY (instance_id),
    FOREIGN KEY (master_id) REFERENCES t_fixed_schedule_masters(master_id)
);

-- 今日の気分
CREATE TABLE t_today_moods (
    today_moods_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    mood_date DATETIME NOT NULL,
    mood VARCHAR(4) NOT NULL,
    PRIMARY KEY (today_moods_id),
    FOREIGN KEY (user_id) REFERENCES t_users(user_id),
    CHECK (mood IN ('普通', 'しんどい', '元気'))
);

-- タスク作業ログ
CREATE TABLE t_task_work_logs (
    work_id INT NOT NULL AUTO_INCREMENT,
    task_id INT NOT NULL,
    work_date DATE,
    work_min INT(3) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    create_at DATETIME NOT NULL,
    PRIMARY KEY(work_id),
    FOREIGN KEY(task_id) REFERENCES t_tasks(task_id)
);

-- タスク提案
CREATE TABLE t_task_suggestions (
    task_suggestion_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    created_at DATE NOT NULL,
    mood VARCHAR(4) NOT NULL,
    PRIMARY KEY (task_suggestion_id),
    FOREIGN KEY (user_id) REFERENCES t_users(user_id)
);

-- タスク提案詳細
CREATE TABLE t_task_suggestion_detail (
    task_suggestion_detail_id INT NOT NULL AUTO_INCREMENT,
    task_suggestion_id INT NOT NULL,
    task_id INT NOT NULL,
    plan_min INT NOT NULL,
    PRIMARY KEY (task_suggestion_detail_id),
    FOREIGN KEY (task_suggestion_id) REFERENCES t_task_suggestions(task_suggestion_id),
    FOREIGN KEY (task_id) REFERENCES t_tasks(task_id)
);

-- タスク提案評価
CREATE TABLE t_task_suggestion_reviews (
    task_suggestion_reviews_id INT NOT NULL AUTO_INCREMENT,
    task_suggestion_id INT NOT NULL,
    task_id INT NOT NULL,
    plan_min INT NOT NULL,
    PRIMARY KEY (task_suggestion_reviews_id),
    FOREIGN KEY (task_suggestion_id) REFERENCES t_task_suggestions(task_suggestion_id),
    FOREIGN KEY (task_id) REFERENCES t_tasks(task_id)
);

-- ==========================================
-- 2. INSERT 文（一括）
-- ==========================================

-- 優先度
INSERT INTO t_priorities (priority_name) VALUES ('高'), ('中'), ('低');

-- しんどさレベル
INSERT INTO t_fatigue_levels (fatigue_name) VALUES ('しんどい'), ('ふつう'), ('がんばる');

-- ユーザー
INSERT INTO t_users (email, user_name, password, wakeup_time, sleep_time) VALUES
('user1@example.com','ふわじぃ','pass000001','07:00:00','23:30:00'),
('user2@example.com','ふわちゃん','pass000002','06:30:00','23:00:00'),
('user3@example.com','ふわばぁ','pass000003','08:00:00','22:30:00');

-- タスク
INSERT INTO t_tasks (user_id, task_name, priority_id, fatigue_id, deadline, duration_min, created_date, category_name) VALUES
(1,'レポート作成',1,2,'2026-01-31',120,'2026-01-26','仕事'),
(2,'コードレビュー',2,3,'2026-01-28',60,'2026-01-25','仕事'),
(3,'会議準備',3,1,'2026-02-02',90,'2026-01-26','仕事');

-- タスク評価
INSERT INTO t_task_reviews (task_id, evaluation, evaluation_day) VALUES
(1,1,'2026-01-26'),
(2,3,'2026-01-25'),
(3,2,'2026-01-26');

-- 固定予定マスター
INSERT INTO t_fixed_schedule_masters (user_id, title, duration_min, start_time, end_time, repeat_type, day_of_week, location, tag, memo) VALUES
(1,'朝会',30,'09:00:00','09:30:00','毎日','月火水木金','会議室A','仕事','毎朝実施'),
(2,'昼休み',60,'12:00:00','13:00:00','毎日','月火水木金','食堂','休憩','昼食時間'),
(3,'運動',45,'18:00:00','18:45:00','毎週','火木','ジム','健康','筋トレ');

-- 固定予定インスタンス
INSERT INTO t_fixed_schedule_instances (master_id, schedule_date, start_time, end_time, is_cancelled) VALUES
(1,'2026-01-27','09:00:00','09:30:00',0),
(1,'2026-01-28','09:00:00','09:30:00',0),
(1,'2026-01-29','09:00:00','09:30:00',0),
(1,'2026-01-30','09:00:00','09:30:00',0),
(1,'2026-01-31','09:00:00','09:30:00',0),
(2,'2026-01-27','12:00:00','13:00:00',0),
(2,'2026-01-28','12:00:00','13:00:00',0),
(2,'2026-01-29','12:00:00','13:00:00',0),
(2,'2026-01-30','12:00:00','13:00:00',0),
(2,'2026-01-31','12:00:00','13:00:00',0),
(3,'2026-01-28','18:00:00','18:45:00',0),
(3,'2026-01-30','18:00:00','18:45:00',0),
(3,'2026-02-04','18:00:00','18:45:00',0);

-- 今日の気分
INSERT INTO t_today_moods (user_id, mood_date, mood) VALUES
(1,'2026-01-27 08:00:00','普通'),
(2,'2026-01-27 08:30:00','元気'),
(3,'2026-01-27 09:00:00','しんどい');

-- タスク作業ログ
INSERT INTO t_task_work_logs (task_id, work_date, work_min, start_time, end_time, create_at) VALUES
(1, '2026-01-26', 60, '09:00:00', '10:00:00', '2026-01-26 10:05:00'),
(1, '2026-01-27', 60, '10:00:00', '11:00:00', '2026-01-27 11:02:00'),
(2, '2026-01-25', 30, '14:00:00', '14:30:00', '2026-01-25 14:35:00'),
(2, NULL, 30, '14:30:00', '15:00:00', '2026-01-25 15:05:00'),
(3, '2026-01-26', 45, '10:00:00', '10:45:00', '2026-01-26 10:50:00'),
(3, '2026-01-27', 45, '10:45:00', '11:30:00', '2026-01-27 11:35:00');

-- タスク提案
INSERT INTO t_task_suggestions (user_id, created_at, mood) VALUES
(1,'2026-01-26','普通'),
(2,'2026-01-26','元気'),
(3,'2026-01-26','しんどい');

-- タスク提案詳細
INSERT INTO t_task_suggestion_detail (task_suggestion_id, task_id, plan_min) VALUES
(1,1,60),
(1,2,30),
(2,2,45),
(3,3,90);

-- タスク提案評価
INSERT INTO t_task_suggestion_reviews (task_suggestion_id, task_id, plan_min) VALUES
(1,1,60),
(1,2,30),
(2,2,45),
(3,3,90);