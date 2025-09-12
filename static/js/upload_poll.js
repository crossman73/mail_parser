// Simple polling helper for upload job status
function pollJobStatus(jobId, onUpdate, interval = 1000) {
  let timer = null;
  async function check() {
    try {
      const res = await fetch(`/api/upload/job/${jobId}`);
      if (!res.ok) {
        onUpdate({ status: "error", code: res.status });
        clearInterval(timer);
        return;
      }
      const j = await res.json();
      onUpdate(j);
      if (j.status === "completed" || j.status === "failed") {
        clearInterval(timer);
      }
    } catch (e) {
      onUpdate({ status: "error", message: e.toString() });
      clearInterval(timer);
    }
  }
  timer = setInterval(check, interval);
  check();
  return () => clearInterval(timer);
}

export { pollJobStatus };
