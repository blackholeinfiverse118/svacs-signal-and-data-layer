"""
SVACS Hybrid Signal Builder
============================
Combines synthetic vessel signals with a realistic ocean noise floor.

Layer model:
    final_signal = ocean_noise_base + vessel_signal

Ocean noise is synthesised from oceanographic principles:
  - Gaussian background (thermal / shipping)
  - Low-frequency swell (0.1-2 Hz modulation)
  - Tonal interference lines (biologics / distant machinery)

If a real NOAA WAV file is available it can be loaded via
HybridSignalBuilder(noise_file="path/to/noaa_ocean.wav").
"""

import numpy as np
import time
import os


class OceanNoiseGenerator:
    def __init__(self, sample_rate: int = 4000, seed: int = None):
        self.sample_rate = sample_rate
        self.rng = np.random.default_rng(seed)

    def generate(self, n_samples: int) -> np.ndarray:
        t = np.arange(n_samples) / self.sample_rate
        background = self.rng.normal(0, 0.25, n_samples)
        swell_freq = self.rng.uniform(0.1, 1.0)
        swell = 0.08 * np.sin(2 * np.pi * swell_freq * t)
        tonal_freq = self.rng.uniform(50, 150)
        tonal = 0.05 * np.sin(2 * np.pi * tonal_freq * t)
        bio_freq = self.rng.uniform(200, 800)
        bio = 0.04 * np.sin(2 * np.pi * bio_freq * t)
        ocean = background + swell + tonal + bio
        peak = np.max(np.abs(ocean)) or 1.0
        return ocean / peak * 0.4


class HybridSignalBuilder:
    def __init__(self, sample_rate: int = 4000, duration: float = 1.0,
                 noise_file: str = None, seed: int = None):
        from signal_generator import SignalGenerator
        self.generator = SignalGenerator(sample_rate=sample_rate, duration=duration, seed=seed)
        self.ocean = OceanNoiseGenerator(sample_rate=sample_rate, seed=seed)
        self.noise_file = noise_file
        self._real_noise_cache = None
        if noise_file and os.path.exists(noise_file):
            self._load_real_noise(noise_file)

    def _load_real_noise(self, path: str):
        try:
            import scipy.io.wavfile as wav
            rate, data = wav.read(path)
            if data.ndim > 1:
                data = data[:, 0]
            data = data.astype(np.float32)
            data /= np.max(np.abs(data)) or 1.0
            self._real_noise_cache = (rate, data)
            print(f"[HybridBuilder] Loaded real noise: {path} ({rate} Hz, {len(data)} samples)")
        except Exception as exc:
            print(f"[HybridBuilder] Could not load noise file ({exc}). Using synthetic noise.")

    def _get_noise_slice(self, n_samples: int) -> np.ndarray:
        if self._real_noise_cache is not None:
            rate, data = self._real_noise_cache
            if len(data) >= n_samples:
                start = np.random.randint(0, len(data) - n_samples)
                return data[start: start + n_samples] * 0.4
        return self.ocean.generate(n_samples)

    def build(self, vessel_type: str, scenario_id: int = None) -> dict:
        """
        Build a hybrid signal chunk with pipeline-ready schema.
        Passes scenario_id through for full traceability.

        final_signal = ocean_noise + vessel_signal
        """
        chunk = self.generator.generate_chunk(vessel_type, scenario_id=scenario_id)

        vessel_signal = np.array(chunk["samples"])
        ocean_noise   = self._get_noise_slice(len(vessel_signal))
        hybrid        = vessel_signal + ocean_noise

        max_val = np.max(np.abs(hybrid)) or 1.0
        hybrid = hybrid / max_val

        chunk["samples"]        = hybrid.tolist()
        chunk["hybrid"]         = True
        chunk["noise_floor_db"] = round(float(20 * np.log10(np.std(ocean_noise) + 1e-9)), 2)
        chunk["snr_db"]         = round(float(20 * np.log10(
            (np.std(vessel_signal) + 1e-9) / (np.std(ocean_noise) + 1e-9)
        )), 2)

        return chunk

    def build_batch(self, vessel_type: str, n: int = 10) -> list:
        return [self.build(vessel_type) for _ in range(n)]


if __name__ == "__main__":
    builder = HybridSignalBuilder(seed=7)
    for vtype in ["cargo", "speedboat", "submarine", "low_confidence", "anomaly"]:
        chunk = builder.build(vtype)
        s = chunk["samples"]
        print(
            f"[{vtype:<16}] len={len(s):5d}  trace={chunk['trace_id'][:8]}...  "
            f"SNR={chunk['snr_db']:+6.1f} dB  NoiseFloor={chunk['noise_floor_db']:+6.1f} dB"
        )