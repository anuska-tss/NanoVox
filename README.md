# NanoVox - Call Intelligence Dashboard

A minimal full-stack application for audio call analysis.

## Project Structure

```
NanoVox/
├── backend/          # Python FastAPI server
│   ├── main.py
│   └── requirements.txt
└── frontend/         # React + Vite client
    └── src/
        └── App.jsx
```

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`

## Features

- **Audio Upload**: Upload audio files for analysis
- **Transcript Display**: View call transcripts (placeholder)
- **Sentiment Analysis**: View sentiment scores (placeholder)

## Tech Stack

- **Backend**: Python, FastAPI, Uvicorn
- **Frontend**: React, Vite
