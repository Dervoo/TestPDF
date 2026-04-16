import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm


def _register_fonts() -> dict:
    """
    Uses Windows Arial TTFs when available so Polish diacritics render correctly.
    """
    fonts = {
        "regular": "Helvetica",
        "bold": "Helvetica-Bold",
        "mono": "Courier",
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


SLIDE_RE = re.compile(r"^##\s*Slajd\s*(\d+)/(\d+)\s*[—-]\s*(.+?)\s*$")


def _parse_presentation(markdown_text: str) -> list[dict]:
    slides = []
    current = None

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip("\n")
        m = SLIDE_RE.match(line)
        if m:
            idx = int(m.group(1))
            total = int(m.group(2))
            title = m.group(3).strip()
            current = {
                "idx": idx,
                "total": total,
                "title": title,
                "bullets": [],
                "tables": [],
                "free_text": [],
            }
            slides.append(current)
            continue

        if current is None:
            continue

        if not line.strip():
            continue

        if line.lstrip().startswith("- "):
            # Strip markdown bullet prefix.
            bullet = line.lstrip()[2:].strip()
            bullet = bullet.replace("**", "")
            current["bullets"].append(bullet)
            continue

        if line.strip().startswith("|") and "|" in line.strip()[1:]:
            # Collect table lines as-is (we'll print them with monospace).
            current["tables"].append(line.strip())
            continue

        # Narrative line (e.g., slide 8/9/table intro).
        cleaned = line.replace("**", "")
        current["free_text"].append(cleaned)

    # Fallback: remove any empty-only slides (shouldn't happen).
    return [s for s in slides if s["idx"]]


def _strip_md_inline(text: str) -> str:
    # Minimal: remove emphasis markers, keep everything else.
    return text.replace("**", "").replace("`", "")


def _wrap_text(text: str, font: str, font_size: int, max_width: float) -> list[str]:
    # Greedy wrap on spaces.
    words = text.split(" ")
    lines = []
    current = ""
    for w in words:
        if not current:
            candidate = w
        else:
            candidate = current + " " + w
        width = pdfmetrics.stringWidth(candidate, font, font_size)
        if width <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            # If a single word is too long, hard-split.
            if pdfmetrics.stringWidth(w, font, font_size) <= max_width:
                current = w
            else:
                # hard split by characters
                chunk = ""
                for ch in w:
                    cand2 = chunk + ch
                    if pdfmetrics.stringWidth(cand2, font, font_size) <= max_width:
                        chunk = cand2
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = ch
                current = chunk
    if current:
        lines.append(current)
    return lines


def _parse_table(table_lines: list[str]) -> dict:
    """
    Expects markdown table rows like:
      | A | B |
      |---|---:|
      | 1 | 2 |
    """
    # Remove surrounding whitespace; ignore empty.
    lines = [ln.strip() for ln in table_lines if ln.strip()]
    if len(lines) < 2:
        return {}

    def split_row(ln: str) -> list[str]:
        # Remove leading/trailing | then split.
        ln2 = ln.strip()
        if ln2.startswith("|"):
            ln2 = ln2[1:]
        if ln2.endswith("|"):
            ln2 = ln2[:-1]
        parts = [p.strip() for p in ln2.split("|")]
        return parts

    header = split_row(lines[0])
    sep = split_row(lines[1])

    # Alignments: '---:' => right, ':---' => left, '---' => center.
    aligns = []
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


def _draw_wrapped_lines(
    c: canvas.Canvas,
    lines: list[str],
    font: str,
    font_size: float,
    x: float,
    y_top: float,
    line_gap: float,
    fill: colors.Color,
) -> float:
    c.setFont(font, font_size)
    c.setFillColor(fill)
    y = y_top
    for ln in lines:
        c.drawString(x, y, ln)
        y -= line_gap
    return y


def build_pdf(md_path: str, out_pdf_path: str) -> None:
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()

    slides = _parse_presentation(md)
    if not slides:
        raise RuntimeError("Nie znaleziono slajdów w presentation.md")

    fonts = _register_fonts()

    page_w, page_h = landscape(A4)
    c = canvas.Canvas(out_pdf_path, pagesize=(page_w, page_h))

    header_h = 92
    margin_x = 34
    margin_bottom = 48
    max_content_width = page_w - 2 * margin_x

    header_bg = colors.HexColor("#0B3D91")
    header_text = colors.white
    footer_text = colors.HexColor("#555555")
    accent = colors.HexColor("#FF7A00")
    box_bg = colors.HexColor("#F3F6FB")
    box_border = colors.HexColor("#D8E1F0")
    grid = colors.HexColor("#E2E6EE")

    for s in slides:
        c.setFillColor(header_bg)
        c.rect(0, page_h - header_h, page_w, header_h, stroke=0, fill=1)

        # Full-width card background for the slide content area.
        card_x = margin_x
        card_y_bottom = margin_bottom
        card_y_top = page_h - header_h - 12
        card_h = card_y_top - card_y_bottom
        c.setFillColor(box_bg)
        c.setStrokeColor(box_border)
        c.setLineWidth(1)
        c.roundRect(card_x, card_y_bottom, max_content_width, card_h, 14, stroke=1, fill=1)

        # Subtle side accent (red/yellow-ish) to match the sample theme.
        accent_y = card_y_bottom
        accent_h = card_h
        c.setFillColor(colors.HexColor("#E53935"))
        c.roundRect(card_x, accent_y, 10, accent_h, 10, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#FBC02D"))
        c.roundRect(card_x + 8, accent_y + 26, 6, min(140, accent_h - 26), 6, stroke=0, fill=1)

        content_top_y = card_y_top - 10

        # Title + slide badge.
        c.setFillColor(header_text)
        c.setFont(fonts["bold"], 12)
        slide_badge_text = f"Slajd {s['idx']}/{s['total']}"
        badge_w = 110
        badge_h = 28
        badge_x = page_w - margin_x - badge_w
        badge_y = page_h - header_h + (header_h - badge_h) / 2
        c.setFillColor(colors.white)
        c.roundRect(badge_x, badge_y, badge_w, badge_h, 8, stroke=0, fill=1)
        c.setFillColor(header_bg)
        c.setFont(fonts["bold"], 12)
        c.drawCentredString(badge_x + badge_w / 2, badge_y + 8, slide_badge_text)

        title_font_size = 18
        title = _strip_md_inline(s["title"])
        title_lines = _wrap_text(title, fonts["bold"], title_font_size, max_content_width - badge_w - 24)
        if len(title_lines) >= 4:
            title_font_size = 16
            title_lines = _wrap_text(title, fonts["bold"], title_font_size, max_content_width - badge_w - 24)

        # Title inside the card (not in the header strip).
        y_title = card_y_top - 30
        c.setFillColor(header_bg)
        c.setFont(fonts["bold"], title_font_size)
        for tl in title_lines[:3]:
            c.drawString(margin_x, y_title, tl)
            y_title -= 22

        # Optional "lead" box (narrative / assumptions).
        y = content_top_y
        free = [_strip_md_inline(t) for t in s["free_text"] if t.strip()]
        lead_paragraph = " ".join(free).strip()
        has_lead = bool(lead_paragraph)
        if has_lead:
            lead_font = 12.8
            lead_line_gap = 15
            # Wrap lead as one paragraph.
            wrapped_lead = _wrap_text(lead_paragraph, fonts["regular"], lead_font, max_content_width)
            max_lead_lines = 5 if not s["tables"] else 4
            shown = wrapped_lead[:max_lead_lines]
            lead_box_h = min(130, 22 + len(shown) * lead_line_gap)

            c.setFillColor(box_bg)
            c.setStrokeColor(box_border)
            c.setLineWidth(1)
            c.roundRect(
                margin_x,
                y - lead_box_h + 8,
                max_content_width,
                lead_box_h,
                10,
                stroke=1,
                fill=1,
            )
            # Lead label
            c.setFillColor(header_bg)
            c.setFont(fonts["bold"], 11.2)
            c.drawString(margin_x + 12, y - 18, "Uwaga / kontekst:")

            # Lead text
            c.setFillColor(colors.black)
            start_y = y - 32
            _draw_wrapped_lines(
                c,
                shown,
                fonts["regular"],
                lead_font,
                margin_x + 12,
                start_y,
                lead_line_gap,
                colors.black,
            )
            y = y - lead_box_h - 10

        # Optional table block (slide 9).
        if s["tables"]:
            parsed = _parse_table(s["tables"])
            if parsed:
                header = parsed["header"]
                aligns = parsed["aligns"]
                rows = parsed["rows"]
                cols = len(header)
                col_w = max_content_width / cols
                table_x = margin_x
                table_y_top = y
                table_font = 10.3
                header_font = 10.5
                row_gap = 1
                pad_x = 6
                pad_y = 4

                # Render header row
                row_h = 18
                c.setFillColor(header_bg)
                c.setStrokeColor(header_bg)
                c.setLineWidth(0.3)
                for i in range(cols):
                    c.rect(table_x + i * col_w, table_y_top - row_h, col_w, row_h, stroke=0, fill=1)
                    c.setFillColor(colors.white)
                    c.setFont(fonts["bold"], header_font)
                    cell_text = _strip_md_inline(header[i]) if i < len(header) else ""
                    wrapped = _wrap_text(cell_text, fonts["bold"], header_font, col_w - 2 * pad_x)
                    # One line expected; fallback to first.
                    txt = wrapped[0] if wrapped else ""
                    if aligns[i] == "right":
                        c.drawRightString(table_x + (i + 1) * col_w - pad_x, table_y_top - 12, txt)
                    elif aligns[i] == "left":
                        c.drawString(table_x + i * col_w + pad_x, table_y_top - 12, txt)
                    else:
                        c.drawCentredString(table_x + (i + 0.5) * col_w, table_y_top - 12, txt)

                y = table_y_top - row_h - 8

                # Render data rows with dynamic height.
                c.setLineWidth(0.4)
                for row_idx, r in enumerate(rows):
                    # Compute wrapped lines per cell.
                    cell_wrapped = []
                    max_lines = 1
                    for i in range(cols):
                        cell = r[i] if i < len(r) else ""
                        cell = _strip_md_inline(cell)
                        wrapped = _wrap_text(cell, fonts["regular"], table_font, col_w - 2 * pad_x)
                        wrapped = wrapped[:3]  # keep rows compact
                        cell_wrapped.append(wrapped)
                        max_lines = max(max_lines, len(wrapped))
                    row_h = 12 + max_lines * 12

                    # Cells background + borders
                    # Subtle striping
                    c.setFillColor(colors.white if (row_idx % 2 == 0) else colors.HexColor("#FCFDFF"))
                    for i in range(cols):
                        c.setStrokeColor(grid)
                        c.rect(table_x + i * col_w, y - row_h, col_w, row_h, stroke=1, fill=1)

                        # Draw text
                        c.setFillColor(colors.black)
                        x_cell_left = table_x + i * col_w + pad_x
                        x_cell_right = table_x + (i + 1) * col_w - pad_x
                        y_text = y - 16
                        lines = cell_wrapped[i]
                        for li, txt in enumerate(lines):
                            yy = y_text - li * 12
                            if aligns[i] == "right":
                                c.drawRightString(x_cell_right, yy, txt)
                            elif aligns[i] == "left":
                                c.drawString(x_cell_left, yy, txt)
                            else:
                                c.drawCentredString((x_cell_left + x_cell_right) / 2, yy, txt)

                    y = y - row_h - 8

        # Bullets section
        c.setFillColor(colors.black)
        bullets = list(s["bullets"])
        n = len(bullets)

        # Detect QR placeholder bullet on demo slide.
        qr_idx = None
        for i, b in enumerate(bullets):
            if "QR" in b.upper():
                qr_idx = i
                break
        qr_bullet = None
        if qr_idx is not None:
            qr_bullet = bullets.pop(qr_idx)
            n = len(bullets)

        if n:
            is_table_slide = bool(s["tables"])

            # If few bullets, show them full-page (bigger font, 1 column).
            if n <= 3 and not qr_bullet:
                bullet_font = 17.2
                line_gap = 22
                inner_pad = 18
                col_gap = 0
                content_w = max_content_width - inner_pad * 2
                col_w = content_w
                col_x0 = margin_x + inner_pad
                col_x1 = col_x0

                bottom_limit = margin_bottom + 26

                y_col = y
                x_dot = col_x0 - 2
                x_text = col_x0 + 10
                for b in bullets:
                    if y_col < bottom_limit:
                        break
                    text = _strip_md_inline(b)
                    wrapped = _wrap_text(text, fonts["regular"], int(bullet_font), col_w - 6)
                    c.setFillColor(accent)
                    c.circle(x_dot, y_col - 6, 4.8, stroke=0, fill=1)
                    c.setFillColor(colors.black)
                    y_text = y_col
                    for li, ln in enumerate(wrapped):
                        c.setFont(fonts["regular"], int(bullet_font))
                        c.drawString(x_text, y_text - li * line_gap, ln)
                    y_col = y_col - (len(wrapped) * line_gap) - 12

            else:
                # Default: 2 columns, but when QR exists reserve right side.
                bullet_font = 14.8 if not is_table_slide else 13.4
                line_gap = 19 if not is_table_slide else 17

                inner_pad = 14
                col_gap = 26
                content_w = max_content_width - inner_pad * 2
                col_w = (content_w - col_gap) / 2

                col_x0 = margin_x + inner_pad
                col_x1 = margin_x + inner_pad + col_w + col_gap

                bottom_limit = margin_bottom + 26

                def draw_bullet_column(col_bullets: list[str], col_x: float) -> None:
                    y_col = y
                    x_dot = col_x - 2
                    x_text = col_x + 10

                    for b in col_bullets:
                        if y_col < bottom_limit:
                            return

                        text = _strip_md_inline(b)
                        wrapped = _wrap_text(text, fonts["regular"], int(bullet_font), col_w - 6)

                        c.setFillColor(accent)
                        c.circle(x_dot, y_col - 6, 4.6, stroke=0, fill=1)
                        c.setFillColor(colors.black)

                        y_text = y_col
                        for li, ln in enumerate(wrapped):
                            c.setFont(fonts["regular"], int(bullet_font))
                            c.drawString(x_text, y_text - li * line_gap, ln)

                        y_col = y_col - (len(wrapped) * line_gap) - 10

                if qr_bullet:
                    # QR box on the right, bullets only on the left.
                    qr_size = 44 * mm
                    qr_pad = 8
                    qr_x = col_x1 + col_w - qr_size
                    qr_y_top = card_y_top - 210
                    qr_y = qr_y_top - qr_size
                    c.setFillColor(colors.HexColor("#FFFFFF"))
                    c.setStrokeColor(box_border)
                    c.setLineWidth(1)
                    c.roundRect(qr_x, qr_y, qr_size, qr_size, 12, stroke=1, fill=1)
                    # simple pseudo-QR: dotted pattern
                    c.setFillColor(colors.HexColor("#0B3D91"))
                    step = max(5, int(qr_size / 14))
                    for yy in range(int(qr_y) + 10, int(qr_y + qr_size) - 10, step):
                        for xx in range(int(qr_x) + 10, int(qr_x + qr_size) - 10, step):
                            if (xx + yy) % (step * 2) == 0:
                                c.circle(xx, yy, 1.2, stroke=0, fill=1)

                    c.setFillColor(colors.HexColor("#555555"))
                    c.setFont(fonts["bold"], 10.5)
                    c.drawCentredString(col_x1 + col_w / 2, qr_y - 14, "Skanuj QR")
                    left_count = n
                    left_col = bullets[:left_count]
                    draw_bullet_column(left_col, col_x0)
                else:
                    left_count = (n + 1) // 2
                    left_col = bullets[:left_count]
                    right_col = bullets[left_count:]
                    draw_bullet_column(left_col, col_x0)
                    if right_col:
                        draw_bullet_column(right_col, col_x1)

        # Footer
        c.setFont(fonts["regular"], 10)
        c.setFillColor(footer_text)
        c.drawRightString(page_w - margin_x, 30, f"Slajd {s['idx']}/{s['total']}")
        c.drawString(margin_x, 30, "CCIG Employee Churn Predictor")

        c.showPage()

    c.save()


if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.abspath(__file__))
    args = sys.argv[1:]
    md_path = os.path.join(repo_root, "presentation.md")
    out_pdf_path = os.path.join(repo_root, "presentation.pdf")
    if len(args) >= 1:
        md_path = args[0]
    if len(args) >= 2:
        out_pdf_path = args[1]
    build_pdf(md_path, out_pdf_path)
    print(f"Zapisano PDF: {out_pdf_path}")

