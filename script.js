/**
 * GapSight — script.js
 * Clean rewrite with working reset
 */

const API_URL = "https://gapsight-szx4.onrender.com/analyze";

let currentMode = "url";

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ GapSight JS loaded successfully");
  console.log("📡 Backend URL:", API_URL);
  const btn = document.getElementById("analyze-btn");
  if (btn) {
    btn.addEventListener("click", runAnalysis);
    console.log("✅ Analyze button found and listener attached");
  } else {
    console.error("❌ Could not find #analyze-btn");
  }
});

function switchMode(mode) {
  currentMode = mode;
  console.log("🔀 Switched to mode:", mode);
  const urlSection    = document.getElementById("mode-url");
  const manualSection = document.getElementById("mode-manual");
  const btnUrl        = document.getElementById("btn-url");
  const btnManual     = document.getElementById("btn-manual");
  if (urlSection)    urlSection.style.display    = mode === "url"    ? "block" : "none";
  if (manualSection) manualSection.style.display = mode === "manual" ? "block" : "none";
  if (btnUrl)        btnUrl.classList.toggle("active",    mode === "url");
  if (btnManual)     btnManual.classList.toggle("active", mode === "manual");
  hideError();
}

function fillExample(type) {
  const input = document.getElementById("product-url");
  if (!input) return;
  input.value = type === "ph"
    ? "https://www.producthunt.com/products/notion"
    : "https://www.trustpilot.com/review/notion.so";
}

async function runAnalysis() {
  console.log("🚀 runAnalysis() called — mode:", currentMode);
  hideError();
  let body = {};

  if (currentMode === "url") {
    const urlInput = document.getElementById("product-url");
    if (!urlInput) { showError("product-url input not found."); return; }
    let url = urlInput.value.trim().replace(/^["']|["']$/g, "");
    if (!url) { showError("Please paste a Product Hunt or Trustpilot URL."); return; }
    if (!url.startsWith("http")) url = "https://" + url;
    if (!url.includes("producthunt.com") && !url.includes("trustpilot.com")) {
      showError("Please enter a Product Hunt or Trustpilot URL.");
      return;
    }
    console.log("🔗 Sending URL:", url);
    body = { url };
  } else {
    const descEl = document.getElementById("product-desc");
    const revsEl = document.getElementById("reviews-input");
    if (!descEl || !revsEl) { showError("Input fields not found."); return; }
    const desc    = descEl.value.trim();
    const rawRevs = revsEl.value.trim();
    if (!desc)    { showError("Please enter a product description."); return; }
    if (!rawRevs) { showError("Please paste at least one review."); return; }
    const reviews = rawRevs.split("\n").map(r => r.trim()).filter(r => r.length > 0);
    if (reviews.length === 0) { showError("No valid reviews found."); return; }
    body = { product_description: desc, reviews };
  }

  console.log("📤 Sending to backend...");
  setLoading(true);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    console.log("📥 Response status:", response.status);
    const data = await response.json();
    console.log("📥 Response data:", data);
    if (!response.ok) throw new Error(data.detail || `Server error ${response.status}`);
    renderResults(data);
  } catch (err) {
    console.error("❌ Error:", err);
    if (err.message.includes("Failed to fetch")) {
      showError("Cannot reach backend. Make sure the Render backend is running.");
    } else {
      showError(`Error: ${err.message}`);
    }
    setLoading(false);
  }
}

function renderResults(data) {
  console.log("🎨 Rendering results");
  const nameEl  = document.getElementById("results-product-name");
  const metaEl  = document.getElementById("results-meta");
  const badgeEl = document.getElementById("results-badge");
  if (nameEl)  nameEl.textContent  = data.product_name || "Your Product";
  if (metaEl)  metaEl.textContent  = `${data.review_count || 0} reviews · ${data.source || ""}`;
  if (badgeEl) badgeEl.textContent = "✓ Gap Analysis Complete";

  populateList("blind-spots-list",        data.blind_spots        || []);
  populateList("weak-signals-list",       data.weak_signals       || []);
  populateList("opportunities-list",      data.opportunities      || []);
  populateList("strategic-insights-list", data.strategic_insights || []);

  setLoading(false);

  const loading = document.getElementById("loading-section");
  const results = document.getElementById("results");
  const form    = document.getElementById("form-section");

  if (loading) loading.style.display = "none";
  if (form)    form.style.display    = "none";
  if (results) {
    results.style.display = "block";
    results.scrollIntoView({ behavior: "smooth" });
  }
}

function populateList(listId, items) {
  const ul = document.getElementById(listId);
  if (!ul) return;
  ul.innerHTML = "";
  if (!items || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = "Nothing detected.";
    li.style.color = "var(--text-dim)";
    ul.appendChild(li);
    return;
  }
  items.forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    ul.appendChild(li);
  });
}

function setLoading(on) {
  const btn     = document.getElementById("analyze-btn");
  const form    = document.getElementById("form-section");
  const loading = document.getElementById("loading-section");
  if (on) {
    if (form)    form.style.display    = "none";
    if (loading) loading.style.display = "block";
    if (btn)     btn.disabled          = true;
    animateLoadingSteps();
  } else {
    if (loading) loading.style.display = "none";
    if (btn) {
      btn.disabled = false;
      btn.style.pointerEvents = "auto";
      btn.style.opacity = "1";
    }
    stopLoadingAnimation();
  }
}

function resetForm() {
  console.log("🔄 resetForm called");

  // Hide results and loading
  const results = document.getElementById("results");
  const loading = document.getElementById("loading-section");
  const form    = document.getElementById("form-section");
  const btn     = document.getElementById("analyze-btn");

  if (results) results.style.display = "none";
  if (loading) loading.style.display = "none";

  // Clear inputs
  ["product-url","product-desc","reviews-input"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });

  // Clear result cards
  ["blind-spots-list","weak-signals-list","opportunities-list","strategic-insights-list"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = "";
  });

  // Reset button
  if (btn) {
    btn.disabled = false;
    btn.style.pointerEvents = "auto";
    btn.style.opacity = "1";
    btn.innerHTML = '<span class="btn-icon">⬡</span> <span id="btn-label">Analyze Gap</span>';
  }

  // Reset steps and errors
  ["step-1","step-2","step-3","step-4"].forEach(id => markStep(id, ""));
  hideError();
  switchMode("url");

  // Show form
  if (form) {
    form.style.display = "flex";
    form.style.pointerEvents = "auto";
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

let stepInterval = null;

function animateLoadingSteps() {
  const steps = ["step-1","step-2","step-3","step-4"];
  let current = 0;
  markStep(steps[0], "active");
  stepInterval = setInterval(() => {
    if (current < steps.length - 1) {
      markStep(steps[current], "done");
      current++;
      markStep(steps[current], "active");
    }
  }, 2200);
}

function stopLoadingAnimation() {
  if (stepInterval) { clearInterval(stepInterval); stepInterval = null; }
  ["step-1","step-2","step-3","step-4"].forEach(id => markStep(id, "done"));
}

function markStep(id, state) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove("active","done");
  if (state) el.classList.add(state);
}

function showError(msg) {
  console.error("🔴 Error:", msg);
  const el = document.getElementById("error-msg");
  if (el) { el.textContent = `⚠ ${msg}`; el.style.display = "block"; }
}

function hideError() {
  const el = document.getElementById("error-msg");
  if (el) { el.textContent = ""; el.style.display = "none"; }
}
