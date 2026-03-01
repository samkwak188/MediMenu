export default function RestaurantAnalytics({ analytics }) {
    if (!analytics) {
        return <p className="muted">Analytics will appear here once diners start scanning your menu.</p>;
    }

    const { total_scans, top_flagged_allergens } = analytics;
    const maxCount = top_flagged_allergens.length > 0
        ? Math.max(...top_flagged_allergens.map((a) => a.count))
        : 1;

    return (
        <div className="analytics-card">
            <h3>Diner Insights</h3>

            <div className="analytics-stat-row">
                <div className="analytics-stat">
                    <span className="analytics-stat-value">{total_scans}</span>
                    <span className="analytics-stat-label">Total Scans</span>
                </div>
                <div className="analytics-stat">
                    <span className="analytics-stat-value">{top_flagged_allergens.length}</span>
                    <span className="analytics-stat-label">Allergens Flagged</span>
                </div>
            </div>

            {top_flagged_allergens.length > 0 ? (
                <>
                    <h4 className="analytics-subtitle">Most Flagged Allergens</h4>
                    <div className="analytics-bars">
                        {top_flagged_allergens.map(({ allergen, count }) => (
                            <div key={allergen} className="analytics-bar-row">
                                <span className="analytics-bar-label">{allergen}</span>
                                <div className="analytics-bar-track">
                                    <div
                                        className="analytics-bar-fill"
                                        style={{ width: `${(count / maxCount) * 100}%` }}
                                    />
                                </div>
                                <span className="analytics-bar-count">{count}</span>
                            </div>
                        ))}
                    </div>
                </>
            ) : (
                <p className="muted">No allergen flags recorded yet.</p>
            )}
        </div>
    );
}
