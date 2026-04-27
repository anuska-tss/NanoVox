# NanoVox Production Refactoring - Detailed Task Breakdown
## 10-Day Sprint Plan (Ready for Excel)

---

## PHASE 1: SETUP & PLANNING (Day 1)

| Task ID | Task Name | Module | Day | Hours | Story Points | Dependencies | Priority | Status |
|---------|-----------|--------|-----|-------|--------------|--------------|----------|--------|
| 1.1 | Environment Setup & Feature Branch | DevOps | 1 | 1 | 1 | None | Critical | Not Started |
| 1.2 | Code Audit & Current State Documentation | Documentation | 1 | 2 | 2 | None | High | Not Started |
| 1.3 | Create Project Directory Structure | Backend | 1 | 1 | 1 | 1.1 | High | Not Started |

### Task 1.1: Environment Setup & Feature Branch
**Description:** Create a feature branch for the refactoring, ensure all dependencies are installed, verify code runs.

**Acceptance Criteria:**
- [ ] Git feature branch created (`feature/production-refactoring`)
- [ ] All existing tests pass on current branch
- [ ] Backend and frontend run without errors
- [ ] DevOps documented in README

**Technical Details:**
```bash
git checkout -b feature/production-refactoring
# Run existing tests
pytest backend/
npm test  # if exists
```

---

### Task 1.2: Code Audit & Current State Documentation
**Description:** Document current state of App.jsx, main.py, and logging implementation. Identify pain points.

**Acceptance Criteria:**
- [ ] App.jsx analyzed: line count, state count, components
- [ ] main.py analyzed: route count, logic mixed with routes
- [ ] Logging analyzed: debug log instances, anti-patterns found
- [ ] Document created: `CURRENT_STATE_AUDIT.md`
- [ ] Risks identified and documented

**Deliverables:**
- Current state analysis document
- Before screenshots (visual line counts)
- Identified issues list

---

### Task 1.3: Create Project Directory Structure
**Description:** Create all new directories for refactored backend structure (services, routers, config, etc.).

**Acceptance Criteria:**
- [ ] `backend/app/` directory created with `__init__.py`
- [ ] `backend/app/config/` created
- [ ] `backend/app/api/routers/` created
- [ ] `backend/app/services/` created
- [ ] `backend/app/core/` created
- [ ] `backend/app/models/` created (separate from existing models.py)
- [ ] `backend/app/ml/` created
- [ ] All `__init__.py` files created
- [ ] Structure verified with tree command

---

## PHASE 2: FRONTEND REFACTORING (Days 2-5)

| Task ID | Task Name | Module | Day | Hours | Story Points | Dependencies | Priority | Status |
|---------|-----------|--------|-----|-------|--------------|--------------|----------|--------|
| 2.1 | Create Constants & Utils Layer | Frontend | 2 | 3 | 2 | None | High | Not Started |
| 2.2 | Create Custom Hooks | Frontend | 2-3 | 5 | 3 | 2.1 | High | Not Started |
| 2.3 | Create View Components | Frontend | 3 | 4 | 3 | 2.2 | High | Not Started |
| 2.4 | Refactor App.jsx | Frontend | 4 | 3 | 2 | 2.3 | Critical | Not Started |
| 2.5 | Frontend Testing & Bug Fixes | Frontend | 5 | 3 | 2 | 2.4 | High | Not Started |

### Task 2.1: Create Constants & Utils Layer
**Description:** Extract all constants from config.js and App.jsx into dedicated constant files.

**Acceptance Criteria:**
- [ ] `src/constants/storageKeys.js` created with STORAGE_KEYS
- [ ] `src/constants/weights.js` created with DEFAULT_WEIGHTS
- [ ] `src/constants/analysis.js` created with ANALYSIS_CONFIG
- [ ] `src/constants/processingSteps.js` created with PROCESSING_STEPS, PROCESSING_STEP_STATUS
- [ ] `src/utils/validators.js` created with file validation logic
- [ ] `src/utils/formatters.js` created with formatting helpers
- [ ] `src/utils/helpers.js` updated with getScoreColor and other utils
- [ ] All constants imported correctly in App.jsx
- [ ] Linting passes (ESLint)
- [ ] No import errors

**Files to Create:**
- `frontend/src/constants/storageKeys.js`
- `frontend/src/constants/weights.js`
- `frontend/src/constants/analysis.js`
- `frontend/src/constants/processingSteps.js`
- `frontend/src/utils/validators.js` (new)
- `frontend/src/utils/formatters.js` (new)

---

### Task 2.2: Create Custom Hooks
**Description:** Extract business logic from App.jsx into reusable custom hooks.

**Acceptance Criteria:**
- [ ] `useAnalysis.js` hook created with analysis orchestration logic
- [ ] `useTheme.js` hook created with theme management
- [ ] `useWeights.js` hook created with weight state + localStorage
- [ ] `useHistory.js` hook created with history fetching
- [ ] `useFileUpload.js` hook created with file validation
- [ ] All hooks properly documented with JSDoc
- [ ] Each hook tested independently (unit tests)
- [ ] No external dependencies added
- [ ] React hook rules followed (ESLint)

**Files to Create:**
- `frontend/src/hooks/useAnalysis.js`
- `frontend/src/hooks/useTheme.js`
- `frontend/src/hooks/useWeights.js`
- `frontend/src/hooks/useHistory.js`
- `frontend/src/hooks/useFileUpload.js`

**Testing:**
- Render each hook in test component
- Verify state changes work
- Verify localStorage integration
- Test error scenarios

---

### Task 2.3: Create View Components
**Description:** Create page-level view components that use the hooks.

**Acceptance Criteria:**
- [ ] `LandingView.jsx` created (file upload + profile selector)
- [ ] `ProcessingView.jsx` created (progress display)
- [ ] `DashboardView.jsx` created (results display)
- [ ] `HistoryView.jsx` created (call history)
- [ ] `Header.jsx` (layout component) created
- [ ] Each view component properly styled
- [ ] Props properly typed/documented
- [ ] No API calls in view components (only from hooks)
- [ ] Views render without errors
- [ ] Responsive design verified

**Files to Create:**
- `frontend/src/components/views/LandingView.jsx`
- `frontend/src/components/views/LandingView.css`
- `frontend/src/components/views/ProcessingView.jsx`
- `frontend/src/components/views/ProcessingView.css`
- `frontend/src/components/views/DashboardView.jsx`
- `frontend/src/components/views/DashboardView.css`
- `frontend/src/components/views/HistoryView.jsx`
- `frontend/src/components/views/HistoryView.css`
- `frontend/src/components/layout/Header.jsx`
- `frontend/src/components/layout/Header.css`

---

### Task 2.4: Refactor App.jsx
**Description:** Replace monolithic App.jsx with thin router using hooks and view components.

**Acceptance Criteria:**
- [ ] App.jsx refactored to <100 lines
- [ ] All state logic removed (moved to hooks)
- [ ] All rendering logic removed (moved to views)
- [ ] App.jsx only handles routing and hook coordination
- [ ] All props flow correctly to views
- [ ] No breaking changes in functionality
- [ ] All existing features work identically
- [ ] App renders without console errors
- [ ] Code passes linting

**Changes:**
- Replace 300+ lines with 80 lines
- Import hooks at top
- Use hooks to get state/functions
- Render view components conditionally
- Pass props to views

---

### Task 2.5: Frontend Testing & Bug Fixes
**Description:** Test all frontend changes, fix any bugs, verify functionality.

**Acceptance Criteria:**
- [ ] Landing page renders and accepts file upload
- [ ] Processing view shows progress correctly
- [ ] Dashboard displays results correctly
- [ ] Theme toggle works and persists
- [ ] Weight changes persist in localStorage
- [ ] History fetching works
- [ ] All error messages display correctly
- [ ] File validation works (size limit)
- [ ] Test mode works (JSON transcript input)
- [ ] Navigation between views works
- [ ] No console errors or warnings
- [ ] Mobile responsive verified

**Testing Checklist:**
- [ ] Manual testing of all features
- [ ] Browser DevTools checked (no errors)
- [ ] Lighthouse performance check
- [ ] Accessibility check (a11y)
- [ ] Cross-browser testing (Chrome, Firefox, Edge)

---

## PHASE 3: BACKEND REFACTORING (Days 2-7)

| Task ID | Task Name | Module | Day | Hours | Story Points | Dependencies | Priority | Status |
|---------|-----------|--------|-----|-------|--------------|--------------|----------|--------|
| 3.1 | Create Config Layer | Backend | 2 | 2 | 2 | 1.3 | High | Not Started |
| 3.2 | Create Models Layer | Backend | 2 | 2 | 1 | 1.3 | High | Not Started |
| 3.3 | Create Service Layer | Backend | 3-4 | 6 | 3 | 3.1, 3.2 | Critical | Not Started |
| 3.4 | Create Router Files | Backend | 4-5 | 5 | 3 | 3.3 | Critical | Not Started |
| 3.5 | Refactor main.py | Backend | 6 | 2 | 2 | 3.4 | Critical | Not Started |
| 3.6 | Backend Testing & Integration | Backend | 7 | 3 | 2 | 3.5 | High | Not Started |

### Task 3.1: Create Config Layer
**Description:** Create centralized configuration management.

**Acceptance Criteria:**
- [ ] `app/config/settings.py` created with Settings class
- [ ] Settings loaded from environment variables (.env)
- [ ] Settings loaded from JSON config files (backward compat)
- [ ] `.env` file created with example variables
- [ ] `.env.example` file created for team
- [ ] `app/config/__init__.py` created
- [ ] Settings class has proper defaults
- [ ] Settings can be overridden by environment
- [ ] No hardcoded secrets in code

**Files to Create:**
- `backend/app/config/__init__.py`
- `backend/app/config/settings.py`
- `backend/.env`
- `backend/.env.example`

**Environment Variables:**
```
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_RETENTION_DAYS=7
THREAD_POOL_MAX_WORKERS=4
WHISPER_MODEL=base
MAX_UPLOAD_SIZE_MB=50
TEMP_UPLOAD_DIR=temp_uploads
```

---

### Task 3.2: Create Models Layer
**Description:** Organize Pydantic models into separate files by domain.

**Acceptance Criteria:**
- [ ] `app/models/__init__.py` created
- [ ] `app/models/requests.py` created (TestAnalysisRequest, RescoreRequest)
- [ ] `app/models/responses.py` created (AnalysisResponse, etc.)
- [ ] `app/models/analysis.py` created (ParameterResult, TranscriptSegment, etc.)
- [ ] All existing models moved/copied to new location
- [ ] Models can be imported from old location (backward compat layer)
- [ ] Pydantic v2 compatibility verified
- [ ] Model docstrings/examples updated
- [ ] No circular imports

**Files to Create:**
- `backend/app/models/__init__.py`
- `backend/app/models/requests.py`
- `backend/app/models/responses.py`
- `backend/app/models/analysis.py`

**Keep for Backward Compatibility:**
- Update `backend/models.py` to re-export from new location

---

### Task 3.3: Create Service Layer
**Description:** Extract business logic from main.py into service classes.

**Acceptance Criteria:**
- [ ] `AnalysisService` created with `analyze_transcript()` method
- [ ] `HistoryService` created with query methods
- [ ] `FileService` created with validation/upload handling
- [ ] `WeightService` created with weight defaults/validation
- [ ] Each service has clear single responsibility
- [ ] Services use logging only in except blocks
- [ ] Services can be tested independently
- [ ] Services inject dependencies (no global state)
- [ ] Error handling consistent across services
- [ ] Services documented with docstrings

**Files to Create:**
- `backend/app/services/__init__.py`
- `backend/app/services/analysis_service.py`
- `backend/app/services/history_service.py`
- `backend/app/services/file_service.py`
- `backend/app/services/weight_service.py`

**Testing:**
- Unit test each service method
- Test error scenarios
- Test with mock dependencies
- Verify no logging in happy path

---

### Task 3.4: Create Router Files
**Description:** Move all API routes from main.py into separate router files by domain.

**Acceptance Criteria:**
- [ ] `routers/analysis.py` created with /api/analyze, /api/test-analysis routes
- [ ] `routers/history.py` created with history endpoints
- [ ] `routers/weights.py` created with weights endpoints
- [ ] `routers/health.py` created with health check
- [ ] Each router imports from services (not duplicating logic)
- [ ] Routers only handle HTTP logic (validation, responses)
- [ ] Routers use services for business logic
- [ ] Error handling consistent (HTTPException with proper codes)
- [ ] All routes pass existing tests
- [ ] Router endpoints documented with docstrings

**Files to Create:**
- `backend/app/api/__init__.py`
- `backend/app/api/routers/__init__.py`
- `backend/app/api/routers/analysis.py`
- `backend/app/api/routers/history.py`
- `backend/app/api/routers/weights.py`
- `backend/app/api/routers/health.py`

**Routes to Move:**
- POST /api/analyze → analysis.py
- POST /api/test-analysis → analysis.py
- POST /api/rescore → analysis.py
- GET /api/history → history.py
- GET /api/history/{id} → history.py
- GET /api/stats → history.py
- GET /api/weights/defaults → weights.py
- GET / → health.py

---

### Task 3.5: Refactor main.py
**Description:** Strip main.py down to app creation, middleware, and router registration.

**Acceptance Criteria:**
- [ ] main.py reduced to 50-60 lines
- [ ] Only FastAPI setup in main.py
- [ ] All routes moved to routers
- [ ] All business logic moved to services
- [ ] Middleware registration in main.py
- [ ] Startup/shutdown events in main.py
- [ ] CORS configured from settings
- [ ] Routers included via app.include_router()
- [ ] All imports are clean
- [ ] No circular dependencies

**New main.py Structure:**
```python
# 1. Imports
# 2. Load settings
# 3. Setup logging
# 4. Create FastAPI app
# 5. Add middleware
# 6. Define startup/shutdown
# 7. Include routers
# 8. Done!
```

---

### Task 3.6: Backend Testing & Integration
**Description:** Test all backend changes, verify API endpoints, integration testing.

**Acceptance Criteria:**
- [ ] All API endpoints still work (/analyze, /test-analysis, /rescore, /history, /stats)
- [ ] File upload validation works (size check)
- [ ] Audio transcription works (Whisper integration)
- [ ] All analyzers run (talk ratio, sentiment, empathy, resolution, SLM)
- [ ] Scoring calculation correct
- [ ] Database save/retrieval works
- [ ] Error handling returns correct HTTP codes
- [ ] CORS allows frontend requests
- [ ] No console errors or warnings
- [ ] All existing tests pass

**Testing:**
- [ ] Test each router independently
- [ ] Test services with mocked dependencies
- [ ] Integration test: full pipeline (file → transcription → analysis → save)
- [ ] Test error scenarios (bad file, bad weights, etc.)
- [ ] Performance test (timing for analysis)

---

## PHASE 4: LOGGING CLEANUP (Days 3-4, Parallel with Backend)

| Task ID | Task Name | Module | Day | Hours | Story Points | Dependencies | Priority | Status |
|---------|-----------|--------|-----|-------|--------------|--------------|----------|--------|
| 4.1 | Remove Debug Logs | Backend | 3-4 | 2 | 1 | 1.2 | High | Not Started |
| 4.2 | Implement Error-Focused Logging | Backend | 4 | 3 | 2 | 4.1 | High | Not Started |
| 4.3 | Logging Testing | Backend | 4 | 2 | 1 | 4.2 | High | Not Started |

### Task 4.1: Remove Debug Logs
**Description:** Remove all "🧪 [DEBUG]" and debug-level logs from codebase.

**Acceptance Criteria:**
- [ ] Search for "🧪" in all Python files - result: 0
- [ ] Search for "[DEBUG]" in all Python files - result: 0
- [ ] No logger.debug() calls in main code (only in tests)
- [ ] All "logger.info()" calls in business logic removed
- [ ] Logging remains in:
  - app/main.py startup messages (INFO)
  - Except blocks (ERROR)
  - Critical business transitions (if any)
- [ ] Code audit document updated
- [ ] Tests pass

**Search & Replace Pattern:**
```python
# Find
logger.info("🧪 [DEBUG]
logger.debug(
logger.info(f"Processing {
logger.info("Starting

# Replace with
(nothing)
```

---

### Task 4.2: Implement Error-Focused Logging
**Description:** Add proper error logging with try-except blocks where needed.

**Acceptance Criteria:**
- [ ] All API route handlers have try-except blocks
- [ ] All service methods have try-except blocks
- [ ] All analyzer calls wrapped in try-except
- [ ] Errors logged with `logger.error(..., exc_info=True)`
- [ ] HTTPExceptions raised with proper status codes
- [ ] Client errors (400s) logged as WARNING level
- [ ] Server errors (500s) logged as ERROR level
- [ ] Error messages are user-friendly in HTTP response
- [ ] Error messages are detailed in logs
- [ ] No sensitive data in error logs

**Error Logging Pattern:**
```python
try:
    # business logic
    result = do_something()
    return result
except ValueError as e:
    logger.warning(f"Invalid input: {str(e)}")
    raise HTTPException(status_code=400, detail=str(e))
except DatabaseError as e:
    logger.error(f"Database error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Database error")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

---

### Task 4.3: Logging Testing
**Description:** Verify logging works correctly in all scenarios.

**Acceptance Criteria:**
- [ ] Happy path produces 0 log lines
- [ ] Error scenario produces ERROR log with traceback
- [ ] Warning scenario produces WARNING log
- [ ] Startup logs appear once on app start
- [ ] Shutdown logs appear once on app shutdown
- [ ] Logs go to both console and file
- [ ] Log file rotation works daily
- [ ] Old logs deleted after 7 days
- [ ] No sensitive data in logs

**Testing:**
- [ ] Trigger each error scenario
- [ ] Check logs/backend.log.YYYY-MM-DD
- [ ] Verify format and content
- [ ] Check console output
- [ ] Verify no excessive logging

---

## PHASE 5: DIARIZATION FEATURE (Days 5-8)

| Task ID | Task Name | Module | Day | Hours | Story Points | Dependencies | Priority | Status |
|---------|-----------|--------|-----|-------|--------------|--------------|----------|--------|
| 5.1 | Design Diarization Service Architecture | Backend | 5 | 2 | 2 | 3.1 | High | Not Started |
| 5.2 | Create SLM Diarization Module | Backend | 6 | 5 | 3 | 5.1 | Critical | Not Started |
| 5.3 | Integrate Diarization into Analysis Pipeline | Backend | 7 | 4 | 3 | 5.2, 3.3 | Critical | Not Started |
| 5.4 | Diarization Testing & Validation | Backend | 8 | 3 | 2 | 5.3 | High | Not Started |

### Task 5.1: Design Diarization Service Architecture
**Description:** Design how diarization will work with SLM, what data it will produce, how it integrates.

**Acceptance Criteria:**
- [ ] Design document created: `DIARIZATION_DESIGN.md`
- [ ] SLM prompt designed for speaker identification
- [ ] Input/output models defined
- [ ] Integration points identified (where in pipeline)
- [ ] Performance impact assessed
- [ ] Error handling strategy defined
- [ ] Fallback strategy if SLM fails
- [ ] Example output documented

**Design Document Should Include:**
```markdown
# Diarization Design

## Overview
- Use SLM (phi3.5 via Ollama) for speaker identification
- Not pyannote (too heavy for offline)
- Called after transcription, before analysis

## Input
- Raw transcript from Whisper (list of segments)

## Processing
1. SLM analyzes each segment
2. SLM identifies speaker (Agent/Customer/Other)
3. SLM estimates speaker turn boundaries
4. Output: enhanced transcript with speaker labels

## Output
- Enhanced transcript with speaker labels
- Confidence scores per label
- Speaker summary (who spoke, how much)

## Integration
- After: Whisper transcription
- Before: Analysis pipeline (talk_ratio, sentiment, etc.)

## Error Handling
- If SLM unavailable: use Whisper speaker detection fallback
- If SLM fails on segment: mark as uncertain, continue
- If SLM timeout: continue without diarization

## Performance
- Estimate: ~20% of analysis time
- Can be cached for re-analysis
```

---

### Task 5.2: Create SLM Diarization Module
**Description:** Implement speaker identification using SLM (Small Language Model).

**Acceptance Criteria:**
- [ ] `app/services/diarization_service.py` created
- [ ] SLM prompt engineered for speaker identification
- [ ] Function `identify_speakers()` works correctly
- [ ] Handles different speaker types (Agent, Customer, System, Other)
- [ ] Returns enhanced transcript with speaker labels
- [ ] Confidence scores calculated per speaker
- [ ] Timeouts handled (default: 30s per segment)
- [ ] Ollama integration working
- [ ] Fallback to Whisper labels if SLM fails
- [ ] Service documented with docstrings
- [ ] Performance benchmarked

**Files to Create:**
- `backend/app/services/diarization_service.py`

**Implementation Details:**

```python
class DiarizationService:
    """Identify speakers using SLM (Small Language Model)."""
    
    def identify_speakers(self, transcript: List[TranscriptSegment]) -> List[TranscriptSegment]:
        """
        Identify speakers in transcript using SLM.
        
        Args:
            transcript: List of segments from Whisper
            
        Returns:
            Enhanced transcript with speaker labels and confidence
        """
        # For each segment, call SLM
        # SLM prompt: "Who is speaking in this segment? Agent or Customer?"
        # Return enhanced segments with speaker and confidence
        pass
    
    def _call_slm(self, text: str, segment_context: str) -> Dict:
        """Call Ollama SLM with speaker identification prompt."""
        prompt = f"""
        Given this call transcript segment, identify who is speaking.
        
        Context:
        {segment_context}
        
        Segment:
        {text}
        
        Question: Is this the Agent or Customer speaking?
        Answer: (Agent/Customer/Unclear)
        Confidence: (0-100)
        """
        # Call Ollama /api/generate
        # Parse response
        # Return speaker and confidence
        pass
```

**SLM Prompt Engineering:**
- Start simple: "Who is speaking: Agent or Customer?"
- Add context from previous segments (conversation flow)
- Add confidence scoring
- Handle edge cases (system messages, silence, overlaps)

---

### Task 5.3: Integrate Diarization into Analysis Pipeline
**Description:** Add diarization to the analysis workflow between transcription and analysis.

**Acceptance Criteria:**
- [ ] Diarization called automatically after transcription
- [ ] Diarization output flows to analyzers
- [ ] Talk ratio analyzer uses speaker labels (more accurate)
- [ ] Sentiment analyzer uses speaker labels
- [ ] No breaking changes to existing analyzers
- [ ] Diarization can be disabled via config
- [ ] Error in diarization doesn't block analysis
- [ ] Analysis service updated with diarization call
- [ ] Router updated if needed
- [ ] Tests pass

**Pipeline Flow:**
```
Audio File
    ↓ (Whisper transcription)
Transcript (without speaker labels)
    ↓ (Diarization - NEW STEP)
Transcript (with speaker labels)
    ↓ (Analyzers - updated to use labels)
Analysis Results
    ↓ (Scoring)
Final Score
```

**Code Changes in analysis_service.py:**
```python
def analyze_transcript(self, transcript, weights, profile):
    # 1. Transcription (already done)
    
    # 2. NEW: Diarization
    try:
        transcript = self.diarization_service.identify_speakers(transcript)
    except Exception as e:
        logger.error(f"Diarization failed, continuing without: {e}", exc_info=True)
        # Continue - transcript still has Whisper speaker labels
    
    # 3. Run analyzers (they now use enhanced speaker labels)
    analyzer_results = run_all_analyzers(transcript, profile_config)
    
    # ... rest of analysis
```

---

### Task 5.4: Diarization Testing & Validation
**Description:** Test diarization module, verify accuracy, test edge cases.

**Acceptance Criteria:**
- [ ] Unit test: SLM prompt works correctly
- [ ] Unit test: speaker identification accuracy >85%
- [ ] Unit test: confidence scores reasonable
- [ ] Unit test: timeout handling works
- [ ] Unit test: error handling works (SLM unavailable)
- [ ] Integration test: diarization + analysis pipeline works
- [ ] Integration test: talk ratio more accurate with diarization
- [ ] Integration test: sentiment more accurate with diarization
- [ ] Manual test: sample call analyzed with diarization
- [ ] Performance acceptable (< 5 min for 30 min call)
- [ ] Documentation updated

**Test Scenarios:**
- [ ] Normal call (Agent + Customer)
- [ ] Call with system messages
- [ ] Call with overlapping speech
- [ ] Short call (1 min)
- [ ] Long call (60 min)
- [ ] SLM timeout scenario
- [ ] Ollama unavailable scenario
- [ ] Whisper already has speaker labels

**Validation Metrics:**
- Diarization accuracy: % correct speaker identification
- Comparison with manual review: sample 5-10 calls
- Performance: average time per minute of audio
- Error rate: % segments where diarization failed

---

## PHASE 6: INTEGRATION & QA (Days 9-10)

| Task ID | Task Name | Module | Day | Hours | Story Points | Dependencies | Priority | Status |
|---------|-----------|--------|-----|-------|--------------|--------------|----------|--------|
| 6.1 | End-to-End Testing | QA | 9 | 4 | 3 | 5.4, 3.6 | Critical | Not Started |
| 6.2 | Performance & Load Testing | QA | 9 | 3 | 2 | 6.1 | High | Not Started |
| 6.3 | Code Review & Documentation | Documentation | 10 | 3 | 2 | 6.2 | High | Not Started |
| 6.4 | Deployment Prep & Release | DevOps | 10 | 2 | 1 | 6.3 | Critical | Not Started |

### Task 6.1: End-to-End Testing
**Description:** Complete testing of entire application (frontend + backend + new features).

**Acceptance Criteria:**
- [ ] Upload audio file → transcription → diarization → analysis → results displayed
- [ ] All parameters calculated correctly
- [ ] Weights adjustable and rescore works
- [ ] History saved and retrievable
- [ ] Theme toggle persists
- [ ] Error handling works (bad file, network error, etc.)
- [ ] Mobile view responsive
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] No console errors

**Test Cases:**
1. Happy path: upload audio → get results
2. Weight adjustment: change weights → rescore shows new results
3. History: view previous analyses
4. Error path: upload too-large file → error message shown
5. Error path: network fails → user sees error
6. Diarization: speaker labels visible in transcript
7. Cross-browser: Chrome, Firefox, Edge
8. Mobile: iPhone, iPad, Android

---

### Task 6.2: Performance & Load Testing
**Description:** Test performance, response times, resource usage.

**Acceptance Criteria:**
- [ ] Frontend initial load: < 3 seconds
- [ ] API response time (analyze): < 2 minutes for 30MB file
- [ ] Rescore response: < 500ms
- [ ] History fetch: < 1 second
- [ ] Database query: < 100ms
- [ ] No memory leaks (check with DevTools)
- [ ] CPU usage reasonable (< 80% during analysis)
- [ ] Disk usage reasonable (temp files cleaned up)
- [ ] Log files not growing excessively

**Performance Benchmarks:**
```
Task                    Target      Actual
─────────────────────────────────────────
Frontend load           < 3s        ___
Transcription (30MB)    < 60s       ___
Diarization             < 30s       ___
Analysis (all)          < 60s       ___
Rescore                 < 500ms     ___
History fetch           < 1s        ___
Total pipeline          < 3 min     ___
```

---

### Task 6.3: Code Review & Documentation
**Description:** Review all code, update documentation, prepare for production.

**Acceptance Criteria:**
- [ ] Code review: frontend refactoring
- [ ] Code review: backend refactoring
- [ ] Code review: diarization feature
- [ ] Code review: logging changes
- [ ] All feedback addressed
- [ ] README.md updated
- [ ] ARCHITECTURE.md created (new folder structure)
- [ ] DIARIZATION.md created (feature documentation)
- [ ] API.md updated (with new structure)
- [ ] DEPLOYMENT.md updated
- [ ] Comments added to complex code
- [ ] Docstrings complete

**Documentation Files:**
- [ ] Update `README.md` with new architecture
- [ ] Create `ARCHITECTURE.md` (folder structure + design)
- [ ] Create `DIARIZATION.md` (how diarization works)
- [ ] Create `MIGRATION.md` (how to upgrade from old version)
- [ ] Update `LOGGING_GUIDE.md` (reflect new logging approach)
- [ ] Create `DEVELOPER_SETUP.md` (how to set up local env)

---

### Task 6.4: Deployment Prep & Release
**Description:** Prepare for production deployment, create release notes.

**Acceptance Criteria:**
- [ ] All tests passing
- [ ] All PRs merged/closed
- [ ] Git tags created (v2.0.0)
- [ ] Release notes written
- [ ] Migration guide prepared
- [ ] Rollback plan documented
- [ ] Monitoring checks in place
- [ ] Backup procedures verified
- [ ] Team training completed
- [ ] Ready for production

**Deliverables:**
- [ ] Release notes (v2.0.0)
- [ ] Migration guide
- [ ] Rollback procedure
- [ ] Monitoring dashboard
- [ ] Team documentation

---

## SUMMARY TABLE (For Excel/Spreadsheet)

| Phase | Days | Tasks | Hours | Story Points | Key Deliverables |
|-------|------|-------|-------|--------------|------------------|
| 1: Setup | 1 | 3 | 4 | 4 | Feature branch, audit doc |
| 2: Frontend | 2-5 | 5 | 18 | 12 | Refactored App.jsx, hooks, views |
| 3: Backend | 2-7 | 6 | 20 | 13 | Services, routers, refactored main.py |
| 4: Logging | 3-4 | 3 | 7 | 4 | Clean, error-focused logging |
| 5: Diarization | 5-8 | 4 | 14 | 10 | Speaker identification feature |
| 6: QA & Deploy | 9-10 | 4 | 12 | 8 | Tests pass, release notes, deployment |
| **TOTAL** | **10** | **25** | **75** | **51** | **Production-ready v2.0** |

---

## DEPENDENCIES GRAPH

```
Day 1
├─ 1.1: Setup ✓
├─ 1.2: Audit ✓
└─ 1.3: Create dirs ✓

Day 2
├─ 2.1: Frontend constants (→ 2.2)
├─ 3.1: Backend config (→ 3.2, 3.3)
└─ 3.2: Backend models (→ 3.3)

Day 3-4
├─ 2.2: Frontend hooks (→ 2.3)
├─ 3.3: Backend services (→ 3.4)
└─ 4.1: Remove debug logs (parallel)

Day 4-5
├─ 2.3: Frontend views (→ 2.4)
├─ 3.4: Backend routers (→ 3.5)
├─ 4.2: Error-focused logging (→ 4.3)
└─ 5.1: Diarization design (→ 5.2)

Day 5-6
├─ 2.4: Refactor App.jsx (→ 2.5)
├─ 3.5: Refactor main.py (→ 3.6)
├─ 4.3: Logging testing
└─ 5.2: SLM diarization module (→ 5.3)

Day 6-7
├─ 2.5: Frontend testing
├─ 3.6: Backend testing
└─ 5.3: Integrate diarization (→ 5.4)

Day 7-8
├─ 5.4: Diarization testing (→ 6.1)

Day 9-10
├─ 6.1: E2E testing (→ 6.3)
├─ 6.2: Performance testing (→ 6.3)
├─ 6.3: Code review & docs (→ 6.4)
└─ 6.4: Deployment prep
```

---

## SCRUM METRICS

### Velocity
- **Total Story Points**: 51
- **Days**: 10 (2 weeks)
- **Average Per Day**: 5.1 points/day

### Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| SLM diarization too slow | Medium | High | Cache results, fallback to whisper labels |
| Frontend refactor breaks features | Low | High | Extensive testing, feature parity checks |
| Backend services hard to test | Low | Medium | Use dependency injection, mocking |
| Diarization accuracy < 80% | Medium | Medium | Augment with Whisper speaker detection |
| Performance degradation | Medium | High | Benchmark daily, optimize if needed |

### Success Criteria
- ✅ All 25 tasks completed
- ✅ All tests passing (frontend, backend, integration)
- ✅ Diarization accuracy > 80%
- ✅ Performance within targets
- ✅ Zero breaking changes to API
- ✅ Documentation complete
- ✅ Team trained on new architecture

---

