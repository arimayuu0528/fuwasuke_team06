-- -------------------------------------------------------------------
-- HEW用 説明時：削除コマンド (PHPMyadmin:SQLタブで実行)
-- -------------------------------------------------------------------
-- 1) 今日の評価ログ（1行）
DELETE FROM t_task_evaluation_logs
WHERE user_id = 1
    AND target_date = '2026-03-06';

-- 2) 今日の提案明細（FK対策：存在するなら消す）
DELETE d
FROM t_task_suggestion_detail d
JOIN t_task_suggestions s
    ON s.task_suggestion_id = d.task_suggestion_id
WHERE s.user_id = 1
    AND s.suggestion_date = '2026-03-06';

-- 3) 今日の提案ヘッダ（選択済みで1行だけ残ってる想定）
DELETE FROM t_task_suggestions
WHERE user_id = 1
    AND suggestion_date = '2026-03-06';

-- 4) 今日の気分（日時型でも日付で一致させる）
DELETE FROM t_today_moods
WHERE user_id = 1
    AND mood_date >= '2026-03-06 00:00:00'
    AND mood_date <  '2026-03-07 00:00:00';
