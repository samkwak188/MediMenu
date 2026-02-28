function toLocalTime(isoString) {
  const date = new Date(isoString);
  return Number.isNaN(date.getTime()) ? isoString : date.toLocaleString();
}

function countRisk(dishes, risk) {
  return dishes.filter((item) => item.risk === risk).length;
}

export default function HistoryPanel({ analyses, onSelect }) {
  if (!analyses || analyses.length === 0) {
    return (
      <section className="panel">
        <h2>Scan History</h2>
        <p className="muted">No previous scans yet.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>Scan History</h2>
      <div className="history-list">
        {analyses.map((entry) => (
          <article key={entry.analysis_id} className="history-item">
            <div>
              <p className="history-time">{toLocalTime(entry.created_at)}</p>
              <p className="muted">
                Red {countRisk(entry.dishes, "red")} / Yellow {countRisk(entry.dishes, "yellow")} / Green{" "}
                {countRisk(entry.dishes, "green")}
              </p>
            </div>
            <button className="btn btn-ghost" type="button" onClick={() => onSelect(entry)}>
              View
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
