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
    -- ここにフラグを追加
    is_completed BOOLEAN NOT NULL DEFAULT FALSE, -- 0:表示(false), 1:非表示(true)
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

    coef_value FLOAT NOT NULL,                           -- 係数（直近7日など）
    evaluation INT NULL,                                 -- 評価（1〜5）※未評価 NULL可
    evaluation_multiplier FLOAT NOT NULL DEFAULT 1.0,    -- 評価補正倍率（例：0.8/1.0/1.2）
    target_task_level INT NOT NULL,                      -- 今日の目標タスクレベル

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
CREATE TABLE t_fixed_schedule_logs (
    log_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    master_id INT NOT NULL,
    target_date DATE NOT NULL,
    done BOOLEAN NOT NULL,
    PRIMARY KEY (log_id),
    UNIQUE KEY unique_log (user_id, master_id, target_date)
);
CREATE TABLE t_task_evaluation_logs (
    evaluation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    target_date DATE NOT NULL,
    mood VARCHAR(50),             -- その日の気分
    evaluation_score VARCHAR(20),  -- 満足、ふつう、不満
    completed_task_ids TEXT,      -- 達成したタスクID（例: "101,105,110"）
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY (user_id, target_date) -- 1人1日1回（2回目はUPDATE対象にするため）
);
-- ================================================================================================
-- ★追加：
-- - t_task_evaluation_logs に評価ログが1行追加されたら
-- - t_task_suggestionsの該当する提案(同じuser_id & 同じ日付)に評価値と倍率をコピーして更新する
---------------------------------------------------------------------------------------------------
-- - t_task_evaluation_logs の既存ログが更新されたら
-- - t_task_suggestionsの該当する提案(同じuser_id & 同じ日付)も更新して常に一致させる
---------------------------------------------------------------------------------------------------
-- - ※ task.py の INSERT/UPDATEは今のままでOK（DB側で自動反映）
-- ================================================================================================
DELIMITER // -- 命令の区切り文字を ; から // に変更 ※途中の ; でSQL文完了だと認識させないため

CREATE TRIGGER trg_eval_logs_to_suggestions_ai -- トリガ名 trg_eval_logs_to_suggestions_ai
AFTER INSERT ON t_task_evaluation_logs -- t_task_evaluation_logs に INSERT された後に、このトリガを実行する
FOR EACH ROW -- 行ごとに1回ずつトリガを実行する
BEGIN -- UPDATEをまとめるブロック
    UPDATE t_task_suggestions
        SET evaluation = CASE NEW.evaluation_score -- NEW ＝「今INSERT/UPDATEされたログのその行」を表す変数
                            WHEN '不満' THEN 1     -- 条件分岐
                            WHEN 'ふつう' THEN 2
                            WHEN '満足' THEN 3
                            ELSE NULL
                        END,
            evaluation_multiplier = CASE NEW.evaluation_score -- NEW ＝「今INSERT/UPDATEされたログのその行」を表す変数
                                        WHEN '不満' THEN 0.8 -- 条件分岐
                                        WHEN 'ふつう' THEN 1.0
                                        WHEN '満足' THEN 1.2
                                        ELSE 1.0
                                END
    WHERE user_id = NEW.user_id -- t_task_suggestionsの中から 同じユーザー(user_id)同じ日付(suggestion_date)の行を探す
        AND suggestion_date = NEW.target_date;
END//

CREATE TRIGGER trg_eval_logs_to_suggestions_au-- トリガ名 trg_eval_logs_to_suggestions_au
AFTER UPDATE ON t_task_evaluation_logs -- t_task_evaluation_logs に UPDATE された後に、このトリガを実行する
FOR EACH ROW -- 行ごとに1回ずつトリガを実行する
BEGIN-- UPDATEをまとめるブロック
    UPDATE t_task_suggestions
        SET evaluation = CASE NEW.evaluation_score -- NEW ＝「今INSERT/UPDATEされたログのその行」を表す変数
                            WHEN '不満' THEN 1 -- 条件分岐
                            WHEN 'ふつう' THEN 2
                            WHEN '満足' THEN 3
                            ELSE NULL
                        END,
            evaluation_multiplier = CASE NEW.evaluation_score -- NEW ＝「今INSERT/UPDATEされたログのその行」を表す変数
                                        WHEN '不満' THEN 0.8 -- 条件分岐
                                        WHEN 'ふつう' THEN 1.0
                                        WHEN '満足' THEN 1.2
                                        ELSE 1.0
                                    END
    WHERE user_id = NEW.user_id -- t_task_suggestionsの中から 同じユーザー(user_id)同じ日付(suggestion_date)の行を探す
        AND suggestion_date = NEW.target_date;
END//

DELIMITER ; -- 命令の区切り文字を // から ; に戻す

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
INSERT INTO t_tasks (user_id, task_name, motivation_id, deadline, duration_min, remaining_min, created_date, category_name, is_completed) VALUES
-- user_id = 1
(1,'メール返信',2,'2026-02-03',25,25,'2026-01-27','仕事', FALSE),
(1,'部屋の片付け',3,'2026-02-04',40,40,'2026-01-28','生活', FALSE),
(1,'ランニング',3,'2026-02-06', 50,50,'2026-01-27','健康', FALSE),
(1,'資格試験の勉強',1,'2026-02-20',120,120,'2026-01-28','学習', FALSE),
(1,'プレゼント購入',2,'2026-02-05',30,30,'2026-01-27','プライベート', FALSE),
(1,'課題レポート下書き',2,'2026-02-16',45,45,'2026-01-27','学校', FALSE),
(1,'課題レポート清書',2,'2026-03-02',30,30,'2026-01-27','学校', FALSE),
(1,'チームMTG議事録',1,'2026-02-23',15,15,'2026-01-27','学校', FALSE),
(1,'Gitコミット整理',3,'2026-03-30',120,120,'2026-01-27','生活', FALSE),
(1,'ポートフォリオREADME更新',3,'2026-02-20',75,75,'2026-01-28','ポートフォリオ', FALSE),
(1,'studylog DB設計見直し',1,'2026-02-17',10,10,'2026-01-28','studyLog', FALSE),
(1,'studylog 画面遷移確認',2,'2026-02-20',30,30,'2026-01-28','studyLog', FALSE),
(1,'Flask ルーティング整理',3,'2026-03-01',120,120,'2026-01-28','studyLog', FALSE),
(1,'SQL初期データ作成',1,'2026-03-25',10,10,'2026-01-28','studyLog', FALSE),
(1,'Unity Raycast挙動調整',2,'2026-03-08',60,60,'2026-01-28','Unity', FALSE),
(1,'Unity UIレイアウト調整',2,'2026-03-01',60,60,'2026-01-28','Unity', FALSE),
(1,'就活ES下書き',1,'2026-03-23',20,20,'2026-01-29','就活', FALSE),
(1,'企業研究(1社)',2,'2026-03-22',45,45,'2026-01-29','就活', FALSE),
(1,'SPI対策(非言語)',2,'2026-03-07',60,60,'2026-01-29','就活', FALSE),
(1,'SPI対策(言語)',2,'2026-02-26',60,60,'2026-01-29','就活', FALSE),
(1,'面接想定質問作成',1,'2026-03-22',20,20,'2026-01-29','就活', FALSE),
(1,'自己PRブラッシュアップ',2,'2026-03-03',60,60,'2026-01-29','就活', FALSE),
(1,'ガクチカ整理',2,'2026-03-09',45,45,'2026-01-29','就活', FALSE),
(1,'学習計画作り',3,'2026-03-08',90,90,'2026-01-29','学習', FALSE),
(1,'Python基礎復習',1,'2026-04-07',10,10,'2026-01-29','学習', FALSE),
(1,'Python例外処理学習',3,'2026-03-12',120,120,'2026-01-29','学習', FALSE),
(1,'HTML/CSS微調整',2,'2026-03-21',60,60,'2026-01-29','studyLog', FALSE),
(1,'JSスライダー修正',3,'2026-03-11',90,90,'2026-01-29','studyLog', FALSE),
(1,'バグ修正: 合計時間ずれ',1,'2026-03-02',15,15,'2026-02-01','studyLog', FALSE),
(1,'タスク提案ロジック改善',2,'2026-03-15',45,45,'2026-02-01','studyLog', FALSE),
(1,'評価倍率の確認',2,'2026-03-30',45,45,'2026-02-02','studyLog', FALSE),
(1,'締切補正のテスト',2,'2026-03-04',45,45,'2026-02-02','studyLog', FALSE),
(1,'新規タスク登録UI改善',1,'2026-03-23',20,20,'2026-02-02','studyLog', FALSE),
(1,'ログイン周り確認',2,'2026-03-07',30,30,'2026-02-02','studyLog', FALSE),
(1,'パスワード変更画面',3,'2026-03-18',90,90,'2026-02-02','studyLog', FALSE),
(1,'日報テンプレ作成',1,'2026-03-09',20,20,'2026-02-02','学校', FALSE),
(1,'議事録テンプレ作成',2,'2026-02-25',45,45,'2026-02-02','学校', FALSE),
(1,'DBインデックス検討',3,'2026-03-12',120,120,'2026-02-02','studyLog', FALSE),
(1,'テストケース作成',3,'2026-03-10',90,90,'2026-02-02','studyLog', FALSE),
(1,'単体テスト追加',2,'2026-03-15',60,60,'2026-02-02','studyLog', FALSE),
(1,'コード整形',2,'2026-03-12',30,30,'2026-02-02','studyLog', FALSE),
(1,'修正: task.py',3,'2026-03-26',120,120,'2026-02-03','studyLog', FALSE),
(1,'修正: projects.py',3,'2026-03-09',120,120,'2026-02-03','studyLog', FALSE),
(1,'エラーハンドリング改善',3,'2026-03-08',90,90,'2026-02-03','studyLog', FALSE),
(1,'洗濯',1,'2026-03-18',20,20,'2026-02-03','家事', FALSE),
(1,'部屋掃除',2,'2026-03-03',45,45,'2026-02-03','家事', FALSE),
(1,'買い物(食材)',2,'2026-03-29',30,30,'2026-02-03','家事', FALSE),
(1,'自炊(作り置き)',2,'2026-04-04',45,45,'2026-02-03','家事', FALSE),
(1,'ストレッチ10分',1,'2026-03-11',10,10,'2026-02-03','健康', FALSE),
(1,'散歩20分',1,'2026-02-25',20,20,'2026-02-03','健康', FALSE),
(1,'筋トレ15分',1,'2026-03-09',15,15,'2026-02-03','健康', FALSE),
(1,'睡眠ルーティン整備',2,'2026-03-20',30,30,'2026-02-03','健康', FALSE),
(1,'家計簿',1,'2026-03-24',15,15,'2026-02-03','家事', FALSE),
(1,'メール返信',1,'2026-03-19',15,15,'2026-02-03','生活', FALSE),
(1,'読書30分',2,'2026-03-20',30,30,'2026-02-03','学習', FALSE),
(1,'英単語20分',1,'2026-04-02',20,20,'2026-02-03','学習', FALSE),
(1,'技術記事読む',2,'2026-03-21',45,45,'2026-02-03','学習', FALSE),
(1,'下書き',2,'2026-03-28',60,60,'2026-02-03','ポートフォリオ', FALSE),
(1,'ポートフォリオ画像用意',2,'2026-02-17',45,45,'2026-02-03','ポートフォリオ', FALSE),
(1,'デモ動画撮影',3,'2026-03-12',90,90,'2026-02-03','ポートフォリオ', FALSE),
(1,'スライド作成(発表)',3,'2026-03-23',90,90,'2026-02-04','学校', FALSE),
(1,'発表練習',2,'2026-03-09',60,60,'2026-02-04','学校', FALSE),
(1,'コードレビュー依頼',1,'2026-03-08',10,10,'2026-02-04','studyLog', FALSE),
(1,'レビュー反映',2,'2026-04-04',60,60,'2026-02-04','studyLog', FALSE),
(1,'机整理',2,'2026-03-14',45,45,'2026-02-04','生活', FALSE),
(1,'バックログ優先度付け',2,'2026-02-23',45,45,'2026-02-04','studyLog', FALSE),
(1,'次プロジェクト計画',2,'2026-03-31',60,60,'2026-02-04','studyLog', FALSE),
(1,'DBテストデータ追加',3,'2026-03-08',90,90,'2026-02-04','studyLog', FALSE),
(1,'ER図更新',2,'2026-03-04',30,30,'2026-02-04','studyLog', FALSE),
(1,'API仕様メモ',2,'2026-03-20',60,60,'2026-02-04','studyLog', FALSE),
(1,'UIモック更新',2,'2026-03-09',45,45,'2026-02-04','studyLog', FALSE),
(1,'アクセシビリティ確認',2,'2026-03-26',60,60,'2026-02-04','studyLog', FALSE),
-- user_id = 2
(2, '仕様書レビュー', 1, '2026-02-01', 80, 80, '2026-01-26', '仕事', FALSE),
(2, '夕食の買い出し', 3, '2026-01-29', 30, 30, '2026-01-26', '生活', FALSE),
(2, 'ストレッチ', 3, '2026-01-30', 20, 20, '2026-01-26', '健康', FALSE),
(2, '英語学習', 2, '2026-02-10', 45, 45, '2026-01-27', '学習', FALSE),
(2, '家族への連絡', 2, '2026-01-31', 15, 15, '2026-01-26', 'プライベート', FALSE),
-- user_id = 3
(3, '資料整理', 1, '2026-02-03', 60, 60, '2026-01-27', '仕事', FALSE),
(3, '掃除', 3, '2026-02-01', 30, 30, '2026-01-26', '生活', FALSE),
(3, '筋トレ', 3, '2026-01-30', 45, 45, '2026-01-26', '健康', FALSE),
(3, 'オンライン講座受講', 1, '2026-02-12', 90, 90, '2026-01-27', '学習', FALSE),
(3, '友人と食事の予定調整', 2, '2026-02-05', 20, 20, '2026-01-26', 'プライベート', FALSE);
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
(1,'2026-01-23 10:00:00','元気',3),
(2,'2026-01-24 11:00:00','普通',2),
(3,'2026-01-25 10:00:00','元気',3),
(1,'2026-01-26 08:00:00','普通',2),
(1,'2026-01-27 08:00:00','普通',2),
(2,'2026-01-27 08:30:00','元気',3),
(3,'2026-01-27 09:00:00','元気',3),
(1,'2026-01-28 10:00:00','普通',2),
(2,'2026-01-28 11:00:00','元気',3),
(3,'2026-01-28 10:00:00','普通',2),
(1,'2026-01-29 10:00:00','悪い',1),
(2,'2026-01-29 11:00:00','悪い',1),
(3,'2026-01-29 10:00:00','悪い',1),
(1,'2026-01-30 08:00:00','悪い',1),
(2,'2026-01-30 08:00:00','普通',2),
(3,'2026-01-30 08:00:00','元気',3),
(1,'2026-01-31 08:00:00','悪い',1),
(1,'2026-02-01 08:00:00','悪い',1),
(1,'2026-02-02 08:00:00','普通',2),
(1,'2026-02-03 08:00:00','普通',2),
(1,'2026-02-04 08:00:00','元気',3),
(1,'2026-02-05 08:00:00','普通',2),
(1,'2026-02-06 08:00:00','普通',2),
(1,'2026-02-07 08:00:00','普通',2),
(1,'2026-02-08 08:00:00','悪い',1),
(1,'2026-02-09 08:00:00','普通',2),
(1,'2026-02-10 08:00:00','普通',2),
(1,'2026-02-11 08:00:00','悪い',1),
(1,'2026-02-12 08:00:00','悪い',1),
(1,'2026-02-13 08:00:00','普通',2),
(1,'2026-02-14 08:00:00','元気',3),
(1,'2026-02-15 08:00:00','普通',2),
(1,'2026-02-16 08:00:00','元気',3),
(1,'2026-02-17 08:00:00','元気',3),
(1,'2026-02-18 08:00:00','普通',2),
(1,'2026-02-19 08:00:00','元気',3),
(1,'2026-02-20 08:00:00','普通',2),
(1,'2026-02-21 08:00:00','元気',3),
(1,'2026-02-22 08:00:00','普通',2),
(1,'2026-02-23 08:00:00','普通',2),
(1,'2026-02-24 08:00:00','普通',2),
(1,'2026-02-25 08:00:00','悪い',1),
(1,'2026-02-26 08:00:00','元気',3),
(1,'2026-02-27 08:00:00','普通',2),
(1,'2026-02-28 08:00:00','普通',2),
(1,'2026-03-01 08:00:00','元気',3);


-- タスク作業ログ
INSERT INTO t_task_work_logs (task_id, work_date, work_min, start_time, end_time) VALUES
(1, '2026-01-26', 60, '09:00:00', '10:00:00'),
(1, '2026-01-27', 60, '10:00:00', '11:00:00'),
(2, '2026-01-25', 30, '14:00:00', '14:30:00'),
(2, '2026-01-26', 30, '14:30:00', '15:00:00'),
(3, '2026-01-26', 45, '10:00:00', '10:45:00'),
(3, '2026-01-27', 45, '10:45:00', '11:30:00'),
(1, '2026-02-26', 30, '14:00:00', '14:30:00');

-- タスク提案（ヘッダ）
INSERT INTO t_task_suggestions
(user_id, suggestion_date, mood, mood_point, coef_value, evaluation, evaluation_multiplier, target_task_level)
VALUES
(1,'2026-01-27','普通',2,1.10,3,1.2,3),
(1,'2026-01-28','普通',2,0.95,2,1.0,2),
(1,'2026-01-29','悪い',1,0.80,NULL,1.0,1),

(2,'2026-01-27','元気',3,1.05,3,1.2,3),
(2,'2026-01-28','元気',3,1.20,3,1.2,4),
(2,'2026-01-29','悪い',1,0.85,1,0.80,1),

(3,'2026-01-27','元気',3,1.15,3,1.2,3),
(3,'2026-01-28','普通',2,1.00,1,0.8,2),
(3,'2026-01-29','悪い',1,0.75,NULL,1.0,1),

(1,'2026-01-30','悪い',1,1.10,3,1.2,3),
(2,'2026-01-30','普通',2,1.00,2,1.0,2),
(3,'2026-01-30','元気',3,1.20,3,1.2,4);
-- タスク提案詳細
INSERT INTO t_task_suggestion_detail
(task_suggestion_id, task_id, plan_min, remaining_min_at_suggest, days_left, deadline_multiplier, exec_task_level, priority_score, actual_work_min)
VALUES
(4, 1, 30, 25, 5, 1.2, 2.5, 60.0, NULL),
(4, 2, 20, 40, 6, 1.2, 2.0, 48.0, NULL),

(5, 3, 25, 50, 8, 1.1, 2.2, 55.0, NULL),
(5, 4, 40, 120, 2, 1.3, 1.8, 45.0, NULL),

(6, 5, 15, 30, 7, 1.2, 1.5, 35.0, NULL),

(7, 6, 40, 80, 3, 1.2, 3.0, 70.0, NULL),
(7, 7, 15, 30, 1, 1.3, 2.8, 65.0, NULL),

(8, 8, 20, 20, 2, 1.3, 2.0, 50.0, NULL),

(9, 9, 30, 45, 1, 1.3, 1.6, 40.0, NULL),

(10, 10, 25, 60, 4, 1.2, 2.7, 68.0, NULL),
(11, 11, 20, 30, 6, 1.2, 2.1, 52.0, NULL);