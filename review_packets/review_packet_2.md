# SVACS Signal Layer — Review Packet 2
**Author:** Nupur Gavane  
**Task:** Data Layer Integration Readiness / Signal Pipeline Alignment  
**Status:** Complete — All deliverables present

---

## 1. Entry Point

```bash
# Install dependencies
pip install numpy matplotlib

# Run full test suite (recommended first step)
python run_tests.py

# Generate all 5 labeled scenario files
python scenario_builder.py

# Stream signals in real-time (print mode)
python streaming_simulator.py --vessel all --duration 10

# Stream a single vessel type
python streaming_simulator.py --vessel cargo --duration 10

# Replay a saved scenario
python streaming_simulator.py --scenario scenarios/scenario_1_cargo.json

# Full demo (all 5 scenarios back-to-back)
python streaming_simulator.py --demo

# Stream to a live HTTP endpoint
python streaming_simulator.py --vessel cargo --endpoint http://localhost:8000/ingest
```

**Entry file:** `run_tests.py` → validates all 6 components  
**Signal entry point:** `signal_generator.py` → `SignalGenerator.generate_chunk(vessel_type)`  
**Pipeline entry point:** `streaming_simulator.py` → emits structured chunks in real-time

---

## 2. Core Execution Flow (3 Files)

```
signal_generator.py
    → Generates raw synthetic waveform per vessel type
    → Attaches: trace_id, scenario_id, expected_label, metadata
    → Output: pipeline-ready signal_chunk dict

hybrid_signal_builder.py
    → Calls SignalGenerator.generate_chunk()
    → Overlays synthetic ocean noise (OceanNoiseGenerator)
    → Normalizes combined signal to [-1, 1]
    → Adds: snr_db, noise_floor_db, hybrid=True
    → Output: hybrid signal_chunk (trace_id preserved)

streaming_simulator.py
    → Calls HybridSignalBuilder.build() in a timed loop
    → Emits one chunk per 20-50ms (non-blocking)
    → Each chunk has unique trace_id
    → Supports: single vessel, rotation, scenario replay, HTTP transport
```

---

## 3. Live Flow (Signal → Output)

```
SignalGenerator.generate_chunk("cargo")
    ↓
{
  "trace_id": "e27fe3c2-fde8-48f1-accc-94037a05f55d",  ← NEW: UUID per chunk
  "scenario_id": 1,                                      ← NEW: links to scenario
  "timestamp": 1718000000.123,
  "samples": [0.123, -0.045, ... (4000 floats)],
  "sample_rate": 4000,
  "vessel_type": "cargo",
  "expected_label": {                                    ← NEW: pipeline-ready label block
    "vessel_type": "cargo",
    "confidence_range": [0.80, 1.00],
    "scenario_type": "normal_classification",
    "anomaly_flag": false
  },
  "metadata": {
    "freq_hz": 125.4,
    "amplitude": 1.0,
    "noise_level": 0.08,
    "confidence_expected": "high",
    "scenario_tag": "normal_cargo"
  }
}
    ↓ HybridSignalBuilder.build()
{
  ... (all fields above preserved) ...
  "hybrid": true,
  "noise_floor_db": -18.99,
  "snr_db": 16.30
}
    ↓ StreamTransport.send()
[STREAM #0001] trace=e27fe3c2...  vessel=cargo  conf=high  anomaly=False
    ↓
→ Acoustic Node → Samachar → NICAI → Sanskar → State Engine → Dashboard
```

---

## 4. What Was Built in This Task

### Phase 1 — Schema Alignment
Added `trace_id` (UUID4) and `expected_label` block to every signal chunk:
```json
"trace_id": "e27fe3c2-fde8-48f1-accc-94037a05f55d",
"scenario_id": 1,
"expected_label": {
  "vessel_type": "cargo",
  "confidence_range": [0.80, 1.00],
  "scenario_type": "normal_classification",
  "anomaly_flag": false
}
```

### Phase 2 — Signal Output Structuring
`signal_generator.py` now outputs the full pipeline-ready schema on every `generate_chunk()` call. The `expected_label` block is derived deterministically from the vessel type — no manual mapping required downstream.

### Phase 3 — Scenario Standardization
All 5 `scenarios/*.json` files now include:
- `scenario_id` — integer (1–5), matches `signal.scenario_id`
- `description` — human-readable signal description
- `expected_behavior` — what downstream pipeline should do with this signal
- `anomaly_flag` — explicit boolean (True only for Scenario 5)
- `confidence_range` — numeric range, not just a label string
- `labels.expected_vessel_type` — what the classifier should output

### Phase 4 — Streaming Alignment
`streaming_simulator.py` now:
- Prints `trace_id` on every emitted line
- Assigns a fresh `trace_id` per replay emission (scenario replays)
- Shows `anomaly_flag` status on every stream line
- Passes `scenario_id` through to every live-generated chunk

### Phase 5 — Documentation
- `review_packets/review_packet_2.md` — this file
- `example_outputs/example_signal_chunks.json` — 2 sample outputs (cargo + anomaly)
- `dataset_notes.md` — updated with schema changes

---

## 5. Failure Cases

| Failure | Trigger | Behavior |
|---------|---------|----------|
| Unknown vessel_type | `generate_chunk("destroyer")` | `ValueError` with valid type list |
| Missing scenario files | `streaming_simulator.py --demo` before `scenario_builder.py` | Error message, no crash |
| Bad scenario path | `--scenario nonexistent.json` | `[ERROR] File not found` printed |
| No matplotlib | Visualization test | `[SKIP]` — not a hard failure |
| HTTP endpoint unreachable | `--endpoint http://...` | `[HTTP FAIL]` per chunk, stream continues |
| NOAA WAV file missing | `HybridSignalBuilder(noise_file="...")` | Falls back to synthetic noise, logs warning |
| Low confidence misclassification | Scenario 4 reaches classifier | `confidence_range: [0.10, 0.40]` — downstream must not output HIGH confidence |
| Anomaly reaching vessel classifier | Scenario 5 reaches NICAI | `anomaly_flag: true` must trigger alert path, not vessel path |

---

## 6. Proof (Execution Logs)

### Test Suite — ALL PASSED (5/5)
```
============================================================
  TEST RESULTS SUMMARY
============================================================
  ✓ PASS  signal_generator
  ✓ PASS  hybrid_builder
  ✓ PASS  scenario_builder
  ✓ PASS  validation
  ✓ PASS  visualization

  Total: 5/5 passed
  ✅ ALL TESTS PASSED — Pipeline input layer is ready.
```

### Scenario Generation with trace_id
```
[BUILD] Scenario 1: Normal Cargo Ship
  [SAVED] -> scenarios/scenario_1_cargo.json  [trace_id=8e37ef3b...]
[BUILD] Scenario 2: Speedboat -- Clear Classification
  [SAVED] -> scenarios/scenario_2_speedboat.json  [trace_id=5d40d0f0...]
[BUILD] Scenario 3: Submarine / Stealth Object
  [SAVED] -> scenarios/scenario_3_submarine.json  [trace_id=786c63b7...]
[BUILD] Scenario 4: Low Confidence Signal
  [SAVED] -> scenarios/scenario_4_low_confidence.json  [trace_id=2855af18...]
[BUILD] Scenario 5: Anomaly -- Unknown Pattern
  [SAVED] -> scenarios/scenario_5_anomaly.json  [trace_id=fabab7b9...]
```

### Live Stream — trace_id on every chunk
```
[STREAM #0001] trace=998a4972...  vessel=cargo     conf=high         anomaly=False
[STREAM #0002] trace=46be4a10...  vessel=speedboat conf=medium_high  anomaly=False
[STREAM #0003] trace=8dcbd627...  vessel=submarine conf=medium       anomaly=False
[STREAM #0004] trace=ea04fb2b...  vessel=unknown   conf=low          anomaly=False
[STREAM #0005] trace=aedd2022...  vessel=anomaly   conf=unknown      anomaly=True
[STREAM ENDED] 82 chunks in 3.03s
```

### Sample Signal Chunk Schema (cargo)
```json
{
  "trace_id": "e27fe3c2-fde8-48f1-accc-94037a05f55d",
  "scenario_id": 1,
  "timestamp": 1776923510.33,
  "sample_rate": 4000,
  "vessel_type": "cargo",
  "expected_label": {
    "vessel_type": "cargo",
    "confidence_range": [0.8, 1.0],
    "scenario_type": "normal_classification",
    "anomaly_flag": false
  },
  "metadata": {
    "freq_hz": 166.09,
    "amplitude": 1.0,
    "noise_level": 0.08,
    "confidence_expected": "high",
    "scenario_tag": "normal_cargo"
  },
  "hybrid": true,
  "noise_floor_db": -18.99,
  "snr_db": 16.3
}
```

---

## 7. File Index

| File | Purpose |
|------|---------|
| `signal_generator.py` | Core signal synthesis + pipeline-ready schema |
| `hybrid_signal_builder.py` | Ocean noise overlay layer |
| `scenario_builder.py` | Labeled scenario packaging |
| `streaming_simulator.py` | Real-time streaming engine |
| `utils/signal_utils.py` | FFT, stats, validation, rule-based classifier |
| `run_tests.py` | Full validation suite |
| `scenarios/scenario_*.json` | 5 labeled scenario files |
| `scenarios/index.json` | Scenario index manifest |
| `example_outputs/example_signal_chunks.json` | 2 sample pipeline-ready chunks |
| `dataset_notes.md` | Signal design + scenario documentation |
| `review_packets/review_packet_2.md` | This review packet |
