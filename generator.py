import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

IMAGE_HEIGHT = 64
DEFAULT_WIDTH = 256
LINE_SPACING = 2
FONTS_DIR = Path(__file__).parent / "fonts"
PX_PER_CM = 71

TAPE_SIZES = {
    "12mm": 64,
    "9mm": 64,
    "6mm": 32,
}


def load_font(font_name: str, line_height: int):
    font_path = FONTS_DIR / font_name
    if not font_path.exists():
        available = [f.name for f in FONTS_DIR.iterdir() if f.suffix in (".ttf", ".otf")]
        if not available:
            print(f"Warning: Font '{font_name}' not found and no fonts in {FONTS_DIR}. Using default bitmap font.")
            return ImageFont.load_default()
        print(f"Error: Font '{font_name}' not found in {FONTS_DIR}.")
        print(f"Available fonts: {', '.join(available)}")
        sys.exit(1)

    lo, hi = 1, line_height
    best_font = None
    while lo <= hi:
        mid = (lo + hi) // 2
        try:
            font = ImageFont.truetype(str(font_path), mid)
            bbox = font.getbbox("Ag")
            text_height = bbox[3] - bbox[1]
            if text_height <= line_height:
                best_font = font
                lo = mid + 1
            else:
                hi = mid - 1
        except Exception:
            hi = mid - 1

    return best_font or ImageFont.load_default()


def draw_cut_mark(draw: ImageDraw.ImageDraw, x: int, height: int, dash: int = 4, gap: int = 4):
    y = 0
    while y < height:
        draw.line([(x, y), (x, min(y + dash - 1, height - 1))], fill="black", width=1)
        y += dash + gap


def draw_cut_marks(draw: ImageDraw.ImageDraw, width: int, height: int, dash: int = 4, gap: int = 4):
    draw_cut_mark(draw, 0, height, dash, gap)
    draw_cut_mark(draw, width - 1, height, dash, gap)


def create_label(text: str, font_name: str, width: int = None, padding: int = 0, cut_marks: bool = False, height: int = IMAGE_HEIGHT, text_height: int = None) -> Image.Image:
    lines = text.split("\n")
    num_lines = len(lines)
    if text_height is not None:
        line_height = text_height
    else:
        line_height = (height - LINE_SPACING * (num_lines - 1)) // num_lines

    tmp = Image.new("RGB", (1, 1))
    tmp_draw = ImageDraw.Draw(tmp)
    font = load_font(font_name, line_height)
    line_bboxes = [tmp_draw.textbbox((0, 0), line, font=font) for line in lines]

    if width is None:
        max_text_width = max((b[2] - b[0]) for b in line_bboxes)
        width = max_text_width + padding * 2

    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    line_heights_px = [b[3] - b[1] for b in line_bboxes]
    block_height = sum(line_heights_px) + LINE_SPACING * (num_lines - 1)
    block_top = (height - block_height) // 2

    y = block_top
    for line, bbox in zip(lines, line_bboxes):
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2 - bbox[0]
        draw.text((x, y - bbox[1]), line, fill="black", font=font)
        y += text_height + LINE_SPACING

    if cut_marks:
        draw_cut_marks(draw, width, height)

    return img


def generate_image(text: str, font_name: str, output_path: str, width: int = None, padding: int = 0, cut_marks: bool = False, height: int = IMAGE_HEIGHT, text_height: int = None):
    img = create_label(text, font_name, width=width, padding=padding, cut_marks=cut_marks, height=height, text_height=text_height)
    img.save(output_path, "PNG")
    print(f"Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate a PNG label image with centered text.")
    parser.add_argument("text", help="Text to render on the image. Use \\n for multiple lines.")
    parser.add_argument("--width", type=int, default=None, help="Image width in pixels. Omit to fit the text width.")
    parser.add_argument("--padding", type=int, default=0, help="Horizontal padding in pixels on each side (auto-width mode only).")
    parser.add_argument("--font", default="", help="Font filename inside the fonts/ directory (e.g. arial.ttf)")
    parser.add_argument("--output", default="output.png", help="Output PNG file path (default: output.png)")
    parser.add_argument("--cut-marks", action="store_true", help="Draw cut marks at both ends of the label")
    args = parser.parse_args()

    if not args.font:
        available = [f.name for f in FONTS_DIR.iterdir() if f.suffix in (".ttf", ".otf")] if FONTS_DIR.exists() else []
        if available:
            args.font = available[0]
            print(f"No font specified. Using: {args.font}")
        else:
            args.font = ""

    generate_image(args.text.replace("\\n", "\n"), args.font, args.output, width=args.width, padding=args.padding, cut_marks=args.cut_marks)


if __name__ == "__main__":
    main()
