# SVACS Signal & Data Layer

## Acoustic Signal Simulation & Streaming Input Engine

---

## Overview

This project implements the **Signal & Data Layer** of the SVACS (Smart Vessel Acoustic Classification System), responsible for generating **deterministic, interpretable acoustic signals** and feeding them into the downstream intelligence pipeline.

It simulates **real-world underwater acoustic conditions** using synthetic signal generation combined with modeled ocean noise, enabling controlled testing without reliance on restricted datasets.

The system produces **fully labeled, explainable signal scenarios** and streams them in real-time to mimic live acoustic sensor input.

Every signal is traceable to its generation parameters.
Every scenario is labeled with expected behavior.
Every output is structured for downstream pipeline consumption.

---

## Key Features

* Deterministic signal generation (controlled frequency bands, no randomness leakage)
* Synthetic + hybrid signal modeling (vessel signal + ocean noise)
* 5 predefined vessel scenarios (including anomaly & low-confidence cases)
* Real-time streaming simulation (20–50 ms latency)
* FFT-based validation and signal distinguishability checks
* Scenario labeling with confidence levels and pipeline hints
* JSON-based structured output for seamless integration
* Built-in test suite validating all components
* Visualization layer for signal inspection

---

## System Architecture

```
Signal Generator
    → Hybrid Signal Builder (Ocean Noise Layer)
        → Scenario Builder (Label + Metadata Packaging)
            → Streaming Simulator (Real-Time Feed)
                → SVACS Pipeline (Acoustic Node → Samachar → NICAI → Sanskar → State Engine → Dashboard)
```

---

## Project Structure

```
svacs_signal_layer/

├── signal_generator.py         → Synthetic signal generation engine
├── hybrid_signal_builder.py   → Ocean noise + signal fusion layer
├── scenario_builder.py        → Scenario packaging + labeling system
├── streaming_simulator.py     → Real-time signal streaming engine
├── run_tests.py               → Full validation suite

├── utils/
│   └── signal_utils.py        → FFT, statistics, validation, helpers

├── scenarios/                 → Generated scenario JSON files
│   ├── scenario_1_cargo.json
│   ├── scenario_2_speedboat.json
│   ├── scenario_3_submarine.json
│   ├── scenario_4_low_confidence.json
│   ├── scenario_5_anomaly.json
│   └── index.json

├── dataset_notes.md           → Signal design + scenario documentation
└── README.md
```

---

## Signal Design

| Vessel Type    | Frequency Range | Amplitude | Noise Level | Confidence  |
| -------------- | --------------- | --------- | ----------- | ----------- |
| Cargo Ship     | 50–200 Hz       | High      | Low         | High        |
| Speedboat      | 500–1500 Hz     | High      | High        | Medium–High |
| Submarine      | 20–100 Hz       | Low       | Low         | Medium      |
| Low Confidence | Any             | Very Low  | Very High   | Low         |
| Anomaly        | Mixed           | Variable  | Variable    | Unknown     |

Signals are designed to be **clearly separable in frequency space**, enabling reliable downstream classification.

---

## Scenario System

The system generates **5 labeled scenarios**, each representing a distinct operational condition:

| Scenario          | Description                        |
| ----------------- | ---------------------------------- |
| Normal Cargo Ship | Clean, stable low-frequency signal |
| Speedboat         | High-frequency noisy signal        |
| Submarine         | Low-energy stealth signal          |
| Low Confidence    | Weak signal buried in noise        |
| Anomaly           | Multi-frequency irregular pattern  |

Each scenario includes:

* Ground truth labels
* Expected confidence range
* Pipeline hints (detection strength, classification, anomaly flags)
* Fully packaged signal chunk

Example structure:

```json
{
  "scenario_name": "Normal Cargo Ship",
  "labels": {
    "vessel_type": "cargo",
    "expected_confidence": "high",
    "anomaly_flag": false
  },
  "signal": {
    "timestamp": ...,
    "samples": [...],
    "sample_rate": 4000
  }
}
```

---

## How to Run

### 0. Install Dependencies

```bash
pip install numpy matplotlib
```

---

### 1. Run Full Test Suite (Recommended First)

```bash
python run_tests.py
```

Expected:

```
ALL TESTS PASSED
```

This validates:

* Signal generation
* Hybrid noise modeling
* Scenario creation
* Streaming performance
* Frequency correctness
* Visualization

---

### 2. Generate Scenarios

```bash
python scenario_builder.py
```

Output:

```
scenarios/
  scenario_1_cargo.json
  scenario_2_speedboat.json
  scenario_3_submarine.json
  scenario_4_low_confidence.json
  scenario_5_anomaly.json
  index.json
```

---

### 3. Run Streaming Simulator

#### Single Vessel

```bash
python streaming_simulator.py --vessel cargo --duration 10
```

#### All Vessels

```bash
python streaming_simulator.py --vessel all --duration 20
```

#### Full Demo (Recommended)

```bash
python streaming_simulator.py --demo
```

---

## Signal Output Contract

Each emitted chunk follows a strict structure:

```json
{
  "timestamp": float,
  "samples": [float],
  "sample_rate": int,
  "vessel_type": "cargo",
  "metadata": {
    "freq_hz": float,
    "amplitude": float,
    "noise_level": float,
    "confidence_expected": "high",
    "scenario_tag": "normal_cargo"
  }
}
```

---

## Validation & Testing

The system includes a comprehensive validation layer:

* FFT-based dominant frequency detection
* RMS and variance computation
* Signal distinguishability checks
* Rule-based classification validation

Run:

```bash
python run_tests.py
```

---

## Streaming Engine

* Simulates real-time acoustic feed
* Delay: **20–50 ms between chunks**
* Supports:

  * Single vessel streaming
  * Multi-vessel rotation
  * Scenario replay
  * HTTP endpoint integration

---

## Design Principles

* Deterministic signal generation (controlled randomness)
* Clear frequency separation for classification reliability
* No dependency on restricted datasets
* Fully explainable signals and scenarios
* Modular architecture (each layer independently testable)
* Real-time compatibility (stream-first design)

---

## Use Cases

* Acoustic classification system testing
* Anomaly detection pipeline validation
* Real-time signal processing simulation
* Training data generation for ML models
* Demo environment for SVACS pipeline

---

## Future Improvements (Optional)

* Integration with real NOAA ocean noise datasets
* ML-based classification layer
* Live signal visualization dashboard
* REST API ingestion pipeline (Flask/FastAPI)

---

## Summary

This project delivers a **complete acoustic signal simulation system** that:

* Generates realistic vessel signals
* Models ocean noise conditions
* Produces labeled, structured scenarios
* Streams real-time data for pipeline testing

It forms the **input foundation of the SVACS intelligence pipeline**.

---

## Author

Nupur Gavane

---
