"""
translate.py
------------
Translates Greek meal names to English using Google Translate via deep-translator.
No API key required.
"""

from deep_translator import GoogleTranslator


def _get_all_strings(weeks: list[dict]) -> list[str]:
    """Collect every unique Greek meal string across all weeks."""
    seen = set()
    result = []
    for week in weeks:
        for day in week.values():
            for meal in ("lunch", "dinner"):
                for course in ("first", "main"):
                    for item in day[meal][course]:
                        if item and item not in seen:
                            seen.add(item)
                            result.append(item)
            for item in day.get("extra", []):
                if item and item not in seen:
                    seen.add(item)
                    result.append(item)
    return result


def translate_weeks(weeks: list[dict]) -> list[dict]:
    """
    Returns a new list of week dicts with all meal strings translated to English.
    Batches all unique strings into a single request where possible.
    """
    strings = _get_all_strings(weeks)
    if not strings:
        return weeks

    print(f"Translating {len(strings)} unique meal strings via Google Translate...")
    translator = GoogleTranslator(source="el", target="en")

    translated = translator.translate_batch(strings)
    translation_map = dict(zip(strings, translated))

    def translate_list(items: list[str]) -> list[str]:
        return [translation_map.get(item, item) for item in items]

    translated_weeks = []
    for week in weeks:
        translated_week = {}
        for day_key, day in week.items():
            translated_week[day_key] = {
                "lunch": {
                    "first": translate_list(day["lunch"]["first"]),
                    "main":  translate_list(day["lunch"]["main"]),
                },
                "dinner": {
                    "first": translate_list(day["dinner"]["first"]),
                    "main":  translate_list(day["dinner"]["main"]),
                },
                "extra": translate_list(day["extra"]),
            }
        translated_weeks.append(translated_week)

    print("Done.")
    return translated_weeks
