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
    const activeItem = document.querySelector(".item.is-active");
    if (!activeItem) return;

    const form = activeItem.querySelector("form.start_form");
    if (!form) return;

    // 「4枚目のカスタム画面を開いているか」の判定
    const isCustomPage = activeItem.querySelector(".custom_selection") !== null;

    if (isCustomPage) {
      // 既存の古い hidden input（HTMLに最初からある全タスク分のinputなど）があれば一度クリアする
      // ※これをしないと、選んでいないタスクまで一緒に送られてしまうのを防ぐため
      form.querySelectorAll("input[name='selected_task_ids'], input[name='selected_plan_mins'], input[name='task_name']").forEach(el => el.remove());

      // 画面上で「実際に選択されている（is-selectedがついている）」行だけを全て取得
      const selectedItems = activeItem.querySelectorAll(".task_selectable.is-selected");

      // 1つも選ばれていない場合は送信をブロック（必要に応じてコメントアウトを解除してください）
      // if (selectedItems.length === 0) {
      //   alert("タスクを1つ以上選択してください。");
      //   return;
      // }
      
      // 選択された行のデータをループして、フォームの中に動的にhidden要素を作る
      selectedItems.forEach(el => {
        // HTMLの li要素に仕込んだ data-task-id と data-plan-min を取得
        const taskId = el.getAttribute('data-task-id');
        const planMin = el.getAttribute('data-plan-min');
        
        if (taskId) {
          // 送信用に task_id の隠しインプットを生成してフォームに追加
          const idInput = document.createElement('input');
          idInput.type = 'hidden';
          idInput.name = 'selected_task_ids'; // Python側で受け取る名前
          idInput.value = taskId;
          form.appendChild(idInput);
        }

        if (planMin) {
          // 同一IDで分数が違う場合の対策として plan_min もペアで追加
          const minInput = document.createElement('input');
          minInput.type = 'hidden';
          minInput.name = 'selected_plan_mins';
          minInput.value = planMin;
          form.appendChild(minInput);
        }
      });
    }

    // 通常の1〜3枚目も、4枚目のカスタムも、最終的にここで安全に送信！
    if (form.requestSubmit) form.requestSubmit();
    else form.submit();
  });
}