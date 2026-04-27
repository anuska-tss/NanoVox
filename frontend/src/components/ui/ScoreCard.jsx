import CircularGauge from './CircularGauge'

/**
 * ScoreCard — overall call quality card.
 * Renders the circular gauge, profile badge, and interpretation sentence.
 *
 * Props:
 *   analysis — the analysis object from the backend (or null/error object)
 */
export default function ScoreCard({ analysis }) {
    if (!analysis || analysis.error) {
        return (
            <div className="score-card">
                <div className="score-card-error">
                    <span>Scoring data unavailable</span>
                    {analysis?.message && <p>{analysis.message}</p>}
                </div>
            </div>
        )
    }

    const { final_score, profile_used, interpretation } = analysis

    return (
        <div className="score-card">
            <div className="score-card-header">
                <div>
                    <h3>Call Quality</h3>
                    <span className="profile-badge">{profile_used}</span>
                </div>
                <CircularGauge score={final_score} />
            </div>
            <hr className="score-divider" />
            {interpretation && (
                <p className="score-interpretation">{interpretation}</p>
            )}
        </div>
    )
}
