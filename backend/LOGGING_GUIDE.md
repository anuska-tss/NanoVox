# Logging Implementation Guide

## Architecture: Centralized Configuration + Module Loggers

You've now implemented the **best practice** logging architecture:

### **Two-Layer System:**

```
1. LoggerFactory (utils/logger.py)
   └─ Centralizes configuration (ONE place to configure)
   └─ Handles daily log rotation
   └─ Auto-cleanup old logs after 7 days

2. Module Loggers (one per file)
   └─ Each file: logger = logging.getLogger(__name__)
   └─ Gets module name context automatically
   └─ Inherits configuration from LoggerFactory
```

---

## How It Works

### **Step 1: Initialization (in main.py)**
```python
from utils.logger import LoggerFactory, get_logger

# Called ONCE at startup
LoggerFactory.setup(
    log_dir="logs",
    log_level="INFO",
    retention_days=7
)

# Then get your logger
logger = get_logger(__name__)  # logger for "main"
```

### **Step 2: Use in Other Files**
```python
# database.py
import logging

logger = logging.getLogger(__name__)  # logger for "database"

def init_db():
    logger.info("Initializing database...")
```

```python
# modules/sentiment_analyzer.py
import logging

logger = logging.getLogger(__name__)  # logger for "modules.sentiment_analyzer"

def analyze(transcript):
    logger.info("Starting sentiment analysis...")
```

---

## Log Output Format

### **Console Output (development)**
```
[2026-04-22 10:15:23] main - INFO - Loading models
[2026-04-22 10:15:24] database - INFO - Database initialized
[2026-04-22 10:15:25] modules.sentiment_analyzer - INFO - Sentiment analysis complete
[2026-04-22 10:15:26] modules.talk_ratio_analyzer - INFO - Talk ratio analysis complete
```

### **File Output (logs/backend.log.2026-04-22)**
Same format, persisted to disk with date-based filename.

---

## Log Files (Daily Rotation)

```
logs/
├── backend.log.2026-04-20    (Old, deleted after 7 days)
├── backend.log.2026-04-21
├── backend.log.2026-04-22    (Today's logs)
└── backend.log              (Symlink to today's file)
```

**How it works:**
- Each day at midnight, a new log file is created
- Old files older than 7 days are automatically deleted
- Each file contains 24 hours of logs

---

## Why This Approach is Better

### **Single Logger (❌ Not Recommended)**
```
2026-04-22 10:15:23 - INFO - Loading models
2026-04-22 10:15:24 - INFO - Database initialized
→ Which module? No idea!
```

### **Module Loggers with Central Config (✅ Recommended)**
```
[2026-04-22 10:15:23] main - INFO - Loading models
[2026-04-22 10:15:24] database - INFO - Database initialized
→ Clear module context for debugging!
```

---

## Usage Summary

### **Don't do this:**
```python
# ❌ Old way - hardcoded logging setup in every file
import logging
logging.basicConfig(...)
file_handler = logging.FileHandler("...")
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
```

### **Do this instead:**
```python
# ✅ New way - use centralized LoggerFactory
import logging

logger = logging.getLogger(__name__)  # That's it!
logger.info("My message")
```

---

## Configuration

All logging settings are in `config/backend_config.json`:

```json
{
  "logging": {
    "level": "INFO",        # Can change to DEBUG, WARNING, ERROR, CRITICAL
    "file_name": "backend_debug.log",  # (unused now, kept for config compatibility)
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

---

## Migration: Update All Python Files

To fully implement this, update all Python files that currently have logging:

### **database.py**
```python
# OLD (remove these lines)
import logging
logger = logging.getLogger(__name__)

# NEW (replace with)
import logging
logger = logging.getLogger(__name__)
```
*(No change needed! The old pattern still works.)*

### **modules/sentiment_analyzer.py**
```python
# OLD
import logging
logger = logging.getLogger(__name__)

# NEW (same - no change needed)
import logging
logger = logging.getLogger(__name__)
```

### **report_generator.py**
```python
# OLD
import logging
logger = logging.getLogger(__name__)

# NEW (same)
import logging
logger = logging.getLogger(__name__)
```

**Key Point:** All existing files already use the correct pattern! You just need to ensure they all have:
```python
import logging
logger = logging.getLogger(__name__)
```

---

## Features Unlocked

✅ **Date-wise logs** — One file per day (backend.log.2026-04-22)  
✅ **Auto-cleanup** — Logs older than 7 days deleted automatically  
✅ **Module context** — See exactly which module logged each message  
✅ **Centralized config** — Change log level once in backend_config.json  
✅ **Console + File** — Logs appear in terminal AND on disk  
✅ **No duplication** — Single centralized setup instead of per-file config  

---

## Testing

To verify logging is working:

```bash
# Terminal
cd backend
python main.py

# Should see in console:
# [2026-04-22 10:XX:XX] utils.logger - INFO - ✅ Logging initialized: logs/backend.log (level=INFO, retention=7d)
# [2026-04-22 10:XX:XX] main - INFO - loading models...
```

Check logs directory:
```bash
ls -la logs/
# backend.log.2026-04-22  (today's log)
```

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Setup** | Repeated in every file | Once in LoggerFactory |
| **Log files** | Single file forever | Daily rotation (backend.log.YYYY-MM-DD) |
| **Module context** | ❌ All logs look same | ✅ Each has module name |
| **Old log cleanup** | Manual | Automatic (7 days) |
| **Configuration** | Scattered | Centralized (backend_config.json) |
| **Lines of code** | More (logging setup in every file) | Less (one line per file) |
