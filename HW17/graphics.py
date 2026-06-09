import serial
import threading

PICO_PORT = "/dev/tty.usbmodem101"  # confirm port
_pico_cmds = []

def _read_pico():
    try:
        ser = serial.Serial(PICO_PORT, 115200, timeout=1)
        while True:
            ch = ser.read(1).decode("utf-8", errors="ignore")
            if ch in ("S", "F"):
                _pico_cmds.append(ch)
    except Exception as e:
        print(f"Pico serial error: {e}")

threading.Thread(target=_read_pico, daemon=True).start()

"""
paddle_forcefield.py  —  pgzero haptic paddle force field visualizer
No Pico required — keyboard only.

Controls:
  LEFT / RIGHT  → rotate paddle
  UP / DOWN     → increase / decrease force
  R             → reset
"""

import pgzrun
import math

# ── Window ────────────────────────────────────────────────────────────────────
WIDTH  = 800
HEIGHT = 800
TITLE  = "Haptic Paddle — Force Field"

# ── Visual config ─────────────────────────────────────────────────────────────
ORIGIN    = (WIDTH // 2, HEIGHT // 2)
GRID_N    = 18
ARROW_MAX = 26
PADDLE_R  = 180
FORCE_MAX = 5.0

# ── Colours ───────────────────────────────────────────────────────────────────
C_BG       = (8,   10,  22)
C_GRID_DOT = (28,  34,  60)
C_LOW      = (40,  100, 220)
C_HIGH     = (255,  60,  60)
C_ZERO     = (40,  180, 120)
C_PADDLE   = (255, 220,  60)
C_ARM      = (180, 180, 220)
C_TEXT     = (200, 220, 255)
C_RING     = (50,   60, 100)

# ── State ─────────────────────────────────────────────────────────────────────
state  = {"angle": 0.0, "force": 0.0}
smooth = {"angle": 0.0, "force": 0.0}

# ── Update ────────────────────────────────────────────────────────────────────
def update():
    a = 0.12
    diff = (state["angle"] - smooth["angle"] + 180) % 360 - 180
    smooth["angle"] = (smooth["angle"] + a * diff) % 360
    smooth["force"] +=  a * (state["force"] - smooth["force"])

# ── Helpers ───────────────────────────────────────────────────────────────────
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
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    head   = 5
    screen.draw.line((int(ex), int(ey)),
                     (int(ex - ux*head + px*head*0.5),
                      int(ey - uy*head + py*head*0.5)), color)
    screen.draw.line((int(ex), int(ey)),
                     (int(ex - ux*head - px*head*0.5),
                      int(ey - uy*head - py*head*0.5)), color)

# ── Pre-compute grid points ───────────────────────────────────────────────────
_margin = 60
_step_x = (WIDTH  - _margin * 2) / (GRID_N - 1)
_step_y = (HEIGHT - _margin * 2) / (GRID_N - 1)
GRID_PTS = [
    (_margin + c * _step_x, _margin + r * _step_y)
    for r in range(GRID_N)
    for c in range(GRID_N)
]

# ── Draw ──────────────────────────────────────────────────────────────────────
def draw():
    screen.fill(C_BG)

    angle_rad = math.radians(smooth["angle"])
    force     = smooth["force"]
    ox, oy    = ORIGIN

    pad_ux =  math.cos(angle_rad)
    pad_uy =  math.sin(angle_rad)
    tan_ux = -math.sin(angle_rad)
    tan_uy =  math.cos(angle_rad)

    # Reference rings
    for r in [80, 160, 260, 380]:
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
    screen.draw.text(f"Angle: {smooth['angle']:6.1f}°", topleft=(14, 14), fontsize=24, color=C_TEXT)
    screen.draw.text(f"Force: {force:+6.3f} N",         topleft=(14, 42), fontsize=24, color=C_TEXT)
    screen.draw.text("← → rotate    ↑ ↓ force    R reset",
                     bottomleft=(14, HEIGHT - 12), fontsize=18, color=(100, 120, 160))

# ── Input ─────────────────────────────────────────────────────────────────────
def on_key_down(key):
    if key == keys.LEFT:  state["angle"] = (state["angle"] - 10) % 360
    if key == keys.RIGHT: state["angle"] = (state["angle"] + 10) % 360
    if key == keys.UP:    state["force"] = min(state["force"] + 0.5, FORCE_MAX)
    if key == keys.DOWN:  state["force"] = max(state["force"] - 0.5, -FORCE_MAX)
    if key == keys.R:
        state["angle"] = 0.0
        state["force"] = 0.0

pgzrun.go()