#!/usr/bin/env python

"""
Color tools
(thanks for https://gist.github.com/error454/6b94c46d1f7512ffe5ee)
"""

import math


def hex2rgb(color):
    h = color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(r, g, b):
    return '#{:02X}{:02X}{:02X}'.format(r, g, b)


def hex2xy(color):
    r, g, b = hex2rgb(color)
    rnorm = r / 255.0
    gnorm = g / 255.0
    bnorm = b / 255.0
    rfinal = enhance(rnorm)
    gfinal = enhance(gnorm)
    bfinal = enhance(bnorm)
    x = rfinal * 0.649926 + gfinal * 0.103455 + bfinal * 0.197109
    y = rfinal * 0.234327 + gfinal * 0.743075 + bfinal * 0.022598
    z = rfinal * 0.000000 + gfinal * 0.053077 + bfinal * 1.035763
    if x + y + z == 0:
        return [0, 0]
    else:
        xfinal = x / (x + y + z)
        yfinal = y / (x + y + z)
        return [xfinal, yfinal]


def enhance(norm):
    if norm > 0.04045:
        return math.pow((norm + 0.055) / (1.0 + 0.055), 2.4)
    else:
        return norm / 12.92
