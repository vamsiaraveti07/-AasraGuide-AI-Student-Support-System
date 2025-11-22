window.initPomodoro = function () {
  // DOM
  const workInput = document.getElementById("work-min");
  const breakInput = document.getElementById("break-min");
  const longBreakInput = document.getElementById("long-break-min");

  const applyBtn = document.getElementById("apply-config");
  const startBtn = document.getElementById("pomodoro-start-btn");
  const resetBtn = document.getElementById("pomodoro-reset-btn");
  const statusEl = document.getElementById("pomodoro-status");
  const timerDisplay = document.getElementById("pomodoro-timer-display");

  const notesTextarea = document.getElementById("session-notes");
  const clearNoteBtn = document.getElementById("save-session-note");

  const themePicker = document.getElementById("theme-picker");
  const soundToggle = document.getElementById("sound-toggle");
  const notifToggle = document.getElementById("notif-toggle");

  const sessionList = document.getElementById("pomodoro-session-list");

  // State
  let workLen = parseInt(workInput.value, 10) || 25;
  let breakLen = parseInt(breakInput.value, 10) || 5;
  let longBreakLen = parseInt(longBreakInput.value, 10) || 15;

  let duration = workLen * 60;
  let timer = duration;
  let interval = null;
  let startTime = null;

  const FULL_CIRCLE = 597; // 2πr (r=95)

  let soundOn = localStorage.getItem("pomodoroSound") !== "false";
  let notifOn = localStorage.getItem("pomodoroNotif") !== "false";
  soundToggle.checked = soundOn;
  notifToggle.checked = notifOn;

  let dailyChart = null;
  let weeklyChart = null;

  // Helpers
  function updateDisplay() {
    const m = String(Math.floor(timer / 60)).padStart(2, "0");
    const s = String(timer % 60).padStart(2, "0");
    timerDisplay.textContent = `${m}:${s}`;
    updateCircle();
  }

  function updateCircle() {
    const circle = document.getElementById("progress-ring");
    if (!circle) return;
    const ratio = timer / duration;
    circle.style.strokeDashoffset = FULL_CIRCLE - FULL_CIRCLE * ratio;
  }

  function playSound() {
    if (!soundOn) return;
    const audio = new Audio("/static/ding.mp3"); // place a file or change path
    audio.play().catch(() => {});
  }

  function showNotification(msg) {
    if (!notifOn || !("Notification" in window)) return;
    if (Notification.permission === "granted") {
      new Notification(msg);
    } else if (Notification.permission !== "denied") {
      Notification.requestPermission().then((perm) => {
        if (perm === "granted") new Notification(msg);
      });
    }
  }

  function launchConfetti() {
    if (!window.confetti) return;
    const duration = 1500;
    const end = Date.now() + duration;

    (function frame() {
      confetti({ particleCount: 6, angle: 60, spread: 55, origin: { x: 0 } });
      confetti({ particleCount: 6, angle: 120, spread: 55, origin: { x: 1 } });
      if (Date.now() < end) requestAnimationFrame(frame);
    })();
  }

  function logSession(success) {
    const body = new URLSearchParams({
      start: startTime || new Date().toLocaleTimeString(),
      end: new Date().toLocaleTimeString(),
      success: success ? "true" : "false",
      note: notesTextarea.value || "",
      work_minutes: workLen,
    });

    return fetch("/pomodoro/log", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    }).then((r) => r.json());
  }

  function finishSession(success) {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }

    if (success) {
      statusEl.textContent = "Nice! Session complete 🎉";
      playSound();
      showNotification("Pomodoro session complete!");
      launchConfetti();
    } else {
      statusEl.textContent = "Session cancelled.";
    }

    startBtn.disabled = false;
    resetBtn.disabled = true;

    logSession(success).then(loadHistoryAndStats);
  }

  // History + stats + charts
  function loadHistoryAndStats() {
    fetch("/pomodoro/history")
      .then((r) => r.json())
      .then((list) => {
        const totalSessions = list.length;
        let focusMinutes = 0;
        let currentStreak = 0;
        let bestStreak = 0;

        list.forEach((s) => {
          if (s.success) {
            focusMinutes += s.work_minutes || workLen;
            currentStreak++;
            if (currentStreak > bestStreak) bestStreak = currentStreak;
          } else {
            currentStreak = 0;
          }
        });

        document.getElementById("stats-focus-min").textContent =
          focusMinutes + " min";
        document.getElementById("stats-sessions").textContent =
          String(totalSessions);
        document.getElementById("stats-streak").textContent =
          String(bestStreak);

        // history list
        sessionList.innerHTML = list
          .slice()
          .reverse()
          .map((s) => {
            const mark = s.success ? "✔️" : "✖️";
            const note = s.note ? `<br><em>${s.note}</em>` : "";
            return `<li>${s.date || ""} ${s.start} - ${s.end} ${mark}${note}</li>`;
          })
          .join("");

        loadCharts(list);
      });
  }

  function loadCharts(list) {
    const daily = {};
    const weekly = [0, 0, 0, 0, 0, 0, 0]; // Mon-Sun

    list.forEach((s) => {
      if (!s.success) return;
      const mins = s.work_minutes || workLen;
      const dateKey = s.date || "Unknown";
      daily[dateKey] = (daily[dateKey] || 0) + mins;

      const w = typeof s.weekday === "number" ? s.weekday : 0;
      weekly[w] += mins;
    });

    const dailyLabels = Object.keys(daily);
    const dailyValues = Object.values(daily);

    const dailyCtx = document.getElementById("dailyChart").getContext("2d");
    const weeklyCtx = document.getElementById("weeklyChart").getContext("2d");

    if (dailyChart) dailyChart.destroy();
    if (weeklyChart) weeklyChart.destroy();

    dailyChart = new Chart(dailyCtx, {
      type: "bar",
      data: {
        labels: dailyLabels,
        datasets: [
          {
            label: "Focus minutes",
            data: dailyValues,
          },
        ],
      },
      options: {
        responsive: true,
        scales: { y: { beginAtZero: true } },
      },
    });

    weeklyChart = new Chart(weeklyCtx, {
      type: "line",
      data: {
        labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        datasets: [
          {
            label: "Weekly focus (min)",
            data: weekly,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        scales: { y: { beginAtZero: true } },
      },
    });
  }

  // Events
  applyBtn.onclick = function () {
    workLen = parseInt(workInput.value, 10) || 25;
    breakLen = parseInt(breakInput.value, 10) || 5;
    longBreakLen = parseInt(longBreakInput.value, 10) || 15;
    duration = workLen * 60;
    timer = duration;
    updateDisplay();
  };

  startBtn.onclick = function () {
    if (interval) return;
    workLen = parseInt(workInput.value, 10) || 25;
    duration = workLen * 60;
    timer = duration;
    updateDisplay();

    startTime = new Date().toLocaleTimeString();
    statusEl.textContent = "";
    interval = setInterval(() => {
      if (timer > 0) {
        timer--;
        updateDisplay();
      } else {
        finishSession(true);
      }
    }, 1000);

    startBtn.disabled = true;
    resetBtn.disabled = false;
  };

  resetBtn.onclick = function () {
    if (interval) {
      finishSession(false);
    } else {
      timer = duration;
      updateDisplay();
      statusEl.textContent = "";
      startBtn.disabled = false;
      resetBtn.disabled = true;
    }
  };

  clearNoteBtn.onclick = () => {
    notesTextarea.value = "";
  };

  // Theme
  const storedTheme = localStorage.getItem("pomodoroTheme") || "dark";
  themePicker.value = storedTheme;
  applyTheme(storedTheme);

  themePicker.onchange = function () {
    const t = this.value;
    applyTheme(t);
    localStorage.setItem("pomodoroTheme", t);
  };

  function applyTheme(theme) {
    document.body.classList.remove("theme-dark", "theme-light", "theme-mint");
    document.body.classList.add("theme-" + theme);
  }

  // Toggles
  soundToggle.onchange = function () {
    soundOn = this.checked;
    localStorage.setItem("pomodoroSound", soundOn ? "true" : "false");
  };
  notifToggle.onchange = function () {
    notifOn = this.checked;
    localStorage.setItem("pomodoroNotif", notifOn ? "true" : "false");
  };

  // Init
  timer = duration;
  updateDisplay();
  loadHistoryAndStats();
};
