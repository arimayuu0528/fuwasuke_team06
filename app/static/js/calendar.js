// calendar.js

document.addEventListener('turbo:load', function() {
    const container = document.getElementById('calendar-container');
    const titleDisplay = document.getElementById('current-month-display');

    if (!container || !titleDisplay) return;

    // 多重生成防止
    container.innerHTML = '';

    // --- データの読み込み ---
    const holidaysRaw = container.getAttribute('data-holidays');
    const eventsRaw = container.getAttribute('data-events');
    try {
        window.HOLIDAYS = JSON.parse(holidaysRaw || '{}');
        window.EVENTS = JSON.parse(eventsRaw || '{}');
    } catch (e) {
        window.HOLIDAYS = {};
        window.EVENTS = {};
    }

    // --- 1. Observer の定義（タイトルの更新用） ---
    // 関数の外ではなく、この中で先に定義します
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                titleDisplay.textContent = `${entry.target.dataset.year}年 ${entry.target.dataset.month}月`;
            }
        });
    }, { root: container, threshold: 0.2 });

    // --- 2. 月を追加する関数 ---
    function addMonth(date, isPrepend = false) {
        const year = date.getFullYear();
        const month = date.getMonth();
        const section = createMonthSection(year, month);

        if (isPrepend) {
            const beforeHeight = container.scrollHeight;
            container.prepend(section);
            const afterHeight = container.scrollHeight;
            // 上に追加した分だけ位置をずらしてガタつきを防止
            container.scrollTop += (afterHeight - beforeHeight);
        } else {
            container.appendChild(section);
        }
        observer.observe(section);
    }

    // --- 3. 管理用の日付変数 ---
    let oldestDate = new Date();
    let newestDate = new Date();
    
    // 初期状態で「今月」を中心に前後3ヶ月分（計7ヶ月分）を表示
    oldestDate.setMonth(oldestDate.getMonth() - 3);
    newestDate.setMonth(newestDate.getMonth() - 3);

    for (let i = 0; i < 7; i++) {
        addMonth(new Date(newestDate));
        if (i < 6) newestDate.setMonth(newestDate.getMonth() + 1);
    }

    // --- 4. 今月の位置へスクロール ---
    const now = new Date();
    const currentMonthId = `month-${now.getFullYear()}-${now.getMonth() + 1}`;
    const currentElement = document.getElementById(currentMonthId);
    if (currentElement) {
        currentElement.scrollIntoView({ behavior: 'auto' });
    }

    // --- 5. 無限スクロールのイベントリスナー ---
    container.addEventListener('scroll', () => {
        // 下端に近づいた（残り300px）
        if (container.scrollHeight - container.scrollTop - container.clientHeight < 300) {
            newestDate.setMonth(newestDate.getMonth() + 1);
            addMonth(new Date(newestDate));
        }
        // 上端に近づいた
        if (container.scrollTop < 300) {
            oldestDate.setMonth(oldestDate.getMonth() - 1);
            addMonth(new Date(oldestDate), true);
        }
    });
});

// --- ヘルパー関数群（これらは今のままでOK） ---
function getDayClass(year, month, d, dayOfWeek) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    let classes = ['day-cell'];
    if (window.HOLIDAYS && window.HOLIDAYS[dateStr]) classes.push('is-holiday');
    if (dayOfWeek === 0) classes.push('is-sunday');
    if (dayOfWeek === 6) classes.push('is-saturday');
    return classes.join(' ');
}

function createMonthSection(year, month) {
    const section = document.createElement('section');
    section.className = 'month-section';
    section.dataset.year = year;
    section.dataset.month = month + 1;
    section.id = `month-${year}-${month + 1}`;

    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();

    let html = '<table class="calendar-table"><tbody><tr>';

    for (let i = 0; i < firstDay; i++) {
        html += '<td></td>';
    }

    for (let d = 1; d <= lastDate; d++) {
        const dayOfWeek = (d + firstDay - 1) % 7;
        if (dayOfWeek === 0 && d !== 1) {
            html += '</tr><tr>';
        }

        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        let eventHtml = '';
        if (window.EVENTS && window.EVENTS[dateStr]) {
            const dayEvents = window.EVENTS[dateStr];
            if (Array.isArray(dayEvents)){
                eventHtml = dayEvents.map(title => `<div class="event-item">${title}</div>`).join('');
            } else{
                eventHtml = `<div class="event-item">${dayEvents}</div>`;
            }
        }

        const cellClass = getDayClass(year, month, d, dayOfWeek);
        html += `<td class="${cellClass}">
                    <span class="day-number">${d}</span>
                    <div class="event-list">${eventHtml}</div>
                </td>`;
    }
    
    // 最後の行の帳尻合わせ
    const lastDay = new Date(year, month, lastDate).getDay();
    for (let i = 1; i < (7 - lastDay); i++) {
        html += '<td></td>';
    }

    html += '</tr></tbody></table>';
    section.innerHTML = html;
    return section;
}