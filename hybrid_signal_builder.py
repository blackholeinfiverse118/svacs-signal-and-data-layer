"""
SVACS Hybrid Signal Builder
============================
Combines synthetic vessel signals with a realistic ocean noise floor.

Layer model:
    final_signal = ocean_noise_base + vessel_signal

Ocean noise is synthesised from oceanographic principles:
  - Gaussian background (thermal / shipping)
  - Low-frequency swell (0.1–2 Hz modulation)
  - Tonal interference lines (biologics / distant machinery)

If a real NOAA WAV file is available it can be loaded via
HybridSignalBuilder(noise_file="path/to/noaa_ocean.wav") and the
synthetic floor is replaced automatically.
"""

import numpy as np
import time
import os


class OceanNoiseGenerator:
    """Produces a band-limited synthetic ocean noise floor."""

    def __init__(self, sample_rate: int = 4000, seed: int = None):
        self.sample_rate = sample_rate
        self.rng = np.random.default_rng(seed)

    def generate(self, n_samples: int) -> np.ndarray:
        """Return `n_samples` of ocean noise."""
        t = np.arange(n_samples) / self.sample_rate

        # ── Gaussian background ────────────────────────────────────────
        background = self.rng.normal(0, 0.25, n_samples)

        # ── Low-frequency swell modulation (0.1–1 Hz) ─────────────────
        swell_freq = self.rng.uniform(0.1, 1.0)
        swell = 0.08 * np.sin(2 * np.pi * swell_freq * t)

        # ── Distant shipping tonal lines (50–150 Hz) ───────────────────
        tonal_freq = self.rng.uniform(50, 150)
        tonal = 0.05 * np.sin(2 * np.pi * tonal_freq * t)

        # ── Biologic interference spike ────────────────────────────────
        bio_freq = self.rng.uniform(200, 800)
        bio = 0.04 * np.sin(2 * np.pi * bio_freq * t)

        ocean = background + swell + tonal + bio

        # Normalise to ±0.4 range so vessel signal dominates
        peak = np.max(np.abs(ocean)) or 1.0
        return ocean / peak * 0.4


class HybridSignalBuilder:
    """Wraps SignalGenerator + OceanNoiseGenerator."""

    def __init__(
        self,
        sample_rate: int = 4000,
        duration: float = 1.0,
        noise_file: str = None,
        seed: int = None,
    ):
        # Import here so this module can be used standalone
        from signal_generator import SignalGenerator

        self.generator = SignalGenerator(
            sample_rate=sample_rate, duration=duration, seed=seed
        )
        self.ocean = OceanNoiseGenerator(sample_rate=sample_rate, seed=seed)
        self.noise_file = noise_file
        self._real_noise_cache = None

        if noise_file and os.path.exists(noise_file):
            self._load_real_noise(noise_file)

    # ------------------------------------------------------------------ #
    #  Real noise loading (optional NOAA WAV)                             #
    # ------------------------------------------------------------------ #

    def _load_real_noise(self, path: str):
        """
        Load a real ocean noise WAV file as the base layer.
        Falls back to synthetic if scipy / soundfile is unavailable.
        """
        try:
            import scipy.io.wavfile as wav
            rate, data = wav.read(path)
            if data.ndim > 1:
                data = data[:, 0]           # mono
            data = data.astype(np.float32)
            data /= np.max(np.abs(data)) or 1.0
            self._real_noise_cache = (rate, data)
            print(f"[HybridBuilder] Loaded real noise: {path} ({rate} Hz, {len(data)} samples)")
        except Exception as exc:
            print(f"[HybridBuilder] Could not load noise file ({exc}). Using synthetic noise.")

    def _get_noise_slice(self, n_samples: int) -> np.ndarray:
        """Return n_samples of noise — real or synthetic."""
        if self._real_noise_cache is not None:
            rate, data = self._real_noise_cache
            # Random crop from the file
            if len(data) >= n_samples:
                start = np.random.randint(0, len(data) - n_samples)
                return data[start : start + n_samples] * 0.4
        # Fallback to synthetic
        return self.ocean.generate(n_samples)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def build(self, vessel_type: str) -> dict:
        """
        Build a hybrid signal chunk.

        final_signal = ocean_noise + vessel_signal

        Returns the same signal_chunk format as SignalGenerator but with
        the noise layer baked in and an extra `hybrid` flag.
        """
        chunk = self.generator.generate_chunk(vessel_type)

        vessel_signal = np.array(chunk["samples"])
        ocean_noise   = self._get_noise_slice(len(vessel_signal))
        hybrid        = vessel_signal + ocean_noise

        # Normalize to [-1, 1]
        max_val = np.max(np.abs(hybrid)) or 1.0
        hybrid = hybrid / max_val

        chunk["samples"]        = hybrid.tolist()
        chunk["hybrid"]         = True
        chunk["noise_floor_db"] = round(
            float(20 * np.log10(np.std(ocean_noise) + 1e-9)), 2
        )
        chunk["snr_db"] = round(
            float(20 * np.log10(
                (np.std(vessel_signal) + 1e-9) / (np.std(ocean_noise) + 1e-9)
            )), 2
        )

        return chunk

    def build_batch(self, vessel_type: str, n: int = 10) -> list:
        """Return n consecutive hybrid chunks."""
        return [self.build(vessel_type) for _ in range(n)]


# ------------------------------------------------------------------ #
#  Quick smoke-test                                                    #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    builder = HybridSignalBuilder(seed=7)

    for vtype in ["cargo", "speedboat", "submarine", "low_confidence", "anomaly"]:
        chunk = builder.build(vtype)
        s = chunk["samples"]
        print(
            f"[{vtype:<16}] "
            f"len={len(s):5d}  "
            f"SNR={chunk['snr_db']:+6.1f} dB  "
            f"NoiseFloor={chunk['noise_floor_db']:+6.1f} dB"
        )