import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { prepareImageForUpload } from "../utils/image";

const RISK_ORDER = { red: 0, yellow: 1, green: 2 };

const RISK_META = {
  red: { label: "Avoid", icon: "⚠️", cardClass: "risk-red", markerClass: "marker-red" },
  yellow: { label: "Caution", sublabel: "Confirm with staff", icon: "⚡", cardClass: "risk-yellow", markerClass: "marker-yellow" },
  green: { label: "OK", icon: "✓", cardClass: "risk-green", markerClass: "marker-green" },
};

function countByRisk(dishes) {
  const counts = { red: 0, yellow: 0, green: 0 };
  dishes.forEach((d) => {
    if (counts[d.risk] !== undefined) counts[d.risk] += 1;
  });
  return counts;
}

function clampUnit(v) {
  if (typeof v !== "number" || Number.isNaN(v)) return 0;
  return Math.max(0, Math.min(1, v));
}

function normalizeLocation(loc) {
  if (!loc) return null;
  // x,y from the API are already the CENTER of the dish title
  const x = clampUnit(loc.x);
  const y = clampUnit(loc.y);
  return { x, y };
}

function IngredientList({ ingredients }) {
  if (!ingredients || ingredients.length === 0) return null;
  return (
    <div className="ingredient-list">
      <span className="ingredient-label">Ingredients:</span>{" "}
      <span className="ingredient-items">{ingredients.join(", ")}</span>
    </div>
  );
}

function DishCard({ dish, index, isSelected, onSelect }) {
  if (!dish) return null;
  const meta = RISK_META[dish.risk] || RISK_META.yellow;
  return (
    <article
      className={`dish-card ${meta.cardClass} ${isSelected ? "dish-card-selected" : ""}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onSelect()}
    >
      <header className="dish-header">
        <div className="dish-title-row">
          <span className={`dish-number ${meta.markerClass}`}>{index + 1}</span>
          <h3>{dish.dish}</h3>
        </div>
        <span className="badge">
          {meta.icon} {meta.label}
        </span>
      </header>

      <IngredientList ingredients={dish.inferred_ingredients} />

      {dish.flags.length > 0 ? (
        <ul className="flag-list">
          {dish.flags.map((f, i) => (
            <li key={`${f.type}-${i}`}>
              <strong>{f.type.replaceAll("_", " ")}</strong>: {f.detail}{" "}
              <span className="severity-tag">{f.severity}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted no-issues">No issues for this dish.</p>
      )}

      {dish.safe_alternatives ? (
        <p className="alt">
          <strong>💡 Safer option:</strong> {dish.safe_alternatives}
        </p>
      ) : null}
    </article>
  );
}

/**
 * Unified panel: upload + image preview + annotated pins + dish card list.
 *
 * Props:
 *  - analysis          current analysis result (or null)
 *  - imageSrc          data-url of the analysed image (or "")
 *  - onAnalyze({ base64, mimeType, imageDataUrl })
 *  - loading           boolean – API call in progress
 */
export default function ResultsView({ analysis, imageSrc, onAnalyze, loading }) {
  /* ── file state ──────────────────────────────────── */
  const [file, setFile] = useState(null);
  const [fileError, setFileError] = useState("");

  const previewUrl = useMemo(() => (file ? URL.createObjectURL(file) : ""), [file]);
  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  /* ── analysis state ──────────────────────────────── */
  const sorted = useMemo(() => {
    if (!analysis) return [];
    return [...analysis.dishes].sort((a, b) => RISK_ORDER[a.risk] - RISK_ORDER[b.risk]);
  }, [analysis]);

  const [selectedIndex, setSelectedIndex] = useState(0);
  const sectionRef = useRef(null);
  const cardListRef = useRef(null);

  useEffect(() => { setSelectedIndex(0); }, [analysis?.analysis_id]);

  // Auto-scroll when results arrive
  useEffect(() => {
    if (analysis && sectionRef.current) {
      sectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [analysis?.analysis_id]);

  /* ── handlers ────────────────────────────────────── */
  async function handleAnalyze() {
    if (!file) { setFileError("Select or capture a menu image first."); return; }
    setFileError("");
    try {
      const prepared = await prepareImageForUpload(file);
      await onAnalyze({
        ...prepared,
        imageDataUrl: `data:${prepared.mimeType};base64,${prepared.base64}`,
      });
    } catch (err) {
      setFileError(err.message || "Could not process this image.");
    }
  }

  const handlePinClick = useCallback((idx) => {
    setSelectedIndex(idx);
    if (cardListRef.current) {
      const cards = cardListRef.current.querySelectorAll(".dish-card");
      if (cards[idx]) cards[idx].scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, []);

  /* ── derived ─────────────────────────────────────── */
  const hasAnalysis = Boolean(analysis);
  const displayedImage = hasAnalysis ? imageSrc : previewUrl;
  const pinItems = sorted
    .map((d, i) => ({ dish: d, index: i, loc: normalizeLocation(d.location) }))
    .filter((p) => p.loc);
  const showPins = hasAnalysis && pinItems.length > 0;
  const counts = hasAnalysis ? countByRisk(sorted) : null;

  /* ── render ──────────────────────────────────────── */
  return (
    <section className="panel unified-panel" ref={sectionRef}>
      <h2>Menu Scanner</h2>

      {/* ── file picker row ───────────────────────── */}
      <div className="capture-bar">
        <label className="file-label">
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={(e) => { setFile(e.target.files?.[0] || null); setFileError(""); }}
          />
        </label>
        {loading ? null : (
          <div className="capture-actions">
            <button className="btn btn-primary" type="button" disabled={loading || !file} onClick={handleAnalyze}>
              Analyze Menu
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setFile(null)} disabled={loading}>
              Clear
            </button>
          </div>
        )}
      </div>

      {fileError ? <p className="error">{fileError}</p> : null}

      {/* ── loading spinner ───────────────────────── */}
      {loading ? (
        <div className="loading-overlay">
          <div className="spinner" />
          <p className="loading-text">Analyzing your menu for allergens and interactions…</p>
        </div>
      ) : null}

      {/* ── summary counters (after analysis) ─────── */}
      {counts ? (
        <div className="summary-grid">
          <div className="summary risk-red">
            <span className="summary-count">{counts.red}</span>
            <span className="summary-label">Avoid</span>
          </div>
          <div className="summary risk-yellow">
            <span className="summary-count">{counts.yellow}</span>
            <span className="summary-label">Caution</span>
          </div>
          <div className="summary risk-green">
            <span className="summary-count">{counts.green}</span>
            <span className="summary-label">Safe</span>
          </div>
        </div>
      ) : null}

      {/* ── main content: image + cards ────────────── */}
      {displayedImage ? (
        <div className={hasAnalysis ? "results-layout" : ""}>
          {/* image column */}
          <div className="results-image-col">
            <div className="annotated-image-shell">
              <img
                className="annotated-image"
                src={displayedImage}
                alt={hasAnalysis ? "Menu with safety pins" : "Menu preview"}
                draggable={false}
              />

              {showPins ? (
                <div className="annotation-layer">
                  {pinItems.map((item) => {
                    const meta = RISK_META[item.dish.risk] || RISK_META.yellow;
                    const isActive = selectedIndex === item.index;
                    return (
                      <button
                        key={item.index}
                        type="button"
                        className={`annotation-pin ${meta.markerClass} ${isActive ? "annotation-selected" : ""}`}
                        style={{
                          left: `${item.loc.x * 100}%`,
                          top: `${item.loc.y * 100}%`,
                        }}
                        onClick={() => handlePinClick(item.index)}
                        aria-label={`${item.dish.dish} — ${meta.label}`}
                      >
                        <span className="pin-number">{item.index + 1}</span>
                      </button>
                    );
                  })}
                </div>
              ) : null}
            </div>
          </div>

          {/* card column (only after analysis) */}
          {hasAnalysis ? (
            <div className="results-card-col" ref={cardListRef}>
              {sorted.map((dish, i) => (
                <DishCard
                  key={`${dish.dish}-${i}`}
                  dish={dish}
                  index={i}
                  isSelected={selectedIndex === i}
                  onSelect={() => setSelectedIndex(i)}
                />
              ))}
            </div>
          ) : null}
        </div>
      ) : (
        <p className="muted placeholder-hint">
          Upload or capture a menu photo above to get started.
        </p>
      )}
    </section>
  );
}
