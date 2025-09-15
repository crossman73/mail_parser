// Shared client-side helpers for async form submission and fetch with progress
export function fetchWithTimeout(url, options = {}, timeout = 120000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout")), timeout);
    fetch(url, options)
      .then((res) => {
        clearTimeout(timer);
        resolve(res);
      })
      .catch((err) => {
        clearTimeout(timer);
        reject(err);
      });
  });
}

export function submitFormAsync(form, { onProgress } = {}) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData(form);

    xhr.open(
      form.method || "POST",
      form.action || window.location.pathname,
      true
    );
    xhr.withCredentials = true;

    if (onProgress && xhr.upload) {
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          try {
            onProgress(percent);
          } catch (_) {}
        }
      });
    }

    xhr.addEventListener("load", () => {
      resolve(xhr);
    });

    xhr.addEventListener("error", () => reject(new Error("network error")));
    xhr.addEventListener("abort", () => reject(new Error("aborted")));

    xhr.send(formData);
  });
}

// Small utility: simple element selector
export function $id(id) {
  return document.getElementById(id);
}
// Common client utilities for synchronous and asynchronous operations

// Perform a fetch with timeout and optional JSON body
export async function fetchWithTimeout(url, options = {}, timeout = 30000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    const resp = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(id);
    return resp;
  } catch (err) {
    clearTimeout(id);
    throw err;
  }
}

// Helper to submit a form via fetch (async) with progress via XHR fallback
export function submitFormAsync(formElement, { onProgress = null } = {}) {
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
