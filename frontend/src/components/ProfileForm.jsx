import { useState } from "react";

const RESTRICTION_OPTIONS = [
  "Vegan",
  "Vegetarian",
  "Halal",
  "Kosher",
  "Gluten-Free",
  "Dairy-Free",
  "Nut-Free",
];

function parseInputList(value) {
  return value
    .split(/[,\n;]+/)
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

export default function ProfileForm({ onSave, loading }) {
  const [allergiesText, setAllergiesText] = useState("");
  const [medicationsText, setMedicationsText] = useState("");
  const [selectedRestrictions, setSelectedRestrictions] = useState([]);
  const [error, setError] = useState("");

  function toggleRestriction(restriction) {
    setSelectedRestrictions((prev) =>
      prev.includes(restriction)
        ? prev.filter((r) => r !== restriction)
        : [...prev, restriction]
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const allergies = parseInputList(allergiesText);
    const medications = parseInputList(medicationsText);
    const dietaryRestrictions = selectedRestrictions.map((r) => r.toLowerCase());

    if (allergies.length === 0 && medications.length === 0 && dietaryRestrictions.length === 0) {
      setError("Enter at least one allergy, medication, or dietary restriction.");
      return;
    }

    try {
      await onSave({ allergies, medications, dietaryRestrictions });
    } catch (err) {
      setError(err.message || "Failed to save profile.");
    }
  }

  return (
    <section className="profile-form-container">
      <h2>Profile Setup</h2>
      <p className="muted">
        Add your allergies, medications, and dietary restrictions. SafePlate uses this profile for every scan to personalize results.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Food Allergies</label>
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

        <div className="form-group">
          <label>Dietary Restrictions</label>
          <div className="restriction-chips">
            {RESTRICTION_OPTIONS.map((r) => (
              <button
                key={r}
                type="button"
                className={`restriction-chip ${selectedRestrictions.includes(r) ? "selected" : ""}`}
                onClick={() => toggleRestriction(r)}
              >
                {selectedRestrictions.includes(r) ? "✓ " : ""}
                {r}
              </button>
            ))}
          </div>
        </div>

        {error ? <p className="error" style={{ marginBottom: "1.5rem" }}>{error}</p> : null}

        <button className="btn btn-primary btn-large" style={{ width: "100%" }} type="submit" disabled={loading}>
          {loading ? "Saving Profile..." : "Save Profile & Start Scanning"}
        </button>
      </form>
    </section>
  );
}
