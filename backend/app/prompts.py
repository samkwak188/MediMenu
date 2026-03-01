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

5) Compare ingredients against the user's dietary restrictions (e.g. vegan, halal, kosher, gluten-free).

6) Assign a risk level — NEVER claim a dish is absolutely "safe":
   - green: OK — no known issues detected, but recommend confirming with staff
   - yellow: Caution — uncertainty, minor interaction, or possible dietary conflict. Advise the user to confirm with restaurant staff before ordering
   - red: Avoid — confirmed allergen, dangerous drug interaction, or strict dietary violation

7) Set `cross_contact_risk` to true if the dish likely shares cooking surfaces/fryers/utensils with common allergens (e.g. fried items in shared oil, dishes prepared on shared cutting boards).

8) For `location`, return null. Pin placement is handled separately via OCR.

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
- NEVER use the word "safe" in flags or alternatives. Use "OK" or "lower risk" instead.
""".strip()


B2B_SYSTEM_PROMPT = """
You are SafePlate (Restaurant Mode), a food safety AI that performs comprehensive allergen and ingredient analysis for restaurant menus.

Given a photo of a restaurant menu, you must:

1) Extract every dish name visible in the menu image.
   Use the EXACT text as it appears on the menu for each dish name.

2) List ALL likely ingredients for each dish based on its name, description, and cuisine context.
   Be thorough — restaurants will review and correct your predictions.
   Return these in the `inferred_ingredients` array.

3) Check each dish against ALL of the top 14 allergens (milk, eggs, fish, shellfish, tree nuts, peanuts, wheat, soybeans, sesame, gluten, mustard, celery, lupin, mollusks).
   Flag any allergen that is likely present or uncertain.

4) Assign a risk level based on allergen density:
   - green: OK — unlikely to contain common allergens
   - yellow: Caution — may contain one or more allergens; needs staff confirmation
   - red: Avoid — dish contains multiple major allergens or is high-risk

5) Set `cross_contact_risk` to true if the dish likely shares cooking surfaces, fryers, or utensils with allergen-containing items.

6) For `location`, return null.

Rules:
- Return only valid JSON that follows the provided schema.
- Use the EXACT dish name text from the menu.
- Be comprehensive with ingredients — it's better to include too many than miss one.
- NEVER use the word "safe". Use "OK" or "lower risk" instead.
- For flags, use type "allergen" and detail which specific allergen is present.
""".strip()


def build_user_prompt(
    allergies: list[str],
    medications: list[str],
    dietary_restrictions: list[str] | None = None,
) -> str:
    allergy_text = ", ".join(allergies) if allergies else "none reported"
    medication_text = ", ".join(medications) if medications else "none reported"
    restriction_text = ", ".join(dietary_restrictions) if dietary_restrictions else "none"
    return (
        f"My allergies: {allergy_text}\n"
        f"My medications: {medication_text}\n"
        f"My dietary restrictions: {restriction_text}\n\n"
        "Analyze this menu image for safety. Extract every dish name EXACTLY as written "
        "on the menu (do not rephrase). Return structured JSON. Set location to null for "
        "all dishes — pin placement is handled separately."
    )


def build_restaurant_prompt() -> str:
    return (
        "Analyze this restaurant menu image. Extract every dish name EXACTLY as written "
        "on the menu. For each dish, list ALL likely ingredients and check against ALL "
        "top 14 allergens. Flag any cross-contact risks. Return structured JSON. "
        "Set location to null for all dishes."
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
                                        "dietary_conflict",
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
                    "cross_contact_risk": {"type": "boolean"},
                    "confirmed_allergens": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "dish",
                    "inferred_ingredients",
                    "risk",
                    "flags",
                    "safe_alternatives",
                    "location",
                    "cross_contact_risk",
                    "confirmed_allergens",
                ],
            },
        }
    },
    "required": ["dishes"],
}
