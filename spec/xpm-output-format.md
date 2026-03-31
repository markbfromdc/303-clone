# XPM Output Format Specification

> Version 1.0 | akai-303 v1.0.0 | 2026-03-31

## 1. Overview

The XPM file is an XML-based Akai MPC keygroup program file (File_Version 2.1). It is the primary output of the akai-303 tool. This specification documents the complete XML structure produced by `build_xpm()` in `src/xpm_builder.py`.

**Target compatibility**: MPC OS 3.7.1+ (MPC One, MPC Live, MPC X, MPC Key, Akai Force), MPC 2 Desktop Software.

**File conventions**: UTF-8 encoding, XML declaration required (`<?xml version='1.0' encoding='UTF-8'?>`), 2-space indentation, all floats formatted as `f"{value:.6f}"` (6 decimal places).

## 2. XML Hierarchy

```
MPCVObject                           (root element)
├── Version
│   ├── File_Version                 "2.1"
│   ├── Application                  "MPC"
│   ├── Application_Version          "3.7.1"
│   └── Platform                     "MPC"
└── Program                          (type="Keygroup" attribute)
    ├── ProgramName                  "TB-303"
    ├── AudioRoute
    │   ├── AudioRoute               "2"
    │   ├── AudioRouteSubIndex       "0"
    │   ├── AudioRouteChannelBitmap  "3"
    │   └── InsertsEnabled           "True"
    ├── Send1..Send4                 "0.000000"
    ├── Volume                       "0.707946"
    ├── Mute                         "False"
    ├── Solo                         "False"
    ├── Pan                          "0.500000"
    ├── AutomationFilter             "1"
    ├── Pitch                        "0.000000"
    ├── TuneCoarse                   "0"
    ├── TuneFine                     "0"
    ├── Mono                         "True"
    ├── Program_Polyphony            "1"
    ├── Instruments
    │   └── Instrument               (see Section 3)
    ├── PadNoteMap                   (128 PadNote entries)
    ├── PadGroupMap                  (128 PadGroup entries)
    ├── KeygroupMasterTranspose      "0.500000"
    ├── KeygroupNumKeygroups         "1"
    ├── KeygroupPitchBendRange       "0.500000"
    ├── KeygroupWheelToLfo           "1.000000"
    ├── KeygroupAftertouchToFilter   "0.000000"
    └── QLinkAssignments
        └── ProgramMode
            └── QLink (x16)          (see Section 6)
```

## 3. Instrument (Keygroup) Tag Reference

One Instrument element spanning the full MIDI range. Tags are emitted in the order listed.

### 3.1 Keygroup Basics

| Tag | Type | Default | Description |
|---|---|---|---|
| `LowNote` | int | `0` | Lowest MIDI note |
| `HighNote` | int | `127` | Highest MIDI note |
| `IgnoreBaseNote` | int | `0` | 0=use base note |
| `ZonePlay` | int | `0` | 0=all layers simultaneous |
| `TriggerMode` | int | `0` | Default trigger |
| `OneShot` | int | `0` | 0=looping enabled |

### 3.2 Filter

| Tag | Type | Range | Default | Description |
|---|---|---|---|---|
| `FilterType` | int | 0-29 | `3` | Low Pass 4-pole (24dB/oct) |
| `Cutoff` | float | 0.0-1.0 | `0.250000` | Filter cutoff frequency |
| `Resonance` | float | 0.0-1.0 | `0.400000` | Filter resonance |
| `FilterEnvAmt` | float | 0.0-1.0 | `0.700000` | Envelope-to-filter modulation depth |
| `FilterKeytrack` | float | 0.0-1.0 | `0.000000` | Filter keyboard tracking (0=none) |
| `VelocityToFilter` | float | 0.0-1.0 | `0.400000` | Velocity-to-cutoff sensitivity |
| `VelocityToFilterEnvelope` | float | 0.0-1.0 | `0.250000` | Velocity-to-envelope-depth |

### 3.3 Filter Envelope

| Tag | Type | Range | Default | Description |
|---|---|---|---|---|
| `FilterAttack` | float | 0.0-1.0 | `0.095000` | Attack time (log-normalized) |
| `FilterHold` | float | 0.0-1.0 | `0.000000` | Hold time |
| `FilterDecay` | float | 0.0-1.0 | `0.500000` | Decay time |
| `FilterSustain` | float | 0.0-1.0 | `0.000000` | Sustain level |
| `FilterRelease` | float | 0.0-1.0 | `0.460000` | Release time |
| `FilterAttackCurve` | float | 0.0-1.0 | `0.500000` | 0.5=linear, >0.5=convex |
| `FilterDecayCurve` | float | 0.0-1.0 | `0.700000` | Convex for exponential RC decay |
| `FilterReleaseCurve` | float | 0.0-1.0 | `0.700000` | Convex for exponential release |

### 3.4 Volume Envelope

| Tag | Type | Range | Default | Description |
|---|---|---|---|---|
| `VolumeAttack` | float | 0.0-1.0 | `0.000000` | Attack time |
| `VolumeHold` | float | 0.0-1.0 | `0.000000` | Hold time |
| `VolumeDecay` | float | 0.0-1.0 | `0.720000` | Decay time (~3.5s) |
| `VolumeSustain` | float | 0.0-1.0 | `0.700000` | Sustain level |
| `VolumeRelease` | float | 0.0-1.0 | `0.460000` | Release time |
| `VolumeAttackCurve` | float | 0.0-1.0 | `0.500000` | Linear |
| `VolumeDecayCurve` | float | 0.0-1.0 | `0.600000` | Slightly convex |
| `VolumeReleaseCurve` | float | 0.0-1.0 | `0.500000` | Linear |

### 3.5 Pitch Envelope

| Tag | Type | Range | Default | Description |
|---|---|---|---|---|
| `PitchAttack` | float | 0.0-1.0 | `0.000000` | — |
| `PitchHold` | float | 0.0-1.0 | `0.000000` | — |
| `PitchDecay` | float | 0.0-1.0 | `0.000000` | — |
| `PitchSustain` | float | 0.0-1.0 | `0.500000` | Neutral center |
| `PitchRelease` | float | 0.0-1.0 | `0.000000` | — |
| `PitchEnvAmount` | float | 0.0-1.0 | `0.500000` | Neutral (no modulation) |

### 3.6 Velocity Routing

| Tag | Type | Range | Default | Description |
|---|---|---|---|---|
| `VelocitySensitivity` | float | 0.0-1.0 | `0.600000` | Velocity-to-amplitude |
| `VelocityToStart` | float | 0.0-1.0 | `0.000000` | Not used |
| `VelocityToFilterAttack` | float | 0.0-1.0 | `0.000000` | Not used |
| `VelocityToPitch` | float | 0.0-1.0 | `0.000000` | Not used |
| `VelocityToVolumeAttack` | float | 0.0-1.0 | `0.000000` | Not used |
| `VelocityToPan` | float | 0.0-1.0 | `0.000000` | Not used |
| `AfterTouchToFilter` | float | 0.0-1.0 | `0.000000` | Not used |

### 3.7 LFO

Depth controls (on Instrument element):

| Tag | Type | Range | Default |
|---|---|---|---|
| `LfoPitch` | float | 0.0-1.0 | `0.000000` |
| `LfoCutoff` | float | 0.0-1.0 | `0.000000` |
| `LfoVolume` | float | 0.0-1.0 | `0.000000` |
| `LfoPan` | float | 0.0-1.0 | `0.000000` |

LFO sub-element:

| Tag | Type | Default |
|---|---|---|
| `LFO/Type` | string | `Sine` |
| `LFO/Rate` | float | `0.100000` |
| `LFO/Sync` | int | `0` |
| `LFO/Reset` | bool | `False` |

## 4. Layer Tag Reference

Each Instrument contains a `Layers` element with exactly 4 `Layer` children. Layers 1 (sawtooth, active) and 2 (square, muted) carry sample data. Layers 3-4 are empty.

| Tag | Type | Active Layer | Empty Layer |
|---|---|---|---|
| `Active` | int | `1` or `0` | `0` |
| `Volume` | float | `0.708000` | `0.000000` |
| `Pan` | float | `0.500000` | `0.500000` |
| `Pitch` | float | `0.000000` | `0.000000` |
| `TuneCoarse` | float | `0.000000` | `0.000000` |
| `TuneFine` | float | `0.000000` | `0.000000` |
| `RootNote` | int | `60` (C3) | `60` |
| `KeyTrack` | int | `1` | `1` |
| `VelStart` | int | `0` | `0` |
| `VelEnd` | int | `127` | `127` |
| `SampleName` | string | e.g. `TB303_Saw` | `""` |
| `SampleFile` | string | e.g. `TB303_Saw.WAV` | `""` |
| `SliceIndex` | int | `0` | `0` |
| `SampleStart` | int | `0` | `0` |
| `SampleEnd` | int | `169` | `0` |
| `LoopStart` | int | `0` | `0` |
| `LoopEnd` | int | `169` | `0` |
| `LoopCrossfadeLength` | int | `0` | `0` |
| `LoopTune` | int | `0` | `0` |
| `Direction` | int | `0` | `0` |
| `Offset` | int | `0` | `0` |

## 5. PadNoteMap and PadGroupMap

**PadNoteMap**: 128 `PadNote` entries, each containing a `Note` element with values 0-127 (identity mapping).

**PadGroupMap**: 128 `PadGroup` entries, each containing a `Group` element with value `0`.

## 6. Q-Link Assignment Format

```xml
<QLinkAssignments>
  <ProgramMode>
    <QLink index="1">
      <Parameter>94</Parameter>
      <Momentary>0</Momentary>
    </QLink>
    <!-- ...16 total entries... -->
  </ProgramMode>
</QLinkAssignments>
```

- `index` attribute: 1-16
- `Parameter`: MIDI CC number, or `2147483647` for unassigned
- `Momentary`: `0` (latching) or `1` (momentary)

## 7. MPC Compatibility Notes

- Sample filenames MUST use uppercase `.WAV` extension
- The MPC XML parser tolerates unknown tags (ignores them without error)
- Portamento tags (`PortamentoTime`, `PortamentoLegato`) are undocumented in XPM 2.1 and not included
- Insert effects cannot be embedded in XPM files — they are stored at the project/track level
- The XPM file and referenced WAV samples should be in the same expansion directory structure

## References

- `src/xpm_builder.py` — `_build_instrument()` (lines 352-459), `_build_layer()` (lines 264-306), `_build_program_header()` (lines 231-261)
- [MPCIC](https://github.com/plule/MPCIC) — Reference XPM template
- [ConvertWithMoss](https://github.com/git-moss/ConvertWithMoss) — XPM tag names and structure
