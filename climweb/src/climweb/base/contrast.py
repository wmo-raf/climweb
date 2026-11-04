"""
WCAG 2.1 colour contrast helpers.

Kept free of Django imports so they can be used anywhere (context processors, admin views)
and tested on their own.
"""

AA_TEXT = 4.5  # normal-size text
AA_LARGE = 3.0  # large text (24px, or 18.66px bold) and UI components


def _hex_to_rgb(hex_color):
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def relative_luminance(hex_color):
    def channel(value):
        value = value / 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in _hex_to_rgb(hex_color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color_a, color_b):
    lighter, darker = sorted((relative_luminance(color_a), relative_luminance(color_b)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _mix_with_white(hex_color, amount):
    # same mixing as base.utils.mix_with_white
    return "#%02x%02x%02x" % tuple(int(v + (255 - v) * amount) for v in _hex_to_rgb(hex_color))


def accessible_tint(hex_color, amount=0.8, minimum=AA_TEXT, max_amount=0.97):
    """
    Light tint of hex_color for panel backgrounds, mixed with at least `amount` white and
    lightened further until hex_color text on it reaches `minimum` contrast. Colours too
    light to ever reach it stop at `max_amount`.
    """
    while amount < max_amount and contrast_ratio(hex_color, _mix_with_white(hex_color, amount)) < minimum:
        amount = round(amount + 0.01, 2)
    return _mix_with_white(hex_color, amount)
