"""
SQLite Persistence Layer for NanoVox

Stores analyzed call results so QA officers can review history,
track trends, and revisit past analyses without re-uploading audio.

Tables:
  - call_history: stores each analyzed call with scores, breakdown, and metadata
"""
import sqlite3
import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "nanovox.db")


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
    return conn


def init_db():
    """
    Initialize the database schema. Safe to call multiple times —
    uses IF NOT EXISTS.
    """
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS call_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_size_bytes INTEGER DEFAULT 0,
                analyzed_at TEXT NOT NULL,
                
                -- Scores
                final_score REAL NOT NULL,
                profile_used TEXT DEFAULT 'Sales',
                interpretation TEXT,
                
                -- Commitment status (from the resolution/commitment analyzer)
                commitment_status TEXT,
                commitment_net_score INTEGER DEFAULT 0,
                
                -- Individual parameter scores
                talk_ratio_score REAL,
                sentiment_score REAL,
                empathy_score REAL,
                commitment_score REAL,
                
                -- Call metadata
                call_duration REAL DEFAULT 0,
                segment_count INTEGER DEFAULT 0,
                agent_name TEXT,
                
                -- Full JSON blobs for detailed drill-down
                analysis_json TEXT,
                transcript_json TEXT,
                insights_json TEXT,
                weights_json TEXT,
                analyzer_results_json TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_analyzed_at ON call_history(analyzed_at DESC);
            CREATE INDEX IF NOT EXISTS idx_final_score ON call_history(final_score);
            CREATE INDEX IF NOT EXISTS idx_agent_name ON call_history(agent_name);
        """)
        conn.commit()
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise
    finally:
        conn.close()


def save_call(
    filename: str,
    file_size_bytes: int,
    response: Dict,
    weights: Optional[Dict] = None,
    agent_name: Optional[str] = None
) -> int:
    """
    Save an analyzed call to the database.

    Args:
        filename: Original uploaded filename
        file_size_bytes: File size in bytes
        response: The full API response dict from /analyze
        weights: The weights used for scoring
        agent_name: Optional agent name tag

    Returns:
        The inserted row ID
    """
    conn = _get_connection()
    try:
        analysis = response.get("analysis", {})
        breakdown = analysis.get("breakdown", {})
        transcription = response.get("transcription", {})
        insights = response.get("insights", {})

        # Extract individual parameter scores
        talk_ratio_score = breakdown.get("talk_ratio", {}).get("score")
        sentiment_score = breakdown.get("sentiment", {}).get("score")
        empathy_score = breakdown.get("empathy", {}).get("score")
        commitment_score = breakdown.get("resolution", {}).get("score")

        # Commitment status
        commitment_meta = breakdown.get("resolution", {}).get("metadata", {})
        commitment_status = commitment_meta.get("status", "Unknown")
        commitment_net = commitment_meta.get("net_score", 0)

        # Call metadata
        transcript_segments = transcription.get("transcript", [])
        segment_count = len(transcript_segments)
        call_duration = 0.0
        if transcript_segments:
            call_duration = max(s.get("end", 0) for s in transcript_segments) - \
                           min(s.get("start", 0) for s in transcript_segments)

        cursor = conn.execute("""
            INSERT INTO call_history (
                filename, file_size_bytes, analyzed_at,
                final_score, profile_used, interpretation,
                commitment_status, commitment_net_score,
                talk_ratio_score, sentiment_score, empathy_score, commitment_score,
                call_duration, segment_count, agent_name,
                analysis_json, transcript_json, insights_json,
                weights_json, analyzer_results_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename,
            file_size_bytes,
            datetime.now(timezone.utc).isoformat(),
            analysis.get("final_score", 0.0),
            analysis.get("profile_used", "Sales"),
            analysis.get("interpretation", ""),
            commitment_status,
            commitment_net,
            talk_ratio_score,
            sentiment_score,
            empathy_score,
            commitment_score,
            round(call_duration, 2),
            segment_count,
            agent_name,
            json.dumps(analysis),
            json.dumps(transcription),
            json.dumps(insights),
            json.dumps(weights) if weights else None,
            json.dumps(analysis.get("analyzer_results", [])),
        ))

        conn.commit()
        row_id = cursor.lastrowid
        logger.info(f"Saved call '{filename}' → ID {row_id} (score: {analysis.get('final_score', 0):.1f})")
        return row_id

    except Exception as e:
        logger.error(f"Failed to save call: {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        conn.close()


def get_history(limit: int = 10, offset: int = 0) -> List[Dict]:
    """
    Get recent analyzed calls, most recent first.

    Args:
        limit: Max number of results (default 10)
        offset: Pagination offset

    Returns:
        List of call summary dicts
    """
    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT
                id, filename, file_size_bytes, analyzed_at,
                final_score, profile_used, interpretation,
                commitment_status, commitment_net_score,
                talk_ratio_score, sentiment_score, empathy_score, commitment_score,
                call_duration, segment_count, agent_name
            FROM call_history
            ORDER BY analyzed_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()

        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"Failed to fetch history: {e}", exc_info=True)
        return []
    finally:
        conn.close()


def get_call_detail(call_id: int) -> Optional[Dict]:
    """
    Get full detail for a specific call, including transcript and analysis JSON.

    Args:
        call_id: The row ID

    Returns:
        Full call dict or None if not found
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM call_history WHERE id = ?", (call_id,)
        ).fetchone()

        if not row:
            return None

        result = dict(row)

        # Parse JSON blobs back to dicts
        for json_col in ["analysis_json", "transcript_json", "insights_json",
                         "weights_json", "analyzer_results_json"]:
            if result.get(json_col):
                try:
                    result[json_col] = json.loads(result[json_col])
                except json.JSONDecodeError:
                    pass

        return result

    except Exception as e:
        logger.error(f"Failed to fetch call {call_id}: {e}", exc_info=True)
        return None
    finally:
        conn.close()


def get_stats() -> Dict:
    """
    Get aggregate stats across all analyzed calls.
    Useful for a manager dashboard overview.
    """
    conn = _get_connection()
    try:
        row = conn.execute("""
            SELECT
                COUNT(*) as total_calls,
                ROUND(AVG(final_score), 1) as avg_score,
                ROUND(MIN(final_score), 1) as min_score,
                ROUND(MAX(final_score), 1) as max_score,
                ROUND(AVG(talk_ratio_score), 1) as avg_talk_ratio,
                ROUND(AVG(sentiment_score), 1) as avg_sentiment,
                ROUND(AVG(empathy_score), 1) as avg_empathy,
                ROUND(AVG(commitment_score), 1) as avg_commitment,
                SUM(CASE WHEN commitment_status = 'Committed' THEN 1 ELSE 0 END) as committed_count,
                SUM(CASE WHEN commitment_status = 'Ghosted/Uncommitted' THEN 1 ELSE 0 END) as ghosted_count
            FROM call_history
        """).fetchone()

        return dict(row) if row else {}

    except Exception as e:
        logger.error(f"Failed to fetch stats: {e}", exc_info=True)
        return {}
    finally:
        conn.close()
