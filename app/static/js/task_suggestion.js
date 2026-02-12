// 窓 と 動かすトラックを取得
const viewport = document.querySelector(".container");
const track = viewport?.querySelector(".track");

// 窓の幅を取得
const step = viewport.clientWidth;

// 進む/戻るボタンを取得
const NextBtn = document.querySelector(".next_btn")
const BackBtn = document.querySelector(".back_btn")

// ドットを取得
const indicators = document.querySelectorAll(".indicator")

// 決定ボタンを取得
const DecideBtn = document.querySelector("#decideBtn");
// スライダーの各タスク案を全て取得
// item[0],item[1],item[2]
const items = track.querySelectorAll(".item");


// 決定ボタン：今のスライドのフォームを送信
if(DecideBtn){
  DecideBtn.addEventListener("click", () => { 
    const activeItem = document.querySelector(".item.is-active");
    const form = activeItem?.querySelector("form.start_form");
    if (!form) return;

    if (form.requestSubmit) form.requestSubmit();
    else form.submit();
  });
}


// スライダーの状態
let SliderStatus = 1;

function updateActive() {
  items.forEach((item, idx) => {
    item.classList.toggle("is-active", idx === SliderStatus - 1);
  });
}
updateActive(); // 初期状態も反映


// 進むボタンが押された時
NextBtn.addEventListener("click", () => {
  switch(SliderStatus){
    case 1:
      SliderStatus = 2;
      updateActive();
      track.style.transform = `translateX(-${step * (SliderStatus - 1)}px)`;
      NextBtn.style.color = "#F7BD58";
      BackBtn.style.color = "#F7BD58";
      indicators[0].style.backgroundColor = "lightgray";
      indicators[1].style.backgroundColor = "#EFAB6F";
      break;
    case 2:
      SliderStatus = 3;
      updateActive();
      track.style.transform = `translateX(-${step * (SliderStatus - 1)}px)`;
      NextBtn.style.color = "lightgray";
      BackBtn.style.color = "#F7BD58";
      indicators[1].style.backgroundColor = "lightgray";
      indicators[2].style.backgroundColor = "#EFAB6F";
      break;
    case 3:
      break;
  }
})

// 戻るボタンが押された時
BackBtn.addEventListener("click", () => {
  switch(SliderStatus){
    case 1:
      updateActive();
      break;
    case 2:
      SliderStatus = 1;
      updateActive();
      track.style.transform = `translateX(-${0}px)`;
      BackBtn.style.color = "lightgray";
      indicators[0].style.backgroundColor = "#EFAB6F";
      indicators[1].style.backgroundColor = "lightgray";
      break;
    case 3:
      SliderStatus = 2;
      updateActive();
      track.style.transform = `translateX(-${step * (SliderStatus - 1)}px)`;
      NextBtn.style.color = "#F7BD58";
      BackBtn.style.color = "#F7BD58";
      indicators[1].style.backgroundColor = "#EFAB6F";
      indicators[2].style.backgroundColor = "lightgray";
      break;
  }
})