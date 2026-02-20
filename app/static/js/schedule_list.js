(function () {
  let pendingId = null;

  /* 削除ボタン — イベント委譲 */
  document.querySelector(".sl-page").addEventListener("click", function (e) {
    const btn = e.target.closest(".sl-delete-btn");
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    pendingId = btn.getAttribute("data-task-id");
    openModal();
  });

  function openModal() {
    const modal = document.getElementById("slDeleteModal");
    modal.classList.add("show");
    modal.addEventListener("click", function outside(e) {
      if (e.target === modal) {
        closeModal();
        modal.removeEventListener("click", outside);
      }
    });
  }

  window.slCloseModal = function () {
    closeModal();
  };

  function closeModal() {
    document.getElementById("slDeleteModal").classList.remove("show");
    pendingId = null;
  }

  window.slConfirmDelete = function () {
    if (!pendingId) return;
    const card = document
      .querySelector(`[data-task-id="${pendingId}"]`)
      ?.closest(".sl-task-card");
    closeModal();
    if (card) {
      card.classList.add("deleting");
      setTimeout(() => {
        const form = document.createElement("form");
        form.method = "POST";
        form.action = "/schedule/delete/" + pendingId;
        document.body.appendChild(form);
        form.submit();
      }, 300);
    }
  };

  /* メモ開閉 */
  window.slToggleComment = function (btn) {
    const content = btn.nextElementSibling;
    const hidden = content.classList.contains("hidden");
    content.classList.toggle("hidden", !hidden);
    btn.classList.toggle("collapsed", !hidden);
  };

  /* カード入場アニメーション */
  document.addEventListener("turbo:load", function () {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) e.target.classList.add("visible");
        });
      },
      { threshold: 0.05 },
    );

    document.querySelectorAll(".sl-task-card").forEach((card, i) => {
      card.style.transitionDelay = i * 0.07 + "s";
      observer.observe(card);
    });

    /* タッチフィードバック */
    document
      .querySelectorAll(".sl-task-card, .sl-weekday.active, .sl-delete-btn")
      .forEach((el) => {
        el.addEventListener("touchstart", () => (el.style.opacity = "0.75"));
        el.addEventListener("touchend", () => (el.style.opacity = "1"));
        el.addEventListener("touchcancel", () => (el.style.opacity = "1"));
      });
  });
})();
