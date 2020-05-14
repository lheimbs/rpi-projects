#!/usr/bin/env python

from math import floor, pow

GRIDLINES = 4


def calculate_ticks(y1_min, y1_max, y2_min, y2_max):
    if y1_min < 0:
        y1_range = y1_max - y1_min
    else:
        y1_range = y1_max

    y1_range = y1_range * 1000
    y1_len = len(str(floor(y1_range)))

    y1_pow10_divisor = pow(10, y1_len - 1)
    y1_firstdigit = floor(y1_range / y1_pow10_divisor)
    y1_max_base = y1_pow10_divisor * y1_firstdigit / 1000

    y1_dtick = y1_max_base / GRIDLINES

    y1_pow10_divisor = pow(10, y1_len - 1) / 1000
    y1_range = y1_range / 1000

    if y2_min < 0:
        y2_range = y2_max - y2_min
    else:
        y2_range = y2_max

    y2_range = y2_range * 1000
    y2_len = len(str(floor(y2_range)))

    y2_pow10_divisor = pow(10, y2_len - 1)
    y2_firstdigit = floor(y2_range / y2_pow10_divisor)
    y2_max_base = y2_pow10_divisor * y2_firstdigit / 1000

    y2_dtick = y2_max_base / GRIDLINES

    y2_pow10_divisor = pow(10, y2_len - 1) / 1000
    y2_range = y2_range / 1000

    y1_dtick_ratio = y1_range / y1_dtick
    y2_dtick_ratio = y2_range / y2_dtick

    global_dtick_ratio = max(y1_dtick_ratio, y2_dtick_ratio)

    negative = False

    if y1_min < 0:
        negative = True
        y1_negative_ratio = abs(y1_min / y1_range) * global_dtick_ratio
    else:
        y1_negative_ratio = 0

    if y2_min < 0:
        negative = True
        y2_negative_ratio = abs(y2_min / y2_range) * global_dtick_ratio
    else:
        y2_negative_ratio = 0

    global_negative_ratio = max(y1_negative_ratio, y2_negative_ratio) + 0.1

    if negative:
        y1_range_min = (global_negative_ratio) * y1_dtick * -1
        y2_range_min = (global_negative_ratio) * y2_dtick * -1
    else:
        y1_range_min = 0
        y2_range_min = 0

    y1_positive_ratio = abs(y1_max / y1_range) * global_dtick_ratio
    y2_positive_ratio = abs(y2_max / y2_range) * global_dtick_ratio

    global_positive_ratio = max(y1_positive_ratio, y2_positive_ratio) + 0.1

    y1_range_max = (global_positive_ratio) * y1_dtick
    y2_range_max = (global_positive_ratio) * y2_dtick

    return y1_range_min, y1_range_max, y1_dtick, y2_range_min, y2_range_max, y2_dtick
