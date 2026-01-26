// Shared client-side helpers for async form submission and fetch with progress

// Perform a fetch with timeout and optional JSON body
function fetchWithTimeout(url, options = {}, timeout = 30000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  return fetch(url, { ...options, signal: controller.signal })
    .then((resp) => {
      clearTimeout(id);
      return resp;
    })
    .catch((err) => {
      clearTimeout(id);
      throw err;
    });
}

// Helper to submit a form via fetch (async) with progress via XHR fallback
function submitFormAsync(formElement, { onProgress = null } = {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const fd = new FormData(formElement);

    xhr.open(
      formElement.method || "POST",
      formElement.action || window.location.href
    );

    xhr.upload.onprogress = function (e) {
      if (onProgress && e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr);
      } else {
        reject(new Error(`HTTP ${xhr.status}`));
      }
    };

    xhr.onerror = function () {
      reject(new Error("Network error"));
    };

    xhr.send(fd);
  });
}

// Small utility: simple element selector
function $id(id) {
  return document.getElementById(id);
}

/**
 * 날짜/시간 포맷 함수 (프로젝트 표준)
 * - 오늘이면 시간만 표시 (HH:mm:ss)
 * - 다른 날이면 날짜만 표시 (YYYY-MM-DD)
 * @param {string|Date} dateStr - 날짜 문자열 또는 Date 객체
 * @returns {string} 포맷된 날짜/시간 문자열
 */
function formatDateTime(dateStr) {
  if (!dateStr) return '-';

  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '-';

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());

  // 오늘이면 시간만 표시
  if (dateOnly.getTime() === today.getTime()) {
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  } else {
    // 다른 날이면 날짜만 표시
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).replace(/\. /g, '-').replace('.', '');
  }
}

/**
 * 전체 날짜/시간 포맷 함수
 * - 오늘: 시간만 표시 (HH:mm)
 * - 오늘이 아닌 경우: 날짜 표시 (YYYY/MM/DD)
 * @param {string|Date} dateStr - 날짜 문자열 또는 Date 객체
 * @returns {string} 포맷된 날짜/시간 문자열
 */
function formatDateTimeFull(dateStr) {
  if (!dateStr) return '-';

  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '-';

  const now = new Date();
  const isToday = date.getFullYear() === now.getFullYear() &&
                  date.getMonth() === now.getMonth() &&
                  date.getDate() === now.getDate();

  if (isToday) {
    // 오늘: 시간만 표시
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    return `${hour}:${minute}`;
  } else {
    // 오늘이 아닌 경우: 날짜만 표시
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}/${month}/${day}`;
  }
}

/**
 * 전체 날짜/시간 (긴 형식) — 항상 YYYY-MM-DD HH:mm:ss 반환
 * @param {string|Date} dateStr
 * @returns {string}
 */
function formatDateTimeLong(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '-';

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hour = String(date.getHours()).padStart(2, '0');
  const minute = String(date.getMinutes()).padStart(2, '0');
  const second = String(date.getSeconds()).padStart(2, '0');

  return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

// Dark mode and mobile menu initialization
document.addEventListener("DOMContentLoaded", function () {
  // Mobile menu toggle
  const mobileMenuToggle = document.getElementById("mobileMenuToggle");
  const navLinks = document.getElementById("navLinks");

  if (mobileMenuToggle && navLinks) {
    mobileMenuToggle.addEventListener("click", function () {
      this.classList.toggle("active");
      navLinks.classList.toggle("active");
    });
  }

  // Mobile dropdown handling
  const evidenceDropdown = document.getElementById("evidenceDropdown");
  if (evidenceDropdown) {
    const dropdownToggle = evidenceDropdown.querySelector(".dropdown-toggle");
    if (dropdownToggle) {
      dropdownToggle.addEventListener("click", function (e) {
        if (window.innerWidth <= 992) {
          e.preventDefault();
          evidenceDropdown.classList.toggle("active");
        }
      });
    }
  }

  // Responsive handling
  window.addEventListener("resize", function () {
    if (window.innerWidth > 992) {
      if (navLinks) navLinks.classList.remove("active");
      if (mobileMenuToggle) mobileMenuToggle.classList.remove("active");
      if (evidenceDropdown) evidenceDropdown.classList.remove("active");
    }
  });

  // Dark mode toggle
  const themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    // Initialize theme from localStorage
    const currentTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", currentTheme);
    updateThemeIcon(currentTheme);

    // Theme toggle event
    themeToggle.addEventListener("click", function () {
      const theme = document.documentElement.getAttribute("data-theme");
      const newTheme = theme === "dark" ? "light" : "dark";

      document.documentElement.setAttribute("data-theme", newTheme);
      localStorage.setItem("theme", newTheme);
      updateThemeIcon(newTheme);
    });

    function updateThemeIcon(theme) {
      const icon = themeToggle.querySelector("i");
      if (icon) {
        if (theme === "dark") {
          icon.className = "fas fa-sun";
        } else {
          icon.className = "fas fa-moon";
        }
      }
    }
  }
});
