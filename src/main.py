"""
Reads ΜΕΝΟΥ-YYYY.pdf and generates a restaurantMenu.js file.

The number of weeks (N) is determined automatically from the PDF -
one page = one week.

Usage:
    python main.py <input_pdf> [output_js]

    output_js defaults to restaurantMenu.js in the current directory.

Dependencies:
    pip install -r requirements.txt
"""

import sys
from utils import build_js, parse_week_from_page
from translate import translate_weeks

try:
    import pdfplumber
except ImportError:
    sys.exit("Missing dependency. Run: pip install -r requirements.txt")


def main():
    if len(sys.argv) < 2:
        sys.exit(f"Usage: python {sys.argv[0]} <input.pdf> [output.js]")

    pdf_path = sys.argv[1]
    js_path  = sys.argv[2] if len(sys.argv) > 2 else "restaurantMenu.js"

    print(f"Reading PDF: {pdf_path}")

    weeks_gr = []
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)
        print(f"Pages found: {num_pages}  ->  {num_pages} week(s) in menu cycle")
        for page in pdf.pages:
            weeks_gr.append(parse_week_from_page(page))

    weeks_en = translate_weeks(weeks_gr)

    js_content = build_js(weeks_gr, weeks_en, len(weeks_gr))

    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Written to: {js_path}")


if __name__ == "__main__":
    main()
