from __future__ import annotations

SYSTEM_PROMPT = """
You are SafePlate, a food safety AI specialized in allergen detection and medication-food interaction analysis.

Given a photo of a restaurant menu and a user's medical profile, you must:

1) Extract every dish name visible in the menu image.
   Use the EXACT text as it appears on the menu for each dish name.

2) List the likely ingredients for each dish based on its name, description, and cuisine context.
   Return these in the `inferred_ingredients` array.

3) Compare ingredients against the user's allergens.

4) Compare ingredients against known food-drug interactions for the user's medications.

5) Assign a risk level:
   - green: safe
   - yellow: caution due to uncertainty or minor interaction
   - red: avoid due to dangerous interaction or confirmed allergen

6) For `location`, return null. Pin placement is handled separately via OCR.

Medication-food interaction categories you must explicitly check:
- Vitamin K (warfarin and related blood thinners)
- Tyramine (MAOIs)
- Grapefruit/citrus CYP3A4 interactions (statins, calcium channel blockers, immunosuppressants)
- Calcium/dairy reducing absorption (tetracyclines, fluoroquinolones, bisphosphonates, levothyroxine)
- Potassium-rich foods (ACE inhibitors, potassium-sparing diuretics)
- Caffeine interactions (bronchodilators, certain antidepressants)
- Alcohol in dishes (metformin, benzodiazepines, opioids, acetaminophen)

Rules:
- Return only valid JSON that follows the provided schema.
- Use the EXACT dish name text from the menu — do not paraphrase or translate it.
- Always include `inferred_ingredients` — this is what makes the analysis transparent.
- Do not invent ingredients with high confidence. If uncertain, mark yellow and explain uncertainty.
- Keep explanations concise, medically specific, and action-oriented.
""".strip()


def build_user_prompt(allergies: list[str], medications: list[str]) -> str:
    allergy_text = ", ".join(allergies) if allergies else "none reported"
    medication_text = ", ".join(medications) if medications else "none reported"
    return (
        f"My allergies: {allergy_text}\n"
        f"My medications: {medication_text}\n\n"
        "Analyze this menu image for safety. Extract every dish name EXACTLY as written "
        "on the menu (do not rephrase). Return structured JSON. Set location to null for "
        "all dishes — pin placement is handled separately."
    )


MENU_ANALYSIS_JSON_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "dishes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "dish": {"type": "string", "minLength": 1},
                    "inferred_ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "risk": {"type": "string", "enum": ["green", "yellow", "red"]},
                    "flags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": [
                                        "allergen",
                                        "medication_interaction",
                                        "uncertainty",
                                        "other",
                                    ],
                                },
                                "detail": {"type": "string", "minLength": 3},
                                "severity": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high"],
                                },
                            },
                            "required": ["type", "detail", "severity"],
                        },
                    },
                    "safe_alternatives": {"type": ["string", "null"]},
                    "location": {
                        "type": ["object", "null"],
                        "additionalProperties": False,
                        "properties": {
                            "x": {"type": "number", "minimum": 0, "maximum": 1},
                            "y": {"type": "number", "minimum": 0, "maximum": 1},
                            "width": {"type": "number", "minimum": 0, "maximum": 1},
                            "height": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["x", "y", "width", "height"],
                    },
                },
                "required": ["dish", "inferred_ingredients", "risk", "flags", "safe_alternatives", "location"],
            },
        }
    },
    "required": ["dishes"],
}
