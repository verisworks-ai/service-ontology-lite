#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import zipfile
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path('/Users/kooyounglee/Documents/service-ontology-lite')
RAW_DIR = ROOT / 'assets/playmcp-logo/raw'
OUT_DIR = ROOT / 'assets/playmcp-logo'
REPORT_DIR = ROOT / 'reports/playmcp-logo'
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILES = sorted(RAW_DIR.glob('*.png'))
if not RAW_FILES:
    raise SystemExit('No raw imagegen files')
# Prefer retry outputs, then latest. The retry incorporated alignment feedback.
SRC = [p for p in RAW_FILES if p.name.endswith('_retry.png')][-1]
TAG = 'service_ontology_lite_playmcp_logo_600_v1'
FINAL = OUT_DIR / f'{TAG}.png'
PREVIEW = OUT_DIR / f'{TAG}_checker_preview.png'
MARK = OUT_DIR / f'{TAG}_mark_transparent.png'
CONTACT = OUT_DIR / f'{TAG}_raw_contact.png'
REPORT = REPORT_DIR / f'{TAG}_report.json'
ZIP = REPORT_DIR / f'{TAG}_pack.zip'


def load_font(size: int, bold: bool = False):
    candidates = [
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/System/Library/Fonts/Supplemental/Helvetica.ttc',
        '/System/Library/Fonts/Helvetica.ttc',
        '/Library/Fonts/Arial.ttf',
    ]
    for c in candidates:
        if c and Path(c).exists():
            try:
                return ImageFont.truetype(c, size=size)
            except Exception:
                pass
    return ImageFont.load_default()


def edge_connected_light_alpha(im: Image.Image) -> Image.Image:
    rgba = im.convert('RGBA')
    arr = np.array(rgba)
    rgb = arr[:, :, :3].astype(np.int16)
    h, w = arr.shape[:2]
    bright = rgb.mean(axis=2) > 214
    low_sat = (rgb.max(axis=2) - rgb.min(axis=2)) < 42
    # also catch checkerboard light gray/near-white background
    bg_candidate = bright & low_sat

    visited = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        if bg_candidate[0, x]:
            q.append((0, x))
        if bg_candidate[h - 1, x]:
            q.append((h - 1, x))
    for y in range(h):
        if bg_candidate[y, 0]:
            q.append((y, 0))
        if bg_candidate[y, w - 1]:
            q.append((y, w - 1))

    while q:
        y, x = q.popleft()
        if y < 0 or y >= h or x < 0 or x >= w or visited[y, x] or not bg_candidate[y, x]:
            continue
        visited[y, x] = True
        q.extend(((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)))

    alpha = arr[:, :, 3].astype(np.int16)
    alpha[visited] = 0
    # soften white halo only near removed background
    halo = bg_candidate & (~visited) & (rgb.mean(axis=2) > 228)
    alpha[halo] = np.minimum(alpha[halo], 80)
    arr[:, :, 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    arr[arr[:, :, 3] == 0, :3] = 0
    return Image.fromarray(arr, 'RGBA')


def alpha_bbox(im: Image.Image):
    a = np.array(im.getchannel('A'))
    ys, xs = np.where(a > 20)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def checker(w, h, cell=20):
    bg = Image.new('RGBA', (w, h), (255,255,255,255))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            color = (232,236,242,255) if ((x//cell + y//cell) % 2) else (255,255,255,255)
            d.rectangle((x,y,x+cell-1,y+cell-1), fill=color)
    return bg


def draw_text_center(draw, xy, text, font, fill):
    bbox = draw.textbbox((0,0), text, font=font)
    w = bbox[2]-bbox[0]
    x = xy[0] - w/2
    draw.text((x, xy[1]), text, font=font, fill=fill)

# Raw contact sheet for audit.
thumbs=[]
for p in RAW_FILES:
    im=Image.open(p).convert('RGBA')
    im.thumbnail((220,220), Image.Resampling.LANCZOS)
    thumbs.append((p.name, im.copy()))
contact=Image.new('RGBA',(460, len(thumbs)*260),(248,250,252,255))
d=ImageDraw.Draw(contact)
fsmall=load_font(15)
for i,(name,im) in enumerate(thumbs):
    y=i*260+12
    contact.alpha_composite(im,(120,y))
    d.text((16,y+225),name,font=fsmall,fill=(30,41,59,255))
contact.save(CONTACT)

src_im = Image.open(SRC).convert('RGBA')
cut = edge_connected_light_alpha(src_im)
bb = alpha_bbox(cut)
if bb is None:
    raise SystemExit('No foreground detected')
# Add crop padding.
pad = 24
bb = (max(0, bb[0]-pad), max(0, bb[1]-pad), min(cut.width, bb[2]+pad), min(cut.height, bb[3]+pad))
mark = cut.crop(bb)
mark.thumbnail((430, 360), Image.Resampling.LANCZOS)
MARK_CANVAS = Image.new('RGBA',(600,420),(0,0,0,0))
MARK_CANVAS.alpha_composite(mark, ((600-mark.width)//2, 34))
MARK_CANVAS.save(MARK)

final = Image.new('RGBA', (600,600), (0,0,0,0))
# subtle transparent-safe radial halo behind mark
halo = Image.new('RGBA',(600,600),(0,0,0,0))
hd = ImageDraw.Draw(halo)
hd.ellipse((105,55,495,445), fill=(14,116,224,24))
halo = halo.filter(ImageFilter.GaussianBlur(30))
final.alpha_composite(halo)
# soft shadow
shadow = Image.new('RGBA',(600,600),(0,0,0,0))
shadow.alpha_composite(MARK_CANVAS, (0,4))
sa = shadow.getchannel('A').filter(ImageFilter.GaussianBlur(7))
shadow = Image.new('RGBA',(600,600),(15,23,42,50))
sa_arr = np.array(sa, dtype=np.float32)
shadow_alpha = Image.fromarray(np.minimum(55, sa_arr * 0.25).astype(np.uint8), 'L')
shadow.putalpha(shadow_alpha)
final.alpha_composite(shadow)
final.alpha_composite(MARK_CANVAS)

draw = ImageDraw.Draw(final)
font_title = load_font(37, bold=True)
font_sub = load_font(17, bold=False)
draw_text_center(draw, (300, 470), 'service-ontology-lite', font_title, (20, 87, 158, 255))
draw_text_center(draw, (300, 516), 'MCP risk graph audit', font_sub, (100, 116, 139, 235))
# small deterministic graph dots under subtitle
for x, r, c in [
    (244, 4, (59, 130, 246, 210)),
    (272, 3, (148, 163, 184, 210)),
    (300, 4, (14, 165, 233, 210)),
    (328, 3, (148, 163, 184, 210)),
    (356, 4, (59, 130, 246, 210)),
]:
    draw.ellipse((x-r,552-r,x+r,552+r), fill=c)
draw.line((248,552,352,552), fill=(148,163,184,140), width=2)
final.save(FINAL)

prev = checker(600,600)
prev.alpha_composite(final)
prev.save(PREVIEW)

arr = np.array(final)
alpha = arr[:,:,3]
opaque = alpha > 0
blueish = int(((arr[:,:,2] > arr[:,:,0]) & opaque).sum())
silver_mask = (
    (np.abs(arr[:, :, 0].astype(int) - arr[:, :, 1].astype(int)) < 18)
    & (np.abs(arr[:, :, 1].astype(int) - arr[:, :, 2].astype(int)) < 24)
    & (arr[:, :, 0] > 115)
    & opaque
)
silver = int(silver_mask.sum())
report = {
    'source_imagegen': str(SRC),
    'raw_candidates': [str(p) for p in RAW_FILES],
    'final': str(FINAL),
    'preview': str(PREVIEW),
    'mark_transparent': str(MARK),
    'raw_contact': str(CONTACT),
    'size': list(final.size),
    'mode': final.mode,
    'alpha_range': [int(alpha.min()), int(alpha.max())],
    'transparent_pixels': int((alpha == 0).sum()),
    'opaque_pixels': int(opaque.sum()),
    'blueish_opaque_pixels': blueish,
    'silver_opaque_pixels': silver,
    'sha256': hashlib.sha256(FINAL.read_bytes()).hexdigest(),
    'notes': (
        'ImageGen source mark + deterministic 600x600 transparent logo composition '
        'with exact service-ontology-lite text.'
    ),
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in [FINAL, PREVIEW, MARK, CONTACT, REPORT, SRC]:
        z.write(p, p.relative_to(ROOT))
with zipfile.ZipFile(ZIP) as z:
    testzip = z.testzip()
report['zip'] = str(ZIP)
report['zip_testzip'] = testzip
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
