function getScoreColor(score) {
    if (score >= 80) return "var(--clr-green)";
    if (score >= 50) return "var(--clr-yellow)";
    return "var(--clr-red)";
}

function getScoreLabel(score) {
    if (score >= 80) return "Excellent";
    if (score >= 60) return "Good";
    if (score >= 40) return "Fair";
    return "Needs Improvement";
}

export default function MenuSafetyScore({ score }) {
    if (score == null) return null;

    const color = getScoreColor(score);
    const label = getScoreLabel(score);
    const circumference = 2 * Math.PI * 54;
    const progress = (score / 100) * circumference;

    return (
        <div className="safety-score-card">
            <h3>Menu Safety Score</h3>
            <div className="score-ring-container">
                <svg viewBox="0 0 120 120" className="score-ring">
                    <circle
                        cx="60" cy="60" r="54"
                        fill="none"
                        stroke="var(--clr-border)"
                        strokeWidth="8"
                    />
                    <circle
                        cx="60" cy="60" r="54"
                        fill="none"
                        stroke={color}
                        strokeWidth="8"
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={circumference - progress}
                        transform="rotate(-90 60 60)"
                        className="score-ring-progress"
                    />
                </svg>
                <div className="score-ring-value">
                    <span className="score-number" style={{ color }}>{Math.round(score)}</span>
                    <span className="score-of">/100</span>
                </div>
            </div>
            <span className="score-label" style={{ color }}>{label}</span>
            <p className="score-hint">Based on allergen presence across all dishes</p>
        </div>
    );
}
