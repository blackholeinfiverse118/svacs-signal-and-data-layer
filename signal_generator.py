"""
SVACS Signal Generator
======================
Generates synthetic acoustic signals for 3 base vessel types + 2 special cases:
  - Cargo Ship      : 50–200 Hz, stable, low noise
  - Speedboat       : 500–1500 Hz, irregular, high noise
  - Submarine       : 20–100 Hz, low energy, partially masked
  - Low Confidence  : weak amplitude + dominant noise (any freq)
  - Anomaly         : multi-frequency spike pattern, bursts, no vessel match

Output format per chunk:
  {
    "timestamp": float,
    "samples": [float, ...],
    "sample_rate": int,
    "vessel_type": str,
    "metadata": {
        "freq_hz": float,
        "amplitude": float,
        "noise_level": float,
        "confidence_expected": str,
        "scenario_tag": str,
        ...vessel-specific fields
    }
  }
"""

import numpy as np
import time


class SignalGenerator:
    def __init__(self, sample_rate: int = 4000, duration: float = 1.0, seed: int = None):
        """
        Args:
            sample_rate : samples per second (4000 Hz → covers 0–2000 Hz Nyquist range)
            duration    : chunk length in seconds
            seed        : optional random seed for reproducibility
        """
        self.sample_rate = sample_rate
        self.duration = duration
        self.rng = np.random.default_rng(seed)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _time_axis(self) -> np.ndarray:
        n = int(self.sample_rate * self.duration)
        return np.linspace(0, self.duration, n, endpoint=False)

    def _sine_wave(self, freq: float, amplitude: float) -> np.ndarray:
        t = self._time_axis()
        return amplitude * np.sin(2 * np.pi * freq * t)

    def _noise(self, level: float, size: int) -> np.ndarray:
        return level * self.rng.standard_normal(size)

    def _amplitude_modulate(self, signal: np.ndarray, mod_depth: float = 0.1) -> np.ndarray:
        """Slow AM envelope to simulate engine rhythm."""
        t = self._time_axis()
        mod = 1.0 + mod_depth * np.sin(2 * np.pi * 0.5 * t)
        return signal * mod

    # ── Vessel profiles ───────────────────────────────────────────────────────

    def cargo_ship(self) -> dict:
        """
        Low frequency (50–200 Hz), stable waveform, low noise.
        Large, slow-moving surface vessel. Clear FFT peak.
        """
        freq      = float(self.rng.uniform(50, 200))
        amplitude = 1.0
        noise_lvl = 0.08

        signal = self._sine_wave(freq, amplitude)
        signal = self._amplitude_modulate(signal, mod_depth=0.05)
        signal += self._noise(noise_lvl, len(signal))

        return {
            "vessel_type": "cargo",
            "metadata": {
                "freq_hz":              round(freq, 2),
                "amplitude":            amplitude,
                "noise_level":          noise_lvl,
                "confidence_expected":  "high",
                "scenario_tag":         "normal_cargo"
            },
            "samples": signal
        }

    def speedboat(self) -> dict:
        """
        High frequency (500–1500 Hz), noisy, irregular waveform.
        Fast small craft with high-RPM engine. Includes 2nd harmonic.
        """
        freq      = float(self.rng.uniform(500, 1500))
        amplitude = 1.2
        noise_lvl = 0.45

        signal  = self._sine_wave(freq, amplitude)
        signal  = self._amplitude_modulate(signal, mod_depth=0.25)
        signal += self._noise(noise_lvl, len(signal))
        signal += 0.3 * self._sine_wave(freq * 2, amplitude)   # 2nd harmonic

        return {
            "vessel_type": "speedboat",
            "metadata": {
                "freq_hz":              round(freq, 2),
                "harmonic_hz":          round(freq * 2, 2),
                "amplitude":            amplitude,
                "noise_level":          noise_lvl,
                "confidence_expected":  "medium_high",
                "scenario_tag":         "speedboat_clear"
            },
            "samples": signal
        }

    def submarine(self) -> dict:
        """
        Very low frequency (20–100 Hz), low energy, partially masked signal.
        Stealth / quiet underwater vessel.
        """
        freq      = float(self.rng.uniform(20, 100))
        amplitude = 0.4
        noise_lvl = 0.04

        signal = self._sine_wave(freq, amplitude)
        signal = self._amplitude_modulate(signal, mod_depth=0.02)

        mask = float(self.rng.uniform(0.25, 0.60))
        signal *= mask
        signal += self._noise(noise_lvl, len(signal))

        return {
            "vessel_type": "submarine",
            "metadata": {
                "freq_hz":              round(freq, 2),
                "amplitude":            round(amplitude * mask, 4),
                "noise_level":          noise_lvl,
                "mask_factor":          round(mask, 3),
                "confidence_expected":  "medium",
                "scenario_tag":         "submarine_stealth"
            },
            "samples": signal
        }

    def low_confidence(self) -> dict:
        """
        Weak signal (0.1–0.2 amplitude) + dominant noise (0.5–0.8).
        Ambiguous — could be any vessel at distance or degraded sensor.
        """
        freq      = float(self.rng.uniform(80, 600))
        amplitude = float(self.rng.uniform(0.1, 0.2))
        noise_lvl = float(self.rng.uniform(0.5, 0.8))

        signal = self._sine_wave(freq, amplitude)
        signal += self._noise(noise_lvl, len(signal))

        return {
            "vessel_type": "unknown",
            "metadata": {
                "freq_hz":              round(freq, 2),
                "amplitude":            round(amplitude, 4),
                "noise_level":          round(noise_lvl, 4),
                "confidence_expected":  "low",
                "scenario_tag":         "low_confidence_noisy"
            },
            "samples": signal
        }

    def anomaly(self) -> dict:
        """
        Mixed multi-frequency spikes + random amplitude bursts.
        Matches NO vessel profile → triggers anomaly flag in pipeline.
        """
        t = self._time_axis()
        n = len(t)

        freqs  = self.rng.uniform(30, 2000, size=5)
        signal = np.zeros(n)
        for f in freqs:
            signal += float(self.rng.uniform(0.1, 0.8)) * np.sin(2 * np.pi * f * t)

        # Burst spikes at random positions
        spike_pos = self.rng.integers(0, n, size=12)
        for sp in spike_pos:
            signal[sp] += float(self.rng.choice([-2.5, 2.5]))

        signal += self._noise(0.5, n)

        return {
            "vessel_type": "anomaly",
            "metadata": {
                "freq_hz":              "mixed",
                "component_freqs_hz":   [round(float(f), 2) for f in freqs],
                "amplitude":            "variable",
                "noise_level":          0.5,
                "confidence_expected":  "unknown",
                "scenario_tag":         "anomaly_unknown_pattern"
            },
            "samples": signal
        }

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_chunk(self, vessel_type: str) -> dict:
        """
        Generate a timestamped signal_chunk for the given vessel type.

        Args:
            vessel_type: 'cargo' | 'speedboat' | 'submarine'
                         | 'low_confidence' | 'anomaly'

        Returns:
            signal_chunk dict — SVACS pipeline format
        """
        dispatch = {
            "cargo":          self.cargo_ship,
            "speedboat":      self.speedboat,
            "submarine":      self.submarine,
            "low_confidence": self.low_confidence,
            "anomaly":        self.anomaly,
        }

        if vessel_type not in dispatch:
            raise ValueError(
                f"Unknown vessel_type '{vessel_type}'. "
                f"Choose from: {list(dispatch.keys())}"
            )

        raw = dispatch[vessel_type]()
        samples = raw.pop("samples")

        return {
            "timestamp":   time.time(),
            "samples":     samples.tolist(),
            "sample_rate": self.sample_rate,
            "vessel_type": raw.get("vessel_type", vessel_type),
            "metadata":    raw.get("metadata", {})
        }


# ── Quick smoke-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    gen = SignalGenerator(seed=42)

    for vtype in ["cargo", "speedboat", "submarine", "low_confidence", "anomaly"]:
        chunk = gen.generate_chunk(vtype)
        s = chunk["samples"]
        print(
            f"[{vtype:<16}] "
            f"n={len(s):5d}  "
            f"min={min(s):+.4f}  max={max(s):+.4f}  "
            f"conf={chunk['metadata'].get('confidence_expected'):<12}  "
            f"tag={chunk['metadata'].get('scenario_tag')}"
        )