# UoWM PDF Menu to JS
 Small script that reads a restaurant menu PDF and converts it into a `restaurantMenu.js` file.

## Requirements

Python 3.10 or higher and `pdfplumber`.

```bash
pip install pdfplumber
```

If you are on a system managed Python install (Arch, for example) you may need to use a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # bash/zsh
source .venv/bin/activate.fish  # fish
pip install pdfplumber
```

## Usage

```bash
python pdf_to_menu.py  [output.js]
```

The second argument is optional. If you leave it out, the output goes to `restaurantMenu.js` in the current directory.

Example:

```bash
python pdf_to_menu.py MENU-2025-2026.pdf src/assets/data/restaurantMenu.js
```

## What the output looks like

The script writes an ES module that exports a single `menu` object. At the top of the object there are a few metadata fields, followed by the breakfast section (which is the same every day), followed by one entry per week.

```js
export const menu = {
  cycleWeeks: 2,
  totalSchoolWeeks: 40,
  fullCycles: 20,
  partialWeeks: 0,
  breakfast: { ... },
  week1: {
    monday: {
      lunch:  { first: [...], main: [...] },
      dinner: { first: [...], main: [...] },
      extra:  ["Γλυκό"]
    },
    ...
  },
  week2: { ... },
};
```

The `cycleWeeks` field is what we use to figure out which week of the rotation is currently active.

## Cycle stats

When you run the script it prints a short summary to the console showing how the menu cycle maps onto the school year:

```
-- Cycle stats -----------------------------------------------
  school_year_start                        2025-09-08
  school_year_end                          2026-06-12
  total_school_weeks                       40
  menu_cycle_weeks                         2
  full_cycles                              20
  partial_weeks_in_last_cycle              0
--------------------------------------------------------------

---
