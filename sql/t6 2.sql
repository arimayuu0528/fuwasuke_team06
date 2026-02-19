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


-- モチベーション
CREATE TABLE t_motivations (
    motivation_id INT NOT NULL AUTO_INCREMENT,
    motivation_name VARCHAR(4) NOT NULL,
    PRIMARY KEY (motivation_id)
);

-- タスク
-- 変更点：
--  - remaining_min を追加（分数入力で減らす残り時間）
--  - motivation_id 外部キー追加(t_motivations：モチベーションテーブル)
CREATE TABLE t_tasks (
    task_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    task_name VARCHAR(50) NOT NULL,
    motivation_id INT NOT NULL,
    deadline DATE NOT NULL,
    duration_min INT NOT NULL,          -- 所要時間：初期の見積（固定）
    remaining_min INT NOT NULL,         -- 所要時間：残り時間（毎日減る）
    created_date DATE NOT NULL DEFAULT CURRENT_DATE,
    category_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (task_id),
    FOREIGN KEY (user_id) REFERENCES t_users(user_id),
    FOREIGN KEY (motivation_id) REFERENCES t_motivations(motivation_id)
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
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_cancelled TINYINT(1) NOT NULL DEFAULT 0,
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
-- 変更点：
--  - mood_point(1〜3) を追加（ロジック用）
CREATE TABLE t_today_moods (
    today_moods_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    mood_date DATETIME NOT NULL,
    mood VARCHAR(4) NOT NULL,
    mood_point INT NOT NULL,
    PRIMARY KEY (today_moods_id),
    FOREIGN KEY (user_id) REFERENCES t_users(user_id)
);

-- タスク作業ログ（分数入力）
-- 変更点：
--  - created_at に統一（元は create_at）
CREATE TABLE t_task_work_logs (
    work_id INT NOT NULL AUTO_INCREMENT,
    task_id INT NOT NULL,
    work_date DATE NOT NULL,
    work_min INT NOT NULL,
    start_time TIME NULL,
    end_time TIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (work_id),
    FOREIGN KEY (task_id) REFERENCES t_tasks(task_id)
);

-- タスク提案（ヘッダ）
-- 変更点：
--  - 係数、評価、評価倍率、目標などを保存できるように追加
CREATE TABLE t_task_suggestions (
    task_suggestion_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    suggestion_date DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    mood VARCHAR(4) NOT NULL,
    mood_point INT NOT NULL,

    coef_value FLOAT NOT NULL,                     -- 係数（直近7日など）
    evaluation INT NULL,                           -- 評価（1〜5）※未評価 NULL可
    evaluation_multiplier FLOAT NOT NULL,          -- 評価補正倍率（例：0.8/1.0/1.2）
    target_task_level INT NOT NULL,                -- 今日の目標タスクレベル

    PRIMARY KEY (task_suggestion_id),
    FOREIGN KEY (user_id) REFERENCES t_users(user_id)
);

-- タスク提案詳細（明細）
-- 変更点：
--  - 分割提案や計算結果を保存できる列を追加
CREATE TABLE t_task_suggestion_detail (
    task_suggestion_detail_id INT NOT NULL AUTO_INCREMENT,
    task_suggestion_id INT NOT NULL,
    task_id INT NOT NULL,

    plan_min INT NOT NULL,                         -- 提案した分数（例：20/25など）
    remaining_min_at_suggest INT NULL,             -- 提案時点の残り分（分母として使った値）
    days_left INT NULL,                            -- 提案時点の残り日数
    deadline_multiplier FLOAT NULL,                -- 締め切り補正倍率

    exec_task_level FLOAT NULL,                    -- 実施タスクレベル
    priority_score FLOAT NULL,                     -- 優先点

    actual_work_min INT NULL,                      -- 実際にやった分数（その日の入力をここに持つ）

    PRIMARY KEY (task_suggestion_detail_id),
    FOREIGN KEY (task_suggestion_id) REFERENCES t_task_suggestions(task_suggestion_id),
    FOREIGN KEY (task_id) REFERENCES t_tasks(task_id)
);

-- 元SQLの「タスク提案評価」は内容が詳細と同じで重複していたため削除
-- CREATE TABLE t_task_suggestion_reviews ... (削除)

-- ==========================================
-- 2. INSERT 文（一括）
-- ==========================================

-- モチベーション
INSERT INTO t_motivations (motivation_id,motivation_name) VALUES 
(1,'かんたん'),
(2,'ふつう'),
(3,'がんばる');

-- ユーザー
INSERT INTO t_users (email, user_name, password, wakeup_time, sleep_time) VALUES
('user1@example.com','ふわじぃ','pass000001','07:00:00','23:30:00'),
('user2@example.com','ふわちゃん','pass000002','06:30:00','23:00:00'),
('user3@example.com','ふわばぁ','pass000003','08:00:00','22:30:00');

-- タスク
-- motivation_id ： 1(かんたん) 2(ふつう) 3(がんばる)
INSERT INTO t_tasks (user_id, task_name, motivation_id, deadline, duration_min, remaining_min, created_date, category_name) VALUES
-- user_id = 1
(1, 'メール返信', 2, '2026-02-03', 25, 25, '2026-01-27', '仕事'),
(1, '部屋の片付け', 3, '2026-02-04', 40, 40, '2026-01-28', '生活'),
(1, 'ランニング', 3, '2026-02-06', 50, 50, '2026-01-27', '健康'),
(1, '資格試験の勉強', 1, '2026-02-20', 120, 120, '2026-01-28', '学習'),
(1, 'プレゼント購入', 2, '2026-02-05', 30, 30, '2026-01-27', 'プライベート'),

-- user_id = 2
(2, '仕様書レビュー', 1, '2026-02-01', 80, 80, '2026-01-26', '仕事'),
(2, '夕食の買い出し', 3, '2026-01-29', 30, 30, '2026-01-26', '生活'),
(2, 'ストレッチ', 3, '2026-01-30', 20, 20, '2026-01-26', '健康'),
(2, '英語学習', 2, '2026-02-10', 45, 45, '2026-01-27', '学習'),
(2, '家族への連絡', 2, '2026-01-31', 15, 15, '2026-01-26', 'プライベート'),

-- user_id = 3
(3, '資料整理', 1, '2026-02-03', 60, 60, '2026-01-27', '仕事'),
(3, '掃除', 3, '2026-02-01', 30, 30, '2026-01-26', '生活'),
(3, '筋トレ', 3, '2026-01-30', 45, 45, '2026-01-26', '健康'),
(3, 'オンライン講座受講', 1, '2026-02-12', 90, 90, '2026-01-27', '学習'),
(3, '友人と食事の予定調整', 2, '2026-02-05', 20, 20, '2026-01-26', 'プライベート');

-- 固定予定マスター
INSERT INTO t_fixed_schedule_masters 
(user_id, title, duration_min, start_time, end_time, repeat_type, day_of_week, location, tag, memo) VALUES
-- user_id = 1
(1,'資料確認',20,'08:30:00','08:50:00','毎日','月火水木金','デスク','仕事','朝の軽いチェック'),
(1,'夕会',30,'17:30:00','18:00:00','毎日','月火水木金','会議室B','仕事','1日の振り返り'),
(1,'メール整理',15,'09:30:00','09:45:00','毎日','月火水木金','デスク','仕事','受信メールの整理'),
(1,'プロジェクトMTG',45,'10:00:00','10:45:00','毎週','火','会議室C','仕事','定例ミーティング'),
(1,'週報作成',60,'16:00:00','17:00:00','毎週','金','デスク','仕事','週次報告書作成'),

-- user_id = 2
(2,'午後休憩',15,'15:00:00','15:15:00','毎日','月火水木金','休憩スペース','休憩','軽い休憩'),
(2,'読書',30,'13:30:00','14:00:00','毎日','月火水木金','ロビー','趣味','リラックスタイム'),
(2,'散歩',20,'12:40:00','13:00:00','毎日','月火水木金','屋外','健康','昼食後の散歩'),
(2,'買い出し',30,'17:00:00','17:30:00','毎週','水','スーパー','生活','日用品補充'),
(2,'カフェ休憩',45,'16:00:00','16:45:00','毎週','金','カフェ','休憩','週末前の息抜き'),

-- user_id = 3
(3,'ストレッチ',20,'07:30:00','07:50:00','毎日','月火水木金','自宅','健康','朝のストレッチ'),
(3,'ランニング',30,'19:00:00','19:30:00','毎週','月水金','公園','健康','有酸素運動'),
(3,'ヨガ',40,'20:00:00','20:40:00','毎週','土','スタジオ','健康','リラックスヨガ'),
(3,'サウナ',60,'21:00:00','22:00:00','毎週','金','スパ','健康','疲労回復'),
(3,'買い物',30,'17:30:00','18:00:00','毎週','日','ショッピングモール','生活','週末の買い出し');

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
-- mood 元気(3) 普通(2) 悪い(1)
INSERT INTO t_today_moods (user_id, mood_date, mood, mood_point) VALUES
(1,'2026-01-27 08:00:00','普通',2),
(2,'2026-01-27 08:30:00','元気',3),
(3,'2026-01-27 09:00:00','悪い',1);

-- タスク作業ログ
INSERT INTO t_task_work_logs (task_id, work_date, work_min, start_time, end_time) VALUES
(1, '2026-01-26', 60, '09:00:00', '10:00:00'),
(1, '2026-01-27', 60, '10:00:00', '11:00:00'),
(2, '2026-01-25', 30, '14:00:00', '14:30:00'),
(2, '2026-01-26', 30, '14:30:00', '15:00:00'),
(3, '2026-01-26', 45, '10:00:00', '10:45:00'),
(3, '2026-01-27', 45, '10:45:00', '11:30:00');

-- タスク提案（ヘッダ）
INSERT INTO t_task_suggestions
(user_id, suggestion_date, mood, mood_point, coef_value, evaluation, evaluation_multiplier, target_task_level)
VALUES
(1,'2026-01-26','普通',2,1.000,3,1.00,2),
(2,'2026-01-26','元気',3,1.000,4,1.20,4),
(3,'2026-01-26','悪い',1,1.000,2,0.80,1);

-- タスク提案詳細
INSERT INTO t_task_suggestion_detail (task_suggestion_id, task_id, plan_min) VALUES
(1,1,60),
(1,2,30),
(2,2,45),
(3,3,90);