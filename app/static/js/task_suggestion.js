// --- 既存の取得コードはそのまま ---
const viewport = document.querySelector(".container");
const track = viewport?.querySelector(".track");
const step = viewport.clientWidth;
const NextBtn = document.querySelector(".next_btn")
const BackBtn = document.querySelector(".back_btn")
const indicators = document.querySelectorAll(".indicator")
const DecideBtn = document.querySelector("#decideBtn");
const items = track.querySelectorAll(".item");

let SliderStatus = 1;
// 最大枚数を取得（4枚なら4）
const maxStatus = items.length;

function updateActive() {
  items.forEach((item, idx) => {
    item.classList.toggle("is-active", idx === SliderStatus - 1);
  });
  
  // ドットの色更新（ループで回すことで枚数変化に対応）
  indicators.forEach((dot, idx) => {
    if (idx === SliderStatus - 1) {
      dot.style.backgroundColor = "#EFAB6F";
    } else {
      dot.style.backgroundColor = "lightgray";
    }
  });

  // ボタンの色の制御
  BackBtn.style.color = (SliderStatus === 1) ? "lightgray" : "#F7BD58";
  NextBtn.style.color = (SliderStatus === maxStatus) ? "lightgray" : "#F7BD58";
}

updateActive();

// 進むボタン：switchを使わず「今の状態 + 1」で計算
NextBtn.addEventListener("click", () => {
  if (SliderStatus < maxStatus) {
    SliderStatus++;
    updateActive();
    track.style.transform = `translateX(-${step * (SliderStatus - 1)}px)`;
  }
});

// 戻るボタン：同様に「今の状態 - 1」で計算
BackBtn.addEventListener("click", () => {
  if (SliderStatus > 1) {
    SliderStatus--;
    updateActive();
    track.style.transform = `translateX(-${step * (SliderStatus - 1)}px)`;
  }
});

// 決定ボタン（既存のまま）
if(DecideBtn){
  DecideBtn.addEventListener("click", () => { 
    const activeItem = document.querySelector(".item.is-active");
    const form = activeItem?.querySelector("form.start_form");
    if (!form) return;
    if (form.requestSubmit) form.requestSubmit();
    else form.submit();
  });
}

// --- 追加：4枚目の「選択ボタン」を動かす処理 ---
document.querySelectorAll('.task_selectable').forEach(el => {
  el.addEventListener('click', () => {
    el.classList.toggle('is-selected'); // 選択状態のクラスを切り替え
    const cb = el.querySelector('input[type="checkbox"]');
    if(cb) cb.checked = !cb.checked; // 隠しチェックボックスを連動
    
    // 合計時間のリアルタイム計算
    let total = 0;
    // 今表示されている（is-active）カード内の、選択済み（is-selected）の分数を合計
    document.querySelectorAll('.item.is-active .is-selected .plan_min').forEach(minEl => {
      total += parseInt(minEl.innerText) || 0;
    });
    const sumEl = document.querySelector('.item.is-active .sum_time');
    if(sumEl) sumEl.innerText = `合計：${total}分`;
  });
});