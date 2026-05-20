import base64
import io
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
from generator import FONTS_DIR, TAPE_SIZES, IMAGE_HEIGHT, LINE_SPACING, create_label, draw_cut_mark
import rfcomm_manager

app = Flask(__name__)
rfcomm_manager.start()


def _to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


@app.route("/")
def index():
    fonts = sorted(f.name for f in FONTS_DIR.iterdir() if f.suffix in (".ttf", ".otf")) if FONTS_DIR.exists() else []
    return render_template("index.html", fonts=fonts, tape_sizes=list(TAPE_SIZES.keys()))


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json()
    text = data.get("text", "")
    width = data.get("width") or None
    padding = int(data.get("padding") or 0)
    font = data.get("font", "")
    height = TAPE_SIZES.get(data.get("tape", "12mm"), IMAGE_HEIGHT)
    text_height = int(data.get("text_height")) if data.get("text_height") else None

    num_lines = len(text.split("\n"))
    auto_text_height = (height - LINE_SPACING * (num_lines - 1)) // num_lines
    actual_text_height = text_height if text_height is not None else auto_text_height

    img = create_label(text, font, width=width, padding=padding, height=height, text_height=text_height)
    return jsonify({"image": _to_b64(img), "width": img.width, "height": img.height, "text_height": actual_text_height})


@app.route("/api/combine", methods=["POST"])
def api_combine():
    data = request.get_json()
    images = [Image.open(io.BytesIO(base64.b64decode(b64))) for b64 in data.get("images", [])]

    if not images:
        return jsonify({"error": "No images provided"}), 400

    spacing_px = int(data.get("spacing_px") or 0)
    cut_marks = bool(data.get("cut_marks", False))

    total_width = sum(img.width for img in images) + spacing_px * (len(images) - 1)
    max_height = max(img.height for img in images)
    combined = Image.new("RGB", (total_width, max_height), color="white")
    x = 0
    for i, img in enumerate(images):
        combined.paste(img, (x, 0))
        x += img.width + (spacing_px if i < len(images) - 1 else 0)

    if cut_marks:
        from PIL import ImageDraw as PILDraw
        draw = PILDraw.Draw(combined)
        draw_cut_mark(draw, 0, combined.height)
        draw_cut_mark(draw, combined.width - 1, combined.height)
        x = 0
        for i, img in enumerate(images[:-1]):
            x += img.width
            cut_x = x + spacing_px // 2 if spacing_px else x
            draw_cut_mark(draw, cut_x, combined.height)
            x += spacing_px

    return jsonify({"image": _to_b64(combined), "width": combined.width, "height": combined.height})


@app.route("/api/status")
def api_status():
    from printer import get_printer_status
    status = get_printer_status()
    return jsonify({"online": status.get("ok", False), **status})


@app.route("/api/print", methods=["POST"])
def api_print():
    from printer import print_image
    img_bytes = base64.b64decode(request.get_json().get("image", ""))
    img = Image.open(io.BytesIO(img_bytes))
    try:
        print_image(img)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    import os
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
