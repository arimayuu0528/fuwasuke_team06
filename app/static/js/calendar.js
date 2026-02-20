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
                eventHtml = dayEvents.map(ev => `<div class="event-item">${ev.title || ev}</div>`).join('');
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


document.addEventListener('turbo:load', function() {
    const container = document.getElementById('calendar-container');
    const titleDisplay = document.getElementById('current-month-display');
    const modal = document.getElementById('event-modal');
    const modalDateTitle = document.getElementById('modal-date-title');
    const modalEventBody = document.getElementById('modal-event-body');
    const closeModal = document.getElementById('close-modal');

    if (!container || !titleDisplay || !modal) return;
    // --- モーダル表示ロジック ---
    container.addEventListener('click', (e) => {
        const cell = e.target.closest('.day-cell');
        if (!cell) return;

        const section = cell.closest('.month-section');
        const dateStr = `${section.dataset.year}-${String(section.dataset.month).padStart(2, '0')}-${String(cell.querySelector('.day-number').textContent).padStart(2, '0')}`;

        const formatTime = (timeStr) => {
            if (!timeStr) return '--:--';
            return timeStr.substring(0, 5); // "09:00:00" -> "09:00"
        };

        modalDateTitle.textContent = `${dateStr.replace(/-/g, '/')} の予定`;
        
        const dayEvents = window.EVENTS[dateStr];
        modalEventBody.innerHTML = ''; // クリア

        if (dayEvents && Array.isArray(dayEvents)) {
            dayEvents.forEach(ev => {
                // 各予定の詳細カードを作成
                const card = `
                    <div class="event-detail-card">
                        <div class="event-detail-title">${ev.title || '無題'}</div>
                        <div class="event-info-grid">
                            <div class="info-label">時間</div>
                            <div class="info-value">${ev.start_time || '--:--'} 〜 ${ev.end_time || '--:--'}</div>
                            
                            <div class="info-label">場所</div>
                            <div class="info-value">${ev.location || '設定なし'}</div>
                            
                            <div class="info-label">タグ</div>
                            <div class="info-value"><span class="tag-badge">${ev.tag || 'なし'}</span></div>
                            
                            <div class="info-label">メモ</div>
                            <div class="info-value">${ev.memo || '-'}</div>
                        </div>
                    </div>
                `;
                modalEventBody.insertAdjacentHTML('beforeend', card);
            });
        } else {
            modalEventBody.innerHTML = '<p style="text-align:center; color:#999;">予定はありません。</p>';
        }

        modal.style.display = 'flex';
    });

    // 閉じるボタン
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // 背景クリックで閉じる
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});