# SVACS Signal & Data Layer

## Acoustic Signal Simulation & Streaming Input Engine

---

## Overview

This project implements the **Signal & Data Layer** of the SVACS (Smart Vessel Acoustic Classification System), responsible for generating **deterministic, interpretable acoustic signals** and feeding them into the downstream intelligence pipeline.

It simulates **real-world underwater acoustic conditions** using synthetic signal generation combined with modeled ocean noise, enabling controlled testing without reliance on restricted datasets.

Every signal is traceable via a unique `trace_id`.
Every scenario is labeled with expected behavior and confidence range.
Every output chunk is structured for direct ingestion by the Acoustic Node and Samachar pipeline.

---

## Key Features

- Deterministic signal generation (controlled frequency bands, no randomness leakage)
- Synthetic + hybrid signal modeling (vessel signal + ocean noise overlay)
- 5 predefined vessel scenarios (including anomaly & low-confidence cases)
- Real-time streaming simulation (20–50 ms latency)
- FFT-based validation and signal distinguishability checks
- Full traceability via UUID4 `trace_id` on every emitted chunk
- Pipeline-ready `expected_label` block for downstream validation
- JSON-based structured output for seamless integration
- Built-in test suite validating all 6 components
- Visualization layer for signal inspection

---

## System Architecture

```
Signal Generator
    → Hybrid Signal Builder (Ocean Noise Layer)
        → Scenario Builder (Label + Metadata Packaging)
            → Streaming Simulator (Real-Time Feed)
                → SVACS Pipeline
                    → Acoustic Node → Samachar → NICAI → Sanskar → State Engine → Dashboard
```

---

## Project Structure

```
svacs_signal_layer/

├── signal_generator.py           → Synthetic signal generation engine
├── hybrid_signal_builder.py      → Ocean noise + signal fusion layer
├── scenario_builder.py           → Scenario packaging + labeling system
├── streaming_simulator.py        → Real-time signal streaming engine
├── run_tests.py                  → Full validation suite (6 tests)

├── utils/
│   └── signal_utils.py           → FFT, statistics, validation, rule-based classifier

├── scenarios/                    → Generated scenario JSON files
│   ├── scenario_1_cargo.json
│   ├── scenario_2_speedboat.json
│   ├── scenario_3_submarine.json
│   ├── scenario_4_low_confidence.json
│   ├── scenario_5_anomaly.json
│   └── index.json

├── example_outputs/              → Sample pipeline-ready signal chunks
│   └── example_signal_chunks.json

├── review_packets/               → Integration review documentation
│   └── review_packet_2.md

├── plots/                        → Signal visualization outputs (auto-generated)
│   ├── signal_cargo.png
│   ├── signal_speedboat.png
│   ├── signal_submarine.png
│   ├── signal_low_confidence.png
│   └── signal_anomaly.png

├── dataset_notes.md              → Signal design + scenario documentation
└── README.md
```

---

## Signal Design

| Vessel Type    | Frequency Range  | Amplitude  | Noise Level | Confidence  |
|----------------|------------------|------------|-------------|-------------|
| Cargo Ship     | 50–200 Hz        | High       | Low         | High        |
| Speedboat      | 500–1500 Hz      | High       | High        | Medium–High |
| Submarine      | 20–100 Hz        | Low        | Low         | Medium      |
| Low Confidence | Any (50–1500 Hz) | Very Low   | Very High   | Low         |
| Anomaly        | Mixed (10–2000 Hz)| Variable  | Variable    | Unknown     |

Signals are designed to be **clearly separable in frequency space**, enabling reliable downstream classification.

---

## Signal Output Contract

Every chunk emitted by the system conforms to this pipeline-ready schema:

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
  "hybrid":         true,
  "noise_floor_db": -18.99,
  "snr_db":         16.3
}
```

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | UUID4 string | Unique ID per chunk — enables end-to-end tracing through the pipeline |
| `scenario_id` | int or null | Links chunk to its source scenario (1–5); null for live-generated chunks |
| `expected_label` | object | Ground truth for downstream validation (NICAI / State Engine) |
| `expected_label.confidence_range` | [float, float] | Numeric min/max confidence the classifier should produce |
| `expected_label.anomaly_flag` | bool | True only for Scenario 5 — triggers anomaly alert path |
| `expected_label.scenario_type` | string | `normal_classification` / `stealth_detection` / `low_confidence` / `anomaly` |
| `hybrid` | bool | True when ocean noise overlay has been applied |
| `snr_db` | float | Signal-to-noise ratio in decibels |
| `noise_floor_db` | float | Ocean noise floor level in decibels |

---

## Scenario System

The system generates **5 labeled scenarios**, each representing a distinct operational condition:

| # | Scenario           | Description                          | Confidence  | Anomaly  |
|---|--------------------|--------------------------------------|-------------|----------|
| 1 | Normal Cargo Ship  | Clean, stable low-frequency signal   | High        | False    |
| 2 | Speedboat          | High-frequency noisy signal          | Medium–High | False    |
| 3 | Submarine          | Low-energy stealth signal            | Medium      | False    |
| 4 | Low Confidence     | Weak signal buried in noise          | Low         | False    |
| 5 | Anomaly            | Multi-frequency irregular pattern    | Unknown     | **True** |

Each scenario JSON contains:

- `scenario_id` — integer (1–5)
- `description` — human-readable signal description
- `expected_behavior` — what the downstream pipeline should do with this signal
- `labels.anomaly_flag` — explicit boolean
- `labels.confidence_range` — numeric range [min, max]
- `pipeline_hints` — detection strength, classification tag, Samachar event tag

---

## How to Run

### 0. Install Dependencies

```bash
pip install numpy matplotlib
```

### 1. Run Full Test Suite (Recommended First)

```bash
python run_tests.py
```

Expected output:

```
  [PASS]  signal_generator
  [PASS]  hybrid_builder
  [PASS]  scenario_builder
  [PASS]  streaming
  [PASS]  validation
  [PASS]  visualization

  Total: 6/6 passed
  ALL TESTS PASSED — Pipeline input layer is ready.
```

### 2. Generate Scenarios Only

```bash
python scenario_builder.py
```

Saves all 5 labeled scenario JSON files into `scenarios/` with `trace_id` logged per file.

### 3. Run Streaming Simulator

```bash
# Single vessel type, 10 seconds
python streaming_simulator.py --vessel cargo --duration 10

# Rotate through all vessel types
python streaming_simulator.py --vessel all --duration 20

# Full demo — all 5 scenarios back-to-back
python streaming_simulator.py --demo

# Replay a saved scenario file
python streaming_simulator.py --scenario scenarios/scenario_1_cargo.json

# Stream to a live HTTP endpoint
python streaming_simulator.py --vessel cargo --endpoint http://localhost:8000/ingest

# Suppress output
python streaming_simulator.py --vessel submarine --duration 5 --quiet
```

---

## Validation & Testing

The test suite covers 6 components:

1. **Signal Generator** — all 5 vessel types, correct sample count and schema fields
2. **Hybrid Builder** — noise overlay, normalization to [-1, 1], SNR computation
3. **Scenario Builder** — all 5 scenarios saved with required labeling fields
4. **Streaming Simulator** — real-time loop, trace_id present on every chunk
5. **Signal Validation** — FFT frequency range checks for cargo, speedboat, submarine
6. **Visualization** — signal plots saved to `plots/`

A **distinguishability check** also runs automatically at the end, confirming clear frequency separation between vessel types so the downstream classifier can reliably tell them apart.

---

## Failure Cases

The pipeline handles these conditions explicitly:

| Condition | Behavior |
|-----------|----------|
| Missing required schema field | Rejected by `validate_chunk()` in signal_utils.py |
| Low SNR (Scenario 4) | Classifier outputs LOW confidence, no vessel type assigned |
| No dominant frequency in known band | Anomaly detection triggered, routed to alert path |
| Multi-peak burst pattern (Scenario 5) | `anomaly_flag=True`, Samachar tag: `anomaly_alert_triggered` |
| Signal amplitude too weak | Classified as `low_confidence`, NOT misclassified as a vessel |

---

## Streaming Engine

- Simulates real-time acoustic feed at sensor input
- Delay: **20–50 ms between chunks** (randomized)
- Every chunk carries a unique `trace_id` (UUID4)
- Supports: single vessel, multi-vessel rotation, scenario replay, HTTP endpoint transport

---

## Design Principles

- Deterministic signal generation (controlled randomness via seeded RNG)
- Clear frequency separation between vessel types for classification reliability
- No dependency on restricted or proprietary datasets
- Fully explainable signals — every parameter is documented
- Modular architecture — each layer is independently testable
- Real-time compatibility — stream-first design
- Full traceability from generation through pipeline ingestion via `trace_id`

---

## Future Improvements (Optional)

- Integration with real NOAA ocean noise datasets (WAV loader already supported)
- ML-based classification layer on top of rule-based validator
- Live signal visualization dashboard
- REST API ingestion pipeline (Flask/FastAPI)

---

## Author

Nupur Gavane