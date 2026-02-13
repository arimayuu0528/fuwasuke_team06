const ctx = document.getElementById('moodChart');

new Chart(ctx, {
    type: 'line',
    data: {
        labels: moodDates,
        datasets: [{
            data: moodValues,
            tension: 0.4,
            cubicInterpolationMode: 'monotone',
            spanGaps: true,
            pointRadius: 5,
            pointHoverRadius: 7
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: false   // ← 「気分」ラベル消す
            }
        },
        scales: {
            x: {
                grid: {
                    display: true   // ← 縦線そのまま表示
                }
            },
            y: {
                min: 1,
                max: 3,
                ticks: {
                    stepSize: 1,
                    callback: function(value) {
                        if (value == 1) return "悪い";
                        if (value == 2) return "普通";
                        if (value == 3) return "元気";
                    }
                }
            }
        }
    }
});