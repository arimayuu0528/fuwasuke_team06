// mood_graph.js
document.addEventListener("turbo:load", function () {

    const canvas = document.getElementById("moodChart");
    if (!canvas) return;

    // 縦を300pxに固定
    const wrapper = canvas.parentElement;
    const newHeight = 300;
    wrapper.style.height = newHeight + "px";
    canvas.height = newHeight;

    // 画像読み込み
    const waruiImg = new Image();
    waruiImg.src = "/static/image/warui.png";
    const futuImg = new Image();
    futuImg.src = "/static/image/futu.png";
    const genkiImg = new Image();
    genkiImg.src = "/static/image/gennki.png"; // ファイル名確認

    // Chart.js 初期化
    const chart = new Chart(canvas, {
        type: "line",
        data: {
            labels: moodDates,
            datasets: [{
                data: moodValues,
                borderColor: "#F09942", // 線の色
                backgroundColor: "rgba(240, 153, 66, 0.2)", // optional 塗りつぶし
                borderWidth: 4,
                tension: 0.4,
                pointRadius: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 120,   // 左余白
                    right: 60,  // 右余白
                    top: 60     // 上余白（画像切れ防止）
                }
            },
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    min: 0.99,
                    max: 3.2,
                    ticks: { stepSize: 1, display: false },
                    grid: { display: false, drawBorder: false } // 縦軸線と目盛り線非表示
                },
                x: {
                    grid: { display: false, drawBorder: false } // 横軸線非表示
                }
            }
        },
        plugins: [{
            id: "yAxisImages",
            afterDraw(chart) {
                const { ctx, chartArea, scales } = chart;
                const yScale = scales.y;
                const size = 50;  // 画像サイズ

                const images = {
                    3: { img: genkiImg, label: "元気" },
                    2: { img: futuImg, label: "普通" },
                    1: { img: waruiImg, label: "悪い" }
                };

                Object.entries(images).forEach(([value, obj]) => {
                    const { img, label } = obj;
                    if (!img.complete) return;

                    const y = yScale.getPixelForValue(Number(value));

                    // 画像描画
                    ctx.drawImage(
                        img,
                        chartArea.left - 80, // 中央寄せに調整
                        y - size / 2,
                        size,
                        size
                    );

                    // 文字描画（画像の下、隙間狭め）
                    ctx.font = "16px Arial";
                    ctx.fillStyle = "#000"; // 文字色
                    ctx.textAlign = "center";
                    ctx.fillText(label, chartArea.left - 80 + size / 2, y + size / 2 + 5);
                });
            }
        }]
    });

    // 画像読み込み後に再描画
    [waruiImg, futuImg, genkiImg].forEach(img => img.onload = () => chart.update());

    // 画面リサイズ時も高さを再計算して再描画
    window.addEventListener("resize", () => {
        wrapper.style.height = newHeight + "px"; // 縦300px固定
        canvas.height = wrapper.offsetHeight;
        chart.resize();
    });
});