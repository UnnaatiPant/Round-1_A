import os
import json
import fitz  # PyMuPDF
import unicodedata

def is_heading_candidate(text):
    if len(text.strip()) < 3:
        return False
    categories = [unicodedata.category(char) for char in text]
    # Must have some letters
    return any(cat.startswith('L') for cat in categories)

def get_outline_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    raw_items = []
    font_stats = {}

    title = os.path.splitext(os.path.basename(pdf_path))[0]

    for pg_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] != 0:
                continue
            for line in b['lines']:
                for span in line['spans']:
                    txt = span['text'].strip()
                    sz = round(span['size'], 1)
                    bold = span.get('flags', 0) & 2  # 2 = bold
                    if not is_heading_candidate(txt):
                        continue
                    font_stats[sz] = font_stats.get(sz, 0) + 1
                    raw_items.append({
                        "text": txt,
                        "size": sz,
                        "bold": bold,
                        "page": pg_num
                    })

    # Pick top 3 sizes as H1-H3
    top_sizes = sorted(font_stats.keys(), reverse=True)[:3]
    top_sizes.sort(reverse=True)

    level_map = {sz: f"H{i+1}" for i, sz in enumerate(top_sizes)}

    structured_outline = []
    for item in raw_items:
        lvl = level_map.get(item["size"])
        if lvl:
            structured_outline.append({
                "level": lvl,
                "text": item["text"],
                "page": item["page"]
            })

    return {
        "title": title,
        "outline": structured_outline
    }

def main():
    input_dir = "input"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    for file in os.listdir(input_dir):
        if file.endswith(".pdf"):
            in_path = os.path.join(input_dir, file)
            out_path = os.path.join(output_dir, file.replace(".pdf", ".json"))
            try:
                result = get_outline_from_pdf(in_path)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error in {file}: {e}")

if __name__ == "__main__":
    main()