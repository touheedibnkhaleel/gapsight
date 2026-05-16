/**
 * GapSight — script.js (Clean Debuggable Version)
 * If nothing happens when you click Analyze, open:
 *   Chrome → Right Click → Inspect → Console tab
 * All errors will appear there.
 */
 
const API_URL = "https://gapsight-backend.onrender.com/analyze"; 
// ── Current mode (url or manual) ──────────────────────────────────────────────
let currentMode = "url";
 
// ── Run as soon as the page loads — verify JS is working ─────────────────────
document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ GapSight JS loaded successfully");
  console.log("📡 Backend URL:", API_URL);
 
  // Attach button click
  const btn = document.getElementById("analyze-btn");
  if (btn) {
    btn.addEventListener("click", runAnalysis);
    console.log("✅ Analyze button found and listener attached");
  } else {
    console.error("❌ Could not find #analyze-btn — check your index.html");
  }
});
 
// ── Switch between URL and Manual mode ───────────────────────────────────────
function switchMode(mode) {
  currentMode = mode;
  console.log("🔀 Switched to mode:", mode);
 
  const urlSection    = document.getElementById("mode-url");
  const manualSection = document.getElementById("mode-manual");
  const btnUrl        = document.getElementById("btn-url");
  const btnManual     = document.getElementById("btn-manual");
 
  if (!urlSection || !manualSection) {
    console.error("❌ mode-url or mode-manual div not found in HTML");
    return;
  }
 
  urlSection.style.display    = mode === "url"    ? "block" : "none";
  manualSection.style.display = mode === "manual" ? "block" : "none";
 
  btnUrl?.classList.toggle("active",    mode === "url");
  btnManual?.classList.toggle("active", mode === "manual");
 
  hideError();
}
 
// ── Fill example URLs ─────────────────────────────────────────────────────────
function fillExample(type) {
  const input = document.getElementById("product-url");
  if (!input) return;
  input.value = type === "ph"
    ? "https://www.producthunt.com/products/notion"
    : "https://www.trustpilot.com/review/notion.so";
}
 
// ── Main Analysis ─────────────────────────────────────────────────────────────
async function runAnalysis() {
  console.log("🚀 runAnalysis() called — mode:", currentMode);
  hideError();
 
  // Build request body
  let body = {};
 
  if (currentMode === "url") {
    const urlInput = document.getElementById("product-url");
    if (!urlInput) { showError("product-url input not found in HTML."); return; }
 
    let url = urlInput.value.trim().replace(/^["']|["']$/g, '');
 
    if (!url) { showError('Please paste a Product Hunt or Trustpilot URL.'); return; }
 
    // Auto-add https:// if user forgot it
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
      urlInput.value = url;
    }
 
    // Validate it's a supported platform
    if (!url.includes('producthunt.com') && !url.includes('trustpilot.com')) {
      showError('Please enter a Product Hunt or Trustpilot URL. Example: https://www.producthunt.com/products/your-product');
      return;
    }
 
    console.log('🔗 Sending URL:', url);
    body = { url };
 
  } else {
    const descEl  = document.getElementById("product-desc");
    const revsEl  = document.getElementById("reviews-input");
 
    if (!descEl || !revsEl) { showError("product-desc or reviews-input not found in HTML."); return; }
 
    const desc    = descEl.value.trim();
    const rawRevs = revsEl.value.trim();
 
    console.log("📝 Manual mode — description length:", desc.length, "reviews length:", rawRevs.length);
 
    if (!desc)    { showError("Please enter a product description."); return; }
    if (!rawRevs) { showError("Please paste at least one review."); return; }
 
    const reviews = rawRevs.split("\n").map(r => r.trim()).filter(r => r.length > 0);
    if (reviews.length === 0) { showError("No valid reviews found. Put each review on a new line."); return; }
 
    body = { product_description: desc, reviews };
  }
 
  console.log("📤 Sending to backend:", JSON.stringify(body).slice(0, 120) + "...");
 
  // ── Show loading ──
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
 
    if (!response.ok) {
      throw new Error(data.detail || `Server returned ${response.status}`);
    }
 
    renderResults(data);
 
  } catch (err) {
    console.error("❌ Fetch error:", err);
 
    if (err.message.includes("Failed to fetch")) {
      showError(
        "Cannot reach backend. Make sure the Render backend is running at https://gapsight-backend.onrender.com"
      );
    } else {
      showError(`Error: ${err.message}`);
    }
 
    setLoading(false);
  }
}
 
// ── Render Results ────────────────────────────────────────────────────────────
function renderResults(data) {
  console.log("🎨 Rendering results:", Object.keys(data));
 
  const nameEl = document.getElementById("results-product-name");
  const metaEl = document.getElementById("results-meta");
  const badgeEl = document.getElementById("results-badge");
 
  if (nameEl)  nameEl.textContent  = data.product_name || "Your Product";
  if (metaEl)  metaEl.textContent  = `${data.review_count || 0} reviews · ${data.source || ""}`;
  if (badgeEl) badgeEl.textContent = "✓ Gap Analysis Complete";
 
  populateList("blind-spots-list",        data.blind_spots        || []);
  populateList("weak-signals-list",       data.weak_signals       || []);
  populateList("opportunities-list",      data.opportunities      || []);
  populateList("strategic-insights-list", data.strategic_insights || []);
 
  // Hide loading, show results
  const loadingSection = document.getElementById("loading-section");
  const resultsSection = document.getElementById("results");
  const formSection    = document.getElementById("form-section");
 
  if (loadingSection) loadingSection.style.display = "none";
  if (formSection)    formSection.style.display    = "none";
  if (resultsSection) {
    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth" });
  }
}
 
// ── Populate a <ul> ───────────────────────────────────────────────────────────
function populateList(listId, items) {
  const ul = document.getElementById(listId);
  if (!ul) {
    console.warn("⚠️ List not found:", listId);
    return;
  }
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
 
// ── Loading state ─────────────────────────────────────────────────────────────
function setLoading(on) {
  const btn            = document.getElementById("analyze-btn");
  const formSection    = document.getElementById("form-section");
  const loadingSection = document.getElementById("loading-section");
 
  if (on) {
    if (formSection)    formSection.style.display    = "none";
    if (loadingSection) loadingSection.style.display = "block";
    if (btn)            btn.disabled = true;
    animateLoadingSteps();
  } else {
    if (loadingSection) loadingSection.style.display = "none";
    if (formSection)    formSection.style.display    = "flex";
    if (btn)            btn.disabled = false;
    stopLoadingAnimation();
  }
}
 
// ── Loading step animation ────────────────────────────────────────────────────
let stepInterval = null;
 
function animateLoadingSteps() {
  const steps = ["step-1", "step-2", "step-3", "step-4"];
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
  el.classList.remove("active", "done");
  if (state) el.classList.add(state);
}
 
// ── Reset ─────────────────────────────────────────────────────────────────────
function resetForm() {
  // Hide results and loading
  document.getElementById("results").style.display          = "none";
  document.getElementById("loading-section").style.display  = "none";

  // Show form
  document.getElementById("form-section").style.display     = "flex";

  // Clear all input fields
  const urlInput = document.getElementById("product-url");
  const descInput = document.getElementById("product-desc");
  const revsInput = document.getElementById("reviews-input");
  if (urlInput)  urlInput.value  = "";
  if (descInput) descInput.value = "";
  if (revsInput) revsInput.value = "";

  // Clear result lists
  ["blind-spots-list","weak-signals-list","opportunities-list","strategic-insights-list"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = "";
  });

  // Reset loading steps
  ["step-1","step-2","step-3","step-4"].forEach(id => markStep(id, ""));

  // Clear errors
  hideError();

  // Switch back to URL mode
  switchMode("url");

  // Scroll to top
  window.scrollTo({ top: 0, behavior: "smooth" });
}
 
// ── Helpers ───────────────────────────────────────────────────────────────────
function showError(msg) {
  console.error("🔴 Showing error:", msg);
  const el = document.getElementById("error-msg");
  if (el) { el.textContent = `⚠ ${msg}`; el.style.display = "block"; }
}
 
function hideError() {
  const el = document.getElementById("error-msg");
  if (el) { el.textContent = ""; el.style.display = "none"; }
}