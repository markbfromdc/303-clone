# TB-303 Parameter Mapping Specification

> Version 1.0 | akai-303 v1.0.0 | 2026-03-31

## 1. Overview

This specification documents how analog circuit behaviors of the Roland TB-303 Bass Line synthesizer are approximated using static MPC XPM keygroup parameters. Each mapping includes the TB-303 circuit behavior, the chosen XPM value, and the rationale for the approximation.

All parameter values are defined in the `TB303Params` dataclass in `src/xpm_builder.py`.

## 2. Envelope Time Normalization

MPC XPM envelope times are stored as normalized 0.0-1.0 floats using logarithmic scaling.

**Formula** (from ConvertWithMoss):
```
normalized = ln(seconds / 0.001) / ln(100000)
```

Equivalently: `ln(seconds / min_s) / ln(max_s / min_s)` where min_s=0.001, max_s=100.0.

**Clamping**: Input seconds are clamped to [0.001, 100.0] before normalization.

**Implementation**: `normalize_env_time()` in `src/xpm_builder.py`.

**Reference values**:

| Physical Time | Normalized | TB-303 Context |
|---|---|---|
| 0.001s (1ms) | 0.000 | Minimum |
| 0.003s (3ms) | 0.095 | Filter attack |
| 0.060s (60ms) | 0.366 | Slide/portamento |
| 0.200s (200ms) | 0.460 | Accent decay, filter release |
| 0.300s (300ms) | 0.496 | Mid-range filter decay |
| 1.000s (1s) | 0.601 | — |
| 2.000s (2s) | 0.661 | Max filter decay |
| 3.500s (3.5s) | 0.710 | VCA decay |
| 100.0s | 1.000 | Maximum |

## 3. Filter (VCF) Mapping

The TB-303 uses a 4-pole diode ladder filter with a mismatched first-pole capacitor (C18=0.18uF vs 0.33uF for poles 2-4), creating an effective ~18dB/oct slope. It does not self-oscillate; high resonance produces saturation/overdrive.

| XPM Tag | Value | TB-303 Behavior | Rationale |
|---|---|---|---|
| `FilterType` | `3` | 4-pole diode ladder ~18dB/oct | Low Pass 4-pole (24dB/oct) is the closest MPC filter. No 18dB option exists. |
| `Cutoff` | `0.250000` | ~500Hz midpoint, range ~210Hz-2.5kHz | Normalized mid-range starting point |
| `Resonance` | `0.400000` | Non-self-oscillating, saturates at high values | Reduced from typical 0.45+ to compensate for 24dB/oct being steeper than ~18dB/oct |
| `FilterEnvAmt` | `0.700000` | Heavy positive envelope-to-filter modulation | Core of the "squelch" sound. Increased for stronger character. |
| `FilterKeytrack` | `0.000000` | No keyboard tracking (stock 303) | Filter cutoff is fixed regardless of pitch — lower notes darker, higher notes brighter |

## 4. Filter Envelope (MEG) Mapping

The TB-303's Main Envelope Generator has ~3ms attack, 200ms-2000ms variable decay, no sustain, and uses RC circuit exponential curves.

| XPM Tag | Value | TB-303 Value | Notes |
|---|---|---|---|
| `FilterAttack` | `0.095000` | ~3ms | `normalize_env_time(0.003) = 0.095` |
| `FilterHold` | `0.000000` | None | No hold stage |
| `FilterDecay` | `0.500000` | ~300ms (mid-range) | Adjustable 200ms-2000ms on 303; accented notes fixed at 200ms |
| `FilterSustain` | `0.000000` | 0 | 303 filter envelope has no sustain |
| `FilterRelease` | `0.460000` | ~200ms | Matches accent decay time |
| `FilterAttackCurve` | `0.500000` | Linear snap | 0.5 = linear |
| `FilterDecayCurve` | `0.700000` | RC circuit exponential | >0.5 = convex (fast initial decay, slow tail). Key 303 character. |
| `FilterReleaseCurve` | `0.700000` | RC circuit exponential | Same convex shape as decay |

## 5. Volume Envelope (VEG) Mapping

The TB-303's Volume Envelope Generator has instant attack and a fixed ~3.5 second decay. This creates the characteristic "pluck from filter, sustain from VCA" behavior — the timbral envelope (filter) is fast and snappy while the amplitude envelope is slow and gentle.

| XPM Tag | Value | TB-303 Value | Notes |
|---|---|---|---|
| `VolumeAttack` | `0.000000` | Instant | Immediate gate open |
| `VolumeHold` | `0.000000` | None | — |
| `VolumeDecay` | `0.720000` | ~3.5 seconds | `normalize_env_time(3.5) ≈ 0.710`. Long gate-like decay. |
| `VolumeSustain` | `0.700000` | Held level | Level maintained during gate |
| `VolumeRelease` | `0.460000` | ~200ms | Quick release after note-off |
| `VolumeAttackCurve` | `0.500000` | Linear | — |
| `VolumeDecayCurve` | `0.600000` | Slightly convex | Smooth exponential VCA decay |
| `VolumeReleaseCurve` | `0.500000` | Linear | — |

## 6. Pitch Envelope

The stock TB-303 has no dedicated pitch envelope. All pitch parameters are set to neutral.

**Neutral convention**: `PitchSustain=0.500000` and `PitchEnvAmount=0.500000` together produce zero pitch modulation. The 0.5 center point means "no offset from base pitch."

| XPM Tag | Value | Notes |
|---|---|---|
| `PitchAttack` | `0.000000` | — |
| `PitchHold` | `0.000000` | — |
| `PitchDecay` | `0.000000` | — |
| `PitchSustain` | `0.500000` | Neutral center |
| `PitchRelease` | `0.000000` | — |
| `PitchEnvAmount` | `0.500000` | Neutral center (no modulation) |

## 7. Velocity / Accent Routing

The TB-303's accent is binary (on/off per step) and triggers three simultaneous effects: filter cutoff sweep, VCA boost, and deeper envelope sweep. MIDI velocity is used to approximate this multi-path behavior.

| XPM Tag | Value | Accent Path | Effect |
|---|---|---|---|
| `VelocityToFilter` | `0.400000` | Filter cutoff | Higher velocity = brighter (filter opens) |
| `VelocitySensitivity` | `0.600000` | VCA amplitude | Higher velocity = louder |
| `VelocityToFilterEnvelope` | `0.250000` | Envelope depth | Higher velocity = deeper filter sweep |

**Unused velocity destinations** (all `0.000000`):
`VelocityToStart`, `VelocityToFilterAttack`, `VelocityToPitch`, `VelocityToVolumeAttack`, `VelocityToPan`, `AfterTouchToFilter`.

## 8. LFO

The LFO is off by default (all depth values 0.0). It is available for the user to enable via Q-Link for slow filter sweeps or vibrato.

| XPM Tag | Value | Notes |
|---|---|---|
| `LFO/Type` | `Sine` | Clean modulation waveform |
| `LFO/Rate` | `0.100000` | Very slow rate as default |
| `LFO/Sync` | `0` | Free-running (not tempo-synced) |
| `LFO/Reset` | `False` | No reset per note trigger |
| `LfoPitch` | `0.000000` | Off (user-configurable) |
| `LfoCutoff` | `0.000000` | Off (user-configurable) |
| `LfoVolume` | `0.000000` | Off |
| `LfoPan` | `0.000000` | Off |

## 9. Q-Link Assignments

Q-Links provide real-time knob control on MPC hardware. Parameter IDs map to MIDI CC numbers.

| Q-Link | Parameter ID | CC | Control | Notes |
|---|---|---|---|---|
| Q1 | 94 | CC#94 | Cutoff | Brightness/filter cutoff |
| Q2 | 71 | CC#71 | Resonance | Filter resonance |
| Q3 | 2147483647 | — | Unassigned | Use Q-Link Learn for Filter Env Amt |
| Q4 | 2147483647 | — | Unassigned | Use Q-Link Learn for Filter Decay |
| Q5 | 7 | CC#7 | Volume | Master volume |
| Q6 | 10 | CC#10 | Pan | Stereo pan |
| Q7-Q16 | 2147483647 | — | Unassigned | — |

`2147483647` (`QLINK_UNASSIGNED`) is the MPC firmware sentinel for "no parameter assigned."

## 10. Limitations and Compromises

| Limitation | Cause | Mitigation |
|---|---|---|
| Filter slope 24dB/oct vs 303's ~18dB/oct | MPC has no 18dB filter mode | Reduced resonance (0.40) to soften the steeper slope; AIR Tube Drive recommended for saturation |
| No portamento in XPM | Portamento tags are undocumented in XPM 2.1 | Manual setup: Program Edit > PORTA/MOD > Time=30, Legato=On |
| No insert effects in XPM | Insert FX stored at project/track level, not in XPM | Manual setup: AIR Tube Drive (Drive=30%, Tone=50%, Mix=100%) |
| No accent stacking | 303's capacitor charge accumulation requires dynamic state | Velocity programming in sequencer approximates consecutive accents |
| No filter self-oscillation | 303 doesn't self-oscillate either; it saturates | AIR Tube Drive provides the overdrive character |

## References

- `src/xpm_builder.py` — TB303Params dataclass (lines 43-207), `normalize_env_time()` (lines 22-36)
- `docs/PRD.md` — Sections 5-6 (TB-303 Technical Reference, Parameter Mapping Table)
- [ConvertWithMoss](https://github.com/git-moss/ConvertWithMoss) — Envelope normalization formula source
- [TB-303 Unique Characteristics — Robin Whittle](https://www.firstpr.com.au/rwi/dfish/303-unique.html)
