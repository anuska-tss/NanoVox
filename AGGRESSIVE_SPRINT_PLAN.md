# NanoVox Production Refactoring - AGGRESSIVE 3-5 DAY SPRINT
## Fast-Track Schedule (Maximum Parallelization)

---

## STRATEGY: MVP + Aggressive Parallelization

### What We KEEP (Critical)
✅ Backend refactoring (services, routers, clean main.py)
✅ Frontend refactoring (hooks, views, clean App.jsx)
✅ Logging cleanup (remove debug logs, add error handling)
✅ Diarization feature (SLM-based speaker ID)

### What We DEFER (Minimal)
⏳ Comprehensive documentation (can be enhanced later)
⏳ Exhaustive testing (basic smoke tests only)
⏳ Performance benchmarking (tune in production)
⏳ Migration guide (defer to follow-up)

### Workday Hours
- **Day 1-3**: 10 hours/day
- **Day 4-5**: 9 hours/day
- **Total**: 57-66 hours (achievable)

---

## DAY 1: FOUNDATIONS (10 hours)
### "Get the structure right"

**Parallel Workstreams (All Start Simultaneously)**

#### 🟦 FRONTEND TRACK (3.5 hours, 2 people or sequential)
**Tasks:**
- 2.1: Extract Constants (1 hour)
- 2.2: Create 5 Custom Hooks (2 hours)
- Start 2.3: Create View Components (skeleton only, 0.5 hours)

**Deliverables by EOD:**
- ✅ `src/constants/` directory with 4 constant files
- ✅ `src/hooks/` directory with 5 custom hooks
- ✅ View component skeletons created (empty)

**Setup (First 30 min):**
```bash
# Create feature branch
git checkout -b feature/production-refactoring

# Frontend: Create directories and constant files
frontend/
  src/
    constants/
      storageKeys.js    # STORAGE_KEYS
      weights.js        # DEFAULT_WEIGHTS
      analysis.js       # ANALYSIS_CONFIG
      processingSteps.js # PROCESSING_STEPS, STEP_STATUS
    hooks/
      useAnalysis.js    # Analysis logic
      useTheme.js       # Theme logic
      useWeights.js     # Weights logic
      useHistory.js     # History logic
      useFileUpload.js  # File validation
    components/
      views/
        LandingView.jsx
        ProcessingView.jsx
        DashboardView.jsx
        HistoryView.jsx
      layout/
        Header.jsx
```

**Quick Implementation (Hooks):**
- Copy business logic from current App.jsx into hooks
- No external dependencies
- Add basic error handling
- No tests (skip for speed)

---

#### 🟫 BACKEND TRACK (3.5 hours, parallel)
**Tasks:**
- 1.3: Create Directory Structure (0.5 hours)
- 3.1: Create Config Layer (1 hour)
- 3.2: Create Models Layer (1 hour)
- Start 3.3: Create Service Layer (1 hour)

**Deliverables by EOD:**
- ✅ `backend/app/` package structure created
- ✅ `app/config/settings.py` with Settings class
- ✅ `.env` and `.env.example` files
- ✅ `app/models/` with split models
- ✅ `app/services/` skeleton with AnalysisService started

**Structure:**
```
backend/app/
  __init__.py
  config/
    __init__.py
    settings.py       # Settings class (DONE)
  models/
    __init__.py
    requests.py       # Pydantic models
    responses.py
    analysis.py
  services/
    __init__.py
    analysis_service.py    # (skeleton)
    history_service.py     # (skeleton)
    file_service.py        # (skeleton)
  api/routers/ (create empty)
  core/ (create empty)
  ml/ (create empty)
  main.py (keep old for now)
```

**Quick Implementation:**
- Copy existing Pydantic models to new files
- Create Settings class from backend_config.json + .env
- No validation of settings yet
- Services: just function signatures, no implementation

---

#### 🟪 LOGGING TRACK (2 hours, parallel)
**Tasks:**
- 1.2: Quick Code Audit (1 hour)
- 4.1: Remove Debug Logs (1 hour)

**Deliverables by EOD:**
- ✅ `CURRENT_STATE_AUDIT.md` document
- ✅ All "🧪 [DEBUG]" logs removed from Python files
- ✅ Baseline metric: X debug logs removed

**Quick Audit (30 min):**
```
# Metrics to gather (quick)
App.jsx: ___ lines, ___ useState, ___ useEffect
main.py: ___ routes, ___ lines, ___ logger.info()
Backend: ___ debug log instances found

Issues:
- [x] Debug logging everywhere
- [x] State scattered in App.jsx
- [x] Routes mixed with logic in main.py
```

**Remove Logs (30 min):**
```bash
# Find and remove
grep -r "🧪 \[DEBUG\]" backend/ # find all
# Replace with nothing (sed or manual)
grep -r "logger.info.*🧪" backend/ # verify
```

---

### END OF DAY 1 CHECKPOINT ✅
```
Frontend:  Constants ✅ | Hooks ✅ | Views skeleton ✅
Backend:   Structure ✅ | Config ✅ | Models ✅ | Services started
Logging:   Audit ✅ | Debug logs removed ✅
Status:    Code still runs | No breaking changes
```

**Commits to Push:**
```bash
git commit -m "feat: create directory structure and constants"
git commit -m "feat: create custom hooks (useAnalysis, useTheme, useWeights, etc)"
git commit -m "feat: create backend config layer with Settings class"
git commit -m "feat: organize Pydantic models into separate files"
git commit -m "chore: remove debug logging from codebase"
```

---

## DAY 2: INTEGRATION (10 hours)
### "Connect the pieces"

#### 🟦 FRONTEND TRACK (4 hours)
**Tasks:**
- 2.3: Create View Components (2 hours)
- 2.4: Refactor App.jsx (1.5 hours)
- 2.5: Quick Frontend Test (0.5 hours)

**Implementation Strategy:**
- Copy rendering logic from old App.jsx into view components
- No new styling (reuse existing CSS)
- Strip App.jsx to bare minimum
- Run in browser and verify basics work

**Time Breakdown:**
```
2.3: Views (2h)
  - LandingView.jsx (30 min)   - Copy from App.jsx
  - ProcessingView.jsx (20 min)
  - DashboardView.jsx (30 min)
  - HistoryView.jsx (20 min)
  - Header.jsx (20 min)
  - Copy corresponding CSS blocks

2.4: Refactor App.jsx (1.5h)
  - Import hooks at top (10 min)
  - Replace state with hook calls (20 min)
  - Replace effects with hook effects (10 min)
  - Replace handlers with hook functions (20 min)
  - Clean up render function (30 min)
  - Result: 80-90 lines ✅

2.5: Test (0.5h)
  - npm run dev
  - Click buttons, verify no errors
  - Test file upload
  - Test theme toggle
```

**Deliverables by EOD:**
- ✅ View components created (minimal styling)
- ✅ App.jsx refactored to 80-90 lines
- ✅ Frontend runs without errors
- ✅ All basic features work

---

#### 🟫 BACKEND TRACK (4 hours)
**Tasks:**
- 3.3: Complete Service Layer (1.5 hours)
- 3.4: Create Router Files (1.5 hours)
- Start 3.5: Begin main.py refactor (1 hour)

**Implementation Strategy:**
- Move logic from current main.py into services
- Services contain business logic, routers just HTTP
- Routers import services and call them
- Keep it simple: no deep abstractions yet

**Time Breakdown:**
```
3.3: Services (1.5h)
  - AnalysisService (0.75h)   - copy logic from main.py
  - HistoryService (0.5h)
  - FileService skeleton (0.25h)

3.4: Routers (1.5h)
  - Create app/api/routers/ files
  - analysis.py: /api/analyze, /api/test-analysis (0.75h)
  - history.py: /api/history endpoints (0.5h)
  - health.py, weights.py (0.25h)
  - Routers call services, no duplicate logic

3.5: main.py (1h)
  - Start new main.py (skeleton)
  - Import routers
  - Test app starts with new structure
```

**Deliverables by EOD:**
- ✅ Services created with business logic
- ✅ Router files created (bare minimum)
- ✅ main.py partially refactored
- ✅ Backend starts without errors

---

#### 🟪 LOGGING TRACK (2 hours)
**Tasks:**
- 4.2: Add Error-Focused Logging (2 hours)

**Implementation Strategy:**
- Wrap key functions in try-except
- Log only errors with `exc_info=True`
- Remove all info-level logs from happy path
- Target: 0 logs when things work, detailed logs on errors

**Time Breakdown:**
```
4.2: Error Logging (2h)
  - Add try-except to API routes (0.5h)
  - Add try-except to services (0.5h)
  - Add try-except to analyzers (0.5h)
  - Pattern: logger.error(..., exc_info=True) (0.5h)
```

**Deliverables by EOD:**
- ✅ Try-except blocks added to critical paths
- ✅ Error logging pattern implemented
- ✅ Info logs removed from happy path
- ✅ Error scenarios log with full tracebacks

---

### END OF DAY 2 CHECKPOINT ✅
```
Frontend:  View components ✅ | App.jsx refactored ✅ | Works ✅
Backend:   Services ✅ | Routers ✅ | main.py started ✅
Logging:   Error-focused logging ✅
Status:    Backend needs final main.py polish | Frontend ready
```

**Commits to Push:**
```bash
git commit -m "feat: create view components and refactor App.jsx"
git commit -m "feat: create backend services layer"
git commit -m "feat: create router files for API endpoints"
git commit -m "feat: implement error-focused logging"
```

---

## DAY 3: BACKEND COMPLETION + DIARIZATION (10 hours)
### "Finish backend refactoring and add speaker ID"

#### 🟫 BACKEND TRACK (5 hours)
**Tasks:**
- 3.5: Complete main.py refactoring (1 hour)
- 3.6: Backend Testing & Integration (1.5 hours)
- Start 5.1-5.2: Diarization Service (2.5 hours)

**Implementation:**
```
3.5: main.py (1h)
  - Clean up app creation (10 min)
  - Register all routers (10 min)
  - Setup CORS from settings (10 min)
  - Define startup/shutdown (20 min)
  - Test all routes work (10 min)

3.6: Backend Testing (1.5h)
  - Test /api/analyze endpoint (20 min)
  - Test /api/test-analysis (15 min)
  - Test /api/rescore (15 min)
  - Test /api/history (15 min)
  - Fix any critical bugs (30 min)

5.1-5.2: Diarization (2.5h)
  - Create DiarizationService skeleton (0.5h)
  - Engineer SLM prompt (1h)
  - Implement identify_speakers() (1h)
  - Basic error handling (0.5h)
```

**Diarization Quick Implementation:**
```python
# app/services/diarization_service.py
class DiarizationService:
    def identify_speakers(self, transcript):
        """Identify speakers using SLM prompt."""
        for segment in transcript:
            try:
                # Call Ollama with prompt
                speaker = call_slm_prompt(segment.text)
                segment.speaker = speaker  # Add label
            except Exception as e:
                logger.error(f"Diarization failed: {e}")
                # Continue with original speaker label
        return transcript

def call_slm_prompt(text):
    """Call Ollama SLM for speaker identification."""
    prompt = f"Is this Agent or Customer speaking? Text: {text}"
    # Call Ollama /api/generate
    # Parse response
    # Return speaker label
    pass
```

**Deliverables by EOD:**
- ✅ main.py fully refactored (50-60 lines)
- ✅ All API endpoints working
- ✅ Backend structure complete
- ✅ DiarizationService created
- ✅ SLM speaker identification working

---

#### 🟪 FRONTEND TRACK (3 hours)
**Tasks:**
- 2.5: Complete Frontend Testing (1 hour)
- Final Polish (2 hours)

**Quick Testing:**
```
- File upload works ✅
- Processing view shows progress ✅
- Results display ✅
- Theme toggle works ✅
- Weights persist ✅
- History loads ✅
- No console errors ✅
```

**Polish (2 hours):**
- Fix any visual bugs
- Verify responsive on mobile
- Check all links work
- Clean up console warnings

**Deliverables by EOD:**
- ✅ Frontend fully working
- ✅ All features verified
- ✅ Ready for integration with backend

---

#### 🟪 INTEGRATION TRACK (2 hours)
**Tasks:**
- Basic E2E Test: Frontend → Backend → Results

**Quick Test:**
```
1. Start backend: python backend/main.py ✅
2. Start frontend: npm run dev ✅
3. Upload file → transcription → analysis ✅
4. Results show in dashboard ✅
5. No errors in console/logs ✅
```

**Deliverables by EOD:**
- ✅ Frontend + Backend integrated
- ✅ Full pipeline works end-to-end
- ✅ No breaking changes

---

### END OF DAY 3 CHECKPOINT ✅
```
Frontend:  Complete ✅ | Tested ✅ | Working ✅
Backend:   Complete ✅ | Tested ✅ | Working ✅
Logging:   Complete ✅
Diarization: Service created ✅ | SLM prompt working ✅
Integration: E2E pipeline working ✅
Status:    READY FOR PRODUCTION ✅ (with diarization integration next)
```

**Commits to Push:**
```bash
git commit -m "feat: complete main.py refactoring"
git commit -m "test: backend API endpoints verified"
git commit -m "feat: create diarization service with SLM"
git commit -m "test: E2E pipeline integration working"
```

---

## DAY 4 (OPTIONAL): DIARIZATION COMPLETION (9 hours)
### "Integrate speaker ID into analysis and test"

#### 🟫 DIARIZATION TRACK (5 hours)
**Tasks:**
- 5.3: Integrate Diarization into Pipeline (2 hours)
- 5.4: Diarization Testing (3 hours)

**Integration (2 hours):**
```python
# Modify app/services/analysis_service.py
def analyze_transcript(self, transcript, weights, profile):
    # Existing: transcription ✅
    
    # NEW: Diarization
    try:
        transcript = self.diarization_service.identify_speakers(transcript)
    except Exception as e:
        logger.error(f"Diarization failed, continuing: {e}")
        # Continue without diarization
    
    # Existing: Run analyzers (now with speaker labels)
    results = run_all_analyzers(transcript, profile_config)
    
    # Rest of analysis...
    return results
```

**Testing (3 hours):**
- Test with sample audio file
- Verify speaker labels in results
- Test error scenario (SLM down)
- Measure performance impact
- Verify accuracy > 75% (acceptable for MVP)

**Deliverables by EOD:**
- ✅ Diarization integrated into analysis
- ✅ Speaker ID appears in results
- ✅ Error handling robust
- ✅ Performance acceptable

---

#### 🟪 TESTING TRACK (3 hours)
**Tasks:**
- Complete E2E testing with diarization
- Performance checks
- Error scenario testing

**Test Scenarios (3 hours):**
```
1. Happy path: upload file → diarization → analysis ✅
2. Error: SLM unavailable → fallback works ✅
3. Performance: analyze 30min file < 5 min ✅
4. Accuracy: speaker ID correct > 75% ✅
5. Cross-browser: Chrome, Firefox ✅
```

**Deliverables by EOD:**
- ✅ All features tested end-to-end
- ✅ With diarization working
- ✅ Error paths covered
- ✅ Performance verified

---

#### 🟪 DOCUMENTATION TRACK (1 hour)
**Tasks:**
- Quick README update
- Quick ARCHITECTURE doc

**Minimal Docs (1 hour):**
```
README.md
- Update "new architecture" section
- Add link to ARCHITECTURE.md

ARCHITECTURE.md (new)
- Folder structure diagram
- Component diagram (brief)
- Data flow (brief)
```

**Deliverables by EOD:**
- ✅ README updated
- ✅ Basic ARCHITECTURE doc

---

### END OF DAY 4 CHECKPOINT ✅
```
Diarization: Integrated ✅ | Tested ✅ | Working ✅
E2E:         All features tested ✅
Performance: Verified ✅
Docs:        Basic docs ✅
Status:      PRODUCTION READY WITH DIARIZATION ✅✅✅
```

**Commits to Push:**
```bash
git commit -m "feat: integrate diarization into analysis pipeline"
git commit -m "test: E2E testing with diarization complete"
git commit -m "docs: update README and architecture documentation"
```

---

## DAY 5 (OPTIONAL): FINAL CLEANUP + RELEASE (9 hours)
### "Polish and prepare for production"

#### 📋 FINAL CHECKS (3 hours)
- Code review of all changes
- Verify no regressions
- Test with sample calls
- Check performance logs

#### 📚 FINAL DOCUMENTATION (2 hours)
- Create DIARIZATION.md (how diarization works)
- Create DEPLOYMENT.md (how to deploy)
- Update API documentation

#### 🚀 RELEASE PREP (2 hours)
- Create git tag `v2.0.0`
- Write release notes
- Document breaking changes (none)
- Verify rollback plan

#### ✅ HANDOFF (2 hours)
- Team meeting: show new architecture
- Demonstrate refactored code
- Explain diarization feature
- Q&A with team

---

### END OF DAY 5 CHECKPOINT ✅
```
Code Review:  All changes verified ✅
Testing:      No regressions ✅
Documentation: Complete ✅
Release:      Ready for deployment ✅
Team:         Trained and ready ✅
Status:       PRODUCTION DEPLOYMENT READY ✅✅✅
```

**Final Commits:**
```bash
git commit -m "docs: add diarization and deployment documentation"
git tag -a v2.0.0 -m "Production refactoring: modular architecture + diarization"
git push origin feature/production-refactoring
git push origin v2.0.0
```

---

## AGGRESSIVE TIMELINE SUMMARY

```
┌─────────────────────────────────────────────────────────────────┐
│                    3-5 DAY SPRINT (AGGRESSIVE)                  │
├─────────────────────────────────────────────────────────────────┤
│ DAY 1 (10h): Structure, Hooks, Services, Clean Logs             │
│ DAY 2 (10h): Views, Routers, Refactor main.py, Error Logging    │
│ DAY 3 (10h): Backend Complete + Diarization Service + E2E Test  │
│ DAY 4 (9h):  Diarization Integration + Testing + Docs           │
│ DAY 5 (9h):  Final Checks + Release Prep (OPTIONAL)             │
├─────────────────────────────────────────────────────────────────┤
│ TOTAL: 48-57 hours | 25 tasks | PRODUCTION READY               │
└─────────────────────────────────────────────────────────────────┘
```

---

## WHAT WE CUT (To fit 3-5 days)

❌ **Comprehensive testing** → Only smoke tests (basic validation)
❌ **Performance benchmarking** → Performance verified, not optimized
❌ **Migration guide** → Can be created in follow-up sprint
❌ **Exhaustive documentation** → Only README + basic architecture
❌ **Unit tests for services** → Will add in follow-up
❌ **Component test coverage** → Will add in follow-up
❌ **Load testing** → Can be done in staging
❌ **Security audit** → Can be done separately
❌ **Accessibility testing** → Can be done in follow-up
❌ **TypeScript migration** → Defer to future

---

## WHAT STAYS (Core Value)

✅ **Architecture** - Clean separation of concerns (frontend/backend)
✅ **Maintainability** - Code organization for team development
✅ **Diarization** - Speaker identification feature
✅ **Logging** - Error-focused, production-ready
✅ **Functionality** - Zero breaking changes to API
✅ **Integration** - Frontend + Backend working together

---

## PARALLEL EXECUTION KEY

### Day 1 Simultaneous Starts (Pick ONE person for each):
```
Person A: Frontend track (constants + hooks)
Person B: Backend track (structure + config + models)
Person C: Logging track (audit + remove debug logs)
```

**Or Solo (Sequence by dependency):**
```
1. 30 min: Audit + directory structure
2. 1 hour: Extract constants (can read existing code)
3. 1.5 hours: Create hooks (copy business logic)
4. 1 hour: Config layer (copy from JSON)
5. 1 hour: Models (move Pydantic models)
6. 1 hour: Remove debug logs
Total: 5.5 hours for Day 1 if solo
```

---

## SUCCESS METRICS

| Metric | Target | Day 3 | Day 5 |
|--------|--------|-------|-------|
| Lines in App.jsx | < 100 | 80 ✅ | 80 ✅ |
| Lines in main.py | < 60 | 55 ✅ | 55 ✅ |
| Debug logs removed | 0 | 0 ✅ | 0 ✅ |
| Error-focused logging | 100% | 95% | 100% ✅ |
| Diarization accuracy | > 75% | 78% | 85% ✅ |
| API endpoints working | 100% | 100% ✅ | 100% ✅ |
| E2E pipeline works | Yes | Yes ✅ | Yes ✅ |
| Breaking changes | 0 | 0 ✅ | 0 ✅ |
| Team ready to use | Yes | Partial | Yes ✅ |

---

## RISK FACTORS

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Parallelization conflicts | Low | Small teams or sequential |
| SLM diarization slow | Medium | Fallback to Whisper labels |
| Backend services have bugs | Medium | Minimal implementation first |
| Frontend styling breaks | Low | Reuse existing CSS only |
| Integration fails | Low | E2E test on Day 3 evening |
| Time overruns | Medium | Cut documentation further |

---

## DAILY CHECKLIST (Print this!)

### DAY 1
- [ ] Feature branch created
- [ ] Frontend: Constants extracted
- [ ] Frontend: 5 hooks created
- [ ] Backend: Directory structure created
- [ ] Backend: Config layer complete
- [ ] Backend: Models organized
- [ ] Logging: Audit document
- [ ] Logging: Debug logs removed
- **Code runs without errors?** YES / NO

### DAY 2
- [ ] Frontend: View components created
- [ ] Frontend: App.jsx refactored (<100 lines)
- [ ] Frontend: Works in browser
- [ ] Backend: Services created
- [ ] Backend: Routers created
- [ ] Backend: main.py partially refactored
- [ ] Logging: Error-focused logging added
- **Frontend runs?** YES / NO
- **Backend starts?** YES / NO

### DAY 3
- [ ] Backend: main.py complete
- [ ] Backend: All API endpoints work
- [ ] Frontend: All features tested
- [ ] Diarization: Service created
- [ ] Diarization: SLM prompts working
- [ ] Integration: E2E pipeline works
- **Full pipeline works?** YES / NO
- **Any breaking changes?** NO / YES

### DAY 4 (Optional)
- [ ] Diarization: Integrated into pipeline
- [ ] Diarization: Tested and working
- [ ] E2E: All scenarios tested
- [ ] Performance: Verified acceptable
- [ ] Docs: README updated
- [ ] Docs: ARCHITECTURE.md created
- **Ready for production?** YES / NO

### DAY 5 (Optional)
- [ ] Final code review
- [ ] Final testing (no regressions)
- [ ] Documentation complete
- [ ] Git tag v2.0.0 created
- [ ] Release notes written
- [ ] Team trained
- **Ready to deploy?** YES / NO

---

## FOR YOUR SCRUM MASTER

**Pitch:**
> We can deliver a production-grade refactoring in 3 business days (or 5 with optional polish). This includes complete architectural restructuring of frontend/backend plus a new diarization feature using SLM. We're cutting scope on testing and documentation to fit the timeline, but all code is production-ready.

**Risks:**
- SLM speaker identification might be slower than expected (have Whisper fallback)
- Integration bugs might surface (E2E testing on Day 3 catches them)
- Some documentation deferred (can be completed in follow-up sprint)

**Deliverables:**
- ✅ Modular frontend architecture (hooks, views, clean App.jsx)
- ✅ Modular backend architecture (services, routers, clean main.py)
- ✅ Production logging (error-focused, debug logs removed)
- ✅ Speaker identification feature (SLM-based diarization)
- ✅ Working E2E pipeline
- ✅ Zero breaking changes to API

**Team Capacity:**
- If 1 developer: **5 days (sequential)**
- If 2 developers (parallel): **3 days**
- If 3 developers (full parallel): **2.5 days**

---

## CSV EXPORT FOR AGGRESSIVE TIMELINE

See next file: `AGGRESSIVE_SPRINT_TASKS.csv`

