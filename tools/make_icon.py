"""Render the Week Aqua integration icon (flat style matching the MD-4.4 icon).

Usage: python make_icon.py <out_dir>
Writes icon.png (256) and icon@2x.png (512).
"""
import math
import os
import sys

from PIL import Image, ImageDraw

S = 2048  # supersampled canvas; everything below is in 1024-units scaled by K
K = S / 1024

BG = (0xEA, 0xF3, 0xDE, 255)
DARK = (0x44, 0x45, 0x40, 255)
FISH = (0xF1, 0x99, 0x95, 255)
EYE = (0x4A, 0x1F, 0x1F, 255)
PLANTS = [(0x1D, 0x9E, 0x75), (0x0F, 0x6E, 0x58), (0x63, 0x98, 0x24), (0x3B, 0x6E, 0x11), (0x5D, 0xC9, 0xA5)]
LEDS = [(0xE8, 0x5D, 0x56), (0x5F, 0xBF, 0x3F), (0x38, 0x8A, 0xDE), (0x8E, 0x63, 0xD9)]
BEAM = (0xFF, 0xE4, 0x7A)


def k(*v):
    return [x * K for x in v]


def circle_mask():
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse(k(12, 12, 1012, 1012), fill=255)
    return m


def beam_layer():
    top, bottom = 238, 770
    grad = Image.new("L", (S, S), 0)
    gd = ImageDraw.Draw(grad)
    for y in range(int(top * K), int(bottom * K)):
        t = (y / K - top) / (bottom - top)
        gd.line([(0, y), (S, y)], fill=int(215 * (1 - t) ** 0.9))
    shape = Image.new("L", (S, S), 0)
    ImageDraw.Draw(shape).polygon(k(285, top, 739, top, 905, bottom, 119, bottom), fill=255)
    alpha = Image.new("L", (S, S), 0)
    alpha.paste(grad, mask=shape)
    layer = Image.new("RGBA", (S, S), BEAM + (0,))
    layer.putalpha(alpha)
    return layer


def plant(d, x0, y0, height, amp, phase, colour, width=26):
    pts = []
    for i in range(41):
        t = i / 40
        y = y0 - t * height
        x = x0 + amp * math.sin(phase + t * 3.1 * math.pi) * (0.35 + 0.65 * t)
        pts.append((x * K, y * K))
    w = int(width * K)
    d.line(pts, fill=colour + (255,), width=w, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=colour + (255,))


def render():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse(k(12, 12, 1012, 1012), fill=BG)

    img.alpha_composite(beam_layer())
    d = ImageDraw.Draw(img)

    # gravel mound and plants
    d.ellipse(k(215, 815, 545, 880), fill=DARK)
    plant(d, 268, 845, 300, 22, 0.4, PLANTS[0])
    plant(d, 322, 848, 420, 26, 1.9, PLANTS[1])
    plant(d, 388, 850, 360, 20, 0.9, PLANTS[2])
    plant(d, 440, 848, 470, 18, 2.6, PLANTS[3])
    plant(d, 490, 845, 330, 16, 1.3, PLANTS[4])

    # fish facing left
    cx, cy = 715, 640
    d.ellipse(k(cx - 125, cy - 75, cx + 125, cy + 75), fill=FISH)
    d.polygon(k(cx + 100, cy, cx + 210, cy - 75, cx + 210, cy + 75), fill=FISH)
    d.ellipse(k(cx - 78, cy - 26, cx - 50, cy + 2), fill=EYE)

    # LED light bar with R, G, B, UV LEDs
    d.rounded_rectangle(k(262, 170, 762, 242), radius=36 * K, fill=DARK)
    for i, colour in enumerate(LEDS):
        x = 362 + i * 100
        d.ellipse(k(x - 20, 186, x + 20, 226), fill=colour + (255,))

    img.putalpha(Image.composite(img.getchannel("A"), Image.new("L", (S, S), 0), circle_mask()))
    return img


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    big = render()
    big.resize((512, 512), Image.LANCZOS).save(os.path.join(out, "icon@2x.png"), optimize=True)
    big.resize((256, 256), Image.LANCZOS).save(os.path.join(out, "icon.png"), optimize=True)
    big.resize((48, 48), Image.LANCZOS).save(os.path.join(out, "preview_48.png"))


if __name__ == "__main__":
    main()
