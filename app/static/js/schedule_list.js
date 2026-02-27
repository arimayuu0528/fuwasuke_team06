(function () {
  let pendingId = null;

  const filters = {
    repeat: null,
    time: null,
    tag: null,
    day: new Set(),
  };

  /* ===== ドロップダウンを直接styleで開閉（CSS競合を完全回避） ===== */
  function openDropdown(wrap) {
    const dropdown = wrap.querySelector(".sl-chip-dropdown");
    if (!dropdown) return;

    const isDays = dropdown.classList.contains("sl-chip-dropdown--days");

    dropdown.style.setProperty(
      "display",
      isDays ? "flex" : "block",
      "important",
    );
    dropdown.style.setProperty("flex-wrap", isDays ? "wrap" : "", "important");
    dropdown.style.setProperty("gap", isDays ? "6px" : "", "important");
    dropdown.style.setProperty("position", "absolute", "important");
    dropdown.style.setProperty("top", "calc(100% + 8px)", "important");
    dropdown.style.setProperty("left", "0", "important");
    dropdown.style.setProperty("background", "#fff", "important");
    dropdown.style.setProperty("border-radius", "14px", "important");
    dropdown.style.setProperty(
      "box-shadow",
      "0 4px 20px rgba(0,0,0,0.12)",
      "important",
    );
    dropdown.style.setProperty("border", "1px solid #f0f0f0", "important");
    dropdown.style.setProperty("padding", isDays ? "10px" : "8px", "important");
    dropdown.style.setProperty("z-index", "9999", "important");
    dropdown.style.setProperty(
      "min-width",
      isDays ? "210px" : "120px",
      "important",
    );
    dropdown.style.setProperty("opacity", "1", "important");
    dropdown.style.setProperty("visibility", "visible", "important");
    dropdown.style.setProperty("pointer-events", "auto", "important");

    // 子要素のボタンも強制的にスタイルを当てる
    dropdown.querySelectorAll(".sl-chip-opt").forEach((opt) => {
      if (opt.classList.contains("sl-chip-opt--day")) {
        opt.style.setProperty("display", "flex", "important");
        opt.style.setProperty("width", "36px", "important");
        opt.style.setProperty("height", "36px", "important");
        opt.style.setProperty("align-items", "center", "important");
        opt.style.setProperty("justify-content", "center", "important");
        opt.style.setProperty("border-radius", "50%", "important");
        opt.style.setProperty("border", "1.5px solid #e0e0e0", "important");
        opt.style.setProperty("font-size", "13px", "important");
        opt.style.setProperty("cursor", "pointer", "important");
        opt.style.setProperty(
          "background",
          opt.classList.contains("selected")
            ? "linear-gradient(135deg,#ffb380,#ff9f5a)"
            : "#fff",
          "important",
        );
        opt.style.setProperty(
          "color",
          opt.classList.contains("selected") ? "#fff" : "#555",
          "important",
        );
      } else {
        opt.style.setProperty("display", "block", "important");
        opt.style.setProperty("width", "100%", "important");
        opt.style.setProperty("padding", "9px 14px", "important");
        opt.style.setProperty("border", "none", "important");
        opt.style.setProperty("border-radius", "8px", "important");
        opt.style.setProperty(
          "background",
          opt.classList.contains("selected") ? "#fff8f3" : "transparent",
          "important",
        );
        opt.style.setProperty(
          "color",
          opt.classList.contains("selected") ? "#ff9f5a" : "#555",
          "important",
        );
        opt.style.setProperty("font-size", "14px", "important");
        opt.style.setProperty("font-weight", "500", "important");
        opt.style.setProperty("text-align", "left", "important");
        opt.style.setProperty("cursor", "pointer", "important");
        opt.style.setProperty("white-space", "nowrap", "important");
        opt.style.setProperty("font-family", "inherit", "important");
        opt.style.setProperty("line-height", "1.4", "important");
        opt.style.setProperty("opacity", "1", "important");
        opt.style.setProperty("visibility", "visible", "important");
      }
    });

    wrap.classList.add("open");
    const arrow = wrap.querySelector(".sl-chip-arrow");
    if (arrow) arrow.style.transform = "rotate(180deg)";
  }

  function closeDropdown(wrap) {
    const dropdown = wrap.querySelector(".sl-chip-dropdown");
    if (!dropdown) return;
    dropdown.style.setProperty("display", "none", "important");
    wrap.classList.remove("open");
    const arrow = wrap.querySelector(".sl-chip-arrow");
    if (arrow) arrow.style.transform = "";
  }

  function closeAllDropdowns() {
    document.querySelectorAll(".sl-chip-wrap").forEach(closeDropdown);
  }

  /* ===== フィルター適用 ===== */
  function applyFilter() {
    const cards = document.querySelectorAll(".sl-task-card");
    let visibleCount = 0;

    cards.forEach((card) => {
      const repeat = card.dataset.repeat || "";
      const start = card.dataset.start || "";
      const days = card.dataset.days || "";
      const tag = card.dataset.tag || "";

      const repeatOk = !filters.repeat || repeat === filters.repeat;

      let timeOk = true;
      if (filters.time) {
        const hour = parseInt(start.split(":")[0], 10);
        timeOk = filters.time === "am" ? hour < 12 : hour >= 12;
      }

      const tagOk = !filters.tag || tag === filters.tag;
      const dayOk =
        filters.day.size === 0 ||
        [...filters.day].some((d) => days.includes(d));

      const show = repeatOk && timeOk && tagOk && dayOk;
      card.classList.toggle("hidden-by-filter", !show);
      if (show) visibleCount++;
    });

    const emptyMsg = document.getElementById("slFilterEmpty");
    if (emptyMsg) emptyMsg.classList.toggle("show", visibleCount === 0);

    renderActiveTags();
    updateChipStates();
  }

  /* ===== チップのアクティブ状態を更新 ===== */
  function updateChipStates() {
    const groups = ["repeat", "time", "tag", "day"];
    groups.forEach((group) => {
      const chip = document.querySelector(`.sl-chip[data-group="${group}"]`);
      if (!chip) return;
      const hasFilter =
        group === "day" ? filters.day.size > 0 : filters[group] !== null;
      chip.classList.toggle("has-filter", hasFilter);

      const labelEl = chip.querySelector(".sl-chip-label");
      const labels = {
        repeat: "繰り返し",
        time: "時間帯",
        tag: "タグ",
        day: "曜日",
      };
      if (hasFilter) {
        if (group === "day") {
          labelEl.textContent = [...filters.day].join("・");
        } else {
          const valueLabel = { am: "午前", pm: "午後" };
          labelEl.textContent = valueLabel[filters[group]] || filters[group];
        }
      } else {
        labelEl.textContent = labels[group];
      }
    });
  }

  /* ===== アクティブフィルタータグを描画 ===== */
  function renderActiveTags() {
    const container = document.getElementById("slActiveFilters");
    if (!container) return;
    container.innerHTML = "";
    const labelMap = { am: "午前", pm: "午後" };

    const addTag = (group, value, label) => {
      const el = document.createElement("div");
      el.className = "sl-active-tag";
      el.innerHTML = `<span>${label}</span><button data-group="${group}" data-value="${value}">×</button>`;
      el.querySelector("button").addEventListener("click", () =>
        removeFilter(group, value),
      );
      container.appendChild(el);
    };

    if (filters.repeat) addTag("repeat", filters.repeat, filters.repeat);
    if (filters.time) addTag("time", filters.time, labelMap[filters.time]);
    if (filters.tag) addTag("tag", filters.tag, filters.tag);
    filters.day.forEach((d) => addTag("day", d, d));
  }

  /* ===== フィルター削除 ===== */
  function removeFilter(group, value) {
    if (group === "day") {
      filters.day.delete(value);
      const opt = document.querySelector(
        `.sl-chip-opt[data-group="day"][data-value="${value}"]`,
      );
      if (opt) opt.classList.remove("selected");
    } else {
      filters[group] = null;
      const opt = document.querySelector(
        `.sl-chip-opt[data-group="${group}"][data-value="${value}"]`,
      );
      if (opt) opt.classList.remove("selected");
    }
    applyFilter();
  }

  /* ===== ドロップダウン初期化 ===== */
  function initDropdowns() {
    // ★これを追加
    const filterChips = document.querySelector(".sl-filter-chips");
    if (filterChips) {
      filterChips.style.setProperty("overflow", "visible", "important");
    }

    // 全ドロップダウンを最初に非表示
    document.querySelectorAll(".sl-chip-dropdown").forEach((dd) => {
      dd.style.setProperty("display", "none", "important");
    });
    // ...以下はそのまま

    // チップボタンクリック
    document.querySelectorAll(".sl-chip").forEach((chip) => {
      chip.addEventListener("click", (e) => {
        e.stopPropagation();
        const wrap = chip.closest(".sl-chip-wrap");
        const isOpen = wrap.classList.contains("open");
        closeAllDropdowns();
        if (!isOpen) openDropdown(wrap);
      });
    });

    // 選択肢クリック
    document.querySelectorAll(".sl-chip-opt").forEach((opt) => {
      opt.addEventListener("click", (e) => {
        e.stopPropagation();
        const group = opt.dataset.group;
        const value = opt.dataset.value;

        if (group === "day") {
          if (filters.day.has(value)) {
            filters.day.delete(value);
            opt.classList.remove("selected");
          } else {
            filters.day.add(value);
            opt.classList.add("selected");
          }
          // 選択状態をスタイルに反映
          opt.style.setProperty(
            "background",
            opt.classList.contains("selected")
              ? "linear-gradient(135deg,#ffb380,#ff9f5a)"
              : "#fff",
            "important",
          );
          opt.style.setProperty(
            "color",
            opt.classList.contains("selected") ? "#fff" : "#555",
            "important",
          );
          opt.style.setProperty(
            "border-color",
            opt.classList.contains("selected") ? "#ff9f5a" : "#e0e0e0",
            "important",
          );
        } else {
          const isSame = filters[group] === value;
          document
            .querySelectorAll(`.sl-chip-opt[data-group="${group}"]`)
            .forEach((o) => {
              o.classList.remove("selected");
              o.style.setProperty("background", "transparent", "important");
              o.style.setProperty("color", "#555", "important");
            });
          if (isSame) {
            filters[group] = null;
          } else {
            filters[group] = value;
            opt.classList.add("selected");
            opt.style.setProperty("background", "#fff8f3", "important");
            opt.style.setProperty("color", "#ff9f5a", "important");
          }
          closeAllDropdowns();
        }
        applyFilter();
      });
    });

    // リセット
    const resetBtn = document.getElementById("slFilterReset");
    if (resetBtn) {
      resetBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        filters.repeat = null;
        filters.time = null;
        filters.tag = null;
        filters.day = new Set();
        document.querySelectorAll(".sl-chip-opt").forEach((o) => {
          o.classList.remove("selected");
          o.style.removeProperty("background");
          o.style.removeProperty("color");
          o.style.removeProperty("border-color");
        });
        closeAllDropdowns();
        applyFilter();
      });
    }

    // 外側クリックで閉じる
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".sl-chip-wrap")) {
        closeAllDropdowns();
      }
    });
  }

  /* ===== モーダル ===== */
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
    fetch(`/schedule/delete/${pendingId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    })
      .then((res) => {
        if (!res.ok) throw new Error();
        location.reload();
      })
      .catch(() => {
        alert("削除に失敗しました");
      });
    closeModal();
  };

  /* ===== メモ開閉 ===== */
  window.slToggleComment = function (btn) {
    const content = btn.nextElementSibling;
    const hidden = content.classList.contains("hidden");
    content.classList.toggle("hidden", !hidden);
    btn.classList.toggle("collapsed", !hidden);
  };

  /* ===== 初期化 ===== */
  function slInit() {
    const page = document.querySelector(".sl-page");
    if (!page) return;

    page.removeEventListener("click", onPageClick);
    page.addEventListener("click", onPageClick);

    initDropdowns();
    applyFilter();

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

    document
      .querySelectorAll(".sl-task-card, .sl-weekday.active, .sl-delete-btn")
      .forEach((el) => {
        el.addEventListener("touchstart", () => (el.style.opacity = "0.75"));
        el.addEventListener("touchend", () => (el.style.opacity = "1"));
        el.addEventListener("touchcancel", () => (el.style.opacity = "1"));
      });
  }

  function onPageClick(e) {
    const btn = e.target.closest(".sl-delete-btn");
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    pendingId = btn.dataset.taskId;
    openModal();
  }

  document.addEventListener("DOMContentLoaded", slInit);
  document.addEventListener("turbo:load", slInit);
})();
