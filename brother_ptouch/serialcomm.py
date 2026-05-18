import serial

from .labelmaker_encode import encode_raster_transfer, read_png
from . import ptcbp
from . import ptstatus
import time


def reset_printer(ser):
    # Flush print buffer
    ser.write(b"\x00" * 64)

    # Initialize
    ser.write(ptcbp.serialize_control('reset'))

    # Enter raster graphics (PTCBP) mode
    ser.write(ptcbp.serialize_control('use_command_set', ptcbp.CommandSet.ptcbp))


def read_status(ser):
    ser.write(ptcbp.serialize_control('get_status'))
    status = ptstatus.unpack_status(ser.read(32))
    return status


def configure_common(ser, compress=True, end_margin=0):
    # Set print chaining off
    ser.write(ptcbp.serialize_control('set_page_mode_advanced', 0x08))

    # Set no mirror, no auto tape cut
    ser.write(ptcbp.serialize_control('set_page_mode', 0x0))

    # Set margin amount (feed amount, in dots)
    ser.write(ptcbp.serialize_control('set_page_margin', end_margin))

    # Set compression mode: TIFF
    ser.write(ptcbp.serialize_control('compression', ptcbp.CompressionType.rle
                                      if compress else
                                      ptcbp.CompressionType.none))


def configure_tape(ser, tape, raster_lines):
    typ, width, length = tape

    ser.write(ptcbp.serialize_control_obj('set_print_parameters', ptcbp.PrintParameters(
        active_fields=(ptcbp.PrintParameterField.width |
                       ptcbp.PrintParameterField.quality |
                       ptcbp.PrintParameterField.recovery),
        media_type=typ,
        width_mm=width,
        length_mm=length,
        length_px=raster_lines,
        is_follow_up=0,
        sbz=0,
    )))


def setup_printer(ser):
    reset_printer(ser)
    configure_common(ser)


def print_label(ser, data, compress=True):
    t0 = time.time()
    status = read_status(ser)
    if status.err != 0x0000 or status.phase_type not in (0x00, 0x01) or status.phase != 0x0000:
        ptstatus.print_status(status)
        raise Exception(f'Printer not ready ({status.err}, {status.phase_type}, {status.phase})')

    raster_lines = len(data) // 16

    tape = (status.tape_type, status.tape_width, status.tape_length)
    configure_tape(ser, tape, raster_lines)

    for line in encode_raster_transfer(data, not compress):
        ser.write(line)

    ser.write(ptcbp.serialize_control('print'))

    raw_status = ser.read(32)
    status = ptstatus.unpack_status(raw_status)
    t1 = time.time()
    print('total time', t1 - t0)


def connect(port):
    ser = serial.Serial(port)
    setup_printer(ser)
    return ser
