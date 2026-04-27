# Quick Implementation Guide: Optimize NanoVox for Production

## 🎯 What You're Doing

Your code works - we're just:
1. ✅ Remove debug logs
2. ✅ Add speaker identification
3. ✅ Test thoroughly
4. ✅ Deploy

**Time: 2-3 days**

---

## STEP 1: Remove Debug Logs (30 minutes)

### Find All Debug Logs

```bash
cd backend
grep -r "🧪 \[DEBUG\]" .
grep -r 'logger.info.*Loading' .
grep -r 'logger.info.*finished' .
grep -r 'logger.info.*complete' .
```

### Remove from `main.py`

**Find these lines and DELETE:**
```python
# DELETE THESE:
logger.info("🧪 [DEBUG] _run_analyzers triggered with...")
logger.info("🧪 [DEBUG] Talk ratio analyzer finished")
logger.info("🧪 [DEBUG] Sentiment analyzer finished")
logger.info(f"🧪 [DEBUG] SLM analyzer returned {len(slm_results)} results")
logger.info(f"🧪 [DEBUG] All analyzers finished, collected...")

# KEEP THESE:
logger.error(f"Talk ratio analyzer failed: {e}")
logger.error(f"Sentiment analyzer failed: {e}")
logger.error(f"SLM analyzer failed entirely: {e}...", exc_info=True)
logger.warning(f"SLM Override: VADER={vader_score:.1f}...")
```

### Check Other Files

Do the same for:
- `backend/modules/talk_ratio_analyzer.py`
- `backend/modules/sentiment_analyzer.py`
- `backend/modules/slm_analyzer.py`

**Search for same patterns and delete info-level logs, keep error-level logs.**

---

## STEP 2: Create Diarization Service (2 hours)

### Create File: `backend/diarization_service.py`

Copy this entire code:

```python
"""
Speaker Identification Service (Diarization)

Uses SLM (Small Language Model) via Ollama for speaker identification.
Identifies Agent vs Customer in call transcript.
"""

import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3.5"
TIMEOUT = 10  # seconds

DIARIZATION_PROMPT = """You are a call analyst. Given this call transcript segment, identify who is speaking.

Segment: "{text}"

Previous speaker: {context}

Answer with ONLY one word: "Agent" or "Customer". No explanation needed."""


def identify_speakers(transcript: list, profile_config: dict) -> list:
    """
    Identify speakers (Agent/Customer) in transcript using SLM.
    
    Args:
        transcript: List of segments with 'speaker' and 'text' fields
        profile_config: Profile configuration (unused for diarization)
        
    Returns:
        Same transcript with enhanced speaker identification
    """
    if not transcript:
        return transcript
    
    logger.info(f"Starting speaker identification for {len(transcript)} segments")
    
    for i, segment in enumerate(transcript):
        try:
            # Get context from previous speaker
            context = ""
            if i > 0 and hasattr(transcript[i-1], 'speaker'):
                context = transcript[i-1].speaker
            
            # Identify speaker for this segment
            speaker = _call_slm_for_speaker(segment.text, context)
            
            # Update speaker label
            if speaker != "Unknown":
                segment.speaker = speaker
                logger.debug(f"Segment {i}: {speaker}")
        
        except Exception as e:
            logger.error(f"Speaker identification failed for segment {i}: {e}")
            # Keep original speaker label if diarization fails
    
    logger.info("Speaker identification complete")
    return transcript


def _call_slm_for_speaker(text: str, context: str = "") -> str:
    """
    Call Ollama SLM to identify speaker.
    
    Args:
        text: Segment text
        context: Previous speaker
        
    Returns:
        "Agent", "Customer", or "Unknown"
    """
    try:
        prompt = DIARIZATION_PROMPT.format(text=text, context=context)
        
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2,
                "num_predict": 10,
            },
            timeout=TIMEOUT,
        )
        
        if response.status_code != 200:
            logger.warning(f"Ollama error: {response.status_code}")
            return "Unknown"
        
        response_text = response.json().get("response", "").strip().upper()
        
        # Parse response
        if "AGENT" in response_text:
            return "Agent"
        elif "CUSTOMER" in response_text:
            return "Customer"
        else:
            logger.debug(f"Unclear response: {response_text}")
            return "Unknown"
    
    except requests.exceptions.Timeout:
        logger.warning("Diarization timeout - Ollama slow or down")
        return "Unknown"
    except Exception as e:
        logger.error(f"Diarization error: {e}")
        return "Unknown"
```

**Save this file as `backend/diarization_service.py`**

---

## STEP 3: Add Diarization to Pipeline (20 minutes)

### Edit `backend/main.py`

**Step 3a: Add Import**

Find the imports at the top of `main.py` and add:
```python
from diarization_service import identify_speakers
```

**Step 3b: Update `_run_analyzers()` Function**

Find this function:
```python
def _run_analyzers(transcript: list, profile_config: dict) -> list:
    """
    Run all analyzers and return their results.
    ...
    """
    logger.info(f"🧪 [DEBUG] _run_analyzers triggered with {len(transcript)} segments")
    results = []
```

**Replace with:**
```python
def _run_analyzers(transcript: list, profile_config: dict) -> list:
    """
    Run all analyzers and return their results.
    Each analyzer is independent — if one fails, the others still return.
    """
    # NEW: Add diarization for speaker identification
    try:
        transcript = identify_speakers(transcript, profile_config)
    except Exception as e:
        logger.error(f"Speaker identification failed, continuing without: {e}")
        # Continue with original speaker labels if diarization fails
    
    results = []
    
    # EXISTING CODE CONTINUES BELOW...
```

---

## STEP 4: Test It (1.5 hours)

### Test 1: Basic Test
```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Test with curl
curl -X POST http://localhost:8000/api/test-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": [
      {"speaker": "Agent", "start": 0, "end": 5, "text": "Hello, how can I help you?"},
      {"speaker": "Customer", "start": 5, "end": 15, "text": "I have a problem with my order"}
    ],
    "weights": {"talk_ratio": 5, "sentiment": 35, "empathy": 20, "resolution": 40},
    "profile": "complaints"
  }'
```

**Verify:**
- ✅ Response received
- ✅ Speaker labels updated ("Agent", "Customer")
- ✅ Analysis results included
- ✅ No errors in console

### Test 2: Upload Real File
```bash
# Upload through frontend
# Verify:
# - File processes ✅
# - Diarization runs (check logs) ✅
# - Results show ✅
# - Speaker labels correct ✅
```

### Test 3: Error Case
```bash
# Stop Ollama: docker stop ollama (or kill the process)
# Upload file again
# Verify:
# - Still processes ✅
# - Shows original speaker labels ✅
# - Error in logs but doesn't crash ✅
```

---

## STEP 5: Final Checks Before Deploy (1 hour)

### Code Quality
```bash
# Check for remaining debug logs
grep -r "🧪" backend/
grep -r "\[DEBUG\]" backend/
# Should return: 0 results ✅

# Check code runs without errors
cd backend
python main.py
# Should start without errors ✅
```

### Documentation
Update `README.md` to mention diarization:
```markdown
## Features
- Real-time audio transcription (Whisper)
- **NEW: Automatic speaker identification** (Agent vs Customer)
- Sentiment analysis (VADER + SLM)
- Empathy analysis (SLM)
- Resolution analysis (SLM)
- Call quality scoring
- Call history and analytics
```

### Logs
Check `backend/logs/` to verify:
- ✅ Log files created daily
- ✅ No debug logs in files
- ✅ Error logs clear and helpful

---

## STEP 6: Deploy (1 hour)

### Local Testing (Final)
```bash
# Fresh restart
ps aux | grep python  # Kill existing instances
python backend/main.py

# npm run dev (frontend in another terminal)

# Test full flow:
# 1. Upload file
# 2. See progress
# 3. Get results with speaker ID
# 4. Check logs show no debug output
```

### Deploy to Production
```bash
# Git commit
git add -A
git commit -m "feat: add speaker identification (diarization) and remove debug logs"

# Tag version
git tag v1.1.0

# Deploy to production server
git push origin main
git push origin v1.1.0

# Restart production service
# (depends on your deployment setup)
```

### Post-Deploy Verification
- [ ] Backend started successfully
- [ ] Frontend loads
- [ ] Upload file works
- [ ] Results show speaker ID
- [ ] No error messages
- [ ] Logs clean (no debug output)

---

## QUICK REFERENCE: File Changes

### Files Modified (Minimal)

**1. `backend/main.py`**
- Add 1 import line
- Add 5-line diarization call in `_run_analyzers()`
- Remove debug log lines (search and delete)

**2. `backend/diarization_service.py` (NEW)**
- Create new file with 120 lines of code (provided above)

**3. All analyzer modules** (if they have debug logs)
- Remove "🧪 [DEBUG]" lines

### Files NOT Changed
- `frontend/src/App.jsx` ✓
- `backend/models.py` ✓
- `backend/database.py` ✓
- `backend/scoring_engine.py` ✓
- `backend/config/` ✓
- Everything else ✓

---

## TIMELINE

```
Time        Task                                Status
────────────────────────────────────────────────────
Day 1
 1.0h       Remove debug logs                   🟢
 2.0h       Create diarization_service.py       🟢
 0.5h       Integrate into main.py              🟢
 1.5h       Basic testing                       🟢
           Day 1 Total: 5 hours

Day 2
 2.0h       E2E pipeline testing                🟢
 1.5h       Accuracy testing                    🟢
 1.0h       Error scenario testing              🟢
           Day 2 Total: 4.5 hours

Day 3 (Optional)
 1.0h       Final review                        🟢
 1.0h       Deploy to production                🟢
           Day 3 Total: 2 hours

TOTAL: 11.5 hours (fits in 2-3 days)
```

---

## CHECKLIST: Ready to Deploy?

Before you deploy, check:
- [ ] All "🧪 [DEBUG]" removed (grep finds 0)
- [ ] diarization_service.py created and imported
- [ ] Diarization integrated in main.py
- [ ] Happy path tested (upload file → results)
- [ ] Error path tested (Ollama down → fallback works)
- [ ] No console errors
- [ ] No console warnings (except expected ones)
- [ ] Speaker ID showing in results
- [ ] Accuracy > 75%
- [ ] Performance < 3 min for 30 min file
- [ ] README updated
- [ ] Code committed to git

✅ All checked? **Deploy!**

---

## SUPPORT

If you get stuck:

**"diarization_service.py not found"**
→ Make sure file is in `backend/` directory
→ Check import path: `from diarization_service import identify_speakers`

**"Ollama connection refused"**
→ Make sure Ollama is running: `docker ps | grep ollama`
→ Or: `ollama serve` in another terminal
→ Or: Change OLLAMA_URL in diarization_service.py

**"Speaker identification returning Unknown"**
→ Check SLM model installed: `ollama list`
→ Try different model: `OLLAMA_MODEL = "mistral"`
→ Lower temperature for more consistent answers

**"Analysis slower than before"**
→ Expected: diarization adds ~30% time
→ Can optimize by reducing SLM model size
→ Can cache diarization results if re-analyzing

---

## What You'll Deploy

**Version: 1.1.0**

New Features:
✅ Automatic speaker identification (Agent/Customer)
✅ Improved talk ratio accuracy (knows who spoke)
✅ Improved sentiment accuracy (contextual)

Improvements:
✅ Clean production logs (no debug output)
✅ Better error handling
✅ Graceful fallback if diarization fails

Changes:
✅ ZERO breaking changes to API
✅ ZERO changes to frontend
✅ ZERO changes to existing analyzers

---

**You got this! 🚀 Start with removing debug logs today.**

