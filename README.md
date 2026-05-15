# GapSight — Review Gap Analyzer

> Find what your users aren't telling you.

GapSight analyzes product reviews from Product Hunt and Trustpilot to surface blind spots, weak signals, and hidden opportunities that founders miss. This is NOT a review summarizer — it's a decision-making tool.

---

## Live Demo

- **Frontend:** https://gapsight.vercel.app
- **Backend API:** https://gapsight-backend.onrender.com

---

## What It Does

Paste a product URL or reviews manually and get:

- **Blind Spots** — features users almost never mention
- **Weak Signals** — subtle frustrations hiding in positive reviews
- **Opportunities** — unmet needs users hint at but never demand
- **Strategic Insights** — specific recommendations for the founder

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| AI Model | OpenRouter (free) — LLaMA, Gemma, Mistral |
| Scraping | BeautifulSoup, Requests |
| Hosting | Vercel (frontend) + Render (backend) |

---

## Supported Platforms

- 🔶 Product Hunt
- ⭐ Trustpilot
- More coming soon (G2, App Store, Google Play)

---

## Run Locally

### 1. Clone the repo
\`\`\`bash
git clone https://github.com/touheedibnkhaleel/gapsight.git
cd gapsight
\`\`\`

### 2. Set up backend
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

### 3. Add your API key
\`\`\`bash
echo 'OPENROUTER_API_KEY=your-key-here' > .env
\`\`\`
Get a free key at: https://openrouter.ai

### 4. Start backend
\`\`\`bash
uvicorn main:app --reload
\`\`\`

### 5. Start frontend
\`\`\`bash
python3 -m http.server 3000
\`\`\`

### 6. Open in browser
\`\`\`
http://localhost:3000
\`\`\`

---

## API Usage

### Analyze by URL
\`\`\`bash
curl -X POST https://gapsight-backend.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.producthunt.com/products/notion"}'
\`\`\`

### Analyze Manually
\`\`\`bash
curl -X POST https://gapsight-backend.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Your product description",
    "reviews": ["review 1", "review 2", "review 3"]
  }'
\`\`\`

### Response Format
\`\`\`json
{
  "product_name": "Notion",
  "source": "Product Hunt",
  "review_count": 24,
  "blind_spots": ["..."],
  "weak_signals": ["..."],
  "opportunities": ["..."],
  "strategic_insights": ["..."]
}
\`\`\`

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | ✅ Yes |

---

## Roadmap

- [ ] Competitor Gap Radar — compare your product vs competitor
- [ ] Gap Health Score — track improvements over time
- [ ] Weekly email digest — new weak signals detected
- [ ] G2 and App Store support
- [ ] Fix Cards — actionable cards with effort and impact scores

---

## Built By

Touheed — [@touheedibnkhaleel](https://github.com/touheedibnkhaleel)

---

## License

MIT License — free to use and modify
