// mypage.js

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. 通知ボタン (ON/OFF) のロジック ---
    const btnOn = document.getElementById('btn_on');
    const btnOff = document.getElementById('btn_off');

    function toggleNotice(activeBtn, inactiveBtn) {
        activeBtn.classList.add('is_active');
        inactiveBtn.classList.remove('is_active');
    }

    if (btnOn && btnOff) {
        btnOn.addEventListener('click', () => toggleNotice(btnOn, btnOff));
        btnOff.addEventListener('click', () => toggleNotice(btnOff, btnOn));
    }

    // --- 2. 保存ボタンの活性化ロジック ---
    const form = document.querySelector('.life_rhythm_form');
    const saveButton = document.getElementById('save-button');
    const inputs = document.querySelectorAll('.time_input');
    const initialValues = {};

    inputs.forEach(input => {
        initialValues[input.name] = input.value;
    });

    function checkChanges() {
        let isChanged = false;
        inputs.forEach(input => {
            if (input.value !== initialValues[input.name]) isChanged = true;
        });
        if (saveButton) saveButton.disabled = !isChanged;
    }

    inputs.forEach(input => {
        input.addEventListener('input', checkChanges);
    });

    // --- 3. モーダル制御ロジック ---
    const modal = document.getElementById('save-modal');
    const closeBtn = document.getElementById('close-modal');

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault(); 
            if (modal) modal.style.display = 'flex';
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            if (modal) modal.style.display = 'none';
            // 現在の値を新しい初期値として保存（ボタンを再度グレーアウト）
            inputs.forEach(input => {
                initialValues[input.name] = input.value;
            });
            if (saveButton) saveButton.disabled = true;
        });
    }

    const logoutBtn = document.querySelector('.logout'); // ログアウトボタン本体
    const logoutModal = document.getElementById('logout-modal');
    const confirmLogout = document.getElementById('confirm-logout');
    const cancelLogout = document.getElementById('cancel-logout');

    if (logoutBtn && logoutModal) {
        // ログアウトボタンを押したらモーダルを表示
        logoutBtn.addEventListener('click', () => {
            logoutModal.style.display = 'flex';
        });

        // 「いいえ」ボタン：モーダルを閉じる
        cancelLogout.addEventListener('click', () => {
            logoutModal.style.display = 'none';
        });

        // 「はい」ボタン：ログアウト処理を実行
        confirmLogout.addEventListener('click', () => {
            // FlaskなどのバックエンドのログアウトURLへリダイレクト
            window.location.href = "/logout"; 
        });

        // 背景（オーバーレイ）をクリックしても閉じるようにする
        logoutModal.addEventListener('click', (e) => {
            if (e.target === logoutModal) {
                logoutModal.style.display = 'none';
            }
        });
    }
});