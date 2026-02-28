import { useState } from "react";

function parseInputList(value) {
  return value
    .split(/[,\n;]+/)
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

export default function ProfileForm({ onSave, loading }) {
  const [allergiesText, setAllergiesText] = useState("");
  const [medicationsText, setMedicationsText] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const allergies = parseInputList(allergiesText);
    const medications = parseInputList(medicationsText);

    if (allergies.length === 0 && medications.length === 0) {
      setError("Enter at least one allergy or one medication.");
      return;
    }

    try {
      await onSave({ allergies, medications });
    } catch (err) {
      setError(err.message || "Failed to save profile.");
    }
  }

  return (
    <section className="profile-form-container">
      <h2>Profile Setup</h2>
      <p className="muted">
        Add your allergies and medications once. SafePlate uses this profile for every scan to ensure your safety.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Food Allergies & Restrictions</label>
          <textarea
            placeholder="e.g. peanuts, shellfish, sesame, gluten"
            value={allergiesText}
            onChange={(event) => setAllergiesText(event.target.value)}
            rows={3}
          />
        </div>

        <div className="form-group">
          <label>Current Medications</label>
          <textarea
            placeholder="e.g. warfarin, lisinopril, statins..."
            value={medicationsText}
            onChange={(event) => setMedicationsText(event.target.value)}
            rows={3}
          />
        </div>

        {error ? <p className="error" style={{ marginBottom: "1.5rem" }}>{error}</p> : null}

        <button className="btn btn-primary btn-large" style={{ width: "100%" }} type="submit" disabled={loading}>
          {loading ? "Saving Profile..." : "Save Profile & Start Scanning"}
        </button>
      </form>
    </section>
  );
}
