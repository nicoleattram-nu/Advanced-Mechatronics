"""
paddle_graph.py  —  matplotlib force vs angle graph (WINDOW 2)
Live-updating graph that syncs with paddle_field.py

Run alongside paddle_field.py — rotations in field.py appear here in real-time!
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import math
import json
import os

FORCE_MAX = 5.0

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))
fig.suptitle("Force Profile — 3 Bumps & Holes", fontsize=16, fontweight='bold')

# Generate force curve
angles = np.linspace(0, 360, 360)
forces = [FORCE_MAX * 0.5 * (1.0 + math.cos(math.radians(a) * 3)) for a in angles]

# Plot curve
ax.plot(angles, forces, 'c-', linewidth=3, label='Force Profile')
ax.fill_between(angles, 0, forces, alpha=0.2, color='cyan')

# Grid
ax.grid(True, alpha=0.3, linestyle='--', color='gray')
ax.set_xlim(0, 360)
ax.set_ylim(-0.5, FORCE_MAX + 0.5)

# Labels & ticks
ax.set_xlabel('Paddle Angle (degrees)', fontsize=12, fontweight='bold')
ax.set_ylabel('Force (N)', fontsize=12, fontweight='bold')
ax.set_xticks(np.arange(0, 361, 45))
ax.set_yticks(np.arange(0, FORCE_MAX + 1, 1))

# Mark bumps and holes
for bump_angle in [0, 120, 240]:
    ax.axvline(bump_angle, color='red', linestyle=':', alpha=0.5, linewidth=1.5)
    ax.text(bump_angle, FORCE_MAX + 0.2, 'BUMP', ha='center', fontsize=10, color='red', fontweight='bold')

for hole_angle in [60, 180, 300]:
    ax.axvline(hole_angle, color='blue', linestyle=':', alpha=0.5, linewidth=1.5)
    ax.text(hole_angle, -0.3, 'HOLE', ha='center', fontsize=10, color='blue', fontweight='bold')

# Current angle marker (starts at 0)
marker_line = ax.axvline(0, color='yellow', linestyle='-', linewidth=2.5, label='Current Angle')
marker_dot, = ax.plot([0], [FORCE_MAX * 0.5 * (1.0 + math.cos(0))], 'yo', markersize=12, label='Current Force')

ax.legend(loc='upper right', fontsize=11)

# Style
ax.set_facecolor('#0a0e16')
fig.patch.set_facecolor('#0a0e16')
ax.spines['bottom'].set_color('white')
ax.spines['left'].set_color('white')
ax.tick_params(colors='white', labelsize=10)
ax.xaxis.label.set_color('white')
ax.yaxis.label.set_color('white')
ax.title.set_color('white')
for text in ax.get_xticklabels() + ax.get_yticklabels():
    text.set_color('white')

# Animation function
def update_marker(frame):
    """Read angle from file and update marker."""
    try:
        if os.path.exists('paddle_state.json'):
            with open('paddle_state.json', 'r') as f:
                data = json.load(f)
                current_angle = data.get('angle', 0.0)
                current_force = FORCE_MAX * 0.5 * (1.0 + math.cos(math.radians(current_angle) * 3))
                
                marker_line.set_xdata([current_angle, current_angle])
                marker_dot.set_data([current_angle], [current_force])
    except:
        pass
    
    return marker_line, marker_dot

# Run animation (update 30 times per second)
ani = animation.FuncAnimation(fig, update_marker, interval=33, blit=True)

plt.tight_layout()
plt.show()