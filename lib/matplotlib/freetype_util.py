"""
Higher-level functionality built on top of the Freetype wrapper.
"""

import numpy as np
from freetype import Face

def get_width_height_descent(face, text):
    slot = face.glyph

    width, height, baseline = 0, 0, 0
    previous = 0
    for i,c in enumerate(text):
        face.load_char(c)
        bitmap = slot.bitmap
        height = max(height,
                     bitmap.rows + max(0,-(slot.bitmap_top-bitmap.rows)))
        baseline = max(baseline, max(0,-(slot.bitmap_top-bitmap.rows)))
        kerning = face.get_kerning(previous, c)
        width += (slot.advance.x >> 6) + (kerning.x >> 6)
        previous = c

    return width, height, baseline

def render_string(face, text):
    slot = face.glyph

    # First pass to compute bbox
    width, height, baseline = get_width_height_descent(face, text)

    Z = np.zeros((height,width), dtype=np.ubyte)

    # Second pass for actual rendering
    x, y = 0, 0
    previous = 0
    for c in text:
        face.load_char(c)
        bitmap = slot.bitmap
        top = slot.bitmap_top
        left = slot.bitmap_left
        w,h = bitmap.width, bitmap.rows
        y = height-baseline-top
        kerning = face.get_kerning(previous, c)
        x += (kerning.x >> 6)
        Z[y:y+h,x:x+w] |= np.array(bitmap.buffer).reshape(h,w)
        x += (slot.advance.x >> 6)
        previous = c

    return Z
