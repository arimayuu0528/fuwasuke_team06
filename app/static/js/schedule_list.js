(function () {
  let pendingId = null;

  /* 削除ボタン — イベント委譲 */
  document.querySelector(".sl-page").addEventListener("click", function (e) {
    const btn = e.target.closest(".sl-delete-btn");
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();

    pendingId = btn.dataset.taskId;
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

  /* 削除確定 */
  window.slConfirmDelete = function () {
    if (!pendingId) return;

    fetch(`/schedule/delete/${pendingId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error();
        // 成功 → リロード
        location.reload();
      })
      .catch(() => {
        alert("削除に失敗しました");
      });

    closeModal();
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
