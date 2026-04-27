# NanoVox: Production Hardening & Folder Reorganization (1-2 Days)

## Strategy: Optimize What Works, Don't Rewrite

**Goal:** Take your working code, clean it up, reorganize folders, and make it production-ready.
**Scope:** Minimal refactoring, maximum stability
**Timeline:** 1-2 days (8-16 hours)
**Risk:** Very low (zero breaking changes)

---

## WHAT WE KEEP AS-IS ✅
- All business logic (analyzers, scoring, etc.)
- All features (upload, analyze, rescore, history)
- All UI/UX (looks and works the same)
- All API endpoints and responses
- Database schema
- Configuration system

---

## WHAT WE CHANGE (Minimal)

### 1️⃣ REMOVE DEBUG LOGS (1 hour)
```bash
# Find all "🧪 [DEBUG]" logs
grep -r "🧪 \[DEBUG\]" backend/

# Count and remove
# Current: ~15 instances
# After: 0 instances
```

**Files to clean:**
- `backend/main.py` - Remove ~10 debug logs
- `backend/modules/slm_analyzer.py` - Remove debug logs if any
- Any other files with "🧪 [DEBUG]"

**Keep these (info level, okay for production):**
- "loading models..."
- "Model loaded!"
- "Database initialized!"
- Startup messages (one-time only)

---

### 2️⃣ REORGANIZE BACKEND FOLDER STRUCTURE (30 min)

**BEFORE:**
```
backend/
├── main.py                 (800+ lines, works fine)
├── database.py             (good)
├── models.py               (good)
├── scoring_engine.py       (good)
├── report_generator.py     (good)
├── parameter_registry.py   (good)
├── modules/
│   ├── __init__.py
│   ├── sentiment_analyzer.py
│   ├── slm_analyzer.py
│   └── talk_ratio_analyzer.py
├── utils/
│   ├── __init__.py
│   ├── config_loader.py
│   └── logger.py
└── config/
    ├── backend_config.json
    └── client_profiles.json
```

**AFTER (Just reorganized, not rewritten):**
```
backend/
├── main.py                 (same, just cleaned logs)
├── config/                 (moved here)
│   ├── backend_config.json
│   └── client_profiles.json
├── core/                   (analyzers + scoring)
│   ├── __init__.py
│   ├── scoring_engine.py   (moved from root)
│   ├── report_generator.py (moved from root)
│   └── parameter_registry.py (moved from root)
├── models/                 (data models)
│   ├── __init__.py
│   ├── models.py          (moved from root)
│   └── schemas.py         (request/response models)
├── analyzers/             (renamed from modules/)
│   ├── __init__.py
│   ├── sentiment_analyzer.py
│   ├── slm_analyzer.py
│   └── talk_ratio_analyzer.py
├── persistence/           (database)
│   ├── __init__.py
│   ├── database.py        (moved from root)
│   └── nanovox.db
├── utils/                 (utilities)
│   ├── __init__.py
│   ├── config_loader.py
│   └── logger.py
├── requirements.txt
├── .env                   (new - environment variables)
├── .env.example          (new - template)
└── logs/                 (generated at runtime)
```

**What this gives you:**
- ✅ Clear separation of concerns
- ✅ Easy to find what you need
- ✅ Team can navigate without explanation
- ✅ Production-standard structure
- ✅ Same functionality, just organized

---

### 3️⃣ REORGANIZE FRONTEND FOLDER STRUCTURE (30 min)

**BEFORE:**
```
frontend/src/
├── App.jsx              (all logic here)
├── App.css
├── index.css
├── main.jsx
├── config.js
├── api/
│   └── nanovoxApi.js
├── components/
│   ├── AnalysisDashboard.jsx
│   ├── FileUpload.jsx
│   ├── ProfileSelector.jsx
│   ├── utils.js
│   └── ui/
│       ├── CircularGauge.jsx
│       ├── icons.jsx
│       └── ScoreCard.jsx
└── assets/
```

**AFTER (Minimal change):**
```
frontend/src/
├── App.jsx              (same)
├── App.css              (same)
├── index.css            (same)
├── main.jsx             (same)
├── config/
│   └── config.js        (moved into folder)
├── api/
│   ├── nanovoxApi.js    (same)
│   └── client.js        (new - axios/fetch wrapper)
├── components/
│   ├── layout/
│   │   └── Header.jsx   (new - extract from App if needed)
│   ├── views/           (new - organize views)
│   │   ├── LandingView.jsx
│   │   ├── DashboardView.jsx
│   │   ├── HistoryView.jsx
│   │   └── ProcessingView.jsx
│   ├── features/        (existing components)
│   │   ├── FileUpload.jsx
│   │   ├── ProfileSelector.jsx
│   │   └── AnalysisDashboard.jsx
│   └── ui/              (same)
├── styles/              (new - centralize CSS)
│   ├── index.css
│   ├── App.css
│   └── components.css
├── utils/
│   ├── helpers.js       (moved from components/)
│   └── formatters.js
├── types/               (new - JSDoc type definitions)
│   └── index.js
├── .env                 (new - environment)
├── .env.example         (new - template)
└── assets/
```

**Why this helps:**
- ✅ Clear component organization
- ✅ Easy to find views vs features
- ✅ CSS centralized
- ✅ Environment variables clear
- ✅ Team knows where to add things

---

## DAY 1: CLEANUP & REORGANIZATION (8 hours)

### Morning (4 hours)
**Backend Cleanup:**

1. **Remove Debug Logs** (30 min)
   ```bash
   # In main.py, find and remove:
   # logger.info(f"🧪 [DEBUG] _run_analyzers triggered...")
   # logger.info("🧪 [DEBUG] Talk ratio analyzer finished")
   # logger.info(f"🧪 [DEBUG] SLM analyzer returned...")
   # logger.info(f"🧪 [DEBUG] All analyzers finished...")
   # And all "🧪 [DEBUG]" in test_analysis endpoint
   ```

2. **Reorganize Backend Folders** (2 hours)
   ```bash
   # Create new structure
   mkdir -p backend/config
   mkdir -p backend/core
   mkdir -p backend/models
   mkdir -p backend/analyzers
   mkdir -p backend/persistence
   mkdir -p backend/utils
   
   # Move files
   mv backend/scoring_engine.py backend/core/
   mv backend/report_generator.py backend/core/
   mv backend/parameter_registry.py backend/core/
   mv backend/models.py backend/models/
   mv backend/database.py backend/persistence/
   mv backend/modules/* backend/analyzers/
   mv config/* backend/config/
   
   # Create __init__.py files
   touch backend/core/__init__.py
   touch backend/models/__init__.py
   touch backend/persistence/__init__.py
   touch backend/analyzers/__init__.py
   ```

3. **Update Imports in main.py** (1 hour)
   ```python
   # Old imports
   from modules import talk_ratio_analyzer, sentiment_analyzer, slm_analyzer
   from models import ParameterResult, TranscriptSegment
   from database import init_db, save_call, get_history
   from scoring_engine import calculate_score
   from report_generator import generate_report
   
   # New imports (same functionality, new paths)
   from analyzers import talk_ratio_analyzer, sentiment_analyzer, slm_analyzer
   from models.models import ParameterResult, TranscriptSegment
   from persistence.database import init_db, save_call, get_history
   from core.scoring_engine import calculate_score
   from core.report_generator import generate_report
   ```

4. **Create .env Files** (30 min)
   ```bash
   # .env (local development)
   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
   LOG_LEVEL=INFO
   LOG_DIR=logs
   WHISPER_MODEL=base
   MAX_UPLOAD_SIZE_MB=50
   
   # .env.example (template for team)
   CORS_ALLOWED_ORIGINS=http://localhost:5173
   LOG_LEVEL=INFO
   LOG_DIR=logs
   WHISPER_MODEL=base
   MAX_UPLOAD_SIZE_MB=50
   ```

### Afternoon (4 hours)
**Frontend Reorganization:**

1. **Create Folder Structure** (1 hour)
   ```bash
   mkdir -p frontend/src/config
   mkdir -p frontend/src/components/layout
   mkdir -p frontend/src/components/views
   mkdir -p frontend/src/components/features
   mkdir -p frontend/src/styles
   mkdir -p frontend/src/utils
   mkdir -p frontend/src/types
   
   # Move files
   mv frontend/src/config.js frontend/src/config/config.js
   mv frontend/src/components/utils.js frontend/src/utils/helpers.js
   mv frontend/src/App.css frontend/src/styles/App.css
   mv frontend/src/index.css frontend/src/styles/index.css
   
   # Keep components as-is for now
   ```

2. **Create .env Files** (30 min)
   ```bash
   # .env (local)
   VITE_API_URL=http://127.0.0.1:8000
   
   # .env.example (template)
   VITE_API_URL=http://127.0.0.1:8000
   ```

3. **Update Frontend Imports** (2 hours)
   ```javascript
   // Old
   import { API_BASE_URL, ... } from './config'
   import { getScoreColor } from './components/utils'
   
   // New
   import { API_BASE_URL, ... } from './config/config'
   import { getScoreColor } from './utils/helpers'
   
   // CSS imports
   import './App.css'
   import './index.css'
   // Becomes
   import './styles/App.css'
   import './styles/index.css'
   ```

4. **Update Vite Config** (30 min)
   ```bash
   # Check vite.config.js - may need to update API_URL reference
   # Usually works as-is, but verify
   ```

5. **Test Frontend Starts** (30 min)
   ```bash
   cd frontend
   npm run dev
   # Should start on http://localhost:5173
   # No import errors ✅
   # All features visible ✅
   ```

---

## DAY 2: TESTING & HARDENING (8 hours)

### Morning (4 hours)
**Backend Testing:**

1. **Start Backend** (30 min)
   ```bash
   cd backend
   python main.py
   # Should start with no import errors
   # Should log: "loading models..." ✅
   # Should log: "Model loaded!" ✅
   # Should log: "Database initialized!" ✅
   ```

2. **Test API Endpoints** (2 hours)
   ```bash
   # Test /
   curl http://localhost:8000/
   # Expected: {"status": "ok", "message": "NanoVox API is running"}
   
   # Test /api/weights/defaults
   curl http://localhost:8000/api/weights/defaults
   # Expected: {"weights": {...}}
   
   # Test /api/test-analysis (manual transcript)
   curl -X POST http://localhost:8000/api/test-analysis \
     -H "Content-Type: application/json" \
     -d '{
       "transcript": [
         {"speaker": "Agent", "start": 0, "end": 5, "text": "Hello"},
         {"speaker": "Customer", "start": 5, "end": 10, "text": "Hi there"}
       ],
       "weights": {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40}
     }'
   # Expected: analysis results with scores
   
   # Test /api/analyze (with file)
   curl -X POST http://localhost:8000/api/analyze \
     -F "file=@test_audio.mp3"
   # Expected: full analysis results
   ```

3. **Check Logs** (1 hour)
   ```bash
   # Check backend_debug.log or logs/backend.log.*
   # Should see:
   # ✅ "loading models..."
   # ✅ "Model loaded!"
   # ✅ "Database initialized!"
   # ✅ NO "🧪 [DEBUG]" messages
   # ✅ Error logs if something fails
   ```

### Afternoon (4 hours)
**End-to-End Testing:**

1. **Manual Testing** (2 hours)
   ```
   ✅ Start backend: python backend/main.py
   ✅ Start frontend: npm run dev (in another terminal)
   ✅ Open browser: http://localhost:5173
   ✅ Click buttons, verify no errors
   ✅ Upload file (or use test mode with JSON)
   ✅ Check results display correctly
   ✅ Check theme toggle works
   ✅ Check history loads
   ✅ Check weights adjustment works
   ```

2. **Browser DevTools Check** (1 hour)
   ```
   ✅ Open DevTools (F12)
   ✅ Console tab: NO RED ERRORS
   ✅ Network tab: All requests 200/201 OK
   ✅ Check for any 500 errors from backend
   ```

3. **Documentation** (1 hour)
   ```bash
   # Create/update key files:
   
   # README.md - Production deployment section
   # Add:
   - Folder structure overview
   - Environment variables required
   - How to run backend
   - How to run frontend
   - API endpoints list
   
   # DEPLOYMENT.md (new)
   - Production setup
   - Environment variables for prod
   - How to deploy
   - Health check commands
   
   # ARCHITECTURE.md (new, brief)
   - Backend folder structure
   - Frontend folder structure
   - Data flow diagram (text-based)
   ```

---

## PRODUCTION HARDENING CHECKLIST

### Backend ✅
- [ ] Remove all "🧪 [DEBUG]" logs
- [ ] Folder structure reorganized
- [ ] All imports updated
- [ ] main.py tested and working
- [ ] All API endpoints respond correctly
- [ ] Error handling functional
- [ ] Database operations work
- [ ] Logging goes to files
- [ ] No import errors on startup

### Frontend ✅
- [ ] Folder structure reorganized
- [ ] All imports updated and working
- [ ] .env file created
- [ ] App starts without errors
- [ ] All features work (upload, analyze, history, etc.)
- [ ] No console errors
- [ ] No 404s for assets
- [ ] API calls work (network tab clean)
- [ ] Mobile responsive verified

### Integration ✅
- [ ] Backend + Frontend communicate
- [ ] File upload → analysis → results works
- [ ] Error messages display correctly
- [ ] No CORS errors
- [ ] History saves and loads
- [ ] Rescore works
- [ ] Theme toggle persists

### Documentation ✅
- [ ] README updated with new structure
- [ ] DEPLOYMENT.md created
- [ ] Environment variables documented
- [ ] API endpoints documented
- [ ] Folder structure explained

---

## FINAL FOLDER STRUCTURE (What you'll have)

```
NanoVox/
├── backend/
│   ├── main.py                      (cleaned, no debug logs)
│   ├── config/
│   │   ├── backend_config.json
│   │   └── client_profiles.json
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scoring_engine.py
│   │   ├── report_generator.py
│   │   └── parameter_registry.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── sentiment_analyzer.py
│   │   ├── slm_analyzer.py
│   │   └── talk_ratio_analyzer.py
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── nanovox.db
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config_loader.py
│   │   └── logger.py
│   ├── logs/                        (generated)
│   ├── requirements.txt
│   ├── .env                         (gitignored)
│   ├── .env.example                 (in repo)
│   ├── start.sh
│   └── start.bat
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── config/
│   │   │   └── config.js
│   │   ├── api/
│   │   │   ├── nanovoxApi.js
│   │   │   └── client.js
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── views/
│   │   │   ├── features/
│   │   │   └── ui/
│   │   ├── styles/
│   │   │   ├── index.css
│   │   │   └── App.css
│   │   ├── utils/
│   │   │   └── helpers.js
│   │   ├── types/
│   │   ├── assets/
│   │   ├── .env
│   │   └── .env.example
│   ├── package.json
│   ├── vite.config.js
│   └── eslint.config.js
├── README.md                        (updated)
├── DEPLOYMENT.md                    (new)
├── ARCHITECTURE.md                  (new)
└── .gitignore
```

---

## DEPLOYMENT CHECKLIST

Before going to production:

### Code ✅
- [ ] All debug logs removed
- [ ] All imports point to new folders
- [ ] Zero error logs in startup
- [ ] All tests pass
- [ ] Git status clean

### Environment ✅
- [ ] .env file created (gitignored)
- [ ] .env.example in repo
- [ ] Backend can read config from .env
- [ ] Frontend can read API URL from .env

### Documentation ✅
- [ ] README has new structure
- [ ] DEPLOYMENT.md explains setup
- [ ] Team can run both backend and frontend
- [ ] Team can modify and extend code

### Testing ✅
- [ ] Manual E2E test passes
- [ ] File upload works
- [ ] Results display correctly
- [ ] No console errors
- [ ] No network errors

### Deployment ✅
- [ ] Create git tag v1.0.0 (or v2.0 if major)
- [ ] Push to main branch
- [ ] Deploy to production server
- [ ] Verify health check: curl http://api.url/
- [ ] Monitor logs for first hour

---

## TIME ESTIMATE

| Task | Time | Effort |
|------|------|--------|
| Remove debug logs | 1h | Easy |
| Reorganize backend folders | 1.5h | Easy |
| Reorganize frontend folders | 1h | Easy |
| Update imports (backend) | 1.5h | Medium |
| Update imports (frontend) | 1h | Easy |
| Test backend | 1.5h | Easy |
| Test frontend | 1.5h | Easy |
| Documentation | 1h | Easy |
| **TOTAL** | **10h** | **Easy** |

**With team:** 1 day (8 hours)
**Solo:** 1-2 days (depending on pace)

---

## RISK ASSESSMENT

| Risk | Chance | Fix |
|------|--------|-----|
| Import errors after moving files | Low | Systematic find-replace |
| API endpoints break | Very Low | Test before pushing |
| Frontend can't find API | Very Low | Verify .env variables |
| Database not found | Very Low | Check DB path in new structure |
| Logging fails | Very Low | Logger config already works |

**Overall Risk: VERY LOW**
(You're just moving files and removing logs, not changing logic)

---

## GIT WORKFLOW

```bash
# 1. Create feature branch
git checkout -b feat/production-hardening

# 2. Day 1: Remove logs + organize folders (commit)
git add -A
git commit -m "chore: remove debug logs and reorganize folder structure"

# 3. Day 1: Update imports (commit)
git add -A
git commit -m "chore: update imports for new folder structure"

# 4. Day 2: Testing fixes (if any)
git add -A
git commit -m "fix: [specific fixes if needed]"

# 5. Day 2: Documentation (commit)
git add -A
git commit -m "docs: update README and add deployment guide"

# 6. Merge to main
git checkout main
git pull origin main
git merge feat/production-hardening
git push origin main

# 7. Tag release
git tag -a v2.0.0 -m "Production-hardened version with optimized structure"
git push origin v2.0.0
```

---

## SUCCESS CRITERIA

When you're done, you should be able to:

✅ **Start backend:** `python backend/main.py` → runs with no errors
✅ **Start frontend:** `npm run dev` → runs with no errors
✅ **Upload file:** Upload audio → see results
✅ **All features:** Theme, weights, history all work
✅ **No logs:** No "🧪 [DEBUG]" messages anywhere
✅ **Team ready:** Anyone can understand the folder structure
✅ **Production ready:** Can deploy to production immediately

---

## Questions Before Starting?

1. **Diarization:** Keep using SLM as-is? (Yes, keep current implementation)
2. **Database:** Keep nanovox.db in persistence folder? (Yes)
3. **Config files:** Keep JSON configs? (Yes, add .env on top)
4. **Logging:** Keep existing logger.py? (Yes, just remove debug logs)
5. **API changes:** Change any endpoints? (No, keep everything as-is)

All answers: **Keep existing code, just organize and clean it**

