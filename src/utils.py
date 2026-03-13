import re
from constants import DAYS_EN, BREAKFAST_GR, BREAKFAST_EN, SKIP_RE


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


def py_to_js_array(lst: list) -> str:
    items = ", ".join(f'"{v}"' for v in lst)
    return f"[{items}]"


def render_day(day_gr: dict, day_en: dict, indent: int = 6) -> str:
    pad  = " " * indent
    pad2 = " " * (indent + 2)
    lines = []

    lines.append(f"{pad}lunch: {{")
    lines.append(f"{pad2}first: {{ gr: {py_to_js_array(day_gr['lunch']['first'])}, en: {py_to_js_array(day_en['lunch']['first'])} }},")
    lines.append(f"{pad2}main:  {{ gr: {py_to_js_array(day_gr['lunch']['main'])},  en: {py_to_js_array(day_en['lunch']['main'])}  }}")
    lines.append(f"{pad}}},")
    lines.append(f"{pad}dinner: {{")
    lines.append(f"{pad2}first: {{ gr: {py_to_js_array(day_gr['dinner']['first'])}, en: {py_to_js_array(day_en['dinner']['first'])} }},")
    lines.append(f"{pad2}main:  {{ gr: {py_to_js_array(day_gr['dinner']['main'])},  en: {py_to_js_array(day_en['dinner']['main'])}  }}")
    lines.append(f"{pad}}},")
    lines.append(f"{pad}extra: {{ gr: {py_to_js_array(day_gr['extra'])}, en: {py_to_js_array(day_en['extra'])} }}")

    return "\n".join(lines)


def render_week(week_gr: dict, week_en: dict, week_num: int) -> str:
    lines = [f"  week{week_num}: {{"]
    for day in DAYS_EN:
        lines.append(f"    {day}: {{")
        lines.append(render_day(week_gr[day], week_en[day]))
        lines.append(f"    }},")
    lines.append(f"  }},")
    return "\n".join(lines)


def render_breakfast(b_gr: dict, b_en: dict) -> str:
    lines = ["  breakfast: {"]
    for key in b_gr:
        lines.append(f"    {key}: {{ gr: {py_to_js_array(b_gr[key])}, en: {py_to_js_array(b_en[key])} }},")
    lines.append("  },")
    return "\n".join(lines)


def build_js(weeks_gr: list[dict], weeks_en: list[dict], cycle_weeks: int) -> str:
    parts = [f"// Menu auto-generated from PDF  ({cycle_weeks}-week cycle)\n", "export const menu = {"]
    parts.append(f"  cycleWeeks: {cycle_weeks},")
    parts.append(render_breakfast(BREAKFAST_GR, BREAKFAST_EN))
    for i, (week_gr, week_en) in enumerate(zip(weeks_gr, weeks_en), start=1):
        parts.append(render_week(week_gr, week_en, i))
    parts.append("};\n")
    return "\n".join(parts)
