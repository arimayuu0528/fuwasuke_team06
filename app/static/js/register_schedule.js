function initSchedPage() {
  // 1. draft を消す
  schedClearDraft();

  // 2. フォーム初期化
  function schedInitializeForm() {
    schedUpdateDayOfWeekInput();

    // ↓ 修正：タグのセクションだけを対象にする
    const tagSection = document
      .getElementById("schedTag")
      .closest(".sched-form-section");
    const activeTag = tagSection.querySelector(
      ".sched-category-btn.sched-category-active",
    );
    if (activeTag) {
      document.getElementById("schedTag").value = activeTag.textContent.trim();
    }

    // 繰り返しタイプも同様に修正
    const repeatSection = document
      .getElementById("schedRepeatType")
      .closest(".sched-form-section");
    const activeRepeat = repeatSection.querySelector(
      ".sched-category-btn.sched-category-active",
    );
    if (activeRepeat) {
      document.getElementById("schedRepeatType").value =
        activeRepeat.textContent.trim();
    }

    const taskNameInput = document.querySelector(
      '.sched-form-input[name="title"]',
    );
    if (taskNameInput && !taskNameInput.value) {
      setTimeout(() => {
        taskNameInput.focus();
      }, 300);
    }
  }

  // 3. 各種セットアップ
  schedSetupFormValidation();
  schedSetupTimeInputs();
  schedSetupTagSelection();
  schedSetupRepeatTypeSelection();
  schedSetupWeekdaySelection();
  schedAddRippleEffects();
  schedSetupFormSubmission();
  schedCalculateDuration();
  schedSetupCharacterCounter();
  schedSetupAutoSave();
}

// DOM がすでに読み込まれている場合でも実行
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initSchedPage);
} else {
  initSchedPage();
}

// Initialize form with default values
function schedInitializeForm() {
  // Set initial day of week value
  schedUpdateDayOfWeekInput();

  // Set initial tag value
  const activeTag = document.querySelector(
    ".sched-category-btn.sched-category-active",
  );
  if (activeTag) {
    document.getElementById("schedTag").value = activeTag.textContent.trim();
  }

  // Auto-focus on task name input
  const taskNameInput = document.querySelector(
    '.sched-form-input[name="title"]',
  );
  if (taskNameInput && !taskNameInput.value) {
    setTimeout(() => {
      taskNameInput.focus();
    }, 300);
  }
}

// Update day of week hidden input
function schedUpdateDayOfWeekInput() {
  const actives = document.querySelectorAll(
    ".sched-weekday-btn.sched-weekday-active",
  );
  const days = Array.from(actives)
    .map((b) => b.dataset.day)
    .join("");
  document.getElementById("schedDayOfWeek").value = days;

  console.log("Selected days:", days);
}

// Select tag
function schedSelectTag(btn) {
  // Remove active class from all tag buttons in the same section
  const tagSection = btn.closest(".sched-form-section");
  const tagBtns = tagSection.querySelectorAll(".sched-category-btn");
  tagBtns.forEach((b) => b.classList.remove("sched-category-active"));

  // Add active class to clicked button
  btn.classList.add("sched-category-active");

  // Update hidden input
  document.getElementById("schedTag").value = btn.textContent.trim();

  // Add haptic feedback if available
  if (navigator.vibrate) {
    navigator.vibrate(10);
  }

  // Add ripple effect
  schedAddRipple(btn, event);
}

// Select repeat type
function schedSelectRepeatType(btn) {
  // Remove active class from all repeat type buttons in the same section
  const repeatSection = btn.closest(".sched-form-section");
  const repeatBtns = repeatSection.querySelectorAll(".sched-category-btn");
  repeatBtns.forEach((b) => b.classList.remove("sched-category-active"));

  // Add active class to clicked button
  btn.classList.add("sched-category-active");

  // Update hidden input
  document.getElementById("schedRepeatType").value = btn.textContent.trim();

  // Add haptic feedback if available
  if (navigator.vibrate) {
    navigator.vibrate(10);
  }

  // Add ripple effect
  schedAddRipple(btn, event);
}

// Calculate duration in minutes
function schedCalculateDuration() {
  const startTime = document.querySelector('input[name="start_time"]');
  const endTime = document.querySelector('input[name="end_time"]');

  if (startTime && endTime) {
    const calculateDurationMin = () => {
      if (startTime.value && endTime.value) {
        const start = schedTimeToMinutes(startTime.value);
        const end = schedTimeToMinutes(endTime.value);

        if (end > start) {
          const duration = end - start;
          console.log("Duration:", duration, "minutes");
          // duration_minはサーバー側で計算するため、ここでは表示のみ
        }
      }
    };

    startTime.addEventListener("change", calculateDurationMin);
    endTime.addEventListener("change", calculateDurationMin);
  }
}

// Setup form validation
function schedSetupFormValidation() {
  const form = document.getElementById("schedTaskForm");
  const inputs = form.querySelectorAll("input[required], textarea[required]");

  inputs.forEach((input) => {
    input.addEventListener("blur", function () {
      schedValidateField(this);
    });

    input.addEventListener("input", function () {
      if (this.classList.contains("sched-error")) {
        schedValidateField(this);
      }
    });
  });
}

// Validate individual field
function schedValidateField(field) {
  if (!field.value.trim() && field.hasAttribute("required")) {
    field.classList.add("sched-error");
    return false;
  } else {
    field.classList.remove("sched-error");
    return true;
  }
}

// Setup time inputs
function schedSetupTimeInputs() {
  const timeInputs = document.querySelectorAll(".sched-time-input");

  timeInputs.forEach((input) => {
    // Format time on change
    input.addEventListener("change", function () {
      schedFormatTimeInput(this);
    });

    // Add focus animation
    input.addEventListener("focus", function () {
      this.parentElement.style.transform = "scale(1.02)";
      this.parentElement.style.transition = "transform 0.2s";
    });

    input.addEventListener("blur", function () {
      this.parentElement.style.transform = "scale(1)";
    });
  });

  // Validate end time is after start time
  const startTime = document.querySelector('input[name="start_time"]');
  const endTime = document.querySelector('input[name="end_time"]');

  if (startTime && endTime) {
    const validateTimes = () => {
      if (startTime.value && endTime.value) {
        const start = schedTimeToMinutes(startTime.value);
        const end = schedTimeToMinutes(endTime.value);

        if (end <= start) {
          endTime.setCustomValidity("終了時間は開始時間より後にしてください");
          schedShowToast("終了時間は開始時間より後にしてください", "warning");
        } else {
          endTime.setCustomValidity("");
        }
      }
    };

    startTime.addEventListener("change", validateTimes);
    endTime.addEventListener("change", validateTimes);
  }
}

// Convert time to minutes for comparison
function schedTimeToMinutes(time) {
  const [hours, minutes] = time.split(":").map(Number);
  return hours * 60 + minutes;
}

// Format time input
function schedFormatTimeInput(input) {
  let value = input.value;
  if (value) {
    // Ensure proper format
    const [hours, minutes] = value.split(":");
    const formattedHours = hours.padStart(2, "0");
    const formattedMinutes = minutes.padStart(2, "0");
    input.value = `${formattedHours}:${formattedMinutes}`;
  }
}

// Setup tag selection
function schedSetupTagSelection() {
  const tagBtns = document.querySelectorAll(".sched-category-btn");

  tagBtns.forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
    });
  });
}

// Setup repeat type selection
function schedSetupRepeatTypeSelection() {
  const repeatBtns = document.querySelectorAll(".sched-category-btn");

  repeatBtns.forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
    });
  });
}

// Setup weekday selection
function schedSetupWeekdaySelection() {
  const weekdayBtns = document.querySelectorAll(".sched-weekday-btn");

  weekdayBtns.forEach((btn) => {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();

      // Toggle処理
      this.classList.toggle("sched-weekday-active");

      // Add haptic feedback if available
      if (navigator.vibrate) {
        navigator.vibrate(10);
      }

      // Update hidden input
      schedUpdateDayOfWeekInput();
    });
  });
}

// Add ripple effects to buttons
function schedAddRippleEffects() {
  const buttons = document.querySelectorAll(
    ".sched-weekday-btn, .sched-category-btn, .sched-submit-btn",
  );

  buttons.forEach((button) => {
    button.addEventListener("click", function (e) {
      schedAddRipple(this, e);
    });
  });
}

// Add ripple effect to element
function schedAddRipple(element, event) {
  const ripple = document.createElement("span");
  ripple.classList.add("sched-ripple");

  const rect = element.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  const x = event.clientX - rect.left - size / 2;
  const y = event.clientY - rect.top - size / 2;

  ripple.style.width = ripple.style.height = size + "px";
  ripple.style.left = x + "px";
  ripple.style.top = y + "px";

  // Remove existing ripples
  const existingRipples = element.querySelectorAll(".sched-ripple");
  existingRipples.forEach((r) => r.remove());

  element.appendChild(ripple);

  setTimeout(() => ripple.remove(), 600);
}

// Setup form submission
function schedSetupFormSubmission() {
  const form = document.getElementById("schedTaskForm");
  const submitBtn = document.querySelector(".sched-submit-btn");

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    // Validate form
    if (!schedValidateForm()) {
      schedShowToast("入力内容を確認してください", "error");
      return;
    }

    // Show loading state
    submitBtn.classList.add("sched-loading");
    submitBtn.disabled = true;

    // Haptic feedback
    if (navigator.vibrate) {
      navigator.vibrate([10, 50, 10]);
    }

    // Simulate form submission (remove this in production)
    setTimeout(() => {
      // Submit the form
      form.submit();

      // Or handle with AJAX:
      // schedSubmitFormAjax(form);
    }, 500);
  });
}

// Validate entire form
function schedValidateForm() {
  const form = document.getElementById("schedTaskForm");
  let isValid = true;

  // Check task name
  const taskName = form.querySelector('input[name="title"]');
  if (!taskName.value.trim()) {
    isValid = false;
    taskName.classList.add("sched-error");
  }

  // Check times
  const startTime = form.querySelector('input[name="start_time"]');
  const endTime = form.querySelector('input[name="end_time"]');
  if (!startTime.value || !endTime.value) {
    isValid = false;
  }

  // Check at least one weekday selected
  const dayOfWeek = document.getElementById("schedDayOfWeek").value;
  if (!dayOfWeek) {
    schedShowToast("繰り返す曜日を選択してください", "warning");
    isValid = false;
  }

  // Check tag selected
  const tag = document.getElementById("schedTag").value;
  if (!tag) {
    schedShowToast("タグを選択してください", "warning");
    isValid = false;
  }

  // Check repeat type selected
  const repeatType = document.getElementById("schedRepeatType").value;
  if (!repeatType) {
    schedShowToast("繰り返しタイプを選択してください", "warning");
    isValid = false;
  }

  return isValid;
}

// Submit form via AJAX (optional)
function schedSubmitFormAjax(form) {
  const formData = new FormData(form);

  fetch(form.action, {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        schedShowToast("固定タスクを登録しました", "success");
        setTimeout(() => {
          window.location.href = data.redirect || "/schedule/list";
        }, 1000);
      } else {
        schedShowToast(data.message || "エラーが発生しました", "error");
        document
          .querySelector(".sched-submit-btn")
          .classList.remove("sched-loading");
        document.querySelector(".sched-submit-btn").disabled = false;
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      schedShowToast("エラーが発生しました", "error");
      document
        .querySelector(".sched-submit-btn")
        .classList.remove("sched-loading");
      document.querySelector(".sched-submit-btn").disabled = false;
    });
}

// Show toast notification
function schedShowToast(message, type = "info") {
  // Remove existing toasts
  const existingToasts = document.querySelectorAll(".sched-toast");
  existingToasts.forEach((toast) => toast.remove());

  const toast = document.createElement("div");
  toast.className = `sched-toast sched-toast-${type}`;
  toast.textContent = message;

  const styles = {
    position: "fixed",
    top: "80px",
    left: "50%",
    transform: "translateX(-50%)",
    padding: "12px 24px",
    borderRadius: "24px",
    color: "#fff",
    fontSize: "14px",
    fontWeight: "500",
    zIndex: "10000",
    animation: "schedSlideDown 0.3s ease-out",
    boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
  };

  Object.assign(toast.style, styles);

  // Set background color based on type
  const colors = {
    success: "#4CAF50",
    error: "#ff6b6b",
    warning: "#FF9F5A",
    info: "#2196F3",
  };
  toast.style.background = colors[type] || colors.info;

  document.body.appendChild(toast);

  // Add animation
  const keyframes = `
    @keyframes schedSlideDown {
      from {
        opacity: 0;
        transform: translateX(-50%) translateY(-20px);
      }
      to {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
      }
    }
  `;

  const styleSheet = document.createElement("style");
  styleSheet.textContent = keyframes;
  document.head.appendChild(styleSheet);

  // Auto remove after 3 seconds
  setTimeout(() => {
    toast.style.animation = "schedSlideUp 0.3s ease-out";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Auto-save draft (optional feature)
function schedSetupAutoSave() {
  const form = document.getElementById("schedTaskForm");
  const inputs = form.querySelectorAll("input, textarea");

  inputs.forEach((input) => {
    input.addEventListener(
      "input",
      schedDebounce(function () {
        schedSaveDraft();
      }, 1000),
    );
  });
}

// Save form data to localStorage
function schedSaveDraft() {
  const form = document.getElementById("schedTaskForm");
  const formData = new FormData(form);
  const data = {};

  for (let [key, value] of formData.entries()) {
    data[key] = value;
  }

  data.dayOfWeek = document.getElementById("schedDayOfWeek").value;
  data.tag = document.getElementById("schedTag").value;
  data.repeatType = document.getElementById("schedRepeatType").value;

  localStorage.setItem("schedTaskDraft", JSON.stringify(data));
  console.log("Draft saved");
}

// Load draft from localStorage
function schedLoadDraft() {
  const draft = localStorage.getItem("schedTaskDraft");
  if (draft) {
    const data = JSON.parse(draft);

    // Fill form with draft data
    Object.keys(data).forEach((key) => {
      const input = document.querySelector(`[name="${key}"]`);
      if (input) {
        input.value = data[key];
      }
    });

    // Restore weekday selections
    if (data.dayOfWeek) {
      const days = data.dayOfWeek.split("");
      const weekdayBtns = document.querySelectorAll(".sched-weekday-btn");
      weekdayBtns.forEach((btn) => {
        if (days.includes(btn.dataset.day)) {
          btn.classList.add("sched-weekday-active");
        } else {
          btn.classList.remove("sched-weekday-active");
        }
      });
    }

    // Restore tag selection
    if (data.tag) {
      const tagBtns = document.querySelectorAll(".sched-category-btn");
      tagBtns.forEach((btn) => {
        if (btn.textContent.trim() === data.tag) {
          btn.classList.add("sched-category-active");
        } else {
          btn.classList.remove("sched-category-active");
        }
      });
    }

    // Restore repeat type selection
    if (data.repeatType) {
      const repeatBtns = document.querySelectorAll(".sched-category-btn");
      repeatBtns.forEach((btn) => {
        if (btn.textContent.trim() === data.repeatType) {
          btn.classList.add("sched-category-active");
        }
      });
    }
  }
}

// Debounce function
function schedDebounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Clear draft after successful submission
function schedClearDraft() {
  localStorage.removeItem("schedTaskDraft");
}

// Character counter for memo textarea (optional)
function schedSetupCharacterCounter() {
  const textarea = document.querySelector(".sched-memo-textarea");
  if (textarea) {
    const counter = document.createElement("div");
    counter.className = "sched-character-counter";
    counter.style.cssText =
      "text-align: right; color: #999; font-size: 12px; margin-top: 4px;";

    textarea.parentElement.appendChild(counter);

    const updateCounter = () => {
      const length = textarea.value.length;
      const maxLength = textarea.getAttribute("maxlength") || 500;
      counter.textContent = `${length} / ${maxLength}`;

      if (length > maxLength * 0.9) {
        counter.style.color = "#ff6b6b";
      } else {
        counter.style.color = "#999";
      }
    };

    textarea.addEventListener("input", updateCounter);
    updateCounter();
  }
}
