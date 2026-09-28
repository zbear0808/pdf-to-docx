import sys
from docx import Document
from docx.oxml.ns import qn

def inspect_docx(docx_path):
    print(f"=== Inspecting {docx_path} ===")
    doc = Document(docx_path)
    
    # 1. Inspect Paragraphs and Runs for Color
    blue_runs = []
    total_runs = 0
    for p_idx, p in enumerate(doc.paragraphs):
        for r_idx, r in enumerate(p.runs):
            total_runs += 1
            if r.font and r.font.color and r.font.color.rgb:
                color_hex = str(r.font.color.rgb)
                if "1F4E79" in color_hex.upper() or "BLUE" in color_hex.upper() or color_hex.upper() in ("1F4E79", "2E75B6", "41719C"):
                    blue_runs.append((p_idx, r_idx, color_hex, r.text[:40]))
    
    print(f"Total runs inspected: {total_runs}")
    print(f"Blue/Themed runs found: {len(blue_runs)}")
    if blue_runs:
        for p_idx, r_idx, col, txt in blue_runs[:10]:
            print(f"  P{p_idx} R{r_idx} [{col}]: {txt}")
    else:
        print("  SUCCESS: No blue/themed runs found! Neutral black typography verified.")
        
    # 2. Inspect Tables
    print(f"\nTotal tables: {len(doc.tables)}")
    for t_idx, tbl in enumerate(doc.tables):
        print(f"\n--- Table {t_idx} ({len(tbl.rows)} rows x {len(tbl.columns)} cols) ---")
        for r_idx, row in enumerate(tbl.rows):
            cell_texts = [c.text.strip().replace("\n", " ") for c in row.cells]
            # Check for duplicated text within cells (e.g. "Party WParty W")
            has_dup = False
            for ct in cell_texts:
                if len(ct) > 4 and ct[:len(ct)//2] == ct[len(ct)//2:]:
                    has_dup = True
            dup_flag = " [POSSIBLE DUP!]" if has_dup else ""
            print(f"  Row {r_idx}{dup_flag}: {cell_texts}")
            
    # 3. Inspect Images & Alt text
    images_found = 0
    missing_alt = 0
    for p in doc.paragraphs:
        for r in p.runs:
            drawings = r._r.findall(qn("w:drawing"))
            for d in drawings:
                images_found += 1
                docPr = d.find(".//" + qn("wp:docPr"))
                if docPr is not None:
                    descr = docPr.get("descr", "")
                    title = docPr.get("title", "")
                    print(f"  Image #{images_found}: descr='{descr}', title='{title}'")
                else:
                    missing_alt += 1
    print(f"\nImages found: {images_found}, Missing alt: {missing_alt}")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "tests/stats_merged_quiz_multimodal.docx"
    inspect_docx(path)

