# NanoVox: Deep Dive Code Review Guide

**Review Date**: 2026-04-16  
**Application**: NanoVox Call Quality Analysis Platform  
**Architecture**: Python FastAPI Backend + React Frontend  
**Database**: SQLite with WAL mode for concurrent reads

---

## TABLE OF CONTENTS

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Audio Data Flow (Complete Journey)](#2-audio-data-flow-complete-journey)
3. [Backend Function Reference](#3-backend-function-reference)
4. [API Endpoints](#4-api-endpoints)
5. [Configuration System](#5-configuration-system)
6. [Parameter Registry & Scoring](#6-parameter-registry--scoring)
7. [Dependency Analysis: What Breaks If...](#7-dependency-analysis-what-breaks-if)
8. [Testing Strategy](#8-testing-strategy)
9. [Swagger/OpenAPI Documentation](#9-swaggeropenapi-documentation)

---

## 1. SYSTEM ARCHITECTURE OVERVIEW

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                      │
│  - FileUpload.jsx: Audio/JSON input handling                 │
│  - ProfileSelector.jsx: Weight configuration                 │
│  - AnalysisDashboard.jsx: Results visualization              │
│  - App.jsx: Main orchestration & state management            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP Calls
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI/Python)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ main.py - FastAPI Application                         │  │
│  │  - Startup: Load Whisper + VADER models              │  │
│  │  - POST /analyze - Core audio pipeline                │  │
│  │  - POST /api/test-analysis - Manual transcript test   │  │
│  │  - GET /api/history - Fetch past calls                │  │
│  │  - GET /api/report/{call_id} - PDF generation         │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Analyzer Modules (PIPELINE)                           │  │
│  │  1. talk_ratio_analyzer.py - Agent vs Customer ratio │  │
│  │  2. sentiment_analyzer.py - VADER-based frustration   │  │
│  │  3. slm_analyzer.py - Ollama phi3.5 (Empathy+Res.)   │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │ Support Modules                                       │  │
│  │  - scoring_engine.py - Weighted score calculation    │  │
│  │  - parameter_registry.py - Configuration & weights   │  │
│  │  - database.py - SQLite persistence                  │  │
│  │  - models.py - Pydantic data schemas                 │  │
│  │  - report_generator.py - PDF output                  │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐        ┌─────────┐      ┌──────────┐
   │ Whisper │        │  VADER  │      │Ollama    │
   │ (tiny)  │        │Sentiment│      │(phi3.5)  │
   │         │        │         │      │          │
   │CPU-only │        │Python   │      │REST API  │
   └─────────┘        │Lib      │      │localhost:│
                      └─────────┘      │11434     │
                                       └──────────┘
        ▼
   ┌─────────────────┐
   │  nanovox.db     │
   │  SQLite WAL     │
   └─────────────────┘
```

### Key Design Decisions

| Component | Choice | Why |
|-----------|--------|-----|
| **Speech-to-Text** | Whisper (OpenAI) | Cheap, fast on CPU, handles timestamps |
| **Sentiment Analysis** | VADER Inline | Lightweight, no remote deps, explainable |
| **Empathy/Resolution** | Ollama phi3.5 | Local LLM, no API costs, context-aware |
| **Scoring** | Pydantic models | Type safety, schema validation |
| **Database** | SQLite WAL | Zero-config, concurrent reads, dev-friendly |
| **Frontend** | React + Vite | Hot reload, modern tooling |

---

## 2. AUDIO DATA FLOW (COMPLETE JOURNEY)

This is the critical path that answers "if I upload audio, what happens?"

### Step-by-Step Flow (POST /analyze)

#### **Step 1: Audio Upload & Ingestion**
```
Client uploads: audio.wav (multipart/form-data)
├─ File received in FastAPI: file: UploadFile
├─ Custom weights? Form parameter "weights" (optional JSON string)
├─ Save to tempfile (temp_file_path = /tmp/xyz.wav)
└─ File size logged for diagnostics

**Key Code**: main.py lines 282-317
```

**Data Format At This Point:**
- Input: Binary WAV/MP3 file bytes
- Location: Temporary filesystem path
- Size: Logged (for error diagnosis)

---

#### **Step 2: Transcription via Whisper**
```
Load pre-cached Whisper model (tiny)
├─ Model loaded at startup: whisper.load_model("tiny")
├─ Transcribe audio file: result = whisper_model.transcribe(temp_file_path)
├─ Output structure:
│  {
│    "text": "Full conversation text...",
│    "segments": [
│      {
│        "id": 0,
│        "start": 0.0,
│        "end": 5.2,
│        "text": "Hello, how can I help?",
│        "confidence": 0.95  (approx)
│      },
│      ...
│    ]
│  }
└─ Whisper assigns NO speaker labels (this is critical)

**Key Code**: main.py lines 319-322
**Duration**: ~1-5s for 10min audio (CPU-dependent)
**Model Size**: ~140MB (tiny model)
```

**Data Format At This Point:**
```json
{
  "text": "Hello customer. How can I help you?...",
  "segments": [
    {"start": 0.0, "end": 5.2, "text": "...", "id": 0},
    ...
  ]
}
```

---

#### **Step 3: Speaker Attribution (Global Weighted Voting)**
```
Algorithm: Global Weighted Voting System (novel approach)
├─ Input: whisper_segments (no speaker labels)
├─ Step 3a: Assign alternating speaker IDs (0 or 1)
│   └─ Based on pause detection (gap > 0.3s between segments)
├─ Step 3b: Score each speaker globally
│   ├─ AGENT_SIGNALS: ["speaking", "timeline", "budget", "solution", ...]
│   ├─ CUSTOMER_SIGNALS: ["problem", "expensive", "frustrated", ...]
│   └─ Count matches: speaker[0] score += agent_matches - customer_matches
├─ Step 3c: Apply structural bonuses
│   ├─ Anchor bonus: +12 points to first speaker (agents usually initiate)
│   └─ Closer bonus: +6 points to last speaker
├─ Step 3d: Assign labels
│   └─ If scores[0] >= scores[1]: {0→Agent, 1→Customer}
│        Else: {0→Customer, 1→Agent}
└─ Output: transcript with speaker labels

**Key Code**: main.py lines 325-419
**Signal Library**: 24 AGENT + 13 CUSTOMER keywords
```

**Data Format At This Point:**
```json
[
  {
    "speaker": "Agent",
    "start": 0.0,
    "end": 5.2,
    "text": "Hello, how can I help?"
  },
  {
    "speaker": "Customer",
    "start": 5.4,
    "end": 10.1,
    "text": "I have a billing issue."
  },
  ...
]
```

🔴 **CRITICAL DEPENDENCY**: Speaker attribution **has zero fallback**. If this is 100% wrong, all downstream scoring is skewed. Mitigations:
- Pause detection helps (gap > 0.3s)
- Anchor/closer bonuses reduce false positives
- User can manually override in test mode (/api/test-analysis)

---

#### **Step 4: Run Analyzer Pipeline**
```
_run_analyzers(transcript, profile_config):
├─ **1. Talk Ratio Analyzer**
│  ├─ Measures: Agent speaking time vs Customer speaking time
│  ├─ Output: raw_value (0-10), penalty (0-100)
│  └─ Fallback: If no segments → penalty=50
│
├─ **2. Sentiment Analyzer (VADER)**
│  ├─ Input: Customer segments only
│  ├─ Process:
│  │  ├─ Run VADER on each segment: compound score (-1 to +1)
│  │  ├─ Convert to frustration: (1 - compound) * 5 (0-10 scale)
│  │  ├─ Apply tiered penalty (non-linear):
│  │  │  - frustration ≤ 3.0  → penalty = frustration * 5.0 (0-15)
│  │  │  - 3.0 < frustration ≤ 6.0 → penalty = 15 + (f-3)*10 (15-45)
│  │  │  - frustration > 6.0  → penalty = 45 + (f-6)*13.75 (45-100)
│  │  └─ Sentiment journey bonus: If sentiment improved by >0.6 → 60% penalty reduction
│  └─ Output: raw_value (avg frustration), penalty, metadata
│
├─ **3. SLM Analyzer (Empathy + Resolution)**
│  ├─ Input: Full transcript
│  ├─ Ollama Call: POST to http://localhost:11434/api/generate
│  ├─ Model: phi3.5:mini
│  ├─ Timeout: 90 seconds (generous for CPU)
│  ├─ Receives JSON response:
│  │  {
│  │    "empathy_score": 1-10,
│  │    "empathy_reason": "string",
│  │    "resolution_score": 0-10,
│  │    "resolution_reason": "string",
│  │    "overall_sentiment": "Positive|Neutral|Negative"
│  │  }
│  ├─ Converts to 0-100 penalty scale:
│  │  - empathy_penalty = (10 - score) * 10
│  │  - resolution_penalty = (10 - score) * 10
│  └─ Fallback if Ollama down: All three return penalty=50
│
└─ **SLM Override Rule** (post-pipeline):
   ├─ If SLM says "Negative" BUT VADER > 40 → Force VADER to 15 (capturable sarcasm)
   ├─ If SLM says "Positive" BUT VADER < 50 → Force VADER to 85 (valid positivity)
   └─ Logs all overrides for audit trail

**Key Code**: main.py lines 78-157
**Total Duration**: ~3-5s (dominated by Ollama)
```

**Data Format At This Point:**
```python
analyzer_results = [
  ParameterResult(
    name="talk_ratio",
    display_name="Talk-to-Listen Ratio",
    raw_value=6.5,
    score=65.0,
    penalty=35.0,
    metadata={...}
  ),
  ParameterResult(name="sentiment", ...),
  ParameterResult(name="empathy", ...),
  ParameterResult(name="resolution", ...),
  ParameterResult(name="slm_sentiment", ...)  # metadata carrier only
]
```

---

#### **Step 5: Calculate Weighted Final Score**
```
calculate_score(analyzer_results, weights, profile_name):
├─ Input:
│  ├─ analyzer_results: List[ParameterResult]
│  ├─ weights: {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40}
│  └─ profile_name: "complaints"
├─ Process:
│  ├─ Filter weights to match available analyzers
│  ├─ Normalize weights: if weights sum≠100 → scale to 100
│  ├─ For each parameter:
│  │  └─ contribution = -(weight * penalty / 100)
│  ├─ Sum weighted penalties
│  └─ final_score = max(0, min(100, 100 - total_weighted_penalty))
├─ Generate interpretation:
│  └─ 1-2 sentence summary based on score bands
└─ Output: CallScore pydantic model

Formula:
  final_score = 100 - Σ(normalized_weight_i * penalty_i / 100)

Example:
  If weights (after normalization):
    talk_ratio: 5%   × penalty 35% = 1.75 points lost
    sentiment: 35%   × penalty 60% = 21 points lost
    empathy: 20%     × penalty 40% = 8 points lost
    resolution: 40%  × penalty 50% = 20 points lost
  ────────────────────────────────────
  final_score = 100 - 50.75 = 49.25/100

**Key Code**: scoring_engine.py lines 54-131
```

**Data Format At This Point:**
```json
{
  "final_score": 49.25,
  "profile_used": "Complaints",
  "interpretation": "Below-average call needing attention. Needs improvement in talk-to-listen ratio, sentiment.",
  "breakdown": {
    "talk_ratio": {
      "raw_value": 6.5,
      "score": 65.0,
      "penalty": 35.0,
      "weight": 5.0,
      "contribution": -1.75
    },
    ...
  }
}
```

---

#### **Step 6: Save to Database**
```
save_call(filename, file_size_bytes, response, weights):
├─ Extract from response:
│  ├─ Final score, profile used, interpretation
│  ├─ Individual parameter scores (from breakdown)
│  ├─ Resolution status label (e.g., "Resolved", "Escalated")
│  ├─ Transcript segments (for call_duration calculation)
│  └─ Full JSON blobs (for detailed drill-down)
├─ Insert into call_history table:
│  ├─ Scalar columns: id, filename, analyzed_at, final_score, ...
│  ├─ JSON blobs: analysis_json, transcript_json, insights_json, ...
│  └─ Indices: On analyzed_at (DESC), final_score, agent_name
├─ Return: call_id (row ID)
└─ DB accessed via nanovox.db (SQLite WAL)

**Key Code**: database.py lines 85-174
```

---

#### **Step 7: Return Response to Frontend**
```
{
  "filename": "call_20240315.wav",
  "file_size_bytes": 2048000,
  "transcription": {
    "text": "Full concatenated text...",
    "transcript": [
      {"speaker": "Agent", "start": 0.0, "end": 5.2, "text": "..."},
      {...}
    ]
  },
  "insights": {
    "sentiment": "neutral",
    "sentiment_score": 0.0,
    ...  (legacy stub)
  },
  "analysis": {
    "final_score": 49.25,
    "breakdown": {...},
    "profile_used": "Sales",
    "interpretation": "...",
    "analyzer_results": [...]  (cached for rescoring)
  },
  "call_id": 42
}
```

---

### Complete Data Flow Diagram

```
Audio File (.wav)
     ↓
[Whisper via CPU]
     ↓
Raw segments + text (NO speaker labels)
     ↓
[Global Speaker Attribution]
     ↓
Transcript with speakers (Agent/Customer)
     ↓
        ├──→ [Talk Ratio] → penalty
        ├──→ [VADER Sentiment] → penalty + sentiment_journey_bonus
        ├──→ [Ollama phi3.5 (SLM)]
        │    ├──→ Empathy score → penalty
        │    ├──→ Resolution score → penalty
        │    └──→ True sentiment → override signal
        └──→ [SLM Override Logic]
     ↓
All analyzer results + metadata
     ↓
[Profile Config] → Load weights (talk_ratio, sentiment, empathy, resolution)
     ↓
[Scoring Engine]
     ├─ Normalize weights to sum=100
     ├─ Calculate weighted penalties
     └─ final_score = 100 - total_weighted_penalty
     ↓
CallScore object (with breakdown + interpretation)
     ↓
[Database] → Save all results to nanovox.db
     ↓
Return Response JSON to Frontend
     ↓
Frontend renders dashboard with score + parameters
```

---

## 3. BACKEND FUNCTION REFERENCE

### `main.py`

#### **@app.on_event("startup")**
```python
async def load_models():
    """Load ML models at startup"""
```
- **When**: Called once when FastAPI server starts
- **What**: 
  - Loads Whisper (tiny) model (~140MB)
  - Initializes VADER SentimentIntensityAnalyzer
  - Initializes SQLite database
- **Why**: Global state; don't reload every request
- **Failure Mode**: If Whisper fails, entire app won't start
- **Duration**: 30-60 seconds first boot

#### **def _run_analyzers(transcript, profile_config)**
```python
results = _run_analyzers(transcript, profile_config)
```
- **Purpose**: Orchestrate all 5 analysis modules
- **Input**: 
  - `transcript`: List of dicts with speaker/text/start/end
  - `profile_config`: Dict with profile name + config
- **Process**:
  1. Try talk_ratio_analyzer
  2. Try sentiment_analyzer
  3. Try slm_analyzer (returns 3 results: empathy, resolution, slm_sentiment)
  4. Apply SLM override logic if both VADER+SLM present
- **Output**: List[ParameterResult]
- **Error Handling**: Each analyzer wrapped in try/except; continues on failure
- **Critical Path**: YES — if ALL analyzers fail, score is 50 (neutral)

#### **@app.post("/analyze")**
```python
async def analyze_audio(file: UploadFile = File(...), weights: Optional[str] = Form(None))
```
- **Purpose**: Main endpoint — audio upload + full pipeline
- **Input**:
  - `file`: Audio file (wav/mp3/m4a/etc)
  - `weights` (optional): JSON string like `{"talk_ratio":10,"sentiment":20,...}`
- **Process**:
  1. Save file to temp location
  2. Transcribe with Whisper
  3. Attribute speakers (Global Weighted Voting)
  4. Run analyzers via _run_analyzers()
  5. Calculate score via scoring_engine
  6. Save to database
  7. Return full response
- **Response**: JSON with transcription + analysis + analyzer_results
- **Key Code**: main.py lines 282-492
- **Duration**: 10-30s depending on audio length
- **Errors**: 
  - Bad file → logged
  - Ollama down → empathy/resolution fallback to penalty=50
  - Database save failure → doesn't fail request (logged)

#### **@app.post("/api/test-analysis")**
```python
async def test_analysis(request: TestAnalysisRequest)
```
- **Purpose**: Bypass Whisper; test scoring pipeline with manual transcript
- **Input**: 
  ```python
  class TestAnalysisRequest:
      transcript: List[dict]  # [{speaker: "Agent", start: 0, end: 5, text: "..."}]
      weights: Optional[Dict[str, float]]
      profile: Optional[str]  # "complaints" or "sales"
  ```
- **Use Case**: Unit testing, debugging scoring logic without audio file
- **Missing**: No speaker attribution (you provide manually)
- **Key Code**: main.py lines 206-262

#### **@app.post("/api/rescore")**
```python
async def rescore(request: RescoreRequest) -> Dict
```
- **Purpose**: Recalculate score with different weights (no re-analysis)
- **Input**: 
  - `analyzer_results`: Array of analyzer results (cached from /analyze)
  - `weights`: New weights to apply
- **Use Case**: Frontend slider updates → instant rescore
- **Duration**: <100ms (pure calculation)

#### **@app.get("/api/history")**
```python
async def api_history(limit: int = 10, offset: int = 0)
```
- **Purpose**: Fetch recent analyzed calls
- **Output**: List of call summaries (most recent first)

#### **@app.get("/api/history/{call_id}")**
#### **@app.get("/api/stats")**
#### **@app.get("/api/report/{call_id}")**
- See API Endpoints section below

---

### `modules/talk_ratio_analyzer.py`

#### **analyze(transcript, profile_config)**
```python
def analyze(transcript: list, profile_config: dict) -> ParameterResult:
```
- **Purpose**: Measure agent vs customer speaking time
- **Input**: Transcript with speaker labels
- **Logic**:
  1. Sum all "Agent" segment durations → agent_time
  2. Sum all "Customer" segment durations → customer_time
  3. Calculate ratio = agent_time / (agent_time + customer_time)
  4. Score depends on profile ideal_talk_ratio:
     - Complaints: ideal [0.40, 0.55] (customer talks more)
     - Sales: ideal [0.60, 0.70] (agent should lead)
  5. If ratio outside ideal range → penalty increases non-linearly
- **Output**: ParameterResult with penalty (0-100)
- **Fallback**: If no segments → penalty=50
- **Key Code**: backend/modules/talk_ratio_analyzer.py

---

### `modules/sentiment_analyzer.py`

#### **analyze(transcript, profile_config, vader_analyzer)**
```python
def analyze(transcript, profile_config, vader_analyzer) -> ParameterResult:
```
- **Purpose**: Measure customer frustration using VADER
- **Input**: Transcript, VADER analyzer instance
- **Logic**:
  1. Filter customer segments only
  2. For each customer segment:
     - Get VADER compound score (-1 to +1)
     - Convert to frustration: (1 - compound) * 5 (0-10)
  3. Calculate average frustration
  4. Apply tiered penalty (non-linear curves)
  5. Sentiment Journey Bonus:
     - Compare first 3 vs last 3 customer segments
     - If improvement > 0.6 (strong de-escalation) → 60% penalty reduction
     - If improvement > 0.3 (moderate) → 30% penalty reduction
- **Output**: ParameterResult with penalty + journey_bonus metadata
- **Why Non-linear**: Captures that high frustration is disproportionately bad
- **Key Code**: backend/modules/sentiment_analyzer.py lines 20-151

---

### `modules/slm_analyzer.py`

#### **analyze(transcript, profile_config)**
```python
def analyze(transcript: list, profile_config: dict) -> list:
```
- **Purpose**: Run phi3.5 via Ollama for empathy, resolution, true sentiment
- **Input**: Transcript, profile_config (unused here)
- **Ollama Call**:
  - URL: `http://localhost:11434/api/generate`
  - Model: `phi3.5:mini`
  - Timeout: 90s
  - Format: JSON output
  - System prompt: Detailed instructions for call auditor role
- **Output JSON**:
  ```json
  {
    "empathy_score": 1-10,
    "empathy_reason": "string",
    "resolution_score": 0-10,
    "resolution_reason": "string",
    "overall_sentiment": "Positive|Neutral|Negative"
  }
  ```
- **Penalty Conversion**:
  - empathy_penalty = (10 - score) * 10
  - resolution_penalty = (10 - score) * 10
  - slm_sentiment: metadata-only (no penalty)
- **Fallback Chain**:
  1. Ollama unreachable → all three return penalty=50, logged
  2. JSON parse error → all three return penalty=50, logged
  3. Invalid field → use defaults (empathy=5, resolution=5, sentiment=Neutral)
- **Key Code**: backend/modules/slm_analyzer.py lines 186-353

---

### `scoring_engine.py`

#### **calculate_score(analyzer_results, weights, profile_name)**
```python
def calculate_score(analyzer_results, weights, profile_name) -> CallScore:
```
- **Purpose**: Convert analyzer results + weights → final 0-100 score
- **Input**:
  - `analyzer_results`: List[ParameterResult]
  - `weights`: Dict mapping param names to weights (should sum to 100)
  - `profile_name`: String (used in CallScore response)
- **Process**:
  1. Build lookup dict: {param_name → ParameterResult}
  2. Filter weights to match available analyzers
  3. If weight_sum ≠ 100 → normalize: weight_i = weight_i / weight_sum * 100
  4. For each param: contribution = -(weight * penalty / 100)
  5. final_score = 100 - Σ(contribution)
  6. Clamp to [0, 100]
  7. Generate interpretation (1-2 sentences)
- **Output**: CallScore pydantic model
- **Key Code**: scoring_engine.py lines 54-131
- **Edge Cases**:
  - No matching weights → score=50, error metadata
  - Weight sum ≤ 0 → prevent division by zero

---

### `parameter_registry.py`

#### **get_available_parameters()**
```python
def get_available_parameters() -> List[Dict]:
```
- **Output**: Dynamic list of all parameters (frontend reads this for UI)
```json
[
  {
    "name": "talk_ratio",
    "display_name": "Talk-to-Listen Ratio",
    "icon": "🎙️",
    "description": "..."
  },
  ...
]
```

#### **load_profile_config(profile_name)**
```python
def load_profile_config(profile_name: str) -> Dict:
```
- **Purpose**: Load profile-specific settings (weights + ideal talk ratio)
- **Logic**:
  1. Try to load from `backend/config/client_profiles.json`
  2. Fallback to built-in defaults if file missing or key not found
- **Example Return**:
  ```python
  {
    "name": "Complaints",
    "description": "...",
    "weights": {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40},
    "ideal_talk_ratio": [0.40, 0.55]
  }
  ```
- **Profiles Available**:
  - `complaints` (currently in JSON)
  - `sales` (built-in fallback only)

#### **get_default_weights(profile)**
```python
def get_default_weights(profile: str) -> Dict[str, float]:
```
- **Returns**: Weight dict for profile (sums to 100)
- **Key Code**: parameter_registry.py lines 74-84

---

### `database.py`

#### **init_db()**
```python
def init_db():
```
- **Purpose**: Initialize SQLite schema at startup
- **Creates**:
  - `call_history` table with scalar + JSON blob columns
  - Indices on `analyzed_at`, `final_score`, `agent_name`
- **Safe**: Uses `IF NOT EXISTS`

#### **save_call(filename, file_size_bytes, response, weights, agent_name)**
```python
def save_call(...) -> int:
```
- **Returns**: call_id (row ID)
- **Stores**:
  - Scalar columns: final_score, talk_ratio_score, sentiment_score, etc.
  - JSON blobs: full analysis, transcript, insights, analyzer_results
- **Timestamp**: Stored in UTC ISO format

#### **get_history(limit, offset)**
```python
def get_history(limit: int = 10, offset: int = 0) -> List[Dict]:
```
- **Returns**: Recent calls (most recent first)

#### **get_call_detail(call_id)**
```python
def get_call_detail(call_id: int) -> Optional[Dict]:
```
- **Returns**: Full call record with parsed JSON blobs

#### **get_stats()**
```python
def get_stats() -> Dict:
```
- **Returns**: Aggregate stats (total_calls, avg_score, committed_count, etc.)

---

### `models.py`

#### **ParameterResult** (Pydantic Model)
```python
class ParameterResult(BaseModel):
    name: str                      # "talk_ratio", "sentiment", etc.
    display_name: str              # "Talk-to-Listen Ratio"
    icon: str                      # "🎙️"
    raw_value: float               # Original measurement (varies per analyzer)
    score: float                   # 0-100 scale
    penalty: float                 # 0-100 (used in scoring formula)
    metadata: dict = {}            # Extra data (journey_bonus_level, etc.)
```

#### **ParameterBreakdown** (Pydantic Model)
```python
class ParameterBreakdown(BaseModel):
    raw_value: float
    score: float
    penalty: float
    weight: float                  # Normalized weight (percent of 100)
    contribution: float            # Negative points lost from final score
    display_name: str
    icon: str
    metadata: dict = {}
```

#### **CallScore** (Pydantic Model)
```python
class CallScore(BaseModel):
    final_score: float             # 0-100, clamped
    breakdown: Dict[str, ParameterBreakdown]
    profile_used: str
    interpretation: str            # 1-2 sentence summary
    metadata: dict = {}
```

---

## 4. API ENDPOINTS

### Health Check
```
GET /
```
**Response**: `{"status": "ok", "message": "NanoVox API is running"}`

---

### Main Analysis Endpoint
```
POST /analyze
Content-Type: multipart/form-data

Body:
  file: <audio file>
  weights (optional): JSON string like {"talk_ratio":10,"sentiment":20,...}
```
**Response**: Full response object with transcription + analysis + analyzer_results

**Errors**:
- 400: Invalid form data
- 413: File too large
- 500: Internal error (logged)

---

### Test Analysis (Manual Transcript)
```
POST /api/test-analysis
Content-Type: application/json

Body:
{
  "transcript": [
    {"speaker": "Agent", "start": 0.0, "end": 5.2, "text": "..."},
    {"speaker": "Customer", "start": 5.4, "end": 10.1, "text": "..."}
  ],
  "weights": {"talk_ratio":5, "sentiment":35, "empathy":20, "resolution":40},
  "profile": "complaints"
}
```
**Response**: CallScore object (same as analysis.analysis in /analyze response)

---

### Rescore (Recalculate with Different Weights)
```
POST /api/rescore
Content-Type: application/json

Body:
{
  "analyzer_results": [...],
  "weights": {"talk_ratio":15, "sentiment":25, "empathy":20, "resolution":40}
}
```
**Response**: CallScore object

---

### Get Parameters (Dynamic UI)
```
GET /api/parameters/available
```
**Response**: 
```json
{
  "parameters": [
    {
      "name": "talk_ratio",
      "display_name": "Talk-to-Listen Ratio",
      "icon": "🎙️",
      "description": "..."
    },
    ...
  ]
}
```

---

### Get Default Weights
```
GET /api/weights/defaults
```
**Response**: 
```json
{
  "weights": {"talk_ratio": 15, "sentiment": 30, "empathy": 20, "resolution": 35}
}
```

---

### Call History
```
GET /api/history?limit=10&offset=0
```
**Response**: Array of call summaries

---

### Call Detail
```
GET /api/history/{call_id}
```
**Response**: Full call record (with parsed JSON blobs)

---

### Call Statistics
```
GET /api/stats
```
**Response**: Aggregate stats
```json
{
  "total_calls": 42,
  "avg_score": 65.3,
  "min_score": 30.0,
  "max_score": 95.0,
  "avg_talk_ratio": 0.55,
  "avg_sentiment": 50.2,
  "avg_empathy": 72.1,
  "avg_commitment": 68.5,
  "committed_count": 32,
  "ghosted_count": 5
}
```

---

### Generate PDF Report
```
GET /api/report/{call_id}
```
**Response**: PDF file (binary)

---

## 5. CONFIGURATION SYSTEM

### Location: `backend/config/client_profiles.json`

```json
{
  "complaints": {
    "name": "Complaints",
    "description": "Optimized for customer complaint handling—emotional journey and actual resolution matter most",
    "weights": {
      "talk_ratio": 5,
      "sentiment": 35,
      "empathy": 20,
      "resolution": 40
    },
    "ideal_talk_ratio": [0.40, 0.55]
  }
}
```

### How Configuration is Loaded

```
Load Order (in parameter_registry.py):
1. Try to read backend/config/client_profiles.json
2. Look for profile key (e.g., "complaints")
3. If NOT found → Use built-in _FALLBACKS dict
4. If file not found → Use built-in _FALLBACKS dict

Built-in Fallbacks:
├─ Sales: weights {talk_ratio:15, sentiment:30, empathy:20, resolution:35}
└─ Complaints: weights {talk_ratio:5, sentiment:35, empathy:20, resolution:40}
```

### Why This Design?

- **Centralized**: All profile config in one JSON file
- **Resilient**: Hardcoded fallbacks prevent crashes if JSON missing
- **Extendable**: Add new profiles by editing JSON
- **Runtime Reloadable**: Changes don't require restart (but currently no hot-reload endpoint)

---

## 6. PARAMETER REGISTRY & SCORING

### The 4 Analysis Parameters

| Parameter | Analyzer | Raw Value | Good Score | What It Measures |
|-----------|----------|-----------|-----------|------------------|
| **talk_ratio** | talk_ratio_analyzer.py | Agent ÷ (Agent + Customer) | 60-70% for sales, 40-55% for complaints | Balance of speaking time |
| **sentiment** | sentiment_analyzer.py | Avg customer frustration 0-10 | Low frustration (high score) | Customer emotional journey |
| **empathy** | slm_analyzer.py | Agent empathy 1-10 from LLM | 8-10 | Agent emotional intelligence |
| **resolution** | slm_analyzer.py | Problem resolution 0-10 from LLM | 9-10 | Was the issue actually fixed? |

### Score Calculation Example

**Scenario**: Complaints call with these analyzer results:
- talk_ratio: frustration=6.5 → score=65, penalty=35
- sentiment: frustration=7.0 → base_penalty=60, journey_bonus applies → final_penalty=42
- empathy: score=7 → penalty=30
- resolution: score=6 → penalty=40

**Profile**: Complaints
- talk_ratio weight: 5 → (5/100) × 35 = 1.75 points lost
- sentiment weight: 35 → (35/100) × 42 = 14.7 points lost
- empathy weight: 20 → (20/100) × 30 = 6.0 points lost
- resolution weight: 40 → (40/100) × 40 = 16.0 points lost

**Total weighted penalty**: 1.75 + 14.7 + 6.0 + 16.0 = 38.45  
**Final Score**: 100 - 38.45 = **61.55 / 100**

---

## 7. DEPENDENCY ANALYSIS: WHAT BREAKS IF...

### Critical Dependencies

#### **7.1 If Whisper is removed/unavailable**
```
Failure Point: main.py line 64 (model loading)
├─ App startup will CRASH
├─ /analyze endpoint becomes unusable
└─ Mitigation: None (no fallback speech-to-text)

Workaround:
  - Use /api/test-analysis with manual transcript instead
  - Don't require audio upload, only support JSON test mode
```

**Impact**: Audio analysis completely broken. **SEVERITY: CRITICAL**

---

#### **7.2 If VADER sentiment analyzer is not loaded**
```
Failure Point: Main.py line 69-70
├─ Sentiment analyzer will return neutral (penalty=50)
├─ SLM sentiment override won't work (no VADER to override)
└─ Call scores shift toward neutral

Ripple:
  - sentiment parameter not returned
  - SLM override logic skipped but doesn't break
  - Final scores higher (loss of penalty)
```

**Impact**: Sentiment analysis ineffective. **SEVERITY: HIGH** (downstream still works)

---

#### **7.3 If Ollama is unavailable**
```
Failure Point: slm_analyzer.py line 221 (requests.post to Ollama)
├─ ConnectionError → caught at line 340
├─ Returns three neutral results: empathy penalty=50, resolution penalty=50
├─ SLM override not applied (no true_sentiment available)
└─ Call continues with 5 results instead of 5

Impact:
  - Empathy scoring falls back to neutral (penalty=50)
  - Resolution scoring falls back to neutral (penalty=50)
  - SLM-based sarcasm detection disabled
  - Scores trend 5-10 points higher (less penalty)
```

**Mitigation**: Ollama is optional; graceful fallback included.  
**SEVERITY: MEDIUM** (scoring less accurate, but continues)

---

#### **7.4 If speaker attribution is 100% wrong**
```
Current: Global Weighted Voting system (main.py 325-419)
├─ If AGENT_SIGNALS and CUSTOMER_SIGNALS both empty
│  └─ Pause detection alone (~30% accuracy)
├─ If signal libraries are completely wrong
│  └─ Scoring skewed but still executes
└─ If gap threshold (0.3s) is too tight/loose
   └─ Wrong speaker boundaries

Impact:
  - Talk ratio inverted (agent/customer swapped)
  - Sentiment measured on wrong speaker
  - Empathy/resolution mislabeled
  - FINAL SCORE COMPLETELY WRONG

Mitigation:
  - Frontend supports /api/test-analysis for manual override
  - No persistence of bad speaker labels (they're recomputed each time)
  - Signal library is extensive (24+13 keywords) but not perfect
```

**SEVERITY: CRITICAL** (garbage in = garbage out, but at least detectable in test mode)

---

#### **7.5 If database connection fails**
```
Failure Point: database.py line 106 (sqlite3.connect)
├─ save_call() raises exception
├─ Main.py line 482-483: Caught, logged, request still succeeds
├─ Call data NOT persisted
└─ Next /api/history call returns fewer records

Impact:
  - Analysis results returned to frontend (good)
  - History missing records (bad for audit trail)
  - Stats are incomplete
```

**Mitigation**: Database failure doesn't crash /analyze endpoint  
**SEVERITY: MEDIUM** (analysis works, history broken)

---

#### **7.6 If profile config JSON is malformed**
```
Failure Point: parameter_registry.py line 104 (json.load)
├─ json.JSONDecodeError caught
├─ Falls back to _FALLBACKS dict
└─ Uses "sales" weights by default

Impact:
  - User sees default weights, not custom profile
  - If profile key exists but is invalid → uses fallback
  - No exception raised
```

**SEVERITY: LOW** (graceful degradation)

---

#### **7.7 If data types change**
```
Example: Change sentiment.score from float to int

Failure Chain:
  1. Pydantic model validation fails (type mismatch)
  2. calculate_score() receives invalid data
  3. Calculation logic might break (int + float)
  4. final_score becomes nonsensical

Fixed By: Pydantic Type Safety
  - ParameterResult requires score: float
  - Type checked at parse time
  - Invalid data rejected BEFORE scoring engine
```

**SEVERITY: LOW** (Pydantic catches early)

---

#### **7.8 If weights sum ≠ 100**
```
Current Behavior (scoring_engine.py line 90):
├─ Normalize weights: weight_i = (weight_i / weight_sum) * 100
├─ Ensures normalized weights always sum to 100
└─ proportions preserved

Impact:
  - If custom weights from frontend: [10, 20, 15, 30] = 75
  - Normalized to: [13.3, 26.7, 20, 40] = 100
  - Score calculation correct

Edge Case:
  - If weight_sum = 0: Set to 1.0 to prevent division by zero
```

**SEVERITY: LOW** (handled automatically)

---

#### **7.9 If an analyzer returns an unexpected field**
```
Example: sentiment_analyzer returns "sentiment_score" instead of "score"

Failure Point: scoring_engine.py line 98-99
├─ KeyError: 'score' not found
├─ Exception caught? NO — unforeseen bug
└─ /analyze endpoint returns 500 error

Current Safeguard:
  - All analyzers use Pydantic ParameterResult (enforced types)
  - If analyzer tries to return wrong fields → validation error at model creation
```

**SEVERITY: CRITICAL IF HAPPENS** (but prevented by Pydantic)

---

### Dependency Graph

```
/analyze endpoint
    ├─ Whisper (CRITICAL)
    ├─ Speaker Attribution Code (CRITICAL)
    ├─ _run_analyzers()
    │   ├─ talk_ratio_analyzer (fallback: penalty=50)
    │   ├─ sentiment_analyzer
    │   │   └─ VADER instance (fallback: penalty=50)
    │   ├─ slm_analyzer
    │   │   └─ Ollama HTTP (fallback: penalty=50 × 3)
    │   └─ SLM Override Logic
    ├─ scoring_engine (calculate_score)
    ├─ database
    │   └─ nanovox.db (fallback: log error, continue)
    └─ models (Pydantic validation)
```

---

## 8. TESTING STRATEGY

### Unit Testing Approach

#### **Test 1: Speaker Attribution**
```python
# Test speaker_identification with known input
transcript_segments = [
    {"id": 0, "start": 0.0, "end": 2.0, "text": "We have a great solution for you"},
    {"id": 1, "start": 2.5, "end": 5.0, "text": "I'm frustrated with this broken system"},
]

# Expected: First → Agent, Second → Customer
# Validation: AGENT_SIGNALS match first, CUSTOMER_SIGNALS match second
```

#### **Test 2: Sentiment Journey Bonus**
```python
# Test case: Customer starts frustrated, ends happy
transcript = [
    {"speaker": "Customer", "text": "This is terrible!"},  # compound ≈ -0.5
    {"speaker": "Customer", "text": "Actually, that works great!"},  # compound ≈ 0.7
]
# Expected: journey_bonus_level = "strong" (delta > 0.6)
# Assertion: final_penalty = base_penalty * 0.4
```

#### **Test 3: SLM Override Logic**
```python
# VADER scores high (positive), but SLM says Negative
vader_result = ParameterResult(..., score=85.0, penalty=15.0, name="sentiment")
slm_result = ParameterResult(..., metadata={"true_sentiment": "Negative"})

# Expected override: VADER penalty forced from 15 to 85
# Assertion: vader_result.score == 15.0 after override
```

#### **Test 4: Score Calculation with Custom Weights**
```python
# Given:
analyzer_results = [
  ParameterResult(name="talk_ratio", penalty=35),
  ParameterResult(name="sentiment", penalty=40),
  ParameterResult(name="empathy", penalty=50),
  ParameterResult(name="resolution", penalty=60),
]
weights = {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40}

# Calculate:
# normalized_weights = {same, since sum=100}
# weighted_penalty = 0.05*35 + 0.35*40 + 0.20*50 + 0.40*60
#                  = 1.75 + 14.0 + 10.0 + 24.0 = 49.75
# final_score = 100 - 49.75 = 50.25

# Use /api/test-analysis to validate
```

#### **Test 5: Database Persistence**
```python
# After calling /analyze:
call_id = save_call(...)

# Verify:
detail = get_call_detail(call_id)
assert detail['filename'] == original_filename
assert detail['final_score'] == expected_score
assert detail['transcript_json'] includes full transcript
```

### Manual Testing (Code Review Prep)

#### **Scenario 1: Happy Path (Full Pipeline)**
```
1. Upload: sample_complaint.wav (30s audio)
2. Expected:
   - Transcription succeeds (check logs)
   - Speaker attribution: Agent/Customer labels correct
   - All 5 analyzers return results (check analyzer_results array)
   - SLM override applied if needed (check metadata)
   - final_score between 0-100
   - Call saved to database
3. Verify: /api/history returns the new call
```

#### **Scenario 2: Ollama Unavailable**
```
1. Stop Ollama service
2. Upload audio
3. Expected:
   - Empathy, resolution return penalty=50 (neutral)
   - slm_sentiment metadata: model_used="fallback"
   - No crash; final_score still calculated
   - Logs show: "SLM: Ollama not reachable at..."
```

#### **Scenario 3: Manual Transcript Test Mode**
```
1. POST to /api/test-analysis with JSON:
   {
     "transcript": [
       {"speaker": "Agent", "start": 0, "end": 5, "text": "Hello, how can I help?"},
       {"speaker": "Customer", "start": 5, "end": 10, "text": "My billing is wrong."}
     ],
     "profile": "complaints"
   }
2. Expected: CallScore + analyzer_results (no Whisper used)
3. Verify: Correct weights applied from "complaints" profile
```

#### **Scenario 4: Rescore with Different Weights**
```
1. After /analyze receives result with analyzer_results
2. Frontend calls /api/rescore with new weights
3. Expected: new final_score (should differ from original)
4. Verify: Quick (<100ms) response
```

### Integration Testing

```yaml
Test Suite:
  ✓ Audio → Transcription → Speaker Attribution → Analyzers → Score
  ✓ Manual Transcript → Analyzers → Score (no Whisper)
  ✓ Database: Save → History → Detail → Stats
  ✓ Rescore: analyzer_results + weights → new score
  ✓ Error Paths:
    - Bad audio file
    - Ollama timeout
    - Database unreachable
    - Invalid JSON weights
```

---

## 9. SWAGGER/OPENAPI DOCUMENTATION

### Current API Documentation

The API is auto-documented by FastAPI at:
```
http://localhost:8000/docs       (Swagger UI)
http://localhost:8000/redoc      (ReDoc)
http://localhost:8000/openapi.json (raw schema)
```

### How Swagger is Generated

**FastAPI automatically generates Swagger from:**
1. Endpoint signatures: `@app.post("/analyze")`
2. Type hints: `file: UploadFile`, `weights: Optional[str]`
3. Pydantic models: `TestAnalysisRequest`, `RescoreRequest`
4. Docstrings: `async def analyze_audio(...) -> Dict:`

### Enabling Custom Swagger Title/Description

**Edit main.py line 25-29:**
```python
app = FastAPI(
    title="NanoVox API",
    description="Call Intelligence Dashboard API",
    version="1.0.0"
)
```

The title, description, and version appear in Swagger UI.

### Adding Function Docstrings for Swagger

**Each endpoint should have docstring:**
```python
@app.post("/analyze")
async def analyze_audio(...) -> Dict:
    """
    Analyze an audio file: transcribe + run parameter scoring.

    Args:
        file: Audio file (.wav, .mp3, etc.)
        weights: Optional JSON string of custom weights

    Returns:
        Dict with transcription, analysis results, and call_id
    """
```

This docstring appears under the endpoint in Swagger.

### Current Swagger Status

✅ **Auto-generated endpoints**: All endpoints have basic Swagger  
⚠️ **Missing detailed documentation**: Parameter descriptions could be richer  
⚠️ **Response schemas**: Complex nested JSON could use response model types

### How to View Available Endpoints

```bash
# From browser:
http://localhost:8000/docs

# From command line:
curl http://localhost:8000/openapi.json | jq .
```

### How Weights Are Used in API

**In /analyze endpoint:**
```python
@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    weights: Optional[str] = Form(None)
) -> Dict:
    """
    weights: Optional JSON string such as:
    '{"talk_ratio":10,"sentiment":20,"empathy":10,"resolution":60}'
    """
```

In Swagger, `weights` parameter shows as a string input field.

---

## APPENDIX: CRITICAL CODE PATHS FOR REVIEW

### When Code Reviewer Asks: "What Happens If..."

#### Q: "What if an audio file is 1 GB?"
```
A: 
1. UploadFile reads entire file into memory
2. Written to tempfile (~1GB disk)
3. Whisper processes it (may timeout after ~5min realtime)
4. If completes: ~20min to process (CPU-bound)
5. No file size limit enforced (could OOM)

Mitigation needed: Add max file size check in /analyze
```

#### Q: "What if the transcript has no customer segments?"
```
A:
1. sentiment_analyzer detects no customer segments (line 51)
2. Returns neutral: penalty=50, score=50
3. talk_ratio_analyzer calculates agent-only time (might be 1.0)
4. SLM still runs (might say empathy=5)
5. Final score skewed toward neutral
```

#### Q: "What if the database is corrupt?"
```
A:
1. init_db() is idempotent (IF NOT EXISTS)
2. save_call() fails, exception logged
3. /analyze returns successfully anyway (DB save non-critical)
4. /api/history returns empty or partial results
5. No automatic repair
```

#### Q: "What if Ollama returns invalid JSON?"
```
A:
1. json.JSONDecodeError triggered (line 346)
2. Caught: all three SLM results return penalty=50 (neutral)
3. No crash; pipeline continues
4. Log: "Failed to parse JSON from model response"
```

#### Q: "What if my weights sum to 75, not 100?"
```
A:
1. Normalization (scoring_engine line 90) scales to 100
2. Original proportions preserved
3. No error raised
Example: [10, 20, 15, 30] → [13.3, 26.7, 20, 40]
```

---

## KEY TAKEAWAYS FOR CODE REVIEW

✅ **Strengths**:
- Graceful fallback for all external deps (Ollama, VADER, Whisper)
- Pydantic typing ensures schema safety
- SQLite + WAL for safe concurrent access
- Parameter registry enables dynamic UI
- SLM override logic is sophisticated (sarcasm-aware)

⚠️ **Known Issues (Document These)**:
- No max file size enforcement → OOM risk
- Speaker attribution not perfect (keyword matching has upper bound)
- No authentication/authorization
- Ollama must be running separately (not bundled)
- No rate limiting
- PDF generation function not reviewed

🔴 **Critical Paths**:
1. Audio upload → Whisper → Speaker attribution (if any step fails, quality degrades)
2. Analyzer pipeline → Scoring engine (if weights misconfigured, results wrong)
3. Database persistence (non-critical, but audit trail incomplete if fails)

---

**Generated**: 2026-04-16  
**For**: Code Review Preparation  
**Next Step**: Walk through each analyzer function with reviewer
