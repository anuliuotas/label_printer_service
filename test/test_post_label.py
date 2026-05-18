import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from generator import create_label, FONTS_DIR
from printer import print_image

OUTPUT_PATH = Path(__file__).parent / "label.png"


def main():
    available_fonts = [f.name for f in FONTS_DIR.iterdir() if f.suffix in (".ttf", ".otf")] if FONTS_DIR.exists() else []
    font = available_fonts[0] if available_fonts else ""

    img = create_label(text="300px\n5x", font_name=font, width=300, cut_marks=True)
    img.save(str(OUTPUT_PATH), "PNG")
    print(f"Saved: {OUTPUT_PATH}")

    print_image(img)
    print("Printed successfully.")


if __name__ == "__main__":
    main()
