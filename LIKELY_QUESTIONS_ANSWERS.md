# Code Review: Likely Questions & Detailed Answers

**Your reviewers will ask detailed questions about:**
1. Data flow end-to-end
2. Function dependencies and failure modes
3. Configuration and profile behavior
4. What breaks if we change/remove something
5. How everything is tested
6. Swagger/API documentation

**This document has the deep answers they're looking for.**

---

## SECTION 1: DATA FLOW QUESTIONS

### Q1: "If I give you an audio file, walk me through exactly what happens. What format is the data at each step?"

**Your Answer:**

"Let me walk through the complete /analyze pipeline:

**Step 1: Upload (Binary Audio)**
- User uploads `call.wav` via multipart/form-data
- FastAPI receives as `UploadFile` object
- File contents read into memory as bytes
- Saved to `/tmp/xyz.wav` (temporary file)
- Logged: file size, filename, content type
- *Data type: Binary bytes on disk*

**Step 2: Transcription via Whisper (Segments + Text)**
- Whisper model (tiny, 140MB, CPU-only) processes temp file
- Returns dict with:
  ```json
  {
    "text": "Full conversation concatenated",
    "segments": [
      {"id": 0, "start": 0.0, "end": 5.2, "text": "Hello...", "confidence": 0.95},
      {"id": 1, "start": 5.4, "end": 10.1, "text": "Hi there..."}
    ]
  }
  ```
- *Data type: Dict with text + list of segment dicts*
- **CRITICAL**: No speaker labels yet (Whisper can't do speaker diarization by default)
- Duration: 1-5 sec for 10-minute audio

**Step 3: Speaker Attribution (add Agent/Customer labels)**
- Whisper segments have no speaker labels
- Global Weighted Voting algorithm:
  1. Assign alternating speaker IDs (0, 1) based on pause gaps (>0.3s)
  2. Score each ID by counting keyword matches:
     - AGENT_SIGNALS: 'speaking', 'timeline', 'budget', 'solution', etc. (24 keywords)
     - CUSTOMER_SIGNALS: 'problem', 'frustrated', 'expensive', etc. (13 keywords)
     - Add match: score[id] += 1, subtract match: score[id] -= 1
  3. Apply bonuses:
     - First speaker +12 points (anchor, agent usually starts)
     - Last speaker +6 points (closer bonus)
  4. Decision: If score[0] >= score[1]: {0→Agent, 1→Customer}, else swap
- Final output:
  ```json
  [
    {"speaker": "Agent", "start": 0.0, "end": 5.2, "text": "Hello..."},
    {"speaker": "Customer", "start": 5.4, "end": 10.1, "text": "Hi there..."}
  ]
  ```
- *Data type: List of dicts with speaker labels*
- Duration: ~100ms

**Step 4: Run Analyzer Pipeline (5 parallel analyzers)**

The transcript goes to:

a) **Talk Ratio Analyzer**
   - Input: Full transcript with speaker labels
   - Calculate:
     - agent_time = sum of all Agent segment durations
     - customer_time = sum of all Customer segment durations
     - talk_ratio = agent_time / (agent_time + customer_time)
   - Output: penalty (0-100) based on ideal_talk_ratio [0.40-0.55 for complaints]
   - Duration: ~50ms

b) **Sentiment Analyzer (VADER)**
   - Input: Only Customer segments
   - For each customer segment:
     - Run VADER sentiment: compound score (-1 to +1)
     - Convert to frustration: (1 - compound) * 5 (0-10 scale)
   - Average frustration
   - Apply tiered penalty:
     ```
     if frustration ≤ 3.0: penalty = frustration * 5.0 (0-15)
     if 3.0 < frustration ≤ 6.0: penalty = 15 + (f-3)*10 (15-45)
     if frustration > 6.0: penalty = 45 + (f-6)*13.75 (45-100)
     ```
   - Sentiment Journey Bonus:
     - Compare first 3 vs last 3 customer segments
     - If end_sentiment > start_sentiment + 0.6: reduce penalty by 60%
   - Output: penalty + journey_bonus metadata
   - Duration: ~100ms

c) **SLM Analyzer (Ollama phi3.5)**
   - Input: Full transcript (formatted as readable text)
   - HTTP POST to Ollama at localhost:11434/api/generate
   - Model: phi3.5:mini
   - Timeout: 90 seconds
   - System prompt: Detailed call auditor instructions
   - Receives JSON response:
     ```json
     {
       "empathy_score": 1-10,
       "empathy_reason": "string (20 words max)",
       "resolution_score": 0-10,
       "resolution_reason": "string (20 words max)",
       "overall_sentiment": "Positive|Neutral|Negative"
     }
     ```
   - Three outputs:
     1. Empathy: penalty = (10 - score) * 10
     2. Resolution: penalty = (10 - score) * 10
     3. SLM Sentiment: metadata only (no penalty)
   - Output: 3 ParameterResult objects
   - Duration: 1-3 seconds (CPU inference)
   - Fallback if Ollama down: all three return penalty=50

**Step 5: SLM Override Logic (Post-Pipeline)**
- Check if SLM true_sentiment disagrees with VADER
- If SLM says "Negative" + VADER score > 40:
  - Override: sentiment_penalty = 85 (force high penalty)
  - Reason: SLM detects sarcasm/indirect negativity that VADER missed
- If SLM says "Positive" + VADER score < 50:
  - Override: sentiment_penalty = 15 (force low penalty)
  - Reason: SLM detects genuine positivity that VADER underscored
- Log: "SLM Override: VADER=X → forced to Y"
- Output: Modified ParameterResult for sentiment

**Step 6: Scoring Engine**
- Input: 5 ParameterResults + weights (from profile config)
- Normalize weights (ensure they sum to 100):
  ```
  normalized_weight[i] = (profile_weight[i] / sum(weights)) * 100
  ```
- Calculate weighted penalties:
  ```
  For each parameter:
    contribution = -(normalized_weight * penalty / 100)
  total_weighted_penalty = Σ(contribution)
  ```
- Calculate final score:
  ```
  final_score = 100 - total_weighted_penalty
  final_score = max(0, min(100, final_score))  # Clamp to 0-100
  ```
- Generate interpretation (1-2 sentences based on score bands):
  ```
  80+: "Excellent call..."
  50-79: "Adequate call..."
  <50: "Poor call..."
  ```
- Output: CallScore pydantic model
  ```json
  {
    "final_score": 65.3,
    "breakdown": {
      "talk_ratio": {"raw_value": 0.55, "score": 55, "penalty": 45, "weight": 5, "contribution": -2.25},
      "sentiment": {"raw_value": 6.2, "score": 42, "penalty": 58, "weight": 35, "contribution": -20.3},
      "empathy": {"raw_value": 7, "score": 70, "penalty": 30, "weight": 20, "contribution": -6.0},
      "resolution": {"raw_value": 6, "score": 60, "penalty": 40, "weight": 40, "contribution": -16.0}
    },
    "profile_used": "Complaints",
    "interpretation": "Below-average call needing attention. Needs improvement in sentiment.",
    "metadata": {...}
  }
  ```
- Duration: ~50ms

**Step 7: Database Persistence**
- Extract from response:
  - final_score, profile_used, interpretation
  - Individual parameter scores (from breakdown)
  - Full JSON blobs (analysis, transcript, analyzer_results)
- Insert into SQLite call_history table
- Return: call_id (row ID)
- Duration: ~50ms

**Step 8: Return Response to Frontend**
```json
{
  "filename": "call.wav",
  "file_size_bytes": 2048000,
  "transcription": {
    "text": "Full text...",
    "transcript": [...]
  },
  "insights": {...},
  "analysis": {
    "final_score": 65.3,
    "breakdown": {...},
    "analyzer_results": [...]  // Cached for rescoring
  },
  "call_id": 42
}
```

**Total Duration**: ~10-30 seconds (dominated by Whisper + Ollama)

---

### Q2: "What exactly is stored in the database? Can I rebuild the analysis from stored data?"

**Your Answer:**

"Yes, completely. The call_history table stores everything needed to rebuild:

```sql
-- Scalar columns (summary)
id, filename, file_size_bytes, analyzed_at, final_score, profile_used, interpretation
talk_ratio_score, sentiment_score, empathy_score, commitment_score

-- JSON blob columns (full replay)
analysis_json          -- Full CallScore object
transcript_json        -- Full transcript with speaker labels
insights_json          -- Legacy insights (mostly unused)
analyzer_results_json  -- All 5 ParameterResults (cached)
weights_json           -- Weights used for this analysis

-- Indices for fast queries
idx_analyzed_at (DESC)
idx_final_score
idx_agent_name
```

To rebuild the exact same analysis:
1. Load analyzer_results_json (the 5 ParameterResult objects)
2. Load weights_json
3. Call `/api/rescore` with those results + weights
4. Get identical final_score

The analyzer_results are cached because they're expensive (Whisper + Ollama). The scoring engine is deterministic."

---

## SECTION 2: DEPENDENCY & FAILURE MODE QUESTIONS

### Q3: "What happens if the Whisper model fails to load?"

**Your Answer:**

"The app won't start. In main.py, the @app.on_event('startup') function loads Whisper at boot time:

```python
@app.on_event("startup")
async def load_models():
    whisper_model = whisper.load_model("tiny")  # If this fails → exception
    # ...app never starts
```

**Impact**: /analyze endpoint completely broken. No fallback.

**Mitigation**: 
- For development: use /api/test-analysis instead (manual JSON transcript input)
- For production: would need bundled Whisper or remote transcription API fallback

**Why no fallback**: Whisper is fundamental; can't do audio analysis without transcription."

---

### Q4: "What if Ollama is down?"

**Your Answer:**

"Graceful fallback. In slm_analyzer.py line 340-353:

```python
except requests.exceptions.ConnectionError:
    logger.error("SLM: Ollama not reachable at %s", OLLAMA_URL)
    # Falls through to fallback
except requests.exceptions.Timeout:
    logger.error("SLM: Ollama request timed out after %ds", OLLAMA_TIMEOUT)
    # Falls through to fallback

# Fallback: return neutral scores
return [_neutral_empathy(), _neutral_resolution(), _neutral_slm_sentiment()]
```

**What returns**:
- empathy: penalty=50 (neutral)
- resolution: penalty=50 (neutral)
- slm_sentiment: Neutral (metadata only)

**Impact on final score**:
- If Ollama was down for a call, those two parameters are less penalizing
- Final score typically 5-10 points higher (less penalty)
- SLM override logic can't apply (no true_sentiment)

**Example**:
- With Ollama: final_score = 45.2
- Without Ollama: final_score = 54.1 (10 point boost)

**Is this a problem?**: No—Ollama is optional. Graceful degradation. But accuracy is reduced."

---

### Q5: "What if speaker attribution is 100% wrong? (Client labeled agent as customer)"

**Your Answer:**

"Cascading failure. The speaker labels propagate through the entire pipeline:

1. **Talk Ratio**: Scores calculate agent/customer time with WRONG labels
   - If truly agent:customer = 70:30 but labeled 30:70
   - Sees 30:70 (opposite) → might score it as GOOD (meets 40-55% ideal)
   - Output: low penalty (wrong!)

2. **Sentiment**: Measures frustration of WRONG speaker
   - If customer is frustrated but labeled as agent → missed frustration
   - If agent is calm but labeled as customer → sees fake frustration
   - Output: misleading sentiment score

3. **Empathy/Resolution**: LLM reads transcript with WRONG labels
   - Models might still infer from context ('I fully understand' = agent empathy)
   - But less reliable

**Final Impact**: Score is unreliable (GIGO - garbage in, garbage out)

**Mitigation**:
- Frontend /api/test-analysis allows manual transcript with correct labels
- Users can verify transcription is correct
- No persistence of raw audio or speaker labels—every upload re-attributes

**How likely is this?**
- Global Weighted Voting uses 24 AGENT + 13 CUSTOMER keywords
- Mostly correct on real calls
- But keyword matching has upper bound (~85% accuracy on customers)

**Example of wrong case**:
- Audio: [Customer frustrated, Agent helpful] = 'REAL'
- But customer never mentions key words; agent does
- Algorithm scores: agent_score=20, customer_score=5
- Labels as: 0→Agent, 1→Customer (correct by luck)
- But could be opposite if silence or technical call without many keywords"

---

### Q6: "What if we change the sentiment analyzer penalty curve? What breaks?"

**Your Answer:**

"The penalty curve is in sentiment_analyzer.py lines 80-85:

```python
if avg_frustration <= 3.0:
    base_penalty = avg_frustration * 5.0          # 0-15
elif avg_frustration <= 6.0:
    base_penalty = 15.0 + (avg_frustration - 3.0) * 10.0  # 15-45
else:
    base_penalty = 45.0 + (avg_frustration - 6.0) * 13.75  # 45-100
```

**Current design**: Non-linear curve (steep at high frustration)
- Low frustration (0-3): penalty climbs slowly (0-15)
- Medium frustration (3-6): penalty climbs faster (15-45)
- High frustration (6-10): penalty climbs fastest (45-100)
- Rationale: High frustration is disproportionately bad

**If we flatten it (linear)**:
```python
base_penalty = avg_frustration * 10  # Simple linear 0-100
```
- Impact: Calls with low frustration get higher penalties
- Calls with high frustration less penalized
- Final scores decrease across the board

**If we make it more aggressive**:
```python
base_penalty = (avg_frustration / 10) ** 2 * 100  # Quadratic
```
- Impact: High frustration cases severely penalized
- Sensitive calls scored much lower

**What doesn't break**:
- SLM override logic still applies (sarcasm detection independent)
- Journey bonus still applies (de-escalation reward independent)
- Database schema unchanged
- API contracts unchanged

**What might break**:
- Profile comparisons (old calls scored 60, new algorithm gives 40)
- Manager's historical baselines invalid
- Audit trail becomes inconsistent"

---

### Q7: "What if we remove the sentiment journey bonus?"

**Your Answer:**

"The journey bonus rewards de-escalation (turning angry customer around). In complaints context, this is critical.

**Current code** (sentiment_analyzer.py lines 106-123):
```python
if delta > 0.6:  # Strong improvement
    final_penalty = base_penalty * 0.4  # 60% reduction
elif delta > 0.3:  # Moderate improvement
    final_penalty = base_penalty * 0.7  # 30% reduction
```

**If removed**:
```python
final_penalty = base_penalty  # No bonus
```

**Immediate impact**:
- Calls with strong de-escalation lose 60% penalty reduction
- Example: base_penalty=80, with bonus→32, without→80
- Final score drops ~20 points
- De-escalation is no longer rewarded

**Business impact**:
- Complaints calls with happy endings score lower
- Agent who turns customer around gets penalized
- Contradicts complaints profile philosophy

**Why it's hard to remove**:
- Resolution analyzer might be neutral (net_score=0)
- Journey bonus is the PRIMARY BACKUP for resolution neutrality
- Without it, neutral resolution + low sentiment = very low score
- Agent could fix everything but if customer was initially frustrated → penalized anyway

**Alternative approach** (instead of removing):
- Make it configurable per profile
- Complaints: aggressive bonus (60%)
- Sales: no bonus or lower (30%)"

---

## SECTION 3: CONFIGURATION QUESTIONS

### Q8: "How does the configuration system work? What if client_profiles.json is missing?"

**Your Answer:**

"Two-layer config system in parameter_registry.py:

**Layer 1: File-based** (client_profiles.json)
```python
config_path = os.path.join(os.path.dirname(__file__), "config", "client_profiles.json")
try:
    with open(config_path, "r") as f:
        profiles = json.load(f)
except FileNotFoundError:
    profiles = {}  # Empty dict if file missing
```

**Layer 2: Built-in fallbacks** (hardcoded in Python)
```python
_FALLBACKS = {
    "sales": {
        "name": "Sales",
        "weights": {"talk_ratio": 15, "sentiment": 30, "empathy": 20, "resolution": 35},
        "ideal_talk_ratio": [0.60, 0.70]
    },
    "complaints": {
        "name": "Complaints",
        "weights": {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40},
        "ideal_talk_ratio": [0.40, 0.55]
    }
}
```

**Load order** (load_profile_config function):
```
1. Try to read client_profiles.json
2. If file exists AND key exists (e.g., "complaints") → use it
3. If file missing OR key missing → use _FALLBACKS["complaints"]
4. If invalid JSON → caught, logged, use _FALLBACKS
```

**If client_profiles.json is missing**:
- App still starts ✓
- /analyze uses default weights ✓
- Logs warning: \"Profile 'complaints' not found in config—using built-in fallback\"
- All endpoints work normally ✓

**Example missing file scenario**:
```
File missing → profiles = {}
load_profile_config("complaints")
  → "complaints" not in profiles
  → Return _FALLBACKS["complaints"]
  → Weights: {talk_ratio: 5, sentiment: 35, empathy: 20, resolution: 40}
  → No crash
```

**If JSON file is malformed**:
```python
try:
    profiles = json.load(f)
except json.JSONDecodeError:  # Syntax error in JSON
    logger.error(f\"Config file not found: {config_path}\")
    profiles = {}
    # Falls through to _FALLBACKS
```

**How to add a new profile**:
1. Edit client_profiles.json:
   ```json
   {
     \"complaints\": {...},
     \"technical_support\": {
       \"name\": \"Technical Support\",
       \"weights\": {\"talk_ratio\": 10, \"sentiment\": 20, \"empathy\": 25, \"resolution\": 45},
       \"ideal_talk_ratio\": [0.50, 0.70]
     }
   }
   ```
2. Frontend calls /api/test-analysis with profile=\"technical_support\"
3. Backend loads via load_profile_config("technical_support")
4. Weights applied in scoring engine
5. No code changes needed!"

---

### Q9: "What if weights don't sum to 100?"

**Your Answer:**

"Automatically normalized. In scoring_engine.py lines 86-90:

```python
weight_sum = sum(relevant_weights.values())
if weight_sum <= 0:
    weight_sum = 1.0  # Prevent division by zero

normalized_weights = {k: (v / weight_sum) * 100 for k, v in relevant_weights.items()}
```

**Example 1: Weights sum to 75**
```
Input: {talk_ratio: 5, sentiment: 26, empathy: 15, resolution: 29}
Sum = 75

Normalized:
  talk_ratio: (5 / 75) * 100 = 6.67
  sentiment: (26 / 75) * 100 = 34.67
  empathy: (15 / 75) * 100 = 20
  resolution: (29 / 75) * 100 = 38.67
Sum = 100 ✓

Proportions preserved ✓
```

**Example 2: Custom weights from frontend**
```
Frontend sends: {talk_ratio: 10, sentiment: 20, empathy: 10, resolution: 30}
Sum = 70

Normalized: [14.29, 28.57, 14.29, 42.86]
Proportions preserved, key point (resolution emphasized)
```

**Why this matters**:
- Users might set arbitrary weights (not thinking about sum)
- Could come from buggy frontend slider logic
- Normalization ensures proportions still make sense

**What breaks if we DON'T normalize**:
- Final score would be inflated (only 75% penalty applied)
- Examples with sum=75:
  ```
  If we skip normalization:
    total_penalty = 0.05*35 + 0.26*60 + ...  (using 75% not 100%)
    final_score = 100 - (partial_penalty)  → artificially high
  ```
- Scores become incomparable across analyses
- Audit trail breaks (old=100-scale, new=75-scale)"

---

## SECTION 4: TEST & VERIFICATION QUESTIONS

### Q10: "How do I test this without Whisper or Ollama running?"

**Your Answer:**

"Use /api/test-analysis endpoint (manual transcript mode).

**Endpoint**: POST /api/test-analysis
**Request**:
```json
{
  \"transcript\": [
    {\"speaker\": \"Agent\", \"start\": 0.0, \"end\": 5.2, \"text\": \"Hello, how can I help?\"},
    {\"speaker\": \"Customer\", \"start\": 5.4, \"end\": 10.1, \"text\": \"My billing is messed up.\"}
  ],
  \"weights\": {\"talk_ratio\": 5, \"sentiment\": 35, \"empathy\": 20, \"resolution\": 40},
  \"profile\": \"complaints\"
}
```
**Response**: CallScore object (same as /analyze analysis.analysis)

**What's skipped**:
- No Whisper (you provide transcript directly)
- No speaker attribution (you label manually)

**What still happens**:
- All 5 analyzers run (sentiment, empathy, resolution, talk_ratio, slm_sentiment)
- SLM override logic applied
- Scoring engine calculates final_score
- NOT saved to database (test mode only)

**Why this is useful**:
1. Test scoring logic without audio
2. Debug analyzer behavior with known transcript
3. Test different profiles/weights quickly
4. Validate SLM override logic with controlled inputs

**Example test case**:
```python
# Test: Customer starts angry, ends happy (journey bonus)
transcript = [
  {\"speaker\": \"Customer\", \"text\": \"This is the worst system ever\"},
  {\"speaker\": \"Agent\", \"text\": \"Let me help fix that...\"},
  {\"speaker\": \"Customer\", \"text\": \"Actually it works perfectly now!\"}
]

POST /api/test-analysis
# Expected: sentiment journey_bonus_level = \"strong\"
# Variation: final_score higher than if customer stayed angry
```"

---

### Q11: "What if we change one analyzer's penalty output type or scale?"

**Your Answer:**

"Example: Change sentiment analyzer to return penalty as 0-10 instead of 0-100.

**Current**:
```python
return ParameterResult(
    penalty=42.0  # 0-100 scale
)
```

**Modified**:
```python
return ParameterResult(
    penalty=4.2  # 0-10 scale
)
```

**What breaks**:
1. **Scoring formula fails**:
   ```python
   contribution = -(weight * penalty / 100)
   # If penalty=4.2 instead of 42.0:
   #   contribution = -(35 * 4.2 / 100) = -1.47
   #   instead of -(35 * 42 / 100) = -14.7
   # Score is 13.23 points TOO HIGH ✓ BREAKS
   ```

2. **Database comparisons break**:
   - Old calls: sentiment_score=42.0
   - New calls: sentiment_score=4.2
   - Can't compare (different scales)

3. **Interpretation logic breaks**:
   ```python
   if param.penalty <= 15:  # Assumed 0-100 scale
       strengths.append(param.display_name)
   # Now works for all new results (4.2 is always ≤ 15)
   # Interpretation wrong
   ```

**How to prevent**:
- Pydantic model defines scale expectation:
  ```python
  class ParameterResult(BaseModel):
      penalty: float  # Must be 0-100, but type system doesn't enforce
  ```
- Add docstring:
  ```python
  penalty: float  # 0-100 scale (0=perfect, 100=terrible)
  ```
- But this is fragile (not type-checked)

**Better solution**:
- Create strict enum or Bounded type:
  ```python
  class Penalty(BaseModel):
      value: float = Field(ge=0, le=100)  # Pydantic validation
  ```"

---

### Q12: "How is this application tested? What tests exist?"

**Your Answer:**

"Honest answer: **Minimal formal tests**. This is a growing codebase (MVP stage).

**What SHOULD exist** (for production):

1. **Unit Tests: Speaker Attribution**
   ```python
   def test_identify_speakers():
       segments = [
           {\"start\": 0, \"end\": 2, \"text\": \"We have a great solution\"},
           {\"start\": 2.5, \"end\": 5, \"text\": \"I'm frustrated\"}
       ]
       result = identify_speakers(segments)
       assert result[0][\"speaker\"] == \"Agent\"
       assert result[1][\"speaker\"] == \"Customer\"
   ```

2. **Unit Tests: Sentiment Analyzer**
   ```python
   def test_sentiment_journey_bonus():
       transcript = [
           {\"speaker\": \"Customer\", \"text\": \"This is terrible!\"},
           {\"speaker\": \"Customer\", \"text\": \"Actually that works great!\"}
       ]
       result = sentiment_analyzer.analyze(transcript, {}, vader)
       assert result.metadata[\"journey_bonus_level\"] == \"strong\"
       assert result.penalty < base_penalty  # Penalty reduced
   ```

3. **Integration Test: Full Pipeline**
   ```python
   def test_full_analyze():
       audio_file = open(\"test_audio.wav\", \"rb\")
       response = client.post(\"/analyze\", files={\"file\": audio_file})
       assert response.status_code == 200
       assert \"analysis\" in response.json()
       assert 0 <= response.json()[\"analysis\"][\"final_score\"] <= 100
   ```

4. **Manual Test Cases**:
   - Happy path: Upload audio → transcribe → analyze → save
   - Ollama unavailable: Verify fallback to penalty=50
   - Bad weights JSON: Verify error handling
   - Empty transcript: Verify neutral scores

**What exists now**:
- Manual testing via browser and curl
- /api/test-analysis for scoresheet validation
- Logs for debugging

**What's missing**:
- Automated test suite
- CI/CD pipeline
- Load testing
- Security testing (no auth)
- Edge case coverage"

---

## SECTION 5: SWAGGER & DOCUMENTATION QUESTIONS

### Q13: "Where's the API documentation? How does Swagger work here?"

**Your Answer:**

"FastAPI auto-generates Swagger documentation from code.

**Access points**:
- Interactive Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Raw OpenAPI schema: http://localhost:8000/openapi.json

**How it's generated** (automatic):
1. FastAPI reads endpoint signatures:
   ```python
   @app.post(\"/analyze\")
   async def analyze_audio(file: UploadFile = File(...), weights: Optional[str] = Form(None)) -> Dict:
   ```

2. Parses type hints and Pydantic models:
   - UploadFile → file input
   - Optional[str] → string or null
   - -> Dict → response is dictionary

3. Reads docstring:
   ```python
   \"\"\"
   Analyze an audio file: transcribe + run parameter scoring.
   
   Args:
       file: Audio file (.wav, .mp3, etc.)
       weights: Optional JSON string of custom weights
   \"\"\"
   ```
   Docstring appears in Swagger description

4. Generates Swagger UI at /docs

**Example: /analyze endpoint in Swagger**:
```
POST /analyze

Parameters:
  - file (body, required): Upload audio file
  - weights (body, optional): JSON string like {"talk_ratio":10,...}

Response:
  200:
    {
      \"filename\": \"string\",
      \"file_size_bytes\": int,
      \"transcription\": {...},
      \"analysis\": {...},
      \"call_id\": int
    }
```

**How to improve Swagger docs**:
1. Add detailed docstrings:
   ```python
   @app.post(\"/analyze\")
   async def analyze_audio(...):
       \"\"\"
       Analyze an audio file.
       
       This endpoint accepts audio in any format supported by Whisper
       (WAV, MP3, M4A, etc), transcribes it, attributes speakers,
       runs 5 parallel analyzers, and returns a scored result.
       
       Args:
           file: Audio file (multipart/form-data)
           weights: Optional JSON string or null. Example: '{\"talk_ratio\":5,...}'
       
       Returns:
           CallScore with breakdown, analyzer_results, and call_id.
           See /api/history/{id} for full result schema.
       \"\"\"
   ```

2. Add response model types:
   ```python
   @app.post(\"/analyze\")
   async def analyze_audio(...) -> AnalyzeResponse:  # <- Typed response
       ...
   
   class AnalyzeResponse(BaseModel):
       filename: str
       file_size_bytes: int
       transcription: TranscriptionResult
       analysis: CallScore
       call_id: int
   ```

3. Add field descriptions:
   ```python
   class AnalyzeResponse(BaseModel):
       filename: str = Field(..., description=\"Original uploaded filename\")
       file_size_bytes: int = Field(..., description=\"Audio file size in bytes\")
   ```

**Current status**:
- ✅ Endpoints documented
- ✅ Swagger auto-accessible
- ⚠️ Response schemas not fully typed
- ⚠️ Missing detailed parameter descriptions
- ⚠️ No error response examples"

---

### Q14: "If I call /api/rescore, what data format do I need?"

**Your Answer:**

"POST /api/rescore with RescoreRequest:

```python
class RescoreRequest(BaseModel):
    analyzer_results: List[dict]
    weights: Dict[str, float]
```

**Required fields**:
1. **analyzer_results**: Array of analyzer result dicts
   - Source: analyzer_results from /analyze response
   - Format: Each dict must have:
     ```json
     {
       \"name\": \"talk_ratio\",  // or sentiment, empathy, resolution
       \"display_name\": \"Talk-to-Listen Ratio\",
       \"icon\": \"🎙️\",
       \"raw_value\": 6.5,
       \"score\": 65.0,
       \"penalty\": 35.0,
       \"metadata\": {...}
     }
     ```
   - These are cached from original /analyze call

2. **weights**: Dict mapping param names to weights
   - Example: {\"talk_ratio\": 5, \"sentiment\": 35, \"empathy\": 20, \"resolution\": 40}
   - Sum should be 100 (auto-normalized if not)
   - Keys must match analyzer result names

**Example request**:
```bash
curl -X POST http://localhost:8000/api/rescore \
  -H \"Content-Type: application/json\" \
  -d '{
    \"analyzer_results\": [
      {\"name\": \"talk_ratio\", \"display_name\": \"...\", \"raw_value\": 6.5, \"score\": 65.0, \"penalty\": 35.0, \"metadata\": {}},
      {\"name\": \"sentiment\", \"display_name\": \"...\", \"raw_value\": 7.0, \"score\": 40.0, \"penalty\": 60.0, \"metadata\": {}},
      ...
    ],
    \"weights\": {\"talk_ratio\": 10, \"sentiment\": 30, \"empathy\": 20, \"resolution\": 40}
  }'
```

**Response**:
```json
{
  \"final_score\": 52.3,
  \"breakdown\": {...},
  \"profile_used\": \"Sales\",
  \"interpretation\": \"...\",
  \"metadata\": {}
}
```

**Error cases**:
- Missing analyzer_results: 422 Validation Error
- Empty weights: 422 Validation Error
- analyzer_results with missing fields: 422 Validation Error
- weights don't match analyzer names: Silently skipped (normalized to matching params)"

---

## SECTION 6: EDGE CASES & GOTCHAS

### Q15: "What happens if an analyzer throws an exception?"

**Your Answer:**

"In _run_analyzers (main.py lines 78-115), each analyzer is wrapped in try/except:

```python
def _run_analyzers(transcript, profile_config):
    results = []
    
    # 1. Talk Ratio
    try:
        results.append(talk_ratio_analyzer.analyze(transcript, profile_config))
    except Exception as e:
        logger.error(f\"Talk ratio analyzer failed: {e}\")
        # NO fallback added; analyzer is just skipped
    
    # 2. Sentiment
    try:
        results.append(sentiment_analyzer.analyze(transcript, profile_config, vader_analyzer))
    except Exception as e:
        logger.error(f\"Sentiment analyzer failed: {e}\")
        # Skipped
    
    # 3+4+5. SLM
    try:
        slm_results = slm_analyzer.analyze(transcript, profile_config)
        results.extend(slm_results)
    except Exception as e:
        logger.error(f\"SLM analyzer failed entirely: {e}\")
        # Skipped
    
    return results
```

**What happens**:
- Analyzer throws exception → caught → logged
- Result NOT added to results list
- Pipeline continues with remaining analyzers
- /analyze endpoint doesn't crash

**Then in scoring_engine.py line 71-84**:
```python
results_by_name = {r.name: r for r in analyzer_results}
relevant_weights = {k: v for k, v in weights.items() if k in results_by_name}

# If 3 analyzers failed and only talk_ratio returned:
# relevant_weights = {\"talk_ratio\": 5}  # (only this param)
# Weights automatically renormalized to 100
```

**Final score impact**:
- Score calculated with available parameters
- Missing parameters don't contribute
- Example: if sentiment totally fails but empathy works:
  - Empathy weight boosted: 20 → 50 (of total)
  - Score relies more on empathy than intended

**This is NOT ideal**, but it's graceful degradation. Better than crashing.

**Example scenario**:
```
Original weights: {talk_ratio: 5, sentiment: 35, empathy: 20, resolution: 40}
Sentiment analyzer crashes

Results: [talk_ratio, empathy, resolution]
Relevant weights: {talk_ratio: 5, empathy: 20, resolution: 40}  (sum=65)

Normalized weights: {talk_ratio: 7.7, empathy: 30.8, resolution: 61.5}

Final score changed (sentiment was 35% → now 0%)
```

**Why not use neutral fallback**?
- Would be better: sentiment returns penalty=50 instead of failing
- But current design is acceptable for MVP"

---

### Q16: "If I call an endpoint with wrong parameter types, what happens?"

**Your Answer:**

"Pydantic validation catches it immediately.

**Example 1: Send string instead of int for weights**:
```json
{
  \"transcript\": [...],
  \"weights\": \"talk_ratio=5&sentiment=35\"  // Should be Dict, not string
}
```
**Response**: 422 Unprocessable Entity
```json
{
  \"detail\": [
    {
      \"loc\": [\"body\", \"weights\"],
      \"msg\": \"value is not a valid dict\",
      \"type\": \"type_error.dict\"
    }
  ]
}
```

**Example 2: Send string as timestamp in /api/test-analysis**:
```json
{
  \"transcript\": [
    {\"speaker\": \"Agent\", \"start\": 0.0, \"end\": \"five\", \"text\": \"...\"}  // end should be float
  ]
}
```
**Response**: 422 Unprocessable Entity
```json
{
  \"detail\": [
    {
      \"loc\": [\"body\", \"transcript\", 0, \"end\"],
      \"msg\": \"value is not a valid float\",
      \"type\": \"type_error.float\"
    }
  ]
}
```

**Why this is good**:
- Invalid data rejected BEFORE pipeline runs
- No garbage calculations
- Clear error message tells user what's wrong

**The 4xx response means**: \"Your input is malformed; fix it on your end\"

---

### Q17: "What if the transcript is enormous (million segments)?"

**Your Answer:**

"Performance degrades, but doesn't crash:

**Memory impact**:
- List of dicts in RAM
- Each segment: ~200 bytes (speaker, text, start, end, metadata)
- 1M segments = ~200MB RAM
- Pydantic model allocation: extra copy = ~200MB
- Total: ~400-500MB

**Computation**:
1. **Talk ratio**: O(n) — loops through all segments twice (agent + customer)
   - 1M segments = ~1-2ms
2. **Sentiment**: O(n) — VADER on each customer segment
   - 50% customer = 500k segments
   - 500k VADER calls = ~5-10 seconds
3. **SLM**: One HTTP call (full transcript as text)
   - Text length maybe 10-50MB (if transcript is large)
   - Ollama processes it: ~10-60 seconds

**Total**: ~15-60 seconds (dominated by VADER + Ollama)

**What breaks first**:
- Request timeout (FastAPI default: 60s)
- Memory limit (if deployment has cap)
- Ollama window context limit (phi3.5 ~4k tokens = ~16k chars)

**Why 1M segments unlikely**:
- Even 1-hour call: ~250-500 segments (depends on pauses)
- 1M segments = ~50-100 hours of audio
- Most deployments won't see this

**What should be added**:
```python
if len(transcript) > 10000:  # Arbitrary limit
    raise Exception(\"Transcript too large (>10k segments)\")
```"

---

## FINAL PREPARATION

### Things to Memorize (For Rapid Fire Q&A)

1. **The 4 parameters & their sources**:
   - Talk ratio: from transcript timing
   - Sentiment: from VADER on customer segments
   - Empathy: from Ollama LLM
   - Resolution: from Ollama LLM

2. **The scoring formula**:
   ```
   final_score = 100 - Σ(normalized_weight × penalty / 100)
   ```

3. **Critical paths** (if these fail, whole system fails):
   - Whisper (transcription)
   - Speaker attribution logic
   - Scoring engine formula

4. **Graceful fallbacks** (if these fail, accuracy reduced but continues):
   - Ollama/SLM (replaced with penalty=50)
   - VADER (replaced with penalty=50)
   - Database (analysis returned anyway, no history)

5. **Configuration hierarchy**:
   - File (client_profiles.json)
   - Fallback (hardcoded in code)
   - Normalization (auto-scale to 100)

### Practice Answering:

- "Walk me through audio → score"
- "What happens if Ollama is down?"
- "How are weights used in the scoring formula?"
- "What if speaker attribution is completely wrong?"
- "Show me the penalty curve for sentiment"
- "What breaks if we change X analyzer?"
- "How is the database schema designed?"
- "Explain the SLM override logic"

---

**Good luck! You've got this. 🚀**
