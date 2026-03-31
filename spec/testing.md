# Testing Specification

> Version 1.0 | akai-303 v1.0.0 | 2026-03-31

## 1. Overview

The test suite uses pytest and covers unit tests, structural validation, boundary testing, regression tests, and integration tests. All tests use Python standard library assertions plus pytest fixtures and helpers.

## 2. Running Tests

```bash
python -m pytest tests/ -v
```

**Expected result**: 80 tests, ~0.2s execution time.

**Dependencies**: `pytest>=7.0` (the only external dependency in the project).

## 3. Test File Inventory

| File | Tests | Classes | Focus |
|---|---|---|---|
| `test_waveform_generator.py` | 23 | 7 | WAV file generation, sample values, algorithms |
| `test_xpm_builder.py` | 53 | 13 | XPM XML structure, parameters, tag validation |
| `test_integration.py` | 4 | 2 | End-to-end CLI, cross-module consistency |

## 4. Test Classes

### test_waveform_generator.py

| Class | Tests | Validates |
|---|---|---|
| `TestCycleLength` | 2 | `_calculate_cycle_length()` for C3 (169) and A4 (100) |
| `TestSawtooth` | 5 | WAV validity, properties (44100Hz/16-bit/mono/169 frames), ramp direction, .WAV extension, exact endpoint values (-32767, +32767) |
| `TestSquare` | 5 | WAV validity, properties, peak amplitudes (>30000), frame count, exact plateau values (31128) |
| `TestSquareTaper` | 3 | **Regression**: Taper samples nonzero, between zero and peak, symmetrical. Prevents reintroduction of the `cos(π/2)≈0` bug. |
| `TestSquareDutyCycle` | 2 | 75% duty has more positive samples; 25% duty has more negative |
| `TestCustomParameters` | 3 | Custom sample rate (48kHz), custom root freq (440Hz A4), square at 48kHz |
| `TestGenerateAll` | 3 | Both waveforms generated, correct filenames, directory creation |

### test_xpm_builder.py

| Class | Tests | Validates |
|---|---|---|
| `TestNormalizeEnvTime` | 8 | Log normalization at min/max, TB-303 reference times (3ms, 200ms, 2s, 3.5s), clamping |
| `TestBuildXpm` | 14 | Root element, version, program type/name, filter type, all float params in [0.0, 1.0], sample references, root note, layer active/inactive, loop points, pad note map, custom param override |
| `TestMonoMode` | 3 | Mono=True at program level, Program_Polyphony=1, poly mode override |
| `TestFilterKeytrack` | 1 | FilterKeytrack=0.0 |
| `TestEnvelopeCurves` | 3 | All 6 curve params in [0.0, 1.0], FilterDecayCurve>0.5 (convex), FilterReleaseCurve>0.5 |
| `TestVelocityRouting` | 3 | VelocitySensitivity set (>0), VelocityToFilterEnvelope set (>0), AfterTouchToFilter=0 |
| `TestLFO` | 3 | LFO section exists with Type=Sine, LfoCutoff defaults to 0.0, all LFO depths zero |
| `TestQLinkAssignments` | 5 | Section exists, 16 entries, Q1=94 (cutoff), Q2=71 (resonance), unassigned=2147483647 |
| `TestPadGroupMap` | 2 | 128 entries, all Group=0 |
| `TestInsertsEnabled` | 2 | InsertsEnabled=True, AudioRoute section exists |
| `TestXpmParamBounds` | 5 | Cutoff at 0.0 and 1.0, resonance at 0.0 and 1.0, all params at zero boundary |
| `TestWriteXpm` | 4 | Valid XML on disk, parent dir creation, XML declaration, roundtrip structure preservation |

### test_integration.py

| Class | Tests | Validates |
|---|---|---|
| `TestCLI` | 2 | `main()` generates all 3 output files; custom --cutoff/--resonance reflected in XPM |
| `TestXpmWavConsistency` | 2 | XPM SampleFile references match generated WAV filenames; LoopEnd matches WAV frame count |

## 5. Test Categories

| Category | Description | Example |
|---|---|---|
| **Unit** | Pure function correctness | `normalize_env_time(0.003) ≈ 0.095` |
| **Structural** | XPM XML tags exist with correct nesting | `FilterType` tag present under `Instrument` |
| **Behavioral** | Parameter values match TB-303 design intent | `FilterDecayCurve > 0.5` (convex) |
| **Boundary** | Edge case parameter values | All params at 0.0 produce valid XPM |
| **Regression** | Prevents reintroduction of fixed bugs | `TestSquareTaper` — cosine taper nonzero |
| **Integration** | End-to-end execution with cross-module validation | CLI generates files, XPM references match WAVs |

## 6. Test Conventions

- **File I/O**: All tests use `tmp_path` or `tmp_output` fixtures (pytest-provided temp directories). No tests write to the project's `output/` directory.
- **Float comparison**: `pytest.approx(value, abs=tolerance)` for float equality.
- **CLI testing**: `unittest.mock.patch("sys.argv", [...])` to inject CLI arguments into `main()`.
- **WAV reading**: `wave.open()` + `struct.unpack()` to read back and verify sample values.
- **XML parsing**: `xml.etree.ElementTree` for XPM structure validation.

## References

- `tests/test_waveform_generator.py` — 23 tests across 7 classes
- `tests/test_xpm_builder.py` — 53 tests across 13 classes
- `tests/test_integration.py` — 4 tests across 2 classes
- `CLAUDE.md` — Test commands: `python -m pytest tests/ -v`
