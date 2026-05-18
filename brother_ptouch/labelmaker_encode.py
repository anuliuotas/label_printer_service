from PIL import Image, ImageOps
from io import BytesIO
from . import ptcbp


def encode_raster_transfer(data, nocomp=False):
    """ Encode 1 bit per pixel image data for transfer over serial to the printer """
    # Send in chunks of 1 line (128px @ 1bpp = 16 bytes)
    chunk_size = 16
    zero_line = bytearray(b'\x00' * chunk_size)

    for i in range(0, len(data), chunk_size):
        chunk = data[i : i + chunk_size]
        if chunk == zero_line:
            yield ptcbp.serialize_control('zerofill')
        else:
            yield ptcbp.serialize_data(chunk, 'none' if nocomp else 'rle')


def read_png(path, transform=True, padding=True, dither=True):
    """ Read an image file or file-like object and convert to 1bpp raw data """
    image = Image.open(path)
    tmp = image.convert('1', dither=Image.FLOYDSTEINBERG if dither else Image.NONE)
    tmp = ImageOps.invert(tmp.convert('L')).convert('1')
    if transform:
        tmp = tmp.rotate(-90, expand=True)
        tmp = ImageOps.mirror(tmp)
    if padding:
        w, h = tmp.size
        padded = Image.new('1', (128, h))
        x, y = (128 - w) // 2, 0
        padded.paste(tmp, (x, y, x + w, y + h))
        tmp = padded
    return tmp.tobytes()


def read_pil_image(img: Image.Image, transform=True, padding=True, dither=True):
    """ Convert a PIL Image directly to 1bpp raw data """
    buf = BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return read_png(buf, transform=transform, padding=padding, dither=dither)
