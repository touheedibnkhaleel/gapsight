# BlindSpot — Review Gap Analyzer
## Complete Project: Branding · Backend · Frontend

---

## 🏷️ PART 1 — SaaS Branding (10 Name Options)

---

**Name:** BlindSpot
**Tagline:** See what reviews don't say.
**Positioning:** The decision-intelligence tool for founders who know their users are hiding something — even in five-star reviews.
**Domain idea:** getblindspot.com

---

**Name:** Gapwise
**Tagline:** The gaps between reviews are where the truth lives.
**Positioning:** Gapwise surfaces the product feedback no one's explicitly giving you — so you fix what actually matters.
**Domain idea:** gapwise.io

---

**Name:** Signalmap
**Tagline:** Turn review noise into founder signal.
**Positioning:** Signalmap extracts weak signals and invisible patterns from user reviews — before they become churn.
**Domain idea:** signalmap.co

---

**Name:** Radarly
**Tagline:** What's on your users' radar? (Hint: not what they said.)
**Positioning:** Radarly detects the features, failures, and frustrations users think — but never quite write down.
**Domain idea:** radarlyapp.com

---

**Name:** Voidcast
**Tagline:** Broadcast what the silence in your reviews is telling you.
**Positioning:** Voidcast reads between the stars — turning review patterns into strategic product decisions.
**Domain idea:** voidcast.io

---

**Name:** Lacuna
**Tagline:** Fill the gaps your reviews leave behind.
**Positioning:** Lacuna is the gap-intelligence layer for founder-led products — revealing what's missing from your feedback, not just what's there.
**Domain idea:** lacuna.so

---

**Name:** Pulsegap
**Tagline:** Your users' pulse — including the parts they skipped.
**Positioning:** Pulsegap monitors review streams to surface the hidden issues, blind spots, and under-reported product gaps founders need to act on.
**Domain idea:** pulsegap.com

---

**Name:** Substrata
**Tagline:** What lies beneath your best reviews?
**Positioning:** Substrata digs below the surface of user feedback to find the buried signals that shape product-market fit.
**Domain idea:** substrata.ai

---

**Name:** Candor
**Tagline:** Your users are being polite. We're not.
**Positioning:** Candor cuts through review noise to hand founders a direct, unvarnished view of what's broken, unnoticed, or quietly failing.
**Domain idea:** getcandor.app

---

**Name:** Hollowpoint
**Tagline:** Find the gaps your product reviews aren't hitting.
**Positioning:** Hollowpoint is the review intelligence tool for founders who ship fast — pinpointing the weak spots and missed signals before they compound.
**Domain idea:** hollowpoint.io

---

---

## 🖥️ PART 2 — Backend (FastAPI)

### File Structure
```
backend/
├── main.py           ← FastAPI app with /analyze endpoint
└── requirements.txt  ← Python dependencies
```

### How to Run Locally

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Set your OpenAI API key**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**3. Start the server**
```bash
uvicorn main:app --reload
```

**4. Test the API**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Notion is an all-in-one workspace for notes, wikis, and project management.",
    "reviews": [
      "Love the flexibility but onboarding was overwhelming.",
      "Great for personal use but our team struggled with permissions.",
      "Wish there was a better mobile experience."
    ]
  }'
```

**5. Swagger docs**
Open http://localhost:8000/docs for the auto-generated API UI.

### Expected Response
```json
{
  "blind_spots": ["..."],
  "weak_signals": ["..."],
  "opportunities": ["..."],
  "strategic_insights": ["..."]
}
```

---

## 🎨 PART 3 — Frontend

### File Structure
```
frontend/
├── index.html   ← Main UI
├── style.css    ← Dark editorial theme
└── script.js   ← Fetch API + result rendering
```

### How to Run Locally

Just open `index.html` in your browser — no build step needed.

> ⚠️ Make sure your backend is running at `http://localhost:8000` first.
> If you deploy the backend elsewhere, update `API_URL` in `script.js`.

---

## 🔗 Connecting Frontend to Backend

In `script.js`, line 7:
```js
const API_URL = "http://localhost:8000/analyze";
```
Change this URL when you deploy to production (e.g. Railway, Render, Fly.io).

---

## 🚀 Recommended Next Steps

1. **Add API key auth** — simple `X-API-Key` header check
2. **URL scraping** — auto-fetch reviews from Product Hunt / Trustpilot
3. **History** — save past analyses to a SQLite or Supabase DB
4. **Export** — download results as PDF / Notion page
5. **Webhooks** — alert founders when new reviews create new blind spots
