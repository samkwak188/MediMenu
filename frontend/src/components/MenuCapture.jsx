import { useEffect, useMemo, useState } from "react";
import { prepareImageForUpload } from "../utils/image";

export default function MenuCapture({ onAnalyze, loading }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");

  const previewUrl = useMemo(() => {
    if (!file) {
      return "";
    }
    return URL.createObjectURL(file);
  }, [file]);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  async function handleAnalyze() {
    if (!file) {
      setError("Select or capture a menu image first.");
      return;
    }

    setError("");
    try {
      const prepared = await prepareImageForUpload(file);
      await onAnalyze({
        ...prepared,
        imageDataUrl: `data:${prepared.mimeType};base64,${prepared.base64}`,
      });
    } catch (err) {
      setError(err.message || "Could not process this image.");
    }
  }

  return (
    <section className="panel">
      <h2>Menu Scan</h2>
      <p className="muted">
        Use your phone camera or upload a menu photo. Clear, straight images work best.
      </p>

      <label className="file-label">
        <input
          type="file"
          accept="image/*"
          capture="environment"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
        />
      </label>

      {previewUrl ? (
        <div className="preview-wrap">
          <img className="preview-image" src={previewUrl} alt="Selected menu preview" />
        </div>
      ) : null}

      {error ? <p className="error">{error}</p> : null}

      {loading ? (
        <div className="loading-overlay">
          <div className="spinner" />
          <p className="loading-text">Analyzing your menu for allergens and interactions…</p>
        </div>
      ) : (
        <div className="actions">
          <button className="btn btn-primary" type="button" disabled={loading} onClick={handleAnalyze}>
            Analyze Menu
          </button>
          <button className="btn btn-ghost" type="button" onClick={() => setFile(null)} disabled={loading}>
            Clear
          </button>
        </div>
      )}
    </section>
  );
}
