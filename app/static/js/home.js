let currentDate = new Date();

function updateDate() {
    const month = currentDate.getMonth() + 1;
    const day = currentDate.getDate();
    const weekList = ["日","月","火","水","木","金","土"];
    const week = weekList[currentDate.getDay()];

    document.getElementById("today").innerText =
        `${month}月${day}日(${week})`;
}

function changeDate(offset) {
    currentDate.setDate(currentDate.getDate() + offset);
    updateDate();
}

window.onload = updateDate;
