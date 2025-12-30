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
