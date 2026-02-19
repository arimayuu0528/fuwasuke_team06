window.confirmDelete = confirmDelete;
window.toggleComment = toggleComment;
window.closeDeleteModal = closeDeleteModal;
let pendingDeleteTaskId = null;

// イベント委譲で削除ボタンを監視
document.body.addEventListener("click", function (e) {
  if (e.target.classList.contains("delete-btn")) {
    e.preventDefault();
    e.stopPropagation();
    const taskId = e.target.getAttribute("data-task-id");
    console.log("Delete task ID:", taskId);
    pendingDeleteTaskId = taskId;
    showDeleteModal();
  }
});

function showDeleteModal() {
  console.log("showDeleteModal - pendingDeleteTaskId:", pendingDeleteTaskId);
  const modal = document.getElementById("deleteModal");
  modal.classList.add("show");

  modal.onclick = function (e) {
    if (e.target === modal) {
      closeDeleteModal();
    }
  };
}

function closeDeleteModal() {
  const modal = document.getElementById("deleteModal");
  modal.classList.remove("show");
}

function confirmDelete() {
  console.log(
    "confirmDelete called - pendingDeleteTaskId:",
    pendingDeleteTaskId,
  );

  if (!pendingDeleteTaskId) {
    console.error("No task ID to delete");
    return;
  }

  const taskCard = document
    .querySelector(`[data-task-id="${pendingDeleteTaskId}"]`)
    ?.closest(".task-card");

  closeDeleteModal();

  if (taskCard) {
    taskCard.classList.add("deleting");
  }

  setTimeout(
    () => {
      const form = document.createElement("form");
      form.method = "POST";
      form.action = "/schedule/delete/" + pendingDeleteTaskId;
      document.body.appendChild(form);
      console.log("Submitting to:", form.action);
      form.submit();
    },
    taskCard ? 300 : 0,
  );
}

// Toggle comment visibility
function toggleComment(button) {
  const commentContent = button.nextElementSibling;
  if (commentContent.classList.contains("hidden")) {
    commentContent.classList.remove("hidden");
    button.classList.remove("collapsed");
  } else {
    commentContent.classList.add("hidden");
    button.classList.add("collapsed");
  }
}

// Initialize comments as collapsed on page load
document.addEventListener("DOMContentLoaded", function () {
  const commentContents = document.querySelectorAll(".comment-content");
  const commentToggles = document.querySelectorAll(".comment-toggle");

  commentContents.forEach((content) => {
    content.classList.add("hidden");
  });

  commentToggles.forEach((toggle) => {
    toggle.classList.add("collapsed");
  });

  addRippleEffect();
  document.documentElement.style.scrollBehavior = "smooth";
});

function addRippleEffect() {
  const buttons = document.querySelectorAll(
    ".add-task-btn, .tab, .weekday.active",
  );
  buttons.forEach((button) => {
    button.addEventListener("click", function (e) {
      const ripple = document.createElement("span");
      ripple.classList.add("ripple");
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = x + "px";
      ripple.style.top = y + "px";
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  });
}

function switchTab(tabElement) {
  const tabs = document.querySelectorAll(".tab");
  tabs.forEach((tab) => tab.classList.remove("active"));
  tabElement.classList.add("active");
  if (tabElement.textContent.trim() === "タスク") {
    window.location.href = "/tasks";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const tabs = document.querySelectorAll(".tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", function () {
      switchTab(this);
    });
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const touchElements = document.querySelectorAll(
    ".task-card, .weekday, .delete-btn",
  );
  touchElements.forEach((element) => {
    element.addEventListener("touchstart", function () {
      this.style.opacity = "0.7";
    });
    element.addEventListener("touchend", function () {
      this.style.opacity = "1";
    });
    element.addEventListener("touchcancel", function () {
      this.style.opacity = "1";
    });
  });
});

function revealOnScroll() {
  const taskCards = document.querySelectorAll(".task-card");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }
      });
    },
    { threshold: 0.1 },
  );
  taskCards.forEach((card) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(20px)";
    card.style.transition = "opacity 0.4s, transform 0.4s";
    observer.observe(card);
  });
}

document.addEventListener("DOMContentLoaded", revealOnScroll);

let pressTimer;
function setupLongPress() {
  const deleteButtons = document.querySelectorAll(".delete-btn");
  deleteButtons.forEach((btn) => {
    btn.addEventListener("touchstart", function (e) {
      pressTimer = setTimeout(() => {
        if (navigator.vibrate) navigator.vibrate(50);
        const taskCard = this.closest(".task-card");
        taskCard.style.transform = "scale(0.98)";
      }, 500);
    });
    btn.addEventListener("touchend", function () {
      clearTimeout(pressTimer);
      const taskCard = this.closest(".task-card");
      taskCard.style.transform = "scale(1)";
    });
    btn.addEventListener("touchcancel", function () {
      clearTimeout(pressTimer);
      const taskCard = this.closest(".task-card");
      taskCard.style.transform = "scale(1)";
    });
    v;
  });
}
document.addEventListener("DOMContentLoaded", setupLongPress);
