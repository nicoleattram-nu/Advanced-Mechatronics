"""
HW14: HX711 Load Cell Data Analysis
Sends sample count to Pico, collects data, plots raw vs filtered,
and performs FFT analysis.
"""

import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fft, fftfreq
import os

# ── Configuration ──────────────────────────────────────────────────────────
PICO_PORT = "/dev/cu.usbmodem1101"  # ← change to your port
BAUD = 115200
NUM_SAMPLES = 400  # ~20 seconds at 20Hz

# ── Create HW14 directory ──────────────────────────────────────────────────
os.makedirs("HW14", exist_ok=True)

print("=" * 60)
print("HW14: HX711 Load Cell Data Collection & Analysis")
print("=" * 60)

# ── Connect to Pico ────────────────────────────────────────────────────────
try:
    ser = serial.Serial(PICO_PORT, BAUD, timeout=5)
    print(f"✓ Connected to Pico on {PICO_PORT}")
    time.sleep(2)
except Exception as e:
    print(f"✗ Failed to connect: {e}")
    exit(1)

# ── Send command to collect samples ────────────────────────────────────────
print(f"\nRequesting {NUM_SAMPLES} samples from Pico...")
cmd = f"COLLECT {NUM_SAMPLES}\n"
ser.write(cmd.encode())

# ── Wait for data and parse ────────────────────────────────────────────────
raw_data = []
filtered_data = []
time_data = []
t_start = None
collecting = False

try:
    while len(raw_data) < NUM_SAMPLES:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        
        if "DATA_START" in line:
            collecting = True
            print("Receiving data...")
            continue
        
        if "DATA_END" in line:
            collecting = False
            print(f"✓ Collected {len(raw_data)} samples")
            break
        
        if collecting and "," in line:
            try:
                parts = line.split(",")
                raw = int(parts[0])
                filt = int(parts[1])
                t_ms = int(parts[2])
                
                if t_start is None:
                    t_start = t_ms
                
                raw_data.append(raw)
                filtered_data.append(filt)
                time_data.append((t_ms - t_start) / 1000.0)  # convert to seconds
                
                if len(raw_data) % 50 == 0:
                    print(f"  {len(raw_data)}/{NUM_SAMPLES}")
            except:
                pass

except KeyboardInterrupt:
    print("\nInterrupted by user")
except Exception as e:
    print(f"Error: {e}")
finally:
    ser.close()

if len(raw_data) == 0:
    print("No data received!")
    exit(1)

# Convert to numpy arrays
raw = np.array(raw_data, dtype=np.float32)
filtered = np.array(filtered_data, dtype=np.float32)
time_s = np.array(time_data, dtype=np.float32)

# ── Calculate sample rate and Nyquist frequency ────────────────────────────
dt = np.mean(np.diff(time_s))
fs = 1.0 / dt  # sample rate
nyquist = fs / 2.0

print(f"\nData Statistics:")
print(f"  Sample rate: {fs:.2f} Hz")
print(f"  Nyquist frequency: {nyquist:.2f} Hz")
print(f"  Duration: {time_s[-1]:.2f} s")
print(f"  Raw range: [{raw.min():.0f}, {raw.max():.0f}]")
print(f"  Filtered range: [{filtered.min():.0f}, {filtered.max():.0f}]")

# ── Compute FFT ────────────────────────────────────────────────────────────
print("\nComputing FFTs...")

# FFT of raw signal
fft_raw = fft(raw - np.mean(raw))
freq_raw = fftfreq(len(raw), dt)

# FFT of filtered signal
fft_filtered = fft(filtered - np.mean(filtered))
freq_filtered = fftfreq(len(filtered), dt)

# Power spectral density (take positive frequencies only)
idx_pos = freq_raw > 0
power_raw = np.abs(fft_raw[idx_pos]) ** 2
power_filtered = np.abs(fft_filtered[idx_pos]) ** 2
freq_pos = freq_raw[idx_pos]

# ── Create figures ─────────────────────────────────────────────────────────
print("Creating plots...")

# Figure 1: Time domain data
fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

ax1.plot(time_s, raw, 'b-', label='Raw', alpha=0.7, linewidth=1)
ax1.plot(time_s, filtered, 'r-', label='IIR Filtered (α=0.32)', alpha=0.8, linewidth=2)
ax1.set_xlabel('Time (s)', fontsize=12)
ax1.set_ylabel('ADC Value', fontsize=12)
ax1.set_title('HX711 Load Cell: Raw vs Filtered Data', fontsize=14, fontweight='bold')
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3)

# Zoomed in view
start_idx = len(raw) // 4
end_idx = start_idx + 200
ax2.plot(time_s[start_idx:end_idx], raw[start_idx:end_idx], 'b-', label='Raw', alpha=0.7, linewidth=1.5)
ax2.plot(time_s[start_idx:end_idx], filtered[start_idx:end_idx], 'r-', label='Filtered', alpha=0.8, linewidth=2)
ax2.set_xlabel('Time (s)', fontsize=12)
ax2.set_ylabel('ADC Value', fontsize=12)
ax2.set_title('Zoomed View (Middle Section)', fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
fig1.savefig('HW14/01_timeseries.png', dpi=150, bbox_inches='tight')
print("✓ Saved: 01_timeseries.png")
plt.close(fig1)

# Figure 2: FFT comparison
fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(12, 8))

# Linear scale
ax3.semilogy(freq_pos, power_raw, 'b-', label='Raw', alpha=0.7, linewidth=1.5)
ax3.semilogy(freq_pos, power_filtered, 'r-', label='Filtered', alpha=0.8, linewidth=2)
ax3.axvline(25, color='orange', linestyle='--', linewidth=2, label='Touch Noise (25-30 Hz)')
ax3.axvline(30, color='orange', linestyle='--', linewidth=2)
ax3.set_xlabel('Frequency (Hz)', fontsize=12)
ax3.set_ylabel('Power (log scale)', fontsize=12)
ax3.set_title('FFT: Power Spectral Density', fontsize=14, fontweight='bold')
ax3.set_xlim([0, 40])
ax3.legend(fontsize=11)
ax3.grid(True, alpha=0.3, which='both')

# Zoomed on problem frequency
ax4.semilogy(freq_pos, power_raw, 'b-', label='Raw', alpha=0.7, linewidth=2)
ax4.semilogy(freq_pos, power_filtered, 'r-', label='Filtered', alpha=0.8, linewidth=2.5)
ax4.axvline(25, color='orange', linestyle='--', linewidth=2, label='Touch Noise')
ax4.axvline(30, color='orange', linestyle='--', linewidth=2)
ax4.axvline(nyquist, color='green', linestyle=':', linewidth=2, label=f'Nyquist ({nyquist:.1f} Hz)')
ax4.set_xlabel('Frequency (Hz)', fontsize=12)
ax4.set_ylabel('Power (log scale)', fontsize=12)
ax4.set_title('Zoomed: 15-40 Hz', fontsize=12)
ax4.set_xlim([15, 40])
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3, which='both')

plt.tight_layout()
fig2.savefig('HW14/02_fft_comparison.png', dpi=150, bbox_inches='tight')
print("✓ Saved: 02_fft_comparison.png")
plt.close(fig2)

# Figure 3: Filter attenuation at 25-30Hz
fig3, ax5 = plt.subplots(figsize=(10, 6))

# Calculate attenuation ratio
attenuation = power_filtered / (power_raw + 1e-10)
ax5.semilogy(freq_pos, attenuation, 'purple', linewidth=2.5, label='Attenuation Ratio')
ax5.axvline(25, color='orange', linestyle='--', linewidth=2, label='Touch Noise (25-30 Hz)')
ax5.axvline(30, color='orange', linestyle='--', linewidth=2)
ax5.axhline(0.5, color='green', linestyle=':', linewidth=1.5, label='-3dB (0.5)')
ax5.fill_between([25, 30], 1e-4, 10, alpha=0.15, color='red', label='Noise Band')
ax5.set_xlabel('Frequency (Hz)', fontsize=12)
ax5.set_ylabel('Power Ratio (Filtered / Raw)', fontsize=12)
ax5.set_title('IIR Filter Attenuation Performance', fontsize=14, fontweight='bold')
ax5.set_xlim([0, 40])
ax5.set_ylim([1e-3, 2])
ax5.legend(fontsize=11)
ax5.grid(True, alpha=0.3, which='both')

plt.tight_layout()
fig3.savefig('HW14/03_attenuation.png', dpi=150, bbox_inches='tight')
print("✓ Saved: 03_attenuation.png")
plt.close(fig3)

# ── Print summary statistics ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("FILTER PERFORMANCE SUMMARY")
print("=" * 60)

# Find peak power in noise band (25-30 Hz)
noise_mask = (freq_pos >= 25) & (freq_pos <= 30)
raw_noise_power = np.max(power_raw[noise_mask]) if np.any(noise_mask) else 0
filt_noise_power = np.max(power_filtered[noise_mask]) if np.any(noise_mask) else 0

if raw_noise_power > 0:
    attenuation_db = 10 * np.log10(filt_noise_power / raw_noise_power)
    print(f"Noise @ 25-30 Hz:")
    print(f"  Raw power: {raw_noise_power:.2e}")
    print(f"  Filtered power: {filt_noise_power:.2e}")
    print(f"  Attenuation: {attenuation_db:.1f} dB")
else:
    print("No significant noise detected in 25-30 Hz band")

print(f"\nFilter parameters:")
print(f"  Type: First-order IIR low-pass")
print(f"  Alpha (α): 0.32")
print(f"  Cutoff frequency: ~15 Hz")
print(f"  Sample rate: {fs:.1f} Hz")

print("\n✓ Analysis complete! Check HW14/ folder for plots.")
print("=" * 60)

plt.show()