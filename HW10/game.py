# GAME CODE GENERATED IN CLAUDE AND EDITED 

import serial
import threading

PICO_PORT = "/dev/cu.usbmodem1101"  # ← change this
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
🌊 DEEP SWIM - Pygame Zero underwater side-scroller
Controls:
  SPACE or UP  → Swim up (gravity pulls you down)
  Z or X       → Shoot bubble projectile
3 hits → Game Over
"""

import pgzrun
import random
import math

# ── Window ────────────────────────────────────────────────────────────────────
WIDTH  = 800
HEIGHT = 480
TITLE  = "Deep Swim 🌊"

# ── Constants ─────────────────────────────────────────────────────────────────
GRAVITY       = 0.25
SWIM_FORCE    = -5.5
SCROLL_SPEED  = 3
BULLET_SPEED  = 9
ENEMY_SPEED   = 2.0
SPAWN_INTERVAL = 90   # frames between enemy spawns

# ── Colours (RGB) ─────────────────────────────────────────────────────────────
C_BG_TOP    = (0,  60, 120)
C_BG_BOT    = (0, 20,  60)
C_WATER     = (30, 120, 200, 80)
C_PLAYER    = (255, 220, 60)
C_PLAYER_EYE= (20,  20,  20)
C_PLAYER_FIN= (255, 160, 30)
C_ENEMY     = (220, 60,  60)
C_ENEMY_EYE = (255, 255, 255)
C_BULLET    = (200, 240, 255)
C_HIT_FLASH = (255, 80,  80)
C_BUBBLE    = (160, 220, 255)
C_ROCK_DARK = (40,  50,  70)
C_ROCK_MID  = (55,  68,  95)
C_SEAWEED   = (30, 140,  80)
C_UI_TEXT   = (220, 240, 255)
C_HP_GOOD   = (80, 220, 120)
C_HP_BAD    = (220, 80,  80)

# ── Game state ─────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.state       = "playing"   # "playing" | "dead" | "start"
        self.score       = 0
        self.frame       = 0
        self.scroll_x    = 0           # used for parallax only; obstacles use own x

        # Player
        self.py          = HEIGHT // 2
        self.pvy         = 0.0
        self.hp          = 3           # hits remaining
        self.invincible  = 0           # invincibility frames after hit
        self.shoot_cool  = 0

        # Collections
        self.bullets     = []          # [x, y, age]
        self.enemies     = []          # [x, y, vy, wobble_offset]
        self.bubbles     = []          # [x, y, r, vy]  decorative
        self.rocks       = []          # [x, y, w, h, layer]
        self.seaweeds    = []          # [x, phase]
        self.particles   = []          # [x, y, vx, vy, life, color]

        self._spawn_initial_scenery()

    def _spawn_initial_scenery(self):
        for i in range(8):
            self._add_rock(100 + i * 110)
        for i in range(10):
            self._add_seaweed(80 + i * 85)
        for _ in range(15):
            self._add_bubble(random.randint(0, WIDTH),
                             random.randint(0, HEIGHT))

    def _add_rock(self, x):
        layer = random.choice([0, 1])
        w = random.randint(40, 90)
        h = random.randint(20, 50)
        y = HEIGHT - h - random.randint(0, 30)
        self.rocks.append([x, y, w, h, layer])

    def _add_seaweed(self, x):
        self.seaweeds.append([x, random.uniform(0, math.pi * 2)])

    def _add_bubble(self, x, y):
        r  = random.randint(3, 10)
        vy = -random.uniform(0.3, 1.0)
        self.bubbles.append([x, y, r, vy])


G = Game()

# ── Input helpers ──────────────────────────────────────────────────────────────
def _swim():
    G.pvy = SWIM_FORCE

def _shoot():
    if G.shoot_cool <= 0:
        G.bullets.append([64 + 18, G.py, 0])
        G.shoot_cool = 18
        # tiny bubble burst at muzzle
        for _ in range(4):
            G.particles.append([
                64+18, G.py,
                random.uniform(1, 3), random.uniform(-1.5, 1.5),
                12, C_BUBBLE
            ])

def on_key_down(key):
    if G.state in ("dead", "start"):
        G.reset()
        return
    if key in (keys.SPACE, keys.UP, keys.W):
        _swim()
    if key in (keys.Z, keys.X, keys.LCTRL):
        _shoot()

# ── Update ─────────────────────────────────────────────────────────────────────
def update():
    # ── Pico button input ──────────────────────────────────────────────────
    while _pico_cmds:
        cmd = _pico_cmds.pop(0)
        if cmd == "S":
            _swim()
        elif cmd == "F":
            _shoot()

    if G.state != "playing":
        return

    G.frame      += 1
    G.scroll_x   += SCROLL_SPEED
    G.score      += 1
    if G.shoot_cool > 0:
        G.shoot_cool -= 1
    if G.invincible > 0:
        G.invincible -= 1

    # ── Player physics ────────────────────────────────────────────────────────
    G.pvy += GRAVITY
    G.py  += G.pvy
    # clamp to screen
    if G.py < 20:
        G.py  = 20
        G.pvy = 0
    if G.py > HEIGHT - 20:
        G.py  = HEIGHT - 20
        G.pvy = 0

    # ── Bullets ───────────────────────────────────────────────────────────────
    for b in G.bullets:
        b[0] += BULLET_SPEED
        b[2] += 1
    G.bullets = [b for b in G.bullets if b[0] < WIDTH + 20 and b[2] < 60]

    # ── Spawn enemies ─────────────────────────────────────────────────────────
    if G.frame % SPAWN_INTERVAL == 0:
        y  = random.randint(50, HEIGHT - 50)
        vy = random.uniform(-0.6, 0.6)
        G.enemies.append([WIDTH + 40, y, vy, random.uniform(0, math.pi * 2)])

    # ── Move enemies ──────────────────────────────────────────────────────────
    speed = ENEMY_SPEED + G.score / 3000   # get faster over time
    for e in G.enemies:
        e[0] -= speed
        e[3] += 0.05                       # wobble phase
        e[1] += e[2] + math.sin(e[3]) * 0.8
        e[1]  = max(30, min(HEIGHT - 30, e[1]))

    # ── Bullet × Enemy collision ──────────────────────────────────────────────
    dead_e = set()
    dead_b = set()
    for bi, b in enumerate(G.bullets):
        for ei, e in enumerate(G.enemies):
            if abs(b[0] - e[0]) < 22 and abs(b[1] - e[1]) < 18:
                dead_e.add(ei)
                dead_b.add(bi)
                _explode(e[0], e[1], C_ENEMY)
                G.score += 50
    G.enemies = [e for i, e in enumerate(G.enemies) if i not in dead_e]
    G.bullets  = [b for i, b in enumerate(G.bullets)  if i not in dead_b]

    # off-screen enemies
    G.enemies = [e for e in G.enemies if e[0] > -60]

    # ── Player × Enemy collision ──────────────────────────────────────────────
    if G.invincible == 0:
        px, py = 64, G.py
        for e in G.enemies:
            if abs(px - e[0]) < 28 and abs(py - e[1]) < 22:
                G.hp        -= 1
                G.invincible = 80
                _explode(px, py, C_HIT_FLASH)
                if G.hp <= 0:
                    G.state = "dead"
                break

    # ── Scenery scroll & recycle ───────────────────────────────────────────────
    for r in G.rocks:
        r[0] -= SCROLL_SPEED * (0.6 if r[4] == 0 else 1.0)
        if r[0] < -100:
            r[0] = WIDTH + random.randint(20, 80)
            r[2] = random.randint(40, 90)
            r[3] = random.randint(20, 50)
            r[1] = HEIGHT - r[3] - random.randint(0, 30)

    for sw in G.seaweeds:
        sw[0] -= SCROLL_SPEED
        sw[1] += 0.04
        if sw[0] < -20:
            sw[0] = WIDTH + random.randint(10, 50)
            sw[1] = random.uniform(0, math.pi * 2)

    # ── Decorative bubbles ────────────────────────────────────────────────────
    for bb in G.bubbles:
        bb[1] += bb[3]
        bb[0] += math.sin(G.frame * 0.02 + bb[2]) * 0.3
        if bb[1] < -10:
            bb[0] = random.randint(0, WIDTH)
            bb[1] = HEIGHT + 10
    
    # ── Particles ─────────────────────────────────────────────────────────────
    for p in G.particles:
        p[0] += p[2]
        p[1] += p[3]
        p[4] -= 1
    G.particles = [p for p in G.particles if p[4] > 0]


def _explode(x, y, color):
    for _ in range(10):
        G.particles.append([
            x, y,
            random.uniform(-3, 3), random.uniform(-3, 3),
            random.randint(10, 25),
            color
        ])

# ── Draw ───────────────────────────────────────────────────────────────────────
def draw():
    screen.clear()
    _draw_background()
    _draw_scenery()
    _draw_bubbles()
    _draw_seaweeds()
    _draw_enemies()
    _draw_bullets()
    _draw_particles()
    _draw_player()
    _draw_hud()
    if G.state == "dead":
        _draw_game_over()


def _draw_background():
    # Gradient sky-to-deep using horizontal strips
    for row in range(HEIGHT):
        t   = row / HEIGHT
        r   = int(C_BG_TOP[0] * (1-t) + C_BG_BOT[0] * t)
        g   = int(C_BG_TOP[1] * (1-t) + C_BG_BOT[1] * t)
        b   = int(C_BG_TOP[2] * (1-t) + C_BG_BOT[2] * t)
        screen.draw.line((0, row), (WIDTH, row), (r, g, b))

    # Light rays (animated)
    for i in range(5):
        base_x = (int(G.scroll_x * 0.2) + i * 160) % (WIDTH + 80) - 40
        alpha  = 18 + int(math.sin(G.frame * 0.03 + i) * 8)
        for j in range(3):
            x0 = base_x + j * 6
            screen.draw.line(
                (x0, 0), (x0 + 60, HEIGHT),
                (alpha, alpha + 30, alpha + 80)
            )


def _draw_scenery():
    # Far rocks (darker)
    for r in G.rocks:
        if r[4] == 0:
            screen.draw.filled_rect(
                Rect(r[0], r[1], r[2], r[3]), C_ROCK_DARK
            )
    # Near rocks
    for r in G.rocks:
        if r[4] == 1:
            screen.draw.filled_rect(
                Rect(r[0], r[1], r[2], r[3]), C_ROCK_MID
            )


def _draw_seaweeds():
    for sw in G.seaweeds:
        x0, phase = sw
        y_base = HEIGHT
        seg = 12
        for s in range(seg):
            t   = s / seg
            sway = math.sin(phase + t * 2.5) * 12 * t
            x1  = x0 + sway
            y1  = y_base - s * 8
            x2  = x0 + math.sin(phase + (t+0.08) * 2.5) * 12 * (t+0.08)
            y2  = y_base - (s+1) * 8
            green = max(30, 140 - s * 5)
            screen.draw.line((x1, y1), (x2, y2), (20, green, 60))


def _draw_bubbles():
    for bb in G.bubbles:
        x, y, r, _ = bb
        screen.draw.circle((int(x), int(y)), r, C_BUBBLE)


def _draw_player():
    import pygame
    px, py = 64, int(G.py)
    if G.invincible > 0 and (G.frame // 5) % 2 == 0:
        return

    # Tail fin (animated, chunky & rounded)
    tail_sway = int(math.sin(G.frame * 0.18) * 7)
    _filled_triangle([
        (px - 14, py + tail_sway),
        (px - 32, py - 13 + tail_sway),
        (px - 32, py + 13 + tail_sway),
    ], C_PLAYER_FIN)
    # Round tail tip
    screen.draw.filled_circle((px - 32, py - 13 + tail_sway), 6, C_PLAYER_FIN)
    screen.draw.filled_circle((px - 32, py + 13 + tail_sway), 6, C_PLAYER_FIN)

    # Dorsal fin (cute stubby triangle)
    _filled_triangle([
        (px - 2, py - 17),
        (px + 9,  py - 17),
        (px + 3,  py - 27),
    ], C_PLAYER_FIN)
    screen.draw.filled_circle((px + 3, py - 27), 5, C_PLAYER_FIN)

    # Pectoral fin (little side flipper)
    _filled_triangle([
        (px + 2,  py + 5),
        (px + 14, py + 4),
        (px + 6,  py + 16),
    ], C_PLAYER_FIN)

    # Body — big chubby circle
    screen.draw.filled_circle((px, py), 19, C_PLAYER)

    # Belly highlight (lighter oval)
    screen.draw.filled_circle((px + 4, py + 4), 10, (255, 235, 120))

    # Big kawaii eye
    screen.draw.filled_circle((px + 9, py - 5), 6, (255, 255, 255))
    screen.draw.filled_circle((px + 10, py - 5), 4, (30, 20, 20))
    screen.draw.filled_circle((px + 12, py - 7), 1, (255, 255, 255))  # shine

    # Blush cheek
    pygame.draw.ellipse(screen.surface, (255, 160, 160),
                        pygame.Rect(px + 6, py + 2, 10, 6))

    # Tiny smile
    pygame.draw.arc(screen.surface, (180, 80, 80),
                    pygame.Rect(px + 3, py + 3, 10, 6),
                    math.pi, 2 * math.pi, 2)


def _draw_enemies():
    import pygame
    for e in G.enemies:
        ex, ey = int(e[0]), int(e[1])

        # Tail fin (pointing right, toward player)
        _filled_triangle([
            (ex + 16, ey),
            (ex + 30, ey - 10),
            (ex + 30, ey + 10),
        ], (200, 40, 40))
        screen.draw.filled_circle((ex + 30, ey - 10), 5, (200, 40, 40))
        screen.draw.filled_circle((ex + 30, ey + 10), 5, (200, 40, 40))

        # Chubby body
        screen.draw.filled_circle((ex, ey), 16, C_ENEMY)
        # Belly
        screen.draw.filled_circle((ex - 4, ey + 4), 9, (240, 100, 100))

        # Dorsal spiky fin
        _filled_triangle([
            (ex - 4, ey - 16),
            (ex + 5, ey - 16),
            (ex,     ey - 26),
        ], (180, 30, 30))

        # Big angry eye (white + dark + red brow)
        screen.draw.filled_circle((ex - 6, ey - 4), 6, (255, 255, 255))
        screen.draw.filled_circle((ex - 6, ey - 4), 3, (20, 10, 10))
        screen.draw.filled_circle((ex - 5, ey - 6), 1, (255, 255, 255))
        # Angry eyebrow
        screen.draw.line((ex - 10, ey - 11), (ex - 2, ey - 8), (120, 0, 0))

        # Little frown
        pygame.draw.arc(screen.surface, (120, 20, 20),
                        pygame.Rect(ex - 10, ey + 4, 10, 6),
                        0, math.pi, 2)

        # Spines (3 small spikes around body)
        for angle_deg in [200, 240, 280]:
            angle = math.radians(angle_deg)
            x1 = ex + int(math.cos(angle) * 16)
            y1 = ey + int(math.sin(angle) * 16)
            x2 = ex + int(math.cos(angle) * 23)
            y2 = ey + int(math.sin(angle) * 23)
            screen.draw.line((x1, y1), (x2, y2), (255, 80, 80))


def _draw_bullets():
    for b in G.bullets:
        bx, by = int(b[0]), int(b[1])
        screen.draw.filled_circle((bx, by), 5, C_BULLET)
        screen.draw.circle((bx, by), 7, (180, 220, 255))


def _draw_particles():
    for p in G.particles:
        alpha = max(0, min(255, p[4] * 10))
        r = max(2, p[4] // 4)
        screen.draw.filled_circle((int(p[0]), int(p[1])), r, p[5])


def _draw_hud():
    # Score
    screen.draw.text(
        f"SCORE  {G.score:06d}",
        topleft=(14, 12),
        fontsize=26,
        color=C_UI_TEXT,
        shadow=(0, 1),
        scolor=(0, 30, 80)
    )
    # Hearts / HP
    for i in range(3):
        col = C_HP_GOOD if i < G.hp else C_HP_BAD
        hx = WIDTH - 40 - i * 32
        _draw_heart(hx, 18, col)

    # Controls hint (fades after 5 s)
    if G.frame < 300:
        alpha = 255 if G.frame < 200 else max(0, 255 - (G.frame - 200) * 4)
        screen.draw.text(
            "SPACE = swim up   Z = shoot",
            center=(WIDTH // 2, HEIGHT - 22),
            fontsize=20,
            color=(180, 220, 255),
        )


def _draw_game_over():
    # Dark overlay
    screen.draw.filled_rect(Rect(0, 0, WIDTH, HEIGHT), (0, 0, 30))
    screen.draw.text(
        "GAME OVER",
        center=(WIDTH // 2, HEIGHT // 2 - 40),
        fontsize=64,
        color=(220, 60, 60),
        shadow=(2, 2),
        scolor=(80, 0, 0),
    )
    screen.draw.text(
        f"Final Score: {G.score}",
        center=(WIDTH // 2, HEIGHT // 2 + 20),
        fontsize=36,
        color=C_UI_TEXT,
    )
    screen.draw.text(
        "Press any key to play again",
        center=(WIDTH // 2, HEIGHT // 2 + 65),
        fontsize=22,
        color=(160, 200, 240),
    )


# ── Drawing helpers ────────────────────────────────────────────────────────────
def _filled_triangle(pts, color):
    """Draw a filled triangle given 3 (x,y) tuples."""
    # Use screen.draw.polygon (Pygame Zero / Pygame surface)
    import pygame
    points = [(int(p[0]), int(p[1])) for p in pts]
    pygame.draw.polygon(screen.surface, color, points)


def _draw_heart(cx, cy, color):
    import pygame
    # Simple pixelated heart via two circles + triangle
    pygame.draw.circle(screen.surface, color, (cx - 5, cy),     7)
    pygame.draw.circle(screen.surface, color, (cx + 5, cy),     7)
    pygame.draw.polygon(screen.surface, color, [
        (cx - 12, cy + 4),
        (cx + 12, cy + 4),
        (cx,      cy + 17),
    ])


# ── Run ────────────────────────────────────────────────────────────────────────
pgzrun.go()
