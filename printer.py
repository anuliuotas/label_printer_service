from PIL import Image

from brother_ptouch import serialcomm
from brother_ptouch.labelmaker_encode import read_pil_image
from brother_ptouch.ptstatus import MODELS, ERR_FLAGS, TAPE_TYPE, TAPE_BGCOLORS, TAPE_FGCOLORS
from config import PRINTER_PORT

DEFAULT_PORT = PRINTER_PORT


def print_image(img: Image.Image, port: str = DEFAULT_PORT):
    """Print a PIL Image to the Brother PT-P300BT via Bluetooth serial."""
    data = read_pil_image(img)
    ser = serialcomm.connect(port)
    try:
        serialcomm.print_label(ser, data)
    finally:
        ser.close()


def _parse_errors(err_word: int) -> list[str]:
    errors = []
    bit = 0
    while err_word:
        if err_word & 1:
            errors.append(ERR_FLAGS.get(bit, f'Unknown error bit {bit}'))
        bit += 1
        err_word >>= 1
    return errors


def get_printer_status(port: str = DEFAULT_PORT) -> dict:
    """
    Connect to the printer and return a status dict.
    Returns {'ok': True, 'tape_width': 12, ...} or {'ok': False, 'error': '...'}.
    """
    import serial as _serial
    from brother_ptouch import ptcbp
    from brother_ptouch.ptstatus import unpack_status
    try:
        # Use a 5-second read timeout so we never block if the printer is
        # slow to respond (e.g. cover open, low battery).
        ser = _serial.Serial(port, timeout=5)
        try:
            serialcomm.reset_printer(ser)
            ser.write(ptcbp.serialize_control('get_status'))
            raw = ser.read(32)
        finally:
            ser.close()
        if len(raw) != 32:
            return {'ok': False, 'error': f'No response from printer ({len(raw)} of 32 bytes)'}
        status = unpack_status(raw)
        errors = _parse_errors(status.err)
        return {
            'ok': len(errors) == 0,
            'model': MODELS.get(status.model, f'Unknown (0x{status.model:02x})'),
            'tape_width': status.tape_width,
            'tape_type': TAPE_TYPE.get(status.tape_type, f'Unknown (0x{status.tape_type:02x})'),
            'tape_bgcolor': TAPE_BGCOLORS.get(status.tape_bgcolor, f'Unknown (0x{status.tape_bgcolor:02x})'),
            'tape_fgcolor': TAPE_FGCOLORS.get(status.tape_fgcolor, f'Unknown (0x{status.tape_fgcolor:02x})'),
            'errors': errors,
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}
