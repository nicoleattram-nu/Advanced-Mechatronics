"""
paddle_field.py  —  pgzero force field visualizer (WINDOW 1)
Shows the live force field and paddle rotation.

Run alongside paddle_graph.py
Controls: LEFT / RIGHT rotate, R reset
"""

import pgzrun
import math

WIDTH  = 700
HEIGHT = 700
TITLE  = "Force Field"

ORIGIN    = (WIDTH // 2, HEIGHT // 2)
GRID_N    = 18
ARROW_MAX = 26
PADDLE_R  = 180
FORCE_MAX = 5.0

C_BG       = (8,   10,  22)
C_GRID_DOT = (28,  34,  60)
C_LOW      = (40,  100, 220)
C_HIGH     = (255,  60,  60)
C_ZERO     = (40,  180, 120)
C_PADDLE   = (255, 220,  60)
C_ARM      = (180, 180, 220)
C_TEXT     = (200, 220, 255)
C_RING     = (50,   60, 100)

angle = 0.0
smooth_angle = 0.0

def calc_force(angle_deg):
    """3 bumps & holes landscape."""
    angle_rad = math.radians(angle_deg)
    return FORCE_MAX * 0.5 * (1.0 + math.cos(angle_rad * 3))

def update():
    global smooth_angle
    a = 0.12
    diff = (angle - smooth_angle + 180) % 360 - 180
    smooth_angle = (smooth_angle + a * diff) % 360

def _lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def _force_color(force):
    t    = min(abs(force) / FORCE_MAX, 1.0)
    base = _lerp_color(C_ZERO, C_LOW, t)
    return _lerp_color(base, C_HIGH, t * t)

def _draw_arrow(x, y, dx, dy, color):
    if abs(dx) < 0.5 and abs(dy) < 0.5:
        screen.draw.filled_circle((int(x), int(y)), 2, C_GRID_DOT)
        return
    ex, ey = x + dx, y + dy
    screen.draw.line((int(x), int(y)), (int(ex), int(ey)), color)
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    head   = 5
    screen.draw.line((int(ex), int(ey)),
                     (int(ex - ux*head + px*head*0.5),
                      int(ey - uy*head + py*head*0.5)), color)
    screen.draw.line((int(ex), int(ey)),
                     (int(ex - ux*head - px*head*0.5),
                      int(ey - uy*head - py*head*0.5)), color)

_margin = 60
_step_x = (WIDTH - _margin * 2) / (GRID_N - 1) if GRID_N > 1 else 0
_step_y = (HEIGHT - _margin * 2) / (GRID_N - 1) if GRID_N > 1 else 0
GRID_PTS = [
    (_margin + c * _step_x, _margin + r * _step_y)
    for r in range(GRID_N)
    for c in range(GRID_N)
]

def draw():
    screen.fill(C_BG)

    angle_rad = math.radians(smooth_angle)
    force     = calc_force(smooth_angle)
    ox, oy    = ORIGIN

    pad_ux =  math.cos(angle_rad)
    pad_uy =  math.sin(angle_rad)
    tan_ux = -math.sin(angle_rad)
    tan_uy =  math.cos(angle_rad)

    # Reference rings
    for r in [80, 160, 260]:
        screen.draw.circle((ox, oy), r, C_RING)

    # Force field arrows
    for gx, gy in GRID_PTS:
        rx, ry = gx - ox, gy - oy
        dist   = math.hypot(rx, ry) or 1.0
        rux, ruy = rx / dist, ry / dist

        radial_proj  = rux * pad_ux + ruy * pad_uy
        tangent_proj = rux * tan_ux + ruy * tan_uy
        alignment    = max(0.0, radial_proj)
        falloff      = 1.0 / (1.0 + (dist / 120.0) ** 2)
        scale        = abs(force) * alignment * falloff * ARROW_MAX / FORCE_MAX
        sign         = 1.0 if force >= 0 else -1.0

        adx = sign * pad_ux * scale + tan_ux * tangent_proj * scale * 0.3
        ady = sign * pad_uy * scale + tan_uy * tangent_proj * scale * 0.3

        _draw_arrow(gx, gy, adx, ady, _force_color(force))

    # Paddle arm
    tip_x = int(ox + pad_ux * PADDLE_R)
    tip_y = int(oy + pad_uy * PADDLE_R)
    for offset in [-1, 0, 1]:
        screen.draw.line(
            (int(ox + tan_ux * offset), int(oy + tan_uy * offset)),
            (int(tip_x + tan_ux * offset), int(tip_y + tan_uy * offset)),
            C_ARM
        )

    # Paddle tip
    screen.draw.filled_circle((tip_x, tip_y), 10, C_PADDLE)
    screen.draw.circle((tip_x, tip_y), 14, C_ARM)

    # Force bar above tip
    bar_len = int(min(abs(force) / FORCE_MAX, 1.0) * 40)
    if bar_len > 0:
        screen.draw.filled_rect(
            Rect(tip_x - 4, tip_y - bar_len - 18, 8, bar_len),
            _force_color(force)
        )

    # Origin pivot
    screen.draw.filled_circle((ox, oy), 10, C_ARM)
    screen.draw.filled_circle((ox, oy),  5, C_PADDLE)

    # HUD
    force = calc_force(smooth_angle)
    screen.draw.text(f"Angle: {smooth_angle:6.1f}°", topleft=(14, 14), fontsize=22, color=C_TEXT)
    screen.draw.text(f"Force: {force:+6.3f} N",      topleft=(14, 40), fontsize=22, color=C_TEXT)
    screen.draw.text("← → rotate    R reset",        bottomleft=(14, HEIGHT - 12), fontsize=16, color=(100, 120, 160))

def on_key_down(key):
    global angle
    if key == keys.LEFT:  angle = (angle - 10) % 360
    if key == keys.RIGHT: angle = (angle + 10) % 360
    if key == keys.R:     angle = 0.0

pgzrun.go()