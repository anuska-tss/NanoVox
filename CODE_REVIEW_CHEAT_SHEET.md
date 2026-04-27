# NanoVox Code Review: Quick Reference Cheat Sheet

## The 30-Second Elevator Pitch

**NanoVox** is a call quality analysis platform that:
1. Takes audio files (complaint calls)
2. Transcribes with Whisper + attributes speakers using weighted voting
3. Scores 4 parameters: talk ratio, sentiment, empathy, resolution
4. Combines them with configurable profile weights
5. Stores results in SQLite for history/audit trail

**Data Flow**: Audio → Whisper → Speaker Label → Analyzers → Scoring → DB

---

## Must-Know Functions (Top 10)

### Backend (Python/FastAPI)

| Function | File | What It Does | Input | Output | Critical? |
|----------|------|-------------|-------|--------|-----------|
| `@app.post("/analyze")` | main.py | Main audio pipeline | Audio file | Call score + transcript | YES |
| `identify_speakers()` | main.py | Global Weighted Voting speaker attribution | Whisper segments | Transcript with Agent/Customer labels | YES |
| `_run_analyzers()` | main.py | Orchestrate 5 analyzers | Transcript + profile config | List[ParameterResult] | YES |
| `calculate_score()` | scoring_engine.py | Weighted scoring formula | Analyzer results + weights | CallScore (0-100) | YES |
| `analyze()` (sentiment) | modules/sentiment_analyzer.py | VADER frustration measurement | Customer segments | Penalty + journey_bonus | YES |
| `analyze()` (slm) | modules/slm_analyzer.py | Ollama empathy+resolution | Full transcript | 3 ParameterResults (empathy, resolution, sentiment) | MEDIUM |
| `analyze()` (talk ratio) | modules/talk_ratio_analyzer.py | Agent/Customer time ratio | All segments | Penalty based on ideal ratio | LOW |
| `save_call()` | database.py | Persist to SQLite | Analysis results | call_id (row) | MEDIUM |
| `load_profile_config()` | parameter_registry.py | Load weights | Profile name ("complaints"/"sales") | Profile dict | MEDIUM |
| `_generate_interpretation()` | scoring_engine.py | 1-2 sentence summary | Final score + breakdown | String | LOW |

### Frontend (React)

| Component | File | Purpose |
|-----------|------|---------|
| App.jsx | App.jsx | Main orchestration + state |
| processCall() | App.jsx | Calls /analyze or /api/test-analysis |
| handleWeightChange() | App.jsx | Triggers /api/rescore on weight slider |
| AnalysisDashboard | components/AnalysisDashboard.jsx | Displays results |

---

## The Scoring Formula (MEMORIZE THIS)

```python
# Step 1: Load weights for profile (sum = 100)
weights = {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40}

# Step 2: Each analyzer returns a penalty (0-100)
# - penalty=0 means perfect (no loss)
# - penalty=100 means terrible (100% loss)

# Step 3: Calculate weighted contribution of each parameter
total_weighted_penalty = Σ(normalized_weight_i × penalty_i / 100)

# Step 4: Final score
final_score = 100 - total_weighted_penalty
final_score = clamped to [0, 100]
```

**Example**: 
- talk_ratio penalty=35, weight=5% → contributes 1.75 points loss
- sentiment penalty=60, weight=35% → contributes 21 points loss
- ...total loss = 50.75
- **final_score = 49.25 / 100**

---

## The 5 Analyzers (In Order)

### 1. Talk Ratio (keyword-free, phase-aware)
- **What**: Agent speaking time ÷ (Agent + Customer time)
- **Score Range**: 0-10 (converted to 0-100 penalty)
- **Good Value**: Complaints should be 40-55% agent talk (customer leads)
- **Bad Value**: >80% agent talk (agent dominating)

### 2. Sentiment (VADER + journey bonus)
- **What**: Customer frustration level
- **Raw Value**: (1 - VADER_compound) × 5 (0-10 scale)
- **Tiered Penalty**: Non-linear (high frustration disproportionately bad)
- **Journey Bonus**: If start → end sentiment improves >0.6, reduce penalty by 60%
- **Why bonus**: Rewards de-escalation (turning angry customer around)

### 3. Empathy (SLM via Ollama)
- **What**: Agent emotional intelligence (1-10 score from LLM)
- **Source**: phi3.5:mini reading full transcript
- **Penalty**: (10 - score) × 10
- **Fallback**: If Ollama down → penalty=50

### 4. Resolution (SLM via Ollama)
- **What**: Was the customer's problem fixed? (0-10 score from LLM)
- **Good**: 9-10 ("it worked", "I'm fully sorted")
- **Medium**: 5-6 (workaround provided, root issue not fixed)
- **Bad**: 0-2 (customer still angry, nothing done)
- **Fallback**: If Ollama down → penalty=50

### 5. SLM True Sentiment (sarcasm-aware, metadata only)
- **What**: Does true sentiment (sarcasm/indirect) match VADER score?
- **Source**: Same Ollama call as #3 and #4
- **Use**: Drives SLM Override Logic (see below)
- **No Penalty**: Just metadata (doesn't contribute to final score directly)

---

## The SLM Override Logic (CRITICAL)

**Problem**: VADER is blind to sarcasm and indirect negativity  
**Solution**: After all analyzers run, check if SLM disagrees with VADER

```python
if slm_sentiment == "Negative" and vader_score > 40:
    # Override: VADER scored high but SLM detected real negativity
    vader_penalty = 85  # Force high penalty (customer is actually frustrated)
    
elif slm_sentiment == "Positive" and vader_score < 50:
    # Override: VADER scored low but SLM detected real positivity
    vader_penalty = 15  # Force low penalty (customer is actually satisfied)

else:
    # No override needed
    pass
```

**Example**:
- Customer says: "Oh great, another issue" (sarcastic negativity)
- VADER compound: +0.3 (detects positive words "great")
- VADER score: 65 (misleading!)
- SLM true_sentiment: "Negative" (detects sarcasm)
- Result: Override VADER to 15 (force it to reflect true negativity)

---

## What Happens If... (Q&A)

| Scenario | Result | Severity | Mitigation |
|----------|--------|----------|-----------|
| **Whisper unavailable** | App won't start | CRITICAL | Use /api/test-analysis instead |
| **Ollama unreachable** | Empathy/resolution use penalty=50 | MEDIUM | Graceful fallback; scores ~5 pts higher |
| **Speaker attribution wrong** | All downstream scoring skewed | CRITICAL | Users can use /api/test-analysis with manual labels |
| **Audio file 1GB** | Potential OOM crash | HIGH | No file size limit (needs adding) |
| **Weights sum to 75** | Auto-normalized to 100 | LOW | Happens transparently |
| **Database offline** | /analyze still works; history broken | MEDIUM | DB save non-critical |
| **Profile JSON malformed** | Falls back to hardcoded defaults | LOW | Graceful degradation |
| **Transcript has no customer segments** | Sentiment returns neutral (penalty=50) | LOW | Call continues; less accurate |

---

## Profile Weights (Complaints vs Sales)

### Complaints Profile (Current Default)
```json
{
  "talk_ratio": 5,      // Customer should talk more (let them vent)
  "sentiment": 35,      // Emotional journey most important
  "empathy": 20,        // Agent understanding matters
  "resolution": 40      // Did we actually fix the issue?
}
```
**Ideal talk ratio**: 40-55% agent (customer leads)

### Sales Profile (Fallback in Code)
```json
{
  "talk_ratio": 15,     // Agent should lead the call
  "sentiment": 30,      // Sentiment important but secondary
  "empathy": 20,        // Rapport building
  "resolution": 35      // Close the deal
}
```
**Ideal talk ratio**: 60-70% agent (agent leads)

---

## API Endpoints: Quick Reference

| Endpoint | Method | Purpose | Key Parameter |
|----------|--------|---------|----------------|
| `/analyze` | POST | Upload audio + analyze | `file`, `weights` (optional) |
| `/api/test-analysis` | POST | Test scoring with manual transcript | `transcript`, `weights`, `profile` |
| `/api/rescore` | POST | Recalculate score with new weights | `analyzer_results`, `weights` |
| `/api/parameters/available` | GET | Get dynamic param list (for UI) | — |
| `/api/weights/defaults` | GET | Get profile default weights | — |
| `/api/history` | GET | Get recent calls | `limit`, `offset` |
| `/api/history/{id}` | GET | Get full call detail | `id` |
| `/api/stats` | GET | Aggregate stats | — |
| `/api/report/{id}` | GET | Download PDF report | `id` |

---

## Data Models (Pydantic)

### ParameterResult
```python
class ParameterResult:
    name: str              # "talk_ratio", "sentiment", etc.
    display_name: str      # "Talk-to-Listen Ratio"
    icon: str              # "🎙️"
    raw_value: float       # Original measurement
    score: float           # 0-100 scale
    penalty: float         # 0-100 (used in scoring)
    metadata: dict         # Extra data (journey_bonus, etc.)
```

### CallScore
```python
class CallScore:
    final_score: float     # 0-100
    breakdown: Dict        # {param_name: ParameterBreakdown}
    profile_used: str      # "complaints"
    interpretation: str    # 1-2 sentence summary
    metadata: dict         # Combined metadata from all params
```

---

## Common Questions & Answers

### Q: "What format should audio be?"
**A**: WAV, MP3, M4A, FLAC, etc. (Whisper handles most formats)

### Q: "How does speaker attribution work?"
**A**: 
1. Pause detection: gaps > 0.3s likely speaker change
2. Signal matching: count AGENT_SIGNALS vs CUSTOMER_SIGNALS
3. Structural bonuses: first speaker +12 (anchor), last speaker +6 (closer)
4. Global scoring: decide which ID (0 or 1) = Agent based on total score

### Q: "What if customer and agent have similar speaking time?"
**A**: Talk ratio penalty softens (non-linear tiered curve). Not penalized as hard as being way off ideal.

### Q: "Can I override weights after analysis?"
**A**: Yes! `/api/rescore` recalculates with new weights (cached analyzer_results used, no re-analysis needed)

### Q: "What if Ollama times out?"
**A**: 90-second timeout; if exceeded, empathy/resolution use fallback penalty=50. No crash.

### Q: "Where's the Swagger documentation?"
**A**: 
- Go to `http://localhost:8000/docs`
- Auto-generated by FastAPI from code

### Q: "How is the interpretation generated?"
**A**: `_generate_interpretation()` uses score bands and parameter penalties to create summary

### Q: "What happens if I disable one analyzer?"
**A**: That parameter won't be in the results; scoring skips it (weights normalized to remaining params)

### Q: "Is there rate limiting?"
**A**: No (needs adding for production)

### Q: "Is the API authenticated?"
**A**: No (needs adding for production)

---

## Database Schema (3 Key Tables)

### call_history
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
filename TEXT
file_size_bytes INTEGER
analyzed_at TEXT (UTC ISO)

-- Scores
final_score REAL
profile_used TEXT
interpretation TEXT

-- Individual parameters
talk_ratio_score REAL
sentiment_score REAL
empathy_score REAL
commitment_score REAL

-- Full JSON blobs (for drill-down)
analysis_json TEXT
transcript_json TEXT
insights_json TEXT
analyzer_results_json TEXT
weights_json TEXT

-- Indices: ON analyzed_at DESC, final_score, agent_name
```

---

## Files to Review (In This Order)

1. **backend/main.py** — Core endpoint logic + speaker attribution
2. **backend/scoring_engine.py** — Scoring formula + interpretation
3. **backend/modules/sentiment_analyzer.py** — VADER + journey bonus
4. **backend/modules/slm_analyzer.py** — Ollama empathy/resolution
5. **backend/models.py** — Pydantic schemas
6. **backend/parameter_registry.py** — Config + weight loading
7. **backend/database.py** — SQLite persistence
8. **frontend/src/App.jsx** — State orchestration
9. **frontend/src/components/AnalysisDashboard.jsx** — Results display

---

## Red Flags to Discuss

🚩 **No file size limit** → OOM risk  
🚩 **Speaker attribution uses heuristics** → Can be wrong; no ML-based speaker separation  
🚩 **Ollama must be manually started** → No bundled setup  
🚩 **No authentication** → Anyone can call /analyze  
🚩 **No rate limiting** → DoS risk  
🚩 **Sentiment journey bonus is aggressive (60% reduction)** → Might hide poor resolution  
🚩 **SLM override can force VADER to 15 or 85** → Binary override might be too harsh  

---

## Strengths to Highlight

✅ **Graceful fallbacks** — All external deps optional; pipeline continues on failure  
✅ **Type safety** — Pydantic validates all data at boundaries  
✅ **Sarcasm awareness** — SLM override logic handles what VADER misses  
✅ **Parameter flexibility** — Config-driven weights; easy to tune profiles  
✅ **Audit trail** — Full JSON blobs stored; can replay any analysis  
✅ **Sentiment journey bonus** — Rewards de-escalation (important for complaints)  
✅ **Speaker attribution heuristics** — Anchor/closer bonuses reduce false positives  

---

## 60-Second Summary for Reviewers

> NanoVox is a **call quality scoring system** that transcribes audio, attributes speakers using global weighted voting, runs 5 parallel analyzers (talk ratio, sentiment, empathy, resolution, sarcasm detection), combines them with profile-specific weights, and persists to SQLite.
>
> **Key innovation**: SLM-based override logic corrects VADER blindspots to sarcasm.
>
> **Critical dependencies**: Whisper (transcription), speaker attribution heuristics, Ollama-based empathy/resolution.
>
> **Graceful degradation**: All external deps optional; pipeline continues on failure.
>
> **Known gaps**: No file size limit, no auth, no rate limiting—fine for MVP, needs hardening for prod.

---

## Timeline for Review

- **0-10 min**: Overview + architecture
- **10-20 min**: Data flow (audio → final score)
- **20-30 min**: Analyzer functions (deep dive on sentiment + SLM)
- **30-40 min**: Scoring formula + dependencies
- **40-50 min**: Error cases + testing strategy
- **50-60 min**: Q&A + open issues

---

**Print this. Know this. You'll ace the review.** 🚀
