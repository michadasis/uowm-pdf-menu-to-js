# UoWM PDF Menu to JS
 Small script that reads a restaurant menu PDF and converts it into a `restaurantMenu.js` file.

The PDF format it expects is the Greek university cafeteria schedule, where each page is one week and each week has a lunch and dinner section laid out as a table with the days of the week as columns. The number of weeks in the output is determined by the number of pages in the PDF, so if the schedule changes from a 2 week cycle to a 4 week cycle next year, you just run it again with the new PDF and it handles it automatically. It also automatically translates every meal from greek to english so it's possible to have a bilingual page layout.

## Requirements

Python 3.10 or higher 
`pdfplumber`.
`deep-translator`

```bash
pip install -r requirements.txt
```

If you are on a system managed Python install (Arch, for example) you may need to use a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # for bash or zsh
source .venv/bin/activate.fish  # for fish
```

## Usage

```bash
python main.py <input.pdf> [output.js]
```

The second argument is optional. If you leave it out, the output goes to `restaurantMenu.js` in the current directory.

Example:

```bash
python pdf_to_menu.py MENU-2025-2026.pdf src/assets/data/restaurantMenu.js
```
---