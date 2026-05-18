// --- 要素の取得 ---
const viewport = document.querySelector(".container");
const track = viewport?.querySelector(".track");
const NextBtn = document.querySelector(".next_btn");
const BackBtn = document.querySelector(".back_btn");
const indicators = document.querySelectorAll(".indicator");
const DecideBtn = document.querySelector("#decideBtn");
const items = track?.querySelectorAll(".item");

let SliderStatus = 1;
const maxStatus = items ? items.length : 1;

// スライドの位置を動かす関数（常に最新の枠幅を計算）
function moveSlider() {
  if (!viewport || !track) return;
  const currentStep = viewport.clientWidth;
  track.style.transform = `translateX(-${currentStep * (SliderStatus - 1)}px)`;
}

function updateActive() {
  if (!items) return;
  items.forEach((item, idx) => {
    item.classList.toggle("is-active", idx === SliderStatus - 1);
  });
  
  // ドットインジケータの色更新
  indicators.forEach((dot, idx) => {
    dot.style.backgroundColor = (idx === SliderStatus - 1) ? "#EFAB6F" : "lightgray";
  });

  // 矢印ボタンの色の制御
  if (BackBtn) BackBtn.style.color = (SliderStatus === 1) ? "lightgray" : "#F7BD58";
  if (NextBtn) NextBtn.style.color = (SliderStatus === maxStatus) ? "lightgray" : "#F7BD58";
}

// 初期化
updateActive();

// ウィンドウサイズが変わったら位置を自動追従
window.addEventListener("resize", () => {
  moveSlider();
});

// 進むボタン
if (NextBtn) {
  NextBtn.addEventListener("click", () => {
    if (SliderStatus < maxStatus) {
      SliderStatus++;
      updateActive();
      moveSlider();
    }
  });
}

// 戻るボタン
if (BackBtn) {
  BackBtn.addEventListener("click", () => {
    if (SliderStatus > 1) {
      SliderStatus--;
      updateActive();
      moveSlider();
    }
  });
}

// --- 4枚目の「選択ボタン」をクリックした時の処理 ---
document.querySelectorAll('.task_selectable').forEach(el => {
  el.addEventListener('click', () => {
    // 選択状態のクラス（背景色などの見た目）を切り替え
    el.classList.toggle('is-selected'); 
    
    // 中にある隠しチェックボックスを連動（もしHTMLに残っていても安全に動くようにケア）
    const cb = el.querySelector('input[type="checkbox"]');
    if (cb) cb.checked = !cb.checked; 

    // --- 合計時間のリアルタイム計算（〇時間〇分フォーマット） ---
    let totalMinutes = 0;
    // 現在のアクティブなスライド内で、選択されているタスクの分数を集計
    document.querySelectorAll('.item.is-active .is-selected .plan_min').forEach(minEl => {
      totalMinutes += parseInt(minEl.innerText) || 0;
    });

    let displayText = "";
    if (totalMinutes >= 60) {
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;
      displayText = (minutes === 0) ? `${hours}時間` : `${hours}時間${minutes}分`;
    } else {
      displayText = `${totalMinutes}分`;
    }

    const sumEl = document.querySelector('.item.is-active .sum_time');
    if (sumEl) sumEl.innerText = `合計：${displayText}`;
  });
});

// --- 【最重要】決定ボタンを押したときの処理（123枚目・4枚目すべての送信をここで一括制御） ---
if (DecideBtn) {
  DecideBtn.addEventListener("click", () => { 
    // 現在画面に見えているスライド（item）を取得
    const activeItem = document.querySelector(".item.is-active");
    if (!activeItem) return;

    // 今の画面が「4枚目のカスタム選択画面」かどうかを判定
    const isCustomPage = activeItem.querySelector(".custom_selection") !== null;
    
    // そのスライド内にあるフォームを取得
    const form = activeItem.querySelector("form.start_form");
    if (!form) return;

    if (isCustomPage) {
      // --- 4枚目の場合：送信直前のパッキング処理 ---
      // フォーム内に最初から埋め込んであるすべてのタスク用inputを取得
      const hiddenInputs = form.querySelectorAll("input[name='task_name']");
      const selectables = activeItem.querySelectorAll(".task_selectable");

      // HTML側のループ順（インデックス）を合わせてチェック
      selectables.forEach((el, idx) => {
        if (hiddenInputs[idx]) {
          // 選ばれていない（'is-selected' が付いていない）タスクのinputをdisabledにする
          // これにより、選んだタスクだけが1〜3枚目と【完全に同じ形式】で送信されます
          hiddenInputs[idx].disabled = !el.classList.contains("is-selected");
        }
      });

      // カスタム画面で1つも選んでいない場合は、誤送信（空リロード）を防ぐためにブロック
      const selectedCount = activeItem.querySelectorAll(".task_selectable.is-selected").length;
      if (selectedCount === 0) {
        alert("タスクを1つ以上選択してください。");
        return; 
      }
    }

    // --- 1〜3枚目の通常提案、および4枚目のカスタム処理通過後、安全に送信を実行 ---
    if (form.requestSubmit) {
      form.requestSubmit();
    } else {
      form.submit();
    }
  });
}