import argparse
import os
import re
from dataclasses import dataclass
from typing import Any

import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.pagesizes import landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib import colors


SLIDE_RE = re.compile(r"^##\s*Slajd\s*(\d+)\s*\/\s*(\d+).*?[-—]\s*(.+?)\s*$|^##\s*Slajd\s*(\d+)\s*\/\s*(\d+)\s*.*?-\s*(.+?)\s*$")


def _register_fonts() -> dict[str, str]:
    fonts = {
        "regular": "Helvetica",
        "bold": "Helvetica-Bold",
    }
    arial = r"C:\Windows\Fonts\arial.ttf"
    arial_bold = r"C:\Windows\Fonts\arialbd.ttf"
    if os.path.exists(arial):
        pdfmetrics.registerFont(TTFont("ArialTT", arial))
        fonts["regular"] = "ArialTT"
    if os.path.exists(arial_bold):
        pdfmetrics.registerFont(TTFont("ArialBoldTT", arial_bold))
        fonts["bold"] = "ArialBoldTT"
    return fonts


def _ascii_safe(text: str) -> str:
    # Keep it conservative; we will mainly avoid typographic dashes/quotes.
    # ReportLab sometimes renders "weird" chars when the PDF has odd encodings.
    mapping = {
        "–": "-",
        "—": "-",
        "’": "'",
        "„": '"',
        "”": '"',
        "…": "...",
        "\u00a0": " ",
        "\u200b": "",
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    return text


def _parse_deck(md_text: str) -> list[dict[str, Any]]:
    slides: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    lines = md_text.splitlines()
    for line in lines:
        m = SLIDE_RE.match(line.strip())
        if m:
            # Support both dash and em-dash variations.
            if m.group(1) is not None:
                idx = int(m.group(1))
                total = int(m.group(2))
                title = m.group(3).strip()
            else:
                idx = int(m.group(4))
                total = int(m.group(5))
                title = m.group(6).strip()
            current = {"idx": idx, "total": total, "title": title, "bullets": [], "tables": [], "free_text": []}
            slides.append(current)
            continue

        if current is None:
            continue

        if not line.strip():
            continue

        if line.lstrip().startswith("- "):
            bullet = line.lstrip()[2:].strip()
            current["bullets"].append(_ascii_safe(bullet.replace("**", "")))
            continue

        if line.strip().startswith("|"):
            # Collect table row lines.
            current["tables"].append(line.strip())
            continue

        # Narrative / QR placeholder etc.
        cleaned = _ascii_safe(line.replace("**", "")).strip()
        if cleaned:
            current["free_text"].append(cleaned)

    # Remove any accidental empty slides.
    return [s for s in slides if s.get("idx")]


def _parse_table(table_lines: list[str]) -> dict[str, Any]:
    # Markdown table: header, separator, rows.
    lines = [ln.strip() for ln in table_lines if ln.strip()]
    if len(lines) < 2:
        return {}

    def split_row(ln: str) -> list[str]:
        ln2 = ln.strip()
        if ln2.startswith("|"):
            ln2 = ln2[1:]
        if ln2.endswith("|"):
            ln2 = ln2[:-1]
        return [p.strip() for p in ln2.split("|")]

    header = split_row(lines[0])
    sep = split_row(lines[1])

    aligns: list[str] = []
    for cell in sep:
        cell2 = cell.replace("-", "")
        if cell.startswith(":") and cell.endswith(":"):
            aligns.append("center")
        elif cell.endswith(":"):
            aligns.append("right")
        elif cell.startswith(":"):
            aligns.append("left")
        else:
            aligns.append("center")

    rows = [split_row(ln) for ln in lines[2:]]
    return {"header": header, "aligns": aligns, "rows": rows}


def _wrap(text: str, font: str, font_size: float, max_width: float) -> list[str]:
    text = _ascii_safe(text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return [""]
    words = text.split(" ")
    out: list[str] = []
    cur = ""
    for w in words:
        cand = w if not cur else cur + " " + w
        if pdfmetrics.stringWidth(cand, font, font_size) <= max_width:
            cur = cand
        else:
            if cur:
                out.append(cur)
            # If one word is too wide, hard-split.
            if pdfmetrics.stringWidth(w, font, font_size) <= max_width:
                cur = w
            else:
                chunk = ""
                for ch in w:
                    cand2 = chunk + ch
                    if pdfmetrics.stringWidth(cand2, font, font_size) <= max_width:
                        chunk = cand2
                    else:
                        if chunk:
                            out.append(chunk)
                        chunk = ch
                cur = chunk
    if cur:
        out.append(cur)
    return out


def _rl_rect(bbox: tuple[float, float, float, float], page_h: float) -> tuple[float, float, float, float]:
    # bbox: (x0, y0, x1, y1) in PyMuPDF coords with origin top-left
    x0, y0, x1, y1 = bbox
    y_bottom = page_h - y1
    width = x1 - x0
    height = y1 - y0
    return x0, y_bottom, width, height


def _color_int_to_reportlab(c: int) -> colors.Color:
    r = (c >> 16) & 0xFF
    g = (c >> 8) & 0xFF
    b = c & 0xFF
    return colors.Color(r / 255.0, g / 255.0, b / 255.0)


def _extract_spans(page: fitz.Page) -> list[dict[str, Any]]:
    d = page.get_text("dict")
    spans: list[dict[str, Any]] = []
    for block in d.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for sp in line.get("spans", []):
                text = sp.get("text", "")
                if not text or not str(text).strip():
                    continue
                spans.append(
                    {
                        "text": str(text),
                        "size": float(sp.get("size", 0.0)),
                        "color": sp.get("color", 0),
                        "bbox": tuple(sp.get("bbox", (0, 0, 0, 0))),
                    }
                )
    return spans


def _find_title_bbox(spans: list[dict[str, Any]]) -> tuple[float, float, float, float] | None:
    if not spans:
        return None
    max_size = max(s["size"] for s in spans)
    title_spans = [s for s in spans if s["size"] >= max_size * 0.98]
    x0 = min(s["bbox"][0] for s in title_spans)
    y0 = min(s["bbox"][1] for s in title_spans)
    x1 = max(s["bbox"][2] for s in title_spans)
    y1 = max(s["bbox"][3] for s in title_spans)
    return (x0, y0, x1, y1)


def _find_footer_bbox(spans: list[dict[str, Any]]) -> tuple[float, float, float, float] | None:
    # Matches "— 1 of 27 —" like fragments.
    for s in spans:
        if re.search(r"\bof\s+\d+\b", s["text"], flags=re.IGNORECASE):
            # If multiple spans contain the footer, we'll union them.
            break
    footer_spans = [s for s in spans if re.search(r"\bof\s+\d+\b", s["text"], flags=re.IGNORECASE)]
    if not footer_spans:
        return None
    x0 = min(s["bbox"][0] for s in footer_spans)
    y0 = min(s["bbox"][1] for s in footer_spans)
    x1 = max(s["bbox"][2] for s in footer_spans)
    y1 = max(s["bbox"][3] for s in footer_spans)
    return (x0, y0, x1, y1)


def generate_from_template(template_pdf: str, slides_md: str, out_pdf: str, slides_count: int = 12) -> None:
    fonts = _register_fonts()

    with open(slides_md, "r", encoding="utf-8") as f:
        md = f.read()
    slides = _parse_deck(md)
    slides = [s for s in slides if s["idx"] <= slides_count]
    slides.sort(key=lambda x: x["idx"])

    if len(slides) < slides_count:
        raise RuntimeError(f"Za malo slajdów w {slides_md} (mam {len(slides)}, oczekuje {slides_count}).")

    doc = fitz.open(template_pdf)
    if doc.page_count < slides_count:
        raise RuntimeError(f"Template ma tylko {doc.page_count} stron, a potrzebujesz {slides_count}.")

    page0 = doc.load_page(0)
    page_rect = page0.rect  # in points
    page_w, page_h = float(page_rect.width), float(page_rect.height)

    # Render background pages to cache.
    cache_dir = os.path.join(os.path.dirname(out_pdf), "_template_cache")
    os.makedirs(cache_dir, exist_ok=True)

    dpi = 120
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)

    c = canvas.Canvas(out_pdf, pagesize=(page_w, page_h))

    for i in range(slides_count):
        tpl_page_idx = i  # use first N pages as backgrounds
        page = doc.load_page(tpl_page_idx)

        png_path = os.path.join(cache_dir, f"tpl_page_{tpl_page_idx+1}.png")
        if not os.path.exists(png_path):
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(png_path)

        # Background image.
        bg = Image.open(png_path).convert("RGB")
        img_reader = ImageReader(png_path)
        c.drawImage(img_reader, 0, 0, width=page_w, height=page_h, mask="auto")

        spans = _extract_spans(page)
        title_bbox = _find_title_bbox(spans)
        footer_bbox = _find_footer_bbox(spans)

        # Cover all text blocks with "sampled" background color.
        # This keeps template shapes/colors intact around text.
        for sp in spans:
            bbox = sp["bbox"]
            x0, y0, w, h = _rl_rect(bbox, page_h)
            pad = 1.5
            cx = int(min(max((x0 + w / 2) * bg.size[0] / page_w, 0), bg.size[0] - 1))
            cy = int(min(max((page_h - (y0 + h / 2)) * bg.size[1] / page_h, 0), bg.size[1] - 1))
            r, g, b = bg.getpixel((cx, cy))
            c.setFillColor(colors.Color(r / 255.0, g / 255.0, b / 255.0))
            c.setStrokeColor(colors.Color(r / 255.0, g / 255.0, b / 255.0))
            c.setLineWidth(0)
            c.rect(x0 - pad, y0 - pad, w + 2 * pad, h + 2 * pad, stroke=0, fill=1)

        # Determine drawing areas from template.
        body_candidates = []
        for sp in spans:
            bbox = sp["bbox"]
            if title_bbox and sp["bbox"] == title_bbox:
                continue
            if title_bbox:
                tb = title_bbox
                # exclude spans that are fully inside title bbox
                if bbox[0] >= tb[0] and bbox[1] >= tb[1] and bbox[2] <= tb[2] and bbox[3] <= tb[3]:
                    continue
            if footer_bbox:
                fb = footer_bbox
                if bbox[0] >= fb[0] and bbox[1] >= fb[1] and bbox[2] <= fb[2] and bbox[3] <= fb[3]:
                    continue
            body_candidates.append(sp)

        if body_candidates:
            # Union body candidate bboxes.
            x0 = min(s["bbox"][0] for s in body_candidates)
            y0 = min(s["bbox"][1] for s in body_candidates)
            x1 = max(s["bbox"][2] for s in body_candidates)
            y1 = max(s["bbox"][3] for s in body_candidates)
            body_bbox = (x0, y0, x1, y1)
        else:
            # Fallback.
            body_bbox = (80, 120, page_w - 80, page_h - 110)

        s = slides[i]
        title = _ascii_safe(s["title"])
        bullets = s["bullets"]
        free_text = s.get("free_text", [])
        tables = s.get("tables", [])

        # Draw footer slide counter (if footer bbox exists).
        if footer_bbox:
            fx, fy, fw, fh = _rl_rect(footer_bbox, page_h)
            c.setFillColor(colors.HexColor("#555555"))
            c.setFont(fonts["bold"], 11)
            footer_text = f"-- {s['idx']} of {slides_count} --"
            # Centered footer.
            c.drawCentredString(fx + fw / 2, fy + fh / 2 - 4, footer_text)

        # Draw title.
        if title_bbox:
            tx, ty, tw, th = _rl_rect(title_bbox, page_h)
            # Choose font size based on title box height.
            font_size = max(14, min(34, th * 0.38))
            c.setFillColor(colors.HexColor("#0B3D91"))
            c.setFont(fonts["bold"], font_size)
            wrapped = _wrap(title, fonts["bold"], font_size, tw - 20)
            cur_y = ty + th - font_size - 2
            for ln in wrapped[:3]:
                c.drawString(tx + 10, cur_y, ln)
                cur_y -= font_size * 1.15
        else:
            c.setFillColor(colors.HexColor("#0B3D91"))
            c.setFont(fonts["bold"], 28)
            c.drawString(60, page_h - 110, title)

        # Draw content (body box).
        bx, by, bw, bh = _rl_rect(body_bbox, page_h)
        padding_x = 16
        padding_y = 10

        # Tables on slides like 2/9/12.
        if tables:
            t = _parse_table(tables)
            if t:
                cols = len(t["header"])
                rows = t["rows"]
                header = t["header"]
                aligns = t["aligns"]

                # Simplified table drawing: grid + header fill.
                table_x = bx + padding_x
                table_y_top = by + bh - padding_y
                table_w = bw - padding_x * 2
                col_w = table_w / cols

                header_h = min(42, bh * 0.13)
                row_h = min(26, bh * 0.08)
                header_font = 12.2
                body_font = 11.2

                c.setStrokeColor(colors.HexColor("#C7D2E1"))
                c.setLineWidth(0.6)
                c.setFillColor(colors.white)
                c.setFont(fonts["bold"], header_font)
                # Header cells.
                for ci in range(cols):
                    x = table_x + ci * col_w
                    c.setFillColor(colors.HexColor("#E8F0FF"))
                    c.rect(x, table_y_top - header_h, col_w, header_h, stroke=1, fill=1)
                    c.setFillColor(colors.HexColor("#0B3D91"))
                    txt = _ascii_safe(header[ci] if ci < len(header) else "")
                    # center text.
                    tx0, ty0, tw, th2 = x, table_y_top - header_h, col_w, header_h
                    lines = _wrap(txt, fonts["bold"], header_font, col_w - 10)
                    yy = ty0 + header_h / 2 - header_font / 2
                    if lines:
                        c.drawCentredString(tx0 + col_w / 2, yy, lines[0])
                    c.setFillColor(colors.HexColor("#0B3D91"))

                # Data rows.
                c.setFillColor(colors.white)
                c.setFont(fonts["regular"], body_font)
                y = table_y_top - header_h
                for ri, row in enumerate(rows):
                    y_next = y - row_h
                    c.setFillColor(colors.white if ri % 2 == 0 else colors.HexColor("#FCFDFF"))
                    for ci in range(cols):
                        x = table_x + ci * col_w
                        c.rect(x, y_next, col_w, row_h, stroke=1, fill=1)

                        cell = _ascii_safe(row[ci] if ci < len(row) else "")
                        lines = _wrap(cell, fonts["regular"], body_font, col_w - 8)
                        if not lines:
                            continue
                        # Use first line for compactness.
                        yy = y_next + row_h / 2 - body_font / 2
                        if aligns[ci] == "right":
                            c.drawRightString(x + col_w - 5, yy, lines[0])
                        elif aligns[ci] == "left":
                            c.drawString(x + 5, yy, lines[0])
                        else:
                            c.drawCentredString(x + col_w / 2, yy, lines[0])
                    y = y_next

        else:
            # If there is free_text, render it as first block.
            y = by + bh - padding_y - 12

            if free_text:
                lead = " ".join([_ascii_safe(t) for t in free_text]).strip()
                lead_font = 16
                max_w = bw - padding_x * 2
                lead_lines = _wrap(lead, fonts["regular"], lead_font, max_w)
                lead_lines = lead_lines[:3]
                c.setFillColor(colors.black)
                c.setFont(fonts["regular"], lead_font)
                for ln in lead_lines:
                    c.drawString(bx + padding_x, y, ln)
                    y -= lead_font * 1.35
                y -= 8

            # QR placeholder: if any bullet contains "QR", we reserve a right-side box.
            qr_idx = None
            for bi, btxt in enumerate(bullets):
                if "QR" in btxt.upper():
                    qr_idx = bi
                    break
            qr_bullet = None
            if qr_idx is not None:
                qr_bullet = bullets.pop(qr_idx)

            # Layout bullets.
            if bullets:
                if qr_bullet:
                    # Left bullets + right QR box.
                    qr_size = min(110, bh * 0.25)
                    qr_x = bx + bw - padding_x - qr_size
                    qr_y = y - qr_size
                    c.setStrokeColor(colors.HexColor("#D8E1F0"))
                    c.setFillColor(colors.white)
                    c.roundRect(qr_x, qr_y, qr_size, qr_size, 8, stroke=1, fill=1)
                    c.setFillColor(colors.HexColor("#0B3D91"))
                    # pseudo-QR dots
                    dot_step = max(6, int(qr_size / 16))
                    for yy in range(int(qr_y + 10), int(qr_y + qr_size - 10), dot_step):
                        for xx in range(int(qr_x + 10), int(qr_x + qr_size - 10), dot_step):
                            if (xx + yy) % (dot_step * 2) == 0:
                                c.circle(xx, yy, 1.8, stroke=0, fill=1)
                    c.setFillColor(colors.HexColor("#555555"))
                    c.setFont(fonts["bold"], 12)
                    c.drawCentredString(qr_x + qr_size / 2, qr_y - 18, "KOD QR")

                    # left width excludes qr box + gap.
                    left_w = (qr_x - (bx + padding_x)) - 20
                    font_size = 18
                    line_gap = font_size * 1.6
                    bullet_x = bx + padding_x
                    bullet_y = y
                    dot_r = 4.5
                    for btxt in bullets:
                        lines = _wrap(_ascii_safe(btxt), fonts["regular"], font_size, left_w - 20)
                        c.setFillColor(colors.HexColor("#FF7A00"))
                        c.circle(bullet_x + 5, bullet_y - 8, dot_r, stroke=0, fill=1)
                        c.setFillColor(colors.black)
                        for li, ln in enumerate(lines[:4]):
                            c.setFont(fonts["regular"], font_size)
                            c.drawString(bullet_x + 22, bullet_y - li * line_gap, ln)
                        # advance y: reserve per bullet
                        bullet_y -= (min(4, len(lines)) * line_gap) + 15

                elif len(bullets) <= 3:
                    # Single column for few bullets
                    font_size = 22
                    line_gap = font_size * 1.6
                    bullet_x = bx + padding_x + 20
                    bullet_y = y
                    dot_r = 5.5
                    for btxt in bullets:
                        lines = _wrap(_ascii_safe(btxt), fonts["regular"], font_size, bw - padding_x * 2 - 40)
                        c.setFillColor(colors.HexColor("#FF7A00"))
                        c.circle(bullet_x, bullet_y - 10, dot_r, stroke=0, fill=1)
                        c.setFillColor(colors.black)
                        for li, ln in enumerate(lines[:3]):
                            c.setFont(fonts["regular"], font_size)
                            c.drawString(bullet_x + 25, bullet_y - li * line_gap, ln)
                        bullet_y -= (min(3, len(lines)) * line_gap) + 25

                else:
                    # 2 columns bullets.
                    font_size = 16
                    line_gap = font_size * 1.55
                    col_gap = 35
                    inner_pad = 10
                    content_w = bw - inner_pad * 2
                    col_w = (content_w - col_gap) / 2
                    left_x = bx + inner_pad
                    right_x = left_x + col_w + col_gap
                    left = bullets[0::2]
                    right = bullets[1::2]
                    bottom_limit = by + 30
                    for col, x0 in ((left, left_x), (right, right_x)):
                        y_col = y
                        for btxt in col:
                            if y_col < bottom_limit:
                                break
                            lines = _wrap(_ascii_safe(btxt), fonts["regular"], font_size, col_w - 25)
                            c.setFillColor(colors.HexColor("#FF7A00"))
                            c.circle(x0 + 5, y_col - 8, 4.5, stroke=0, fill=1)
                            c.setFillColor(colors.black)
                            for li, ln in enumerate(lines[:5]):
                                c.setFont(fonts["regular"], font_size)
                                c.drawString(x0 + 22, y_col - li * line_gap, ln)
                            y_col -= (min(5, len(lines)) * line_gap) + 18


        c.showPage()

    c.save()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True, help="Path to template PDF")
    ap.add_argument("--slides", required=True, help="Path to slides markdown (e.g. Prezentacja2.md)")
    ap.add_argument("--out", required=True, help="Output PDF path")
    ap.add_argument("--slides-count", type=int, default=12)
    args = ap.parse_args()

    generate_from_template(args.template, args.slides, args.out, slides_count=args.slides_count)


if __name__ == "__main__":
    main()

