import os
from PIL import Image, ImageDraw, ImageFont
from asciifetch.config import load_config
from asciifetch.cv import resolve_crops, resolve_method
from asciifetch.fonts import font_path
from asciifetch.ascii_art import ascii_grid, build_ramp
from asciifetch.mask import pixel_box

def generate_banner(config_path="asciifetch.toml", out_dir="."):
    cfg = load_config(config_path)
    cfg.src = "C:/tmp/maheensayuru/headshot.jpg"
    resolve_crops(cfg)
    mask_method = resolve_method(cfg.mask_method)

    # Font setup
    font_r = font_path("regular", cfg.font_dir)
    font_b = font_path("bold", cfg.font_dir)
    font = ImageFont.truetype(font_r, cfg.font_size)
    fontb = ImageFont.truetype(font_b, cfg.font_size)
    asc = font.getmetrics()[0]
    ramp = build_ramp(font_r, font_b, cfg.cell_w, cfg.cell_h, cfg.font_size)

    # Generate ASCII grid from portrait using grabcut mask
    box = pixel_box(Image.open(cfg.src).size, cfg.portrait_crop)
    prows, idx, colors, m = ascii_grid(
        cfg.src, box, cfg.portrait_cols, len(ramp), cfg.cell_w, cfg.cell_h,
        mask_k=cfg.mask_k, mask_width=cfg.mask_width,
        method=mask_method, even_light=True
    )

    # Calculate info block dimensions
    info_rows_count = 2 + 1 + len(cfg.fields) + 1 + 2  # user + underline + blank + fields + blank + 2 swatches
    total_rows = max(prows, info_rows_count)
    info_start_row = (total_rows - info_rows_count) // 2

    # Columns
    portrait_cols = cfg.portrait_cols
    info_col = cfg.info_col

    max_field_len = 0
    for f in cfg.fields:
        if f:
            lab, val = f
            line_len = cfg.label_width + len(val)
            if line_len > max_field_len:
                max_field_len = line_len
    total_cols = max(info_col + max_field_len + 2, 163)

    # Clean frameless canvas geometry
    pad_x = 24
    pad_y = 20
    can_w = total_cols * cfg.cell_w + 2 * pad_x
    can_h = total_rows * cfg.cell_h + 2 * pad_y
    ox = pad_x
    oy = pad_y

    # Matrix / Dark Terminal Background
    bg_color = (13, 17, 23)  # #0d1117
    im = Image.new("RGB", (can_w, can_h), bg_color)
    draw = ImageDraw.Draw(im)

    cells = []  # (row, col, char, rgb_tuple, is_bold)

    def put_text(col, row, text, fill, bold=False):
        f = fontb if bold else font
        for k_idx, ch in enumerate(text):
            x = ox + (col + k_idx) * cfg.cell_w + cfg.cell_w / 2
            y = oy + row * cfg.cell_h + asc
            draw.text((x, y), ch, font=f, fill=fill, anchor="ms")
            cells.append((row, col + k_idx, ch, fill, bold))

    # Helper function for phosphor / matrix green gradient mapping
    def green_gradient(lum):
        # lum is 0.0 to 1.0
        # Smooth interpolation:
        # Low: dark forest green (25, 75, 40)
        # Mid: emerald matrix green (55, 195, 85)
        # High: vibrant phosphor green (95, 235, 130)
        # Peak: bright pale mint highlight (195, 255, 205)
        if lum < 0.35:
            t = lum / 0.35
            r = int(22 + (45 - 22) * t)
            g = int(70 + (160 - 70) * t)
            b = int(32 + (70 - 32) * t)
        elif lum < 0.75:
            t = (lum - 0.35) / 0.40
            r = int(45 + (95 - 45) * t)
            g = int(160 + (235 - 160) * t)
            b = int(70 + (130 - 70) * t)
        else:
            t = (lum - 0.75) / 0.25
            r = int(95 + (195 - 95) * t)
            g = int(235 + (255 - 235) * t)
            b = int(130 + (205 - 130) * t)
        return (min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b)))

    # Render Green Phosphor ASCII portrait
    for i, k in enumerate(idx):
        if m[i] < 40:
            continue
        ch, bold = ramp[k]
        if ch == " ":
            continue
        
        norm_k = k / (len(ramp) - 1)
        r_p, g_p, b_p = colors[i]
        photo_lum = (0.299 * r_p + 0.587 * g_p + 0.114 * b_p) / 255.0
        combined_lum = 0.45 * norm_k + 0.55 * photo_lum
        curved_lum = min(1.0, max(0.0, (combined_lum ** 0.85)))
        col_rgb = green_gradient(curved_lum)

        pcol = i % portrait_cols
        prow = i // portrait_cols
        
        x = ox + pcol * cfg.cell_w + cfg.cell_w / 2
        y = oy + prow * cfg.cell_h + asc
        draw.text((x, y), ch, font=(fontb if bold else font), fill=col_rgb, anchor="ms")
        cells.append((prow, pcol, ch, col_rgb, bold))

    # All-green terminal palette for text
    color_green_user = (86, 211, 100)      # #56d364 (vivid terminal green)
    color_green_line = (35, 134, 54)       # #238636 (matrix green divider)
    color_green_label = (126, 231, 135)    # #7ee787 (bright mint green for labels)
    color_green_value = (205, 248, 215)    # #cdf8d7 (light phosphor mint green for values)
    color_muted = (90, 160, 105)           # #5aa069 (dim matrix green for continuations)

    # Render Info Block on the right side
    r = info_start_row
    put_text(info_col, r, cfg.user, color_green_user, bold=True)
    put_text(info_col, r + 1, "─" * len(cfg.user), color_green_line)
    r += 3

    for f in cfg.fields:
        if f is None:
            r += 1
            continue
        lab, val = f
        if lab:
            put_text(info_col, r, lab, color_green_label, bold=True)
        put_text(info_col + cfg.label_width, r, val,
                 color_green_value if lab else color_muted)
        r += 1

    r += 1
    swatch_row = r
    # Matrix shades for ANSI swatches
    green_swatches_1 = [(15, 60, 25), (25, 95, 40), (35, 134, 54), (46, 160, 67),
                        (56, 185, 85), (86, 211, 100), (126, 231, 135), (175, 245, 180)]
    green_swatches_2 = [(25, 80, 35), (35, 120, 50), (46, 160, 67), (56, 195, 85),
                        (86, 225, 115), (126, 240, 145), (180, 250, 195), (215, 255, 225)]
    
    for k_row, row_colors in enumerate((green_swatches_1, green_swatches_2)):
        for j, sc in enumerate(row_colors):
            x0 = ox + (info_col + j * 4) * cfg.cell_w
            y0 = oy + (swatch_row + k_row) * cfg.cell_h
            draw.rectangle([x0, y0 + 3, x0 + 4 * cfg.cell_w - 4, y0 + cfg.cell_h - 4], fill=sc)

    # Save PNG
    png_path = os.path.join(out_dir, "fastfetch.png")
    im.save(png_path, "PNG", optimize=True)

    # Generate SVG
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def hx(c):
        return "#%02x%02x%02x" % tuple(int(v) for v in c)

    glyph_w = {}
    def get_glyph_width(ch, bold):
        key = (ch, bold)
        if key not in glyph_w:
            glyph_w[key] = draw.textlength(ch, font=fontb if bold else font)
        return glyph_w[key]

    def svg_row(row_no, row_cells):
        row_cells = sorted(row_cells, key=lambda t: t[0])
        baseline = oy + row_no * cfg.cell_h + asc
        parts = [f'<text y="{baseline}" font-size="{cfg.font_size}" xml:space="preserve">']
        run_fill = run_bold = None
        xs, chars = [], []

        def flush():
            if chars:
                weight = ' font-weight="bold"' if run_bold else ""
                parts.append(f'<tspan x="{" ".join(xs)}" fill="{hx(run_fill)}"{weight}>'
                             f'{esc("".join(chars))}</tspan>')

        for cell_col, ch, fill, bold in row_cells:
            if fill != run_fill or bold != run_bold:
                flush()
                xs, chars = [], []
                run_fill, run_bold = fill, bold
            center = ox + cell_col * cfg.cell_w + cfg.cell_w / 2
            xs.append(str(round(center - get_glyph_width(ch, bold) / 2)))
            chars.append(ch)
        flush()
        parts.append("</text>")
        return "".join(parts)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{can_w}" height="{can_h}" '
        f'viewBox="0 0 {can_w} {can_h}" font-family="\'Source Code Pro\', monospace">',
        f'<rect width="{can_w}" height="{can_h}" fill="{hx(bg_color)}"/>',
    ]

    rows = {}
    for row, col, ch, fill, bold in cells:
        rows.setdefault(row, []).append((col, ch, fill, bold))
    for row_no in sorted(rows):
        out.append(svg_row(row_no, rows[row_no]))

    for k_row, row_colors in enumerate((green_swatches_1, green_swatches_2)):
        for j, sc in enumerate(row_colors):
            x0 = ox + (info_col + j * 4) * cfg.cell_w
            y0 = oy + (swatch_row + k_row) * cfg.cell_h + 3
            out.append(f'<rect x="{x0}" y="{y0}" width="{4 * cfg.cell_w - 3}" '
                       f'height="{cfg.cell_h - 6}" fill="{hx(sc)}"/>')

    out.append("</svg>")
    svg_content = "".join(out)
    svg_path = os.path.join(out_dir, "fastfetch.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    # Generate plain text output
    maxrow = max(r for r, *_ in cells) + 1
    maxcol = max(c for _, c, *_ in cells) + 1
    grid = [[" "] * maxcol for _ in range(maxrow)]
    for r_idx, c_idx, ch, *_ in cells:
        grid[r_idx][c_idx] = ch
    txt_lines = ["".join(row).rstrip() for row in grid]
    txt_content = "\n".join(txt_lines) + "\n"
    txt_path = os.path.join(out_dir, "fastfetch.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_content)

    print(f"Generated green theme successfully: {can_w}x{can_h}px, {total_cols}x{total_rows} chars")
    print(f"  svg: {svg_path}")
    print(f"  png: {png_path}")
    print(f"  txt: {txt_path}")

if __name__ == "__main__":
    generate_banner("C:/tmp/maheensayuru/asciifetch.toml", "C:/tmp/maheensayuru")
