import { getScoreColor, getScoreLabel } from '../utils'

/**
 * CircularGauge — SVG ring gauge for a 0–100 score.
 *
 * Props:
 *   score — number (0–100)
 */
export default function CircularGauge({ score }) {
    const radius       = 44
    const circumference = 2 * Math.PI * radius
    const offset       = circumference - (score / 100) * circumference

    return (
        <div className="gauge-wrapper" role="img" aria-label={`Score: ${score.toFixed(1)} out of 100`}>
            <svg width="100%" height="100%" viewBox="0 0 100 100">
                <defs>
                    <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%"   stopColor="var(--gradient-start)" />
                        <stop offset="100%" stopColor="var(--gradient-end)" />
                    </linearGradient>
                </defs>
                <circle cx="50" cy="50" r={radius} fill="none" stroke="var(--bg-surface)" strokeWidth="6" />
                <circle
                    cx="50" cy="50" r={radius}
                    fill="none"
                    stroke={getScoreColor(score)}
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    transform="rotate(-90 50 50)"
                    style={{ transition: 'stroke-dashoffset 0.8s ease-out, stroke 0.4s ease' }}
                />
            </svg>
            <div className="gauge-center">
                <span className="gauge-score" style={{ color: getScoreColor(score) }}>{score.toFixed(0)}</span>
                <span className="gauge-label">{getScoreLabel(score)}</span>
            </div>
        </div>
    )
}
