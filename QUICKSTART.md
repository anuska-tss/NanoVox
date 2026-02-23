# NanoVox - Quick Start Guide

## Prerequisites
- Python 3.12+ installed
- Node.js 20.19+ installed

## Setup Instructions

### 1. Virtual Environment (Already Created)
A Python virtual environment has been created at `.venv` with all backend dependencies installed.

### 2. Start Backend Server

**Windows:**
```bash
cd backend
start.bat
```

**Unix/Mac:**
```bash
cd backend
chmod +x start.sh
./start.sh
```

The backend will start at: `http://127.0.0.1:8000`
- API Docs: `http://127.0.0.1:8000/docs`

### 3. Start Frontend (In a new terminal)

**Windows:**
```bash
start-frontend.bat
```

**Manual:**
```bash
cd frontend
npm run dev
```

The frontend will start at: `http://localhost:5173`

## Testing

1. Open `http://localhost:5173` in your browser
2. Upload any audio file (.mp3, .wav, etc.)
3. Click "Analyze Call"
4. View mock transcript and sentiment results

## Project Structure

```
NanoVox/
├── .venv/                   # Python virtual environment (Windows)
├── backend/
│   ├── main.py             # FastAPI server
│   ├── requirements.txt    # Python dependencies
│   ├── start.bat          # Windows startup script
│   └── start.sh           # Unix startup script
├── frontend/
│   └── src/
│       ├── App.jsx        # React main component
│       └── App.css        # Styling
└── README.md
```

## Troubleshooting

### Backend won't start
- Make sure port 8000 is not in use
- Check that Python 3.12+ is installed: `python --version`
- Verify venv is activated (you should see `(.venv)` in terminal)

### Frontend won't start
- Make sure port 5173 is not in use
- Run `npm install` in the `frontend` directory first
- Check Node.js version: `node --version` (should be 20.19+)

### CORS errors
- Ensure backend is running before starting frontend
- Backend must be at `http://127.0.0.1:8000`

## Next Steps

Current implementation uses **mock data**. To add real ML:
1. Integrate Whisper for ASR
2. Add sentiment analysis model
3. Implement speaker diarization
4. Update `/analyze` endpoint with ML processing
