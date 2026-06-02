// ─────────────────────────────────────────────
//  LinkForge — Frontend JS
// ─────────────────────────────────────────────

const API = "";  // Same origin

// ── Tab switching ──────────────────────────────────────────
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    if (btn.dataset.tab === "history") loadHistory();
  });
});

// ── Helpers ───────────────────────────────────────────────
function show(el, html) { el.innerHTML = html; el.classList.remove("hidden"); }
function hide(el) { el.classList.add("hidden"); }
function showError(el, msg) { show(el, msg); }
function fmtNum(n) { return n != null ? n.toLocaleString() : "—"; }
function fmtDuration(s) {
  if (!s) return "—";
  const m = Math.floor(s / 60), sec = s % 60;
  return `${m}:${String(sec).padStart(2, "0")}`;
}

// ── URL Shortener ──────────────────────────────────────────

const shortenBtn = document.getElementById("shorten-btn");
const urlInput = document.getElementById("url-input");
const aliasInput = document.getElementById("alias-input");
const resultBox = document.getElementById("shorten-result");
const errorBox = document.getElementById("shorten-error");

shortenBtn.addEventListener("click", async () => {
  const url = urlInput.value.trim();
  if (!url) { showError(errorBox, "Please enter a URL."); return; }

  hide(resultBox); hide(errorBox);
  shortenBtn.disabled = true;
  shortenBtn.querySelector("span").textContent = "Forging…";

  try {
    const body = { original_url: url };
    const alias = aliasInput.value.trim();
    if (alias) body.custom_alias = alias;

    const res = await fetch(`${API}/api/urls/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (!res.ok) {
      showError(errorBox, data.detail || "Something went wrong.");
      return;
    }

    show(resultBox, `
      <div class="result-short">
        <a class="short-url" href="${data.short_url}" target="_blank">${data.short_url}</a>
        <button class="copy-btn" onclick="copyURL(this, '${data.short_url}')">Copy</button>
      </div>
      <div class="result-original">→ ${data.original_url}</div>
    `);
    urlInput.value = ""; aliasInput.value = "";
    loadRecentURLs();
  } catch (e) {
    showError(errorBox, "Network error. Is the server running?");
  } finally {
    shortenBtn.disabled = false;
    shortenBtn.querySelector("span").textContent = "Forge Link";
  }
});

function copyURL(btn, url) {
  navigator.clipboard.writeText(url).then(() => {
    btn.textContent = "Copied!";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = "Copy"; btn.classList.remove("copied"); }, 2000);
  });
}

// Enter key support
urlInput.addEventListener("keydown", e => { if (e.key === "Enter") shortenBtn.click(); });

// ── Recent URLs ────────────────────────────────────────────

async function loadRecentURLs() {
  try {
    const res = await fetch(`${API}/api/urls/?limit=5`);
    const data = await res.json();
    renderURLList("urls-list", data);
  } catch {}
}

async function loadHistory() {
  try {
    const res = await fetch(`${API}/api/urls/?limit=50`);
    const data = await res.json();
    renderURLList("history-list", data);
  } catch {
    document.getElementById("history-list").innerHTML =
      '<div class="empty-state">Could not load history.</div>';
  }
}

function renderURLList(containerId, urls) {
  const container = document.getElementById(containerId);
  if (!urls.length) {
    container.innerHTML = '<div class="empty-state">No links yet.</div>';
    return;
  }
  container.innerHTML = urls.map(u => `
    <div class="url-item">
      <a class="short" href="${u.short_url}" target="_blank">${u.short_url.replace(/https?:\/\//, "")}</a>
      <span class="original">${u.original_url}</span>
      <span class="clicks">${fmtNum(u.click_count)} clicks</span>
    </div>
  `).join("");
}

loadRecentURLs();

// ── YouTube Downloader ─────────────────────────────────────

let currentYTUrl = "";
let selectedFormat = "mp4";
let selectedQuality = "best";

// Toggle groups
document.querySelectorAll(".toggle-group").forEach(group => {
  group.addEventListener("click", e => {
    const btn = e.target.closest(".toggle");
    if (!btn) return;
    group.querySelectorAll(".toggle").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    if (group.closest("#tab-youtube")) {
      if (group === document.querySelector("#fmt-mp4").closest(".toggle-group")) {
        selectedFormat = btn.dataset.val;
        const qg = document.getElementById("quality-group");
        selectedFormat === "mp3" ? qg.style.opacity = "0.4" : qg.style.opacity = "1";
      } else {
        selectedQuality = btn.dataset.val;
      }
    }
  });
});

const ytInfoBtn = document.getElementById("yt-info-btn");
const ytUrlInput = document.getElementById("yt-url-input");
const ytInfoResult = document.getElementById("yt-info-result");
const ytError = document.getElementById("yt-error");
const ytDownloadCard = document.getElementById("yt-download-card");
const ytDownloadBtn = document.getElementById("yt-download-btn");
const dlStatus = document.getElementById("dl-status");

ytInfoBtn.addEventListener("click", async () => {
  const url = ytUrlInput.value.trim();
  if (!url) { showError(ytError, "Please enter a YouTube URL."); return; }

  hide(ytInfoResult); hide(ytError); hide(ytDownloadCard);
  ytInfoBtn.disabled = true;
  ytInfoBtn.querySelector("span").textContent = "Fetching…";

  try {
    const res = await fetch(`${API}/api/youtube/info?url=${encodeURIComponent(url)}`);
    const data = await res.json();

    if (!res.ok) {
      showError(ytError, data.detail || "Could not fetch video info.");
      return;
    }

    currentYTUrl = url;
    show(ytInfoResult, `
      ${data.thumbnail ? `<img class="yt-thumb" src="${data.thumbnail}" alt="thumbnail" />` : ""}
      <div class="yt-meta">
        <div class="yt-title">${data.title}</div>
        <div class="yt-sub">⏱ ${fmtDuration(data.duration)}</div>
        <div class="yt-sub">👤 ${data.uploader || "Unknown"}</div>
        <div class="yt-sub">👁 ${fmtNum(data.view_count)} views</div>
      </div>
    `);
    ytDownloadCard.classList.remove("hidden");

  } catch (e) {
    showError(ytError, "Network error. Is the server running?");
  } finally {
    ytInfoBtn.disabled = false;
    ytInfoBtn.querySelector("span").textContent = "Get Info";
  }
});

ytUrlInput.addEventListener("keydown", e => { if (e.key === "Enter") ytInfoBtn.click(); });

ytDownloadBtn.addEventListener("click", async () => {
  if (!currentYTUrl) return;

  hide(dlStatus);
  ytDownloadBtn.disabled = true;
  ytDownloadBtn.querySelector("span").textContent = "Downloading…";
  show(dlStatus, "⏳ Download in progress. This may take a moment for large files…");

  try {
    const res = await fetch(`${API}/api/youtube/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        video_url: currentYTUrl,
        format: selectedFormat,
        quality: selectedQuality,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      show(dlStatus, `❌ ${err.detail || "Download failed."}`);
      return;
    }

    // Trigger browser file download
    const blob = await res.blob();
    const contentDisposition = res.headers.get("Content-Disposition") || "";
    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
    const filename = filenameMatch ? filenameMatch[1] : `download.${selectedFormat}`;

    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();

    show(dlStatus, `✅ Download complete: ${filename}`);
  } catch (e) {
    show(dlStatus, "❌ Network error during download.");
  } finally {
    ytDownloadBtn.disabled = false;
    ytDownloadBtn.querySelector("span").textContent = "Download";
  }
});
document.getElementById("base-url-prefix").textContent = window.location.host + "/";
