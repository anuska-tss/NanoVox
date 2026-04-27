# NanoVox Refactoring - Daily Sprint Schedule

## **DAY 1 (Monday): Planning & Setup**

### Morning (4 hours)
**Tasks to Complete:**
- ✅ Task 1.1: Environment Setup & Feature Branch (1 hour)
- ✅ Task 1.2: Code Audit & Documentation (2 hours)
- ✅ Task 1.3: Create Directory Structure (1 hour)

**Deliverables:**
- [ ] Feature branch `feature/production-refactoring` created and pushed
- [ ] `CURRENT_STATE_AUDIT.md` document with findings
- [ ] All directories created: `backend/app/{config,api/routers,services,core,models,ml}`
- [ ] All `__init__.py` files created

**Time Allocation:**
```
1.1: Setup (1h)
  - git checkout -b feature/production-refactoring
  - Test backend startup: python backend/main.py
  - Test frontend: npm run dev
  
1.2: Audit (2h)
  - Analyze App.jsx (lines, state count, logic)
  - Analyze main.py (routes, logic, complexity)
  - List all debug logs ("🧪 [DEBUG]")
  - Document in CURRENT_STATE_AUDIT.md
  
1.3: Structure (1h)
  - Create backend/app/ package
  - Create all subdirectories
  - Create __init__.py files everywhere
```

### Standup (30 min)
- Summarize findings from audit
- Highlight risks and dependencies
- Confirm plan with team

### End of Day Checklist
- [ ] Feature branch created and pushed
- [ ] Audit document completed
- [ ] All directories created
- [ ] Code still runs (no breaking changes yet)
- [ ] All 3 tasks marked "Complete"

---

## **DAY 2 (Tuesday): Backend Configuration & Frontend Constants**

### Morning (4 hours) - Backend Configuration
**Tasks to Complete:**
- ✅ Task 3.1: Create Config Layer (2 hours)
- ✅ Task 3.2: Create Models Layer (2 hours)

**Deliverables:**
- [ ] `app/config/settings.py` with Settings class
- [ ] `.env` and `.env.example` files
- [ ] `app/models/` package with split models
- [ ] Backward compatibility layer

**Time Allocation:**
```
3.1: Config (2h)
  - Create app/config/settings.py
  - Define Settings class with defaults
  - Create .env template
  - Test loading from environment
  
3.2: Models (2h)
  - Create app/models/__init__.py
  - Create app/models/requests.py
  - Create app/models/responses.py
  - Create app/models/analysis.py
  - Update backend/models.py to re-export
```

### Afternoon (4 hours) - Frontend Constants
**Tasks to Complete:**
- ✅ Task 2.1: Create Constants & Utils Layer (3 hours)

**Deliverables:**
- [ ] `src/constants/` directory with all constant files
- [ ] `src/utils/` updated with validators and formatters
- [ ] All imports in App.jsx updated
- [ ] No linting errors

**Time Allocation:**
```
2.1: Constants (3h)
  - Create src/constants/storageKeys.js
  - Create src/constants/weights.js
  - Create src/constants/analysis.js
  - Create src/constants/processingSteps.js
  - Create src/utils/validators.js
  - Create src/utils/formatters.js
  - Update src/utils/helpers.js
  - Test imports in App.jsx
```

### End of Day Checklist
- [ ] Backend config created and tested
- [ ] All models organized in new structure
- [ ] Frontend constants extracted
- [ ] All imports working (no errors)
- [ ] Code still runs without breaking
- [ ] Tasks 3.1, 3.2, 2.1 marked "Complete"

---

## **DAY 3 (Wednesday): Frontend Hooks & Backend Services (Parallel)**

### Morning (4 hours) - Frontend Hooks
**Tasks to Complete:**
- ✅ Task 2.2: Create Custom Hooks (4 hours)

**Deliverables:**
- [ ] All 5 custom hooks created in `src/hooks/`
- [ ] Each hook has JSDoc comments
- [ ] Unit tests written for each hook
- [ ] No external dependencies added

**Time Allocation:**
```
2.2: Hooks (4h)
  - Create useAnalysis.js (1.5h)
  - Create useTheme.js (0.5h)
  - Create useWeights.js (0.5h)
  - Create useHistory.js (0.5h)
  - Create useFileUpload.js (0.5h)
  - Test each hook independently (0.5h)
```

### Afternoon (4 hours) - Backend Services (Parallel)
**Tasks to Complete:**
- ✅ Task 3.3: Create Service Layer (4 hours)

**Deliverables:**
- [ ] All service classes created
- [ ] Services have single responsibility
- [ ] Services use dependency injection
- [ ] Error handling implemented
- [ ] Unit test skeletons created

**Time Allocation:**
```
3.3: Services (4h)
  - Create AnalysisService (1.5h)
  - Create HistoryService (1h)
  - Create FileService (0.75h)
  - Create WeightService (0.75h)
  - Add error handling to each (1h)
```

### Parallel: Logging Cleanup
**Tasks (Low Priority - Async):**
- 📝 Task 4.1: Remove Debug Logs (can do in background)

### End of Day Checklist
- [ ] All 5 hooks created and tested
- [ ] All 4 services created with error handling
- [ ] No changes to App.jsx yet (safe point)
- [ ] Tasks 2.2, 3.3 marked "Complete"
- [ ] Task 4.1 ~50% complete (logging audit done)

---

## **DAY 4 (Thursday): Frontend Views & Logging**

### Morning (4 hours) - Frontend Views
**Tasks to Complete:**
- ✅ Task 2.3: Create View Components (4 hours)

**Deliverables:**
- [ ] All 5 view components created
- [ ] All CSS files created
- [ ] Props properly documented
- [ ] Views render without errors
- [ ] Responsive design verified

**Time Allocation:**
```
2.3: Views (4h)
  - Create LandingView.jsx + CSS (1.5h)
  - Create ProcessingView.jsx + CSS (0.75h)
  - Create DashboardView.jsx + CSS (1h)
  - Create HistoryView.jsx + CSS (0.75h)
  - Create Header.jsx + CSS (0.5h)
  - Test all render correctly (0.5h)
```

### Afternoon (4 hours) - Logging & Router Planning
**Tasks to Complete:**
- ✅ Task 4.1: Remove Debug Logs (Complete) (1.5 hours)
- ✅ Task 4.2: Implement Error-Focused Logging (2 hours)
- ✅ Task 3.4: Create Router Files (Design only, 0.5 hours)

**Deliverables:**
- [ ] All debug logs removed
- [ ] Try-except blocks added to key areas
- [ ] Error logging pattern implemented
- [ ] Router file design documented

**Time Allocation:**
```
4.1: Remove Logs (1.5h)
  - Search for "🧪 [DEBUG]" (search: 0.25h)
  - Remove all instances (0.5h)
  - Search for logger.info() in hot paths (0.25h)
  - Remove unnecessary info logs (0.5h)
  
4.2: Error Logging (2h)
  - Add try-except to API routes (0.75h)
  - Add try-except to services (0.75h)
  - Implement error logging pattern (0.5h)
  
3.4: Router Design (0.5h)
  - Plan router file structure
  - Identify which routes go where
```

### End of Day Checklist
- [ ] All view components created and styled
- [ ] Debug logs removed from codebase
- [ ] Error-focused logging implemented
- [ ] Router files designed (ready for next step)
- [ ] Tasks 2.3, 4.1, 4.2 marked "Complete"
- [ ] Code tested and running

---

## **DAY 5 (Friday): Refactor App.jsx & Frontend Testing**

### Morning (4 hours) - Refactor App.jsx
**Tasks to Complete:**
- ✅ Task 2.4: Refactor App.jsx (3 hours)

**Deliverables:**
- [ ] App.jsx reduced to 80-100 lines
- [ ] All state logic moved to hooks
- [ ] All rendering moved to views
- [ ] All imports clean
- [ ] All functionality preserved

**Time Allocation:**
```
2.4: Refactor App.jsx (3h)
  - Remove all state declarations (moved to hooks)
  - Remove all useEffect hooks (moved to hooks)
  - Remove all handlers (replaced with hook functions)
  - Create new minimal App.jsx
  - Test functionality
  - Fix any import errors
```

### Afternoon (4 hours) - Frontend Testing
**Tasks to Complete:**
- ✅ Task 2.5: Frontend Testing & Bug Fixes (4 hours)

**Deliverables:**
- [ ] All features work identically to before
- [ ] Theme toggle works
- [ ] File upload works
- [ ] Weight changes persist
- [ ] History fetching works
- [ ] No console errors
- [ ] Mobile responsive verified

**Time Allocation:**
```
2.5: Testing (4h)
  - Manual test landing page (0.5h)
  - Manual test file upload (0.5h)
  - Manual test processing view (0.5h)
  - Manual test dashboard (0.5h)
  - Manual test history (0.5h)
  - Test theme toggle (0.25h)
  - Test weight persistence (0.25h)
  - Mobile responsive test (0.5h)
  - Fix any bugs found (1h)
```

### Parallel: Diarization Design
**Tasks (Low Priority):**
- 📝 Task 5.1: Design Diarization (can start)

### End of Day Checklist
- [ ] App.jsx refactored and working
- [ ] All frontend features tested
- [ ] No console errors
- [ ] Mobile view responsive
- [ ] Tasks 2.4, 2.5 marked "Complete"
- [ ] **FRONTEND REFACTORING COMPLETE** ✅

---

## **DAY 6 (Monday, Week 2): Backend Routers & Diarization Module**

### Morning (5 hours) - Create Router Files
**Tasks to Complete:**
- ✅ Task 3.4: Create Router Files (4 hours)

**Deliverables:**
- [ ] `routers/analysis.py` created with /api/analyze, /api/test-analysis
- [ ] `routers/history.py` created with history endpoints
- [ ] `routers/weights.py` created with weights endpoint
- [ ] `routers/health.py` created with health check
- [ ] All routers use services (no duplicate logic)
- [ ] All routers have proper error handling
- [ ] All tests pass

**Time Allocation:**
```
3.4: Routers (4h)
  - Create analysis.py (1.5h)
  - Create history.py (1h)
  - Create weights.py (0.5h)
  - Create health.py (0.5h)
  - Test all routes work (0.5h)
```

### Afternoon (3 hours) - Diarization Design
**Tasks to Complete:**
- ✅ Task 5.1: Design Diarization Service (2 hours)
- ✅ Task 5.2: Start SLM Diarization Module (1 hour)

**Deliverables:**
- [ ] `DIARIZATION_DESIGN.md` document completed
- [ ] SLM prompt engineered
- [ ] Architecture documented
- [ ] `app/services/diarization_service.py` skeleton created

**Time Allocation:**
```
5.1: Design (2h)
  - Document diarization overview (0.5h)
  - Design input/output models (0.5h)
  - Design integration points (0.5h)
  - Design error handling (0.5h)
  
5.2: SLM Module Start (1h)
  - Create diarization_service.py skeleton
  - Engineer SLM prompt
  - Design function signatures
```

### End of Day Checklist
- [ ] All router files created and tested
- [ ] Routers properly integrate with services
- [ ] Diarization design documented
- [ ] SLM module skeleton created
- [ ] Tasks 3.4, 5.1 marked "Complete"
- [ ] Task 5.2 ~30% complete

---

## **DAY 7 (Tuesday): Refactor Main.py & Complete Diarization Module**

### Morning (3 hours) - Refactor main.py
**Tasks to Complete:**
- ✅ Task 3.5: Refactor main.py (2 hours)
- ✅ Task 4.3: Logging Testing (1 hour)

**Deliverables:**
- [ ] main.py reduced to 50-60 lines
- [ ] All routes moved to routers
- [ ] Middleware registered
- [ ] Startup/shutdown events defined
- [ ] Logging setup correct
- [ ] App creation clean

**Time Allocation:**
```
3.5: Refactor main.py (2h)
  - Rewrite main.py from scratch (1h)
  - Include all routers (0.25h)
  - Test app starts (0.5h)
  - Verify all routes work (0.25h)
  
4.3: Test Logging (1h)
  - Verify happy path produces 0 logs
  - Trigger errors and verify logging
  - Check log files created correctly
```

### Afternoon (4 hours) - Complete Diarization Module
**Tasks to Complete:**
- ✅ Task 5.2: Create SLM Diarization Module (Complete) (4 hours)

**Deliverables:**
- [ ] `identify_speakers()` function implemented
- [ ] SLM prompt working correctly
- [ ] Confidence scores calculated
- [ ] Timeout handling implemented
- [ ] Fallback to Whisper labels if SLM fails
- [ ] Function well-documented
- [ ] Performance benchmarked

**Time Allocation:**
```
5.2: SLM Module (4h)
  - Implement identify_speakers() (2h)
  - Engineer and test SLM prompt (1h)
  - Add confidence scoring (0.5h)
  - Add error handling/timeouts (0.5h)
```

### End of Day Checklist
- [ ] main.py refactored and working
- [ ] Logging pattern verified
- [ ] Diarization module complete
- [ ] SLM integration tested
- [ ] Tasks 3.5, 4.3, 5.2 marked "Complete"

---

## **DAY 8 (Wednesday): Backend Integration & Testing**

### Morning (4 hours) - Backend Testing
**Tasks to Complete:**
- ✅ Task 3.6: Backend Testing & Integration (3 hours)
- ✅ Task 5.3: Integrate Diarization (1 hour start)

**Deliverables:**
- [ ] All API endpoints tested and working
- [ ] Services tested with mocks
- [ ] Integration test: full pipeline works
- [ ] Error scenarios handled correctly
- [ ] Database operations work
- [ ] All tests passing

**Time Allocation:**
```
3.6: Backend Testing (3h)
  - Test /api/analyze endpoint (0.5h)
  - Test /api/test-analysis endpoint (0.5h)
  - Test /api/rescore endpoint (0.5h)
  - Test /api/history endpoints (0.5h)
  - Test /api/weights endpoint (0.5h)
  - Fix any bugs (0.5h)
  
5.3: Integrate Diarization (1h)
  - Add diarization call to analysis pipeline
  - Ensure error doesn't break analysis
  - Test integration
```

### Afternoon (4 hours) - Diarization Integration & Testing
**Tasks to Complete:**
- ✅ Task 5.3: Integrate Diarization (2 hours, complete)
- ✅ Task 5.4: Diarization Testing (2 hours start)

**Deliverables:**
- [ ] Diarization integrated into analysis pipeline
- [ ] Talk ratio analyzer uses speaker labels
- [ ] Sentiment analyzer uses speaker labels
- [ ] No breaking changes to existing analyzers
- [ ] Error handling robust
- [ ] Diarization tests passing

**Time Allocation:**
```
5.3: Integration (2h)
  - Modify AnalysisService to call diarization
  - Update analyzers to use speaker labels
  - Test full pipeline
  
5.4: Testing (2h)
  - Unit test diarization module
  - Test speaker identification accuracy
  - Test confidence scores
  - Test edge cases
```

### End of Day Checklist
- [ ] All backend APIs working
- [ ] Diarization fully integrated
- [ ] Integration tests passing
- [ ] No breaking changes
- [ ] Tasks 3.6, 5.3 marked "Complete"
- [ ] Task 5.4 ~70% complete

---

## **DAY 9 (Thursday): Diarization Finalization & E2E Testing**

### Morning (3 hours) - Complete Diarization Testing
**Tasks to Complete:**
- ✅ Task 5.4: Diarization Testing & Validation (Complete) (2 hours)

**Deliverables:**
- [ ] Speaker identification accuracy validated (>80%)
- [ ] Performance acceptable (<5 min for 30 min call)
- [ ] All edge cases tested
- [ ] Error handling verified
- [ ] Documentation updated

**Time Allocation:**
```
5.4: Validation (2h)
  - Test with sample calls
  - Measure accuracy
  - Measure performance
  - Test error scenarios
  - Update documentation
```

### Afternoon (5 hours) - End-to-End & Performance Testing
**Tasks to Complete:**
- ✅ Task 6.1: End-to-End Testing (4 hours)
- ✅ Task 6.2: Performance Testing (1 hour start)

**Deliverables:**
- [ ] Complete user flow tested (upload → results)
- [ ] All features work end-to-end
- [ ] Frontend + Backend integration verified
- [ ] All error paths tested
- [ ] Cross-browser tested
- [ ] Mobile responsive verified
- [ ] Performance benchmarked

**Time Allocation:**
```
6.1: E2E Testing (4h)
  - Test file upload flow (0.5h)
  - Test analysis flow (1h)
  - Test results display (0.5h)
  - Test history flow (0.5h)
  - Test error paths (0.5h)
  - Cross-browser test (0.5h)
  - Mobile test (0.5h)
  
6.2: Performance (1h)
  - Measure load times
  - Measure API response times
  - Check resource usage
```

### End of Day Checklist
- [ ] All diarization tests passing
- [ ] E2E tests passing
- [ ] Performance benchmarks completed
- [ ] All features verified
- [ ] Tasks 5.4, 6.1 marked "Complete"
- [ ] Task 6.2 ~30% complete

---

## **DAY 10 (Friday): Documentation, Review & Release**

### Morning (3 hours) - Documentation & Code Review
**Tasks to Complete:**
- ✅ Task 6.3: Code Review & Documentation (3 hours)

**Deliverables:**
- [ ] All code reviewed and approved
- [ ] `ARCHITECTURE.md` created
- [ ] `DIARIZATION.md` created
- [ ] `MIGRATION.md` created
- [ ] `README.md` updated
- [ ] Comments added to complex code
- [ ] All docstrings complete

**Time Allocation:**
```
6.3: Documentation (3h)
  - Review frontend changes (0.5h)
  - Review backend changes (0.5h)
  - Review diarization implementation (0.5h)
  - Create ARCHITECTURE.md (0.75h)
  - Create DIARIZATION.md (0.75h)
  - Create MIGRATION.md (0.5h)
```

### Afternoon (3 hours) - Release Preparation
**Tasks to Complete:**
- ✅ Task 6.2: Performance Testing (Complete) (0.5 hours)
- ✅ Task 6.4: Deployment Prep & Release (2.5 hours)

**Deliverables:**
- [ ] All tests passing
- [ ] Release notes written
- [ ] Git tags created (v2.0.0)
- [ ] Rollback plan documented
- [ ] Team trained on new architecture
- [ ] Ready for production deployment

**Time Allocation:**
```
6.2: Perf Testing (0.5h)
  - Finalize benchmarks
  - Document results
  
6.4: Deployment (2.5h)
  - Write release notes (0.5h)
  - Create git tag v2.0.0 (0.25h)
  - Merge PRs and close issues (0.5h)
  - Document rollback plan (0.5h)
  - Team training/handoff (0.75h)
```

### End of Day Checklist
- [ ] All documentation complete
- [ ] Code reviewed and approved
- [ ] Release notes written
- [ ] All tasks marked "Complete"
- [ ] Git tag v2.0.0 created
- [ ] Team trained
- [ ] **READY FOR PRODUCTION DEPLOYMENT** ✅

---

## SPRINT SUMMARY

```
Week 1 (Mon-Fri)
├─ Day 1: Planning & Setup
├─ Day 2: Backend Config + Frontend Constants
├─ Day 3: Frontend Hooks + Backend Services
├─ Day 4: Frontend Views + Logging Cleanup
└─ Day 5: Refactor App.jsx + Frontend Testing ✅ Frontend Complete

Week 2 (Mon-Fri)
├─ Day 6: Backend Routers + Diarization Design
├─ Day 7: Refactor main.py + Diarization Module
├─ Day 8: Backend Testing + Diarization Integration
├─ Day 9: E2E Testing + Performance Testing
└─ Day 10: Documentation + Release ✅ PRODUCTION READY
```

---

## DAILY TIME BREAKDOWN

| Day | Frontend (h) | Backend (h) | Other (h) | Total |
|-----|--------------|-------------|-----------|-------|
| 1   | 0            | 3           | 1         | 4     |
| 2   | 3            | 4           | 0         | 7     |
| 3   | 4            | 4           | 0         | 8     |
| 4   | 4            | 0           | 4         | 8     |
| 5   | 7            | 0           | 1         | 8     |
| 6   | 0            | 4           | 3         | 7     |
| 7   | 0            | 3           | 1         | 4     |
| 8   | 0            | 4           | 4         | 8     |
| 9   | 0            | 2           | 8         | 10    |
| 10  | 0            | 0           | 6         | 6     |
| --- | --- | --- | --- | --- |
| **TOTAL** | **18** | **24** | **28** | **70** |

---

## DELIVERABLES CHECKLIST

### Frontend Deliverables
- [ ] `src/hooks/` (5 custom hooks)
- [ ] `src/components/views/` (4 view components + Header)
- [ ] `src/constants/` (4 constant files)
- [ ] `src/utils/` (updated with validators/formatters)
- [ ] Refactored `App.jsx` (80-100 lines)
- [ ] All features working identically

### Backend Deliverables
- [ ] `app/config/` (settings.py + .env files)
- [ ] `app/models/` (organized model files)
- [ ] `app/services/` (4 service classes)
- [ ] `app/api/routers/` (4 router files)
- [ ] Refactored `main.py` (50-60 lines)
- [ ] All API endpoints working

### Diarization Deliverables
- [ ] `app/services/diarization_service.py`
- [ ] SLM speaker identification working
- [ ] Integrated into analysis pipeline
- [ ] Accuracy > 80%
- [ ] `DIARIZATION.md` documentation

### Logging Deliverables
- [ ] All debug logs removed
- [ ] Error-focused logging implemented
- [ ] Try-except blocks in critical paths
- [ ] Logging pattern documented

### Documentation Deliverables
- [ ] `ARCHITECTURE.md` (new)
- [ ] `DIARIZATION.md` (new)
- [ ] `MIGRATION.md` (new)
- [ ] Updated `README.md`
- [ ] Release notes (v2.0.0)

---

## RISK MITIGATION

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SLM too slow | Medium | Medium | Cache, use fallback, optimize prompts |
| Features break | Low | High | Extensive E2E testing, feature parity checks |
| Performance degrades | Low | Medium | Daily benchmarking, performance testing |
| Diarization < 80% | Medium | Medium | Augment with Whisper labels, improve prompts |
| Time overruns | Medium | Low | Prioritize frontend first, defer nice-to-haves |

---

## SPRINT VELOCITY

- **Total Hours**: 70
- **Total Story Points**: 51
- **Days**: 10
- **Hours per Day**: 7
- **Story Points per Day**: 5.1

If running 8-hour days: **88 hours available**, so **18 hours buffer** for unknowns.

