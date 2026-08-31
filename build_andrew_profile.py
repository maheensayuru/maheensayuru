import os
import re
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

def generate_andrew_svgs():
    img_path = "C:/tmp/maheensayuru/headshot.jpg"
    
    # 1. Generate 25 lines of ASCII art
    raw_img = Image.open(img_path).convert("L")
    w, h = raw_img.size
    crop_img = raw_img.crop((int(w * 0.10), int(h * 0.03), int(w * 0.90), int(h * 0.96)))
    
    # Andrew6rant ASCII dimensions: 25 rows x 38 cols
    rows = 25
    cols = 38
    
    # Enhance contrast and details for glitch bar and face
    resized = crop_img.resize((cols, rows), Image.LANCZOS)
    enh = ImageEnhance.Contrast(resized).enhance(1.8)
    bright = ImageEnhance.Brightness(enh).enhance(1.1)
    
    # Ramp tailored to Andrew6rant's character set
    ramp_dark = " .'`^~!,:;*|ijkhwpm%@MWNH"
    ramp_light = " .'`^~!,:;*|ijkhwpm%@MWNH"[::-1]
    
    dark_ascii_lines = []
    light_ascii_lines = []
    
    arr = np.array(bright, dtype=np.float32)
    p_lo, p_hi = np.percentile(arr, 2), np.percentile(arr, 98)
    norm = np.clip((arr - p_lo) / max(1, p_hi - p_lo), 0, 1)
    
    for y_idx in range(rows):
        d_line = ""
        l_line = ""
        for x_idx in range(cols):
            val = norm[y_idx, x_idx]
            d_idx = int(val * (len(ramp_dark) - 1))
            l_idx = int(val * (len(ramp_light) - 1))
            d_line += ramp_dark[d_idx]
            l_line += ramp_light[l_idx]
        d_line = d_line.ljust(cols)
        l_line = l_line.ljust(cols)
        dark_ascii_lines.append(d_line)
        light_ascii_lines.append(l_line)
    
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    # 2. Right-side content definition (25 lines)
    right_lines_spec = [
        ("header", "maheensayuru@github", " -———————————————————————————————————————————-—-"),
        ("kv", "Role", "Software Engineering Undergrad (Year 2)"),
        ("kv", "Focus", "AI Agent Systems, DevSecOps, Concurrency"),
        ("kv", "Workflow", "Autonomous AI Agents across Roles"),
        ("kv", "Degree", "BSc (Hons) in Software Engineering"),
        ("kv", "IDE", "VS Code, Neovim, Terminal"),
        ("blank",),
        ("kv", "Languages.Code", "Go, Python, TypeScript, Java, SQL"),
        ("kv", "Systems.Core", "WebAssembly (WASI), TCP/IP, Proxies"),
        ("kv", "Security.Tools", "Shannon Entropy, DevSecOps, Chaos"),
        ("kv", "Infra.Databases", "Neo4j, MySQL, Docker, Linux, Git Hooks"),
        ("blank",),
        ("kv", "Projects.Security", "ShadowGuard (Air-gapped Secret Detection)"),
        ("kv", "Projects.Systems", "Aegis (Zero-Downtime WASI Proxy), FaultLine"),
        ("kv", "Projects.AI-Agent", "GraphRAG Interceptor (AST & Graph Proxy)"),
        ("blank",),
        ("header", "- Contact", " -——————————————————————————————————————————————-—-"),
        ("kv", "Email.Primary", "maheen.sayuru21@gmail.com"),
        ("kv", "LinkedIn", "linkedin.com/in/maheen-sayuru"),
        ("kv", "GitHub", "github.com/maheensayuru"),
        ("kv", "Organizations", "shadowguard-security, madewithai"),
        ("blank",),
        ("header", "- GitHub Stats", " -—————————————————————————————————————————-—-"),
        ("stats_repos_stars", "10", "18", "8"),
        ("stats_commits_followers", "500+", "49"),
    ]

    def build_right_line(spec, y_pos, mode="dark"):
        TOTAL_LINE_LEN = 58
        if spec[0] == "header":
            title, sep = spec[1], spec[2]
            return f'<tspan x="390" y="{y_pos}">{esc(title)}</tspan>{esc(sep)}'
        elif spec[0] == "blank":
            return f'<tspan x="390" y="{y_pos}" class="cc">. </tspan>'
        elif spec[0] == "kv":
            full_key, val = spec[1], spec[2]
            if "." in full_key:
                k_parts = full_key.split(".")
                key_html = f'<tspan class="key">{esc(k_parts[0])}</tspan>.<tspan class="key">{esc(k_parts[1])}</tspan>'
                raw_key_len = len(full_key)
            else:
                key_html = f'<tspan class="key">{esc(full_key)}</tspan>'
                raw_key_len = len(full_key)
            
            dots_len = max(3, TOTAL_LINE_LEN - (raw_key_len + len(val) + 5))
            dots = "." * dots_len
            return f'<tspan x="390" y="{y_pos}" class="cc">. </tspan>{key_html}:<tspan class="cc"> {dots} </tspan><tspan class="value">{esc(val)}</tspan>'
        elif spec[0] == "stats_repos_stars":
            repos, contrib, stars = spec[1], spec[2], spec[3]
            return f'<tspan x="390" y="{y_pos}" class="cc">. </tspan><tspan class="key">Repos</tspan>:<tspan class="cc"> .... </tspan><tspan class="value">{repos}</tspan> {{<tspan class="key">Contributed</tspan>: <tspan class="value">{contrib}</tspan>}} | <tspan class="key">Stars</tspan>:<tspan class="cc"> ........... </tspan><tspan class="value">{stars}</tspan>'
        elif spec[0] == "stats_commits_followers":
            commits, followers = spec[1], spec[2]
            return f'<tspan x="390" y="{y_pos}" class="cc">. </tspan><tspan class="key">Commits</tspan>:<tspan class="cc"> ................ </tspan><tspan class="value">{commits}</tspan> | <tspan class="key">Followers</tspan>:<tspan class="cc"> ....... </tspan><tspan class="value">{followers}</tspan>'

    # 3. Build Dark Mode SVG
    dark_svg_lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        '<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="530px" font-size="16px">',
        "<style>",
        "@font-face {",
        "src: local('Consolas'), local('Consolas Bold');",
        "font-family: 'ConsolasFallback';",
        "font-display: swap;",
        "-webkit-size-adjust: 109%;",
        "size-adjust: 109%;",
        "}",
        ".key {fill: #ffa657;}",
        ".value {fill: #a5d6ff;}",
        ".addColor {fill: #3fb950;}",
        ".delColor {fill: #f85149;}",
        ".cc {fill: #616e7f;}",
        "text, tspan {white-space: pre;}",
        "</style>",
        '<rect width="985px" height="530px" fill="#161b22" rx="15"/>',
        '<text x="15" y="30" fill="#c9d1d9" class="ascii">'
    ]
    
    for i, line in enumerate(dark_ascii_lines):
        y = 30 + i * 20
        dark_svg_lines.append(f'<tspan x="15" y="{y}">{esc(line)}</tspan>')
    dark_svg_lines.append("</text>")
    
    dark_svg_lines.append('<text x="390" y="30" fill="#c9d1d9">')
    for i, spec in enumerate(right_lines_spec):
        y = 30 + i * 20
        formatted = build_right_line(spec, y, "dark")
        dark_svg_lines.append(formatted)
    dark_svg_lines.append("</text>")
    dark_svg_lines.append("</svg>")
    
    dark_svg_content = "\n".join(dark_svg_lines)
    with open("C:/tmp/maheensayuru/dark_mode.svg", "w", encoding="utf-8") as f:
        f.write(dark_svg_content)
        
    # 4. Build Light Mode SVG
    light_svg_lines = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        '<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="530px" font-size="16px">',
        "<style>",
        "@font-face {",
        "src: local('Consolas'), local('Consolas Bold');",
        "font-family: 'ConsolasFallback';",
        "font-display: swap;",
        "-webkit-size-adjust: 109%;",
        "size-adjust: 109%;",
        "}",
        ".key {fill: #953800;}",
        ".value {fill: #0a3069;}",
        ".addColor {fill: #1a7f37;}",
        ".delColor {fill: #cf222e;}",
        ".cc {fill: #c2cfde;}",
        "text, tspan {white-space: pre;}",
        "</style>",
        '<rect width="985px" height="530px" fill="#f6f8fa" rx="15"/>',
        '<text x="15" y="30" fill="#24292f" class="ascii">'
    ]
    
    for i, line in enumerate(light_ascii_lines):
        y = 30 + i * 20
        light_svg_lines.append(f'<tspan x="15" y="{y}">{esc(line)}</tspan>')
    light_svg_lines.append("</text>")
    
    light_svg_lines.append('<text x="390" y="30" fill="#24292f">')
    for i, spec in enumerate(right_lines_spec):
        y = 30 + i * 20
        formatted = build_right_line(spec, y, "light")
        light_svg_lines.append(formatted)
    light_svg_lines.append("</text>")
    light_svg_lines.append("</svg>")
    
    light_svg_content = "\n".join(light_svg_lines)
    with open("C:/tmp/maheensayuru/light_mode.svg", "w", encoding="utf-8") as f:
        f.write(light_svg_content)
        
    print("Generated dark_mode.svg and light_mode.svg successfully!")

if __name__ == "__main__":
    generate_andrew_svgs()
