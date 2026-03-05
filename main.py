"""
pdf_to_menu.py
--------------
Reads ΜΕΝΟΥ-YYYY.pdf and generates a restaurantMenu.js file.

The number of weeks (N) is determined automatically from the PDF —
one page = one week. The script also calculates how many times the
N-week cycle repeats across the school year and prints the stats.

Usage:
    python pdf_to_menu.py <input_pdf> [output_js]

    output_js defaults to restaurantMenu.js in the current directory.

Dependencies:
    pip install pdfplumber --break-system-packages
"""

import sys
import re
from datetime import date, timedelta

try:
    import pdfplumber
except ImportError:
    sys.exit("Missing dependency.  Run:  pip install pdfplumber --break-system-packages")


DAYS_EN = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

BREAKFAST = {
    "drinks":  ["Τσάι", "Γάλα", "Χυμός"],
    "spreads": ["Μαρμελάδα 2 είδη", "Μέλι", "Βούτυρο", "Μαργαρίνη", "Τυρί Edam", "Ζαμπόν"],
    "breads":  ["Ψωμί Λευκό-μαύρο", "Φρυγανιές"],
    "staples": ["Αυγό", "Κέικ", "Corn Flakes (Δημητριακά)"],
}

SKIP_PATTERNS = [
    r"^\d+η\s*εβδομάδα",
    r"^Πρωινό",
    r"^Τσάι",
    r"^ΓΕΥΜΑ",
    r"^ΔΕΙΠΝΟ",
    r"^Πρώτο Πιάτο",
    r"^Κυρίως Πιάτο",
    r"^Τυρί",
    r"^Δυο \(2\)",
    r"^Δύο \(2\)",
    r"^(Γλυκό|Φρούτο)$",
    r"^Δευτέρα",
]

SKIP_RE = re.compile("|".join(SKIP_PATTERNS))


def should_skip(cell: str) -> bool:
    return not cell or SKIP_RE.match(cell.strip())


def clean(text) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def extract_day_columns(table: list, num_days: int = 7) -> list[list[str]]:

    day_col_indices = None
    for row in table:
        cells = [clean(c) for c in row]
        if sum(1 for c in cells if "Δευτέρα" in c or "Τρίτη" in c or
               "Τετάρτη" in c or "Πέμπτη" in c or "Παρασκευή" in c) >= 3:
            day_col_indices = [i for i, c in enumerate(cells) if c and not c.isspace()]
            break

    if not day_col_indices or len(day_col_indices) < num_days:
        if day_col_indices is None:
            day_col_indices = list(range(len(table[0]) if table else 0))

    day_col_indices = day_col_indices[:num_days]

    cols: list[list[str]] = [[] for _ in range(num_days)]
    for row in table:
        cells = [clean(c) for c in row]
        for day_idx, col_idx in enumerate(day_col_indices):
            if col_idx < len(cells):
                val = cells[col_idx]
                if val and not should_skip(val):
                    cols[day_idx].append(val)

    return cols


def parse_section(cols: list[list[str]]) -> list[dict]:
    days = []
    for col in cols:
        n = len(col)
        if n == 0:
            days.append({"first": [], "main": [], "extra": []})
        elif n == 1:
            days.append({"first": [col[0]], "main": [], "extra": []})
        elif n == 2:
            days.append({"first": [col[0]], "main": [col[1]], "extra": []})
        elif n == 3:
            days.append({"first": [col[0]], "main": [col[1], col[2]], "extra": []})
        elif n == 4:
            days.append({"first": [col[0]], "main": [col[1], col[2]], "extra": [col[3]]})
        else:
            days.append({"first": col[:2], "main": col[2:-1], "extra": [col[-1]]})
    return days


DAY_NAMES_GR = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]


def get_day_col_indices(rows: list) -> list[int]:
    from collections import Counter
    col_hits = Counter()
    in_data = False
    for row in rows:
        cells = [clean(c) for c in row]
        joined = " ".join(cells)
        # Start counting after ΓΕΥΜΑ/ΔΕΙΠΝΟ section headers
        if "ΓΕΥΜΑ" in joined or "ΔΕΙΠΝΟ" in joined or "Πρώτο Πιάτο" in joined or "Κυρίως Πιάτο" in joined:
            in_data = True
            continue
        if not in_data:
            continue
        for i, c in enumerate(cells):
            if c and not should_skip(c):
                col_hits[i] += 1

    if len(col_hits) >= 7:
        return sorted(col for col, _ in col_hits.most_common(7))

    for row in rows:
        cells = [clean(c) for c in row]
        found = {}
        for i, c in enumerate(cells):
            for d in DAY_NAMES_GR:
                if d in c:
                    found[d] = i
                    break
        if len(found) >= 5:
            indices = [found.get(d) for d in DAY_NAMES_GR]
            # If Monday header is at col 1 but col 0 has data, shift Monday to 0
            if indices[0] == 1 and col_hits.get(0, 0) > 0:
                indices[0] = 0
            return indices

    return list(range(7))


def parse_section_from_rows(rows: list, day_col_indices: list) -> list[dict]:
    num_days = 7
    in_first = False
    in_main  = False

    first_rows = []
    main_rows  = []
    extra_row  = None

    for row in rows:
        cells = [clean(c) for c in row]
        joined = " ".join(cells)

        if "Πρώτο Πιάτο" in joined:
            in_first, in_main = True, False
            continue
        if "Κυρίως Πιάτο" in joined:
            in_first, in_main = False, True
            continue
        if should_skip(cells[0] if cells else ""):
            # Check for the Γλυκό/Φρούτο row
            vals = [cells[idx] if idx is not None and idx < len(cells) else ""
                    for idx in day_col_indices]
            if any(v in ("Γλυκό", "Φρούτο") for v in vals):
                extra_row = vals
            continue

        mapped = [cells[idx] if idx is not None and idx < len(cells) else ""
                  for idx in day_col_indices]

        if in_first:
            first_rows.append(mapped)
        elif in_main:
            main_rows.append(mapped)

    days = []
    for d in range(num_days):
        first = [r[d] for r in first_rows if r[d]]
        main  = [r[d] for r in main_rows  if r[d]]
        extra = [extra_row[d]] if extra_row and d < len(extra_row) and extra_row[d] else []
        days.append({"first": first, "main": main, "extra": extra})
    return days


def parse_week_from_page(page) -> dict:
    tables = page.extract_tables()
    week = {}

    lunch_rows_by_cols  = None
    dinner_rows_by_cols = None

    for table in tables:
        col_indices = get_day_col_indices(table)
        current = None
        lunch_rows  = []
        dinner_rows = []

        for row in table:
            cells = [clean(c) for c in row]
            joined = " ".join(cells)
            if "ΓΕΥΜΑ" in joined:
                current = "lunch"
                continue
            if "ΔΕΙΠΝΟ" in joined:
                current = "dinner"
                continue
            if current == "lunch":
                lunch_rows.append(row)
            elif current == "dinner":
                dinner_rows.append(row)

        if lunch_rows and lunch_rows_by_cols is None:
            lunch_rows_by_cols = (lunch_rows, col_indices)
        if dinner_rows and dinner_rows_by_cols is None:
            dinner_rows_by_cols = (dinner_rows, col_indices)

    lunch_days  = parse_section_from_rows(*(lunch_rows_by_cols  or ([], list(range(7)))))
    dinner_days = parse_section_from_rows(*(dinner_rows_by_cols or ([], list(range(7)))))

    for i, day_en in enumerate(DAYS_EN):
        week[day_en] = {
            "lunch":  {"first": lunch_days[i]["first"],  "main": lunch_days[i]["main"]},
            "dinner": {"first": dinner_days[i]["first"], "main": dinner_days[i]["main"]},
            "extra":  lunch_days[i]["extra"] or dinner_days[i]["extra"],
        }

    return week

def school_year_cycle_stats(
    num_weeks: int,
    start: date = date(2025, 9, 8),   # typical Greek school year start
    end:   date = date(2026, 6, 12),  # typical Greek school year end
) -> dict:
    first_monday = start + timedelta(days=(7 - start.weekday()) % 7)
    total_weeks  = 0
    d = first_monday
    while d <= end:
        total_weeks += 1
        d += timedelta(weeks=1)

    full_cycles   = total_weeks // num_weeks
    partial_weeks = total_weeks  % num_weeks

    return {
        "school_year_start": str(start),
        "school_year_end":   str(end),
        "total_school_weeks": total_weeks,
        "menu_cycle_weeks":   num_weeks,
        "full_cycles":        full_cycles,
        "partial_weeks_in_last_cycle": partial_weeks,
    }


def py_to_js_array(lst: list) -> str:
    items = ", ".join(f'"{v}"' for v in lst)
    return f"[{items}]"


def render_day(day_data: dict, indent: int = 6) -> str:
    pad  = " " * indent
    pad2 = " " * (indent + 2)
    lines = []
    lines.append(f"{pad}lunch: {{")
    lines.append(f"{pad2}first: {py_to_js_array(day_data['lunch']['first'])},")
    lines.append(f"{pad2}main:  {py_to_js_array(day_data['lunch']['main'])}")
    lines.append(f"{pad}}},")
    lines.append(f"{pad}dinner: {{")
    lines.append(f"{pad2}first: {py_to_js_array(day_data['dinner']['first'])},")
    lines.append(f"{pad2}main:  {py_to_js_array(day_data['dinner']['main'])}")
    lines.append(f"{pad}}},")
    lines.append(f"{pad}extra: {py_to_js_array(day_data['extra'])}")
    return "\n".join(lines)


def render_week(week_data: dict, week_num: int) -> str:
    lines = [f"  week{week_num}: {{"]
    for day in DAYS_EN:
        lines.append(f"    {day}: {{")
        lines.append(render_day(week_data[day]))
        lines.append(f"    }},")
    lines.append(f"  }},")
    return "\n".join(lines)


def render_breakfast(b: dict) -> str:
    lines = ["  breakfast: {"]
    for key, val in b.items():
        lines.append(f"    {key}: {py_to_js_array(val)},")
    lines.append("  },")
    return "\n".join(lines)


def build_js(weeks: list[dict], stats: dict) -> str:
    n = len(weeks)
    header_comment = (
        f"// Menu auto-generated from PDF  ({n}-week cycle)\n"
        f"// School year: {stats['school_year_start']} → {stats['school_year_end']}\n"
        f"// Total school weeks : {stats['total_school_weeks']}\n"
        f"// Full {n}-week cycles: {stats['full_cycles']}  "
        f"(+ {stats['partial_weeks_in_last_cycle']} partial week(s))\n"
    )
    parts = [header_comment, "export const menu = {"]
    parts.append(f"  cycleWeeks: {n},")
    parts.append(f"  totalSchoolWeeks: {stats['total_school_weeks']},")
    parts.append(f"  fullCycles: {stats['full_cycles']},")
    parts.append(f"  partialWeeks: {stats['partial_weeks_in_last_cycle']},")
    parts.append(render_breakfast(BREAKFAST))
    for i, week in enumerate(weeks, start=1):
        parts.append(render_week(week, i))
    parts.append("};\n")
    return "\n".join(parts)


def main():
    if len(sys.argv) < 2:
        sys.exit(f"Usage: python {sys.argv[0]} <input.pdf> [output.js]")

    pdf_path = sys.argv[1]
    js_path  = sys.argv[2] if len(sys.argv) > 2 else "restaurantMenu.js"

    print(f"Reading PDF: {pdf_path}")

    weeks = []
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        print(f"Pages found: {num_pages}  →  {num_pages} week(s) in menu cycle")
        for page in pdf.pages:
            weeks.append(parse_week_from_page(page))

    stats = school_year_cycle_stats(num_weeks=len(weeks))

    print("\nCycle stats")
    for k, v in stats.items():
        print(f"  {k:<40} {v}")

    js_content = build_js(weeks, stats)

    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Written to: {js_path}")


if __name__ == "__main__":
    main()