# WAV Waveform Specification

> Version 1.0 | akai-303 v1.0.0 | 2026-03-31

## 1. Overview

The tool generates two single-cycle WAV files that act as looped oscillators in the MPC keygroup program. When the MPC plays a note, it loops the single-cycle waveform seamlessly, producing a continuous tone at the target pitch. Key tracking transposes the waveform from its root note (C3) across the keyboard.

Implementation: `src/waveform_generator.py`.

## 2. WAV File Properties

| Property | Value |
|---|---|
| Sample rate | 44100 Hz |
| Bit depth | 16-bit signed PCM (little-endian) |
| Channels | 1 (mono) |
| Frame count | 169 samples |
| File size | 382 bytes (44-byte WAV header + 338-byte data) |
| Root note | C3 (MIDI 60, 261.63 Hz) |
| Root frequency | 261.63 Hz |

## 3. Cycle Length Calculation

```
cycle_length = round(sample_rate / root_freq)
             = round(44100 / 261.63)
             = 169 samples
```

Implementation: `_calculate_cycle_length(sample_rate, root_freq) -> int`

For non-default parameters:
- 48000 Hz / 261.63 Hz = 184 samples
- 44100 Hz / 440.0 Hz = 100 samples (A4)

## 4. Sawtooth Algorithm

Linear ramp from -1.0 to +1.0 over one cycle. Produces a rich harmonic spectrum with all harmonics present, matching the TB-303's saw-core VCO.

**Formula**:
```
value[i] = -1.0 + 2.0 * (i / (cycle_len - 1))
sample[i] = int(value[i] * 32767)
```

**Endpoint values** (for 169-sample cycle):
- `sample[0]` = -32767 (exactly)
- `sample[84]` = 0 (midpoint, exactly)
- `sample[168]` = +32767 (exactly)

Implementation: `generate_sawtooth(filepath, sample_rate=44100, root_freq=261.63) -> Path`

## 5. Square Algorithm

Alternating +/- plateaus with 50% duty cycle. The TB-303's square wave is derived from the sawtooth via transistor waveshaping. We use a clean 50% duty cycle with a 1-sample cosine taper at the transition to reduce aliasing.

**Parameters**:
- `amplitude` = 0.95 (slight headroom to avoid clipping)
- `duty` = 0.5 (default)
- `transition_point` = `int(cycle_len * duty)` = 84

**Algorithm**:
```
For each sample index i in [0, cycle_len):
    if i == transition_point - 1:    # index 83
        value = amplitude * cos(π/4)   # ≈ 0.6717 (taper down)
    elif i == transition_point:       # index 84
        value = -amplitude * cos(π/4)  # ≈ -0.6717 (taper down)
    elif i < transition_point:
        value = amplitude               # +0.95
    else:
        value = -amplitude              # -0.95
    sample[i] = int(value * 32767)
```

**Sample values** (for default parameters):
- `sample[0]` through `sample[82]` = 31128 (= `int(0.95 * 32767)`)
- `sample[83]` = 22012 (= `int(0.95 * cos(π/4) * 32767)`) — positive taper
- `sample[84]` = -22012 — negative taper (symmetrical)
- `sample[85]` through `sample[168]` = -31128

**Duty cycle variations**: Non-default duty cycles shift `transition_point`. At duty=0.75, approximately 75% of samples are positive. At duty=0.25, approximately 25% are positive.

Implementation: `generate_square(filepath, sample_rate=44100, root_freq=261.63, duty=0.5) -> Path`

### 5.1 Cosine Taper Bug History

The original implementation used `cos(π/2) ≈ 6.12e-17` (effectively zero) for the taper samples, producing zero-crossing glitches instead of smooth transitions. This was fixed to `cos(π/4) ≈ 0.7071`, which provides proper midpoint interpolation. The regression test is `TestSquareTaper` in `tests/test_waveform_generator.py`.

## 6. Output Files

| File | Waveform | Active in XPM |
|---|---|---|
| `TB303_Saw.WAV` | Sawtooth | Yes (Layer 1, Active=1) |
| `TB303_Square.WAV` | Square | No (Layer 2, Active=0, user-switchable) |

Both files are written to the `{output}/TB-303/Samples/` directory. The uppercase `.WAV` extension is required for MPC compatibility.

Implementation: `generate_all_waveforms(output_dir) -> list[Path]`

## 7. Looping in XPM

The XPM Layer configuration enables seamless looping:

| XPM Tag | Value | Effect |
|---|---|---|
| `LoopStart` | `0` | Loop begins at first sample |
| `LoopEnd` | `169` | Loop ends at last sample |
| `LoopCrossfadeLength` | `0` | No crossfade (single-cycle is inherently seamless) |

## References

- `src/waveform_generator.py` — All generation algorithms
- `tests/test_waveform_generator.py` — TestSquareTaper (regression), TestSawtooth, TestSquare
- `docs/PRD.md` — Section 7 (Waveform Specifications)
