# SVACS Signal & Data Layer — Dataset Documentation

---

## Project Overview

This module generates the **input signal layer** for the SVACS pipeline. It feeds realistic, labeled acoustic signals into:

```
Signal Generator
    → Hybrid Builder (+ Ocean Noise)
        → Scenario Packager
            → Streaming Simulator
                → Acoustic Node → Samachar → NICAI → Sanskar → State Engine → Dashboard
```

All signals are **synthetic or hybrid** — no restricted datasets required.

---

## Signal Design

| Vessel Type   | Frequency Range  | Amplitude  | Noise Level | Confidence  |
|---------------|-----------------|------------|-------------|-------------|
| Cargo Ship    | 50–200 Hz        | 0.9–1.1    | 0.05–0.10   | High        |
| Speedboat     | 500–1500 Hz      | 1.0–1.4    | 0.35–0.45   | Medium-High |
| Submarine     | 20–100 Hz        | 0.4–0.6    | 0.03–0.07   | Medium      |
| Low Conf.     | 50–1500 Hz (any) | 0.1–0.2    | 0.5–0.8     | Low         |
| Anomaly       | 10–2000 Hz (mix) | 0.2–1.5    | 0.3         | Unknown     |

---

## Output Schema (Pipeline-Ready)

Every signal chunk emitted by the system conforms to this structure:

```json
{
  "trace_id":    "e27fe3c2-fde8-48f1-accc-94037a05f55d",
  "scenario_id": 1,
  "timestamp":   1718000000.123,
  "samples":     [0.123, -0.045, "...4000 floats..."],
  "sample_rate": 4000,
  "vessel_type": "cargo",
  "expected_label": {
    "vessel_type":      "cargo",
    "confidence_range": [0.80, 1.00],
    "scenario_type":    "normal_classification",
    "anomaly_flag":     false
  },
  "metadata": {
    "freq_hz":             125.4,
    "amplitude":           1.0,
    "noise_level":         0.08,
    "confidence_expected": "high",
    "scenario_tag":        "normal_cargo"
  },
  "hybrid":          true,
  "noise_floor_db":  -18.99,
  "snr_db":          16.3
}
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | UUID4 string | Unique ID per chunk — enables end-to-end tracing through pipeline |
| `scenario_id` | int or null | Links chunk to its source scenario (1–5); null for live-generated |
| `expected_label` | object | Ground truth for downstream validation (NICAI / State Engine) |
| `expected_label.confidence_range` | [float, float] | Numeric min/max confidence the classifier should produce |
| `expected_label.anomaly_flag` | bool | True only for Scenario 5 — triggers anomaly alert path |
| `expected_label.scenario_type` | string | normal_classification / stealth_detection / low_confidence / anomaly |

---

## Scenario Definitions

### Scenario 1: Normal Cargo Ship
**File:** `scenarios/scenario_1_cargo.json`

- Frequency: 50–200 Hz, stable sine wave
- Noise: very low (0.05–0.10)
- Ocean noise overlay: alpha=0.3
- Expected confidence range: [0.80, 1.00]
- Detection: STRONG | Classification: cargo_ship | anomaly_flag: false
- Expected behavior: Classifier should output HIGH confidence, no ambiguity
- Samachar tag: `vessel_detected_high_conf`

---

### Scenario 2: Speedboat — Clear Classification
**File:** `scenarios/scenario_2_speedboat.json`

- Frequency: 500–1500 Hz + 2nd harmonic (freq x2)
- Noise: high (0.35–0.45), fast AM modulation
- Ocean noise overlay: alpha=0.5
- Expected confidence range: [0.65, 0.85]
- Detection: STRONG | Classification: speedboat | anomaly_flag: false
- Expected behavior: High-frequency dominant peak + harmonic confirms speedboat profile
- Samachar tag: `vessel_detected_medium_conf`

---

### Scenario 3: Submarine / Stealth Object
**File:** `scenarios/scenario_3_submarine.json`

- Frequency: 20–100 Hz (very low, near infrasonic)
- Amplitude: 0.4–0.6 with stealth masking factor 0.25–0.60x
- Noise: minimal (0.03–0.07) — stealth signature
- Ocean noise overlay: alpha=0.4, signal_beta=0.8
- Expected confidence range: [0.45, 0.70]
- Detection: WEAK | Classification: submarine | anomaly_flag: false
- Expected behavior: Requires sensitive low-frequency detection. Must NOT dismiss as noise.
- Samachar tag: `stealth_object_detected`

---

### Scenario 4: Low Confidence Signal
**File:** `scenarios/scenario_4_low_confidence.json`

- Frequency: random (50–1500 Hz) — ambiguous
- Amplitude: 0.1–0.2 (very weak)
- Noise: 0.5–0.8 — noise dominates signal completely
- Ocean noise overlay: alpha=1.0, signal_beta=0.3
- Expected confidence range: [0.10, 0.40]
- Detection: UNCERTAIN | Classification: unknown | anomaly_flag: false
- Expected behavior: Pipeline MUST NOT misclassify with high confidence. Output should be UNCERTAIN.
- Samachar tag: `low_confidence_detection`

Simulates: distant vessel, degraded hydrophone, heavy sea state.

---

### Scenario 5: Anomaly — Unknown Pattern
**File:** `scenarios/scenario_5_anomaly.json`

- 3–7 random frequency spikes (10–2000 Hz each)
- Random amplitude bursts at 12 positions (±2.5x)
- Does NOT match any known vessel propulsion profile
- Ocean noise overlay: alpha=0.4
- Expected confidence range: [0.00, 0.30]
- anomaly_flag: **TRUE**
- Anomaly reason: Multi-peak frequency spectrum + burst artifacts do not correspond to any known vessel propulsion signature
- Expected behavior: Pipeline must flag anomaly_flag=True and route to alert path, NOT vessel classification path
- Samachar tag: `anomaly_alert_triggered`

Simulates: unknown object, biologic event (whale), equipment malfunction, jamming.

---

## Running the Project

```bash
pip install numpy matplotlib

python run_tests.py                                        # Full test suite
python scenario_builder.py                                 # Generate 5 scenarios only
python streaming_simulator.py --vessel cargo --duration 10
python streaming_simulator.py --vessel all --duration 30   # Rotate all types
python streaming_simulator.py --demo                       # All 5 scenarios back-to-back
python streaming_simulator.py --vessel cargo --endpoint http://localhost:8000/ingest
```

---

## Success Checklist

- [x] Signals clearly distinguishable (frequency range separation)
- [x] Pipeline can classify deterministically (consistent FFT peaks)
- [x] Low confidence case (Scenario 4)
- [x] Anomaly case (Scenario 5)
- [x] Streaming non-blocking (20–50ms sleep)
- [x] All signals labeled (vessel_type, confidence, scenario_type)
- [x] Ocean noise overlay (pink 1/f + optional NOAA WAV)
- [x] 5 reproducible, documented scenarios
- [x] HTTP transport ready (plug in pipeline endpoint)
- [x] trace_id on every emitted chunk (UUID4)
- [x] expected_label block on every chunk (pipeline-ready schema)
- [x] scenario_id propagated through all layers
- [x] anomaly_reason field on Scenario 5
- [x] expected_behavior documented per scenario
- [x] REVIEW_PACKET.md present in /review_packets/
- [x] example_outputs/ with 2 sample pipeline-ready chunks