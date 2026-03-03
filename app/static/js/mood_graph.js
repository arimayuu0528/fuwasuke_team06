// static/js/mood_graph.js
(function () {
    "use strict";

const WEEK_JA = ["日", "月", "火", "水", "木", "金", "土"];

function safeJsonParse(text, fallback) {
    try { return JSON.parse(text); } catch { return fallback; }
}

    function readChartData(canvas) {
        const dates = safeJsonParse(canvas.dataset.dates || "[]", []);
        const values = safeJsonParse(canvas.dataset.values || "[]", []);
    return {
        dates: Array.isArray(dates) ? dates : [],
        values: Array.isArray(values) ? values : [],
    };
}
    function onAllImagesLoadedOnce(images, cb) {
    let remain = images.filter(img => !img.complete).length;
    if (remain === 0) return cb();

    const done = () => {
    remain -= 1;
    if (remain === 0) cb();
    };

    images.forEach(img => {
    if (img.complete) return;
    img.addEventListener("load", done, { once: true });
    img.addEventListener("error", done, { once: true }); // エラーでも待ち続けない
    });
}
  // "YYYY-MM-DD" 優先。 "MM-DD" の場合は今年として解釈（保険）
    function weekdayFromLabel(label) {
        const s = String(label);
        let dt = new Date(s + "T00:00:00");
    if (!Number.isNaN(dt.getTime())) return WEEK_JA[dt.getDay()];

    if (/^\d{2}-\d{2}$/.test(s)) {
        const y = new Date().getFullYear();
        dt = new Date(`${y}-${s}T00:00:00`);
        if (!Number.isNaN(dt.getTime())) return WEEK_JA[dt.getDay()];
    }
    return s;
}

    function loadImageWithFallback(paths) {
        const img = new Image();
        let i = 0;
        const tryLoad = () => { img.src = paths[i]; };
        img.onerror = () => { i += 1; if (i < paths.length) tryLoad(); };
        tryLoad();
        return img;
    }

    function destroyChart(canvas) {
        if (!canvas) return;
        if (canvas._moodChart) {
            try { canvas._moodChart.destroy(); } catch (_) {}
            canvas._moodChart = null;
        }
        if (typeof Chart !== "undefined" && typeof Chart.getChart === "function") {
            const c = Chart.getChart(canvas);
        if (c) { try { c.destroy(); } catch (_) {} }
    }
}

    function initMoodChart() {
        const canvas = document.getElementById("moodChart");
        if (!canvas) return;

        destroyChart(canvas);

        const wrapper = canvas.parentElement;
        if (wrapper && wrapper.clientHeight === 0) wrapper.style.height = "320px";

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const { dates, values } = readChartData(canvas);

        // Turbo等でページが差し替わった後に onload で update が走ると落ちるのでフラグで守る
        let alive = true;

        // キャラ画像
        const imgGenki = loadImageWithFallback(["/static/image/gennki.png",]);
        const imgFutu  = loadImageWithFallback(["/static/image/futu.png"]);
        const imgWarui = loadImageWithFallback(["/static/image/warui.png"]);

        const chart = new Chart(ctx, {
        type: "line",
        data: {
            labels: dates,
            datasets: [{
            data: values,
            borderColor: "#E8A65A",
            borderWidth: 3,
            tension: 0,
            fill: true,
            backgroundColor: "#FFF",
            pointRadius: 5,
            pointHoverRadius: 7,
            pointHitRadius: 10,
            spanGaps: false,
            // 点の見た目
            pointBackgroundColor: "#E8A65A",  // 点の塗り
            pointBorderColor: "#FFF",      // 点の枠
            pointBorderWidth: 2.5,   
        }],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,

        // 左にキャラを描くので余白を確保（好みで調整OK）
        layout: { padding: { left: 50, right: 24, top: 24, bottom: 8 } },

        interaction: { mode: "index", intersect: false },
        plugins: {
        legend: { display: false },

        // 点タップ時のポップアップ（tooltip）表示をカスタム
        tooltip: {
            usePointStyle: true, // ●（丸）を使う
            callbacks: {
            // 上段：日付（例：2026-02-20）
            title: (items) => (items[0] ? items[0].label : ""),

            // 下段：● 気分:普通
            label: (item) => {
                const v = item.raw; // 1〜3 or null
                if (v == null) return "気分:未入力";

                const mood =
                    v === 3 ? "元気" :
                    v === 2 ? "普通" :
                    v === 1 ? "悪い" : "不明";

                return `気分:${mood}`;
            },

            // ● を必ず丸にする
            labelPointStyle: () => ({
                pointStyle: "circle",
                rotation: 0,
            }),

            // ● の色
            labelColor: () => ({
                borderColor: "#E8A65A",
                backgroundColor: "#E8A65A",
                borderWidth: 0,
            }),
            },
        },
    },

        scales: {
            y: {
                min: 0.8,
                max: 3.2,
                ticks: { stepSize: 1, display: false }, // 数字は消す（キャラ＋文字で表現）
                grid: { display: false, drawBorder: false },
        },
        x: {
            grid: { display: false, drawBorder: false },
            ticks: {
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
            font: { size: 11 },
            callback: function (value) {
                const label =
                    (this && typeof this.getLabelForValue === "function")
                    ? this.getLabelForValue(value)
                    : dates[value];
                return weekdayFromLabel(label); // 月火水木金土日
                },
            },
        },
        },
    },

    plugins: [{
        // 左側に「キャラ画像＋元気/普通/悪い」を描く
        id: "yAxisImages",
        afterDraw(chart) {
            const { ctx, chartArea, scales } = chart;
            const yScale = scales.y;

            // キャラの大きさ
            const size = 28;

            const items = [
                { v: 3, img: imgGenki, label: "元気" },
                { v: 2, img: imgFutu,  label: "普通" },
                { v: 1, img: imgWarui, label: "悪い" },
            ];

            items.forEach(({ v, img, label }) => {
                const y = yScale.getPixelForValue(v);
                const x = chartArea.left - 50; // 左の描画位置

                // 画像が読み込めていない時はスキップ
                if (img.complete) {
                ctx.drawImage(img, x, y - size / 2, size, size);
                }

            // ラベル文字（画像の下）
            ctx.font = "12px Arial";
            ctx.fillStyle = "#767676";
            ctx.textAlign = "center";
            ctx.fillText(label, x + size / 2, y + size / 2 + 14);
            });
        }
        }]
    });

    canvas._moodChart = chart;

    onAllImagesLoadedOnce([imgGenki, imgFutu, imgWarui], () => {
    // Turbo等でDOMが入れ替わった後にupdateすると落ちるのでガード
    if (!canvas.isConnected) return;
    if (!canvas._moodChart) return;

    canvas._moodChart.update();
    });
    // Turboキャッシュ前に破棄
    document.addEventListener("turbo:before-cache", () => {
        alive = false;
        destroyChart(canvas);
    }, { once: true });

    // 画像ロード後に再描画 ※alive & DOM接続中のみ
    function safeUpdate() {
        if (!alive) return;
        if (!canvas.isConnected) return;
        if (!canvas._moodChart) return;
        try { canvas._moodChart.update(); } catch (_) {}
    }
    [imgGenki, imgFutu, imgWarui].forEach(img => img.onload = safeUpdate);
}

// 二重初期化防止：Turboがあれば turbo:load のみ
if (window.Turbo) {
    document.addEventListener("turbo:load", initMoodChart);
} else {
    document.addEventListener("DOMContentLoaded", initMoodChart);
}
})();