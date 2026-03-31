# Product Requirements Document: TB-303 Emulation for Akai MPC

## 1. Overview

This project creates a Python tool that generates an Akai MPC-compatible XPM keygroup program file emulating the Roland TB-303 Bass Line synthesizer. The tool produces a single optimized preset with programmatically generated single-cycle waveforms (sawtooth and square) and an XML-based XPM file with TB-303 parameters carefully mapped to MPC equivalents.

## 2. Goals

- Produce an authentic TB-303 sound approximation using MPC keygroup program parameters
- Generate single-cycle WAV waveforms (sawtooth, square) for alias-free bass synthesis
- Output a valid XPM file that loads on MPC OS 3.7.1+ hardware without errors
- Use only Python standard library (no external runtime dependencies)

## 3. Non-Goals

- Not a real-time DSP plugin or audio processor
- Not a multi-preset generator (single optimized preset only)
- Not a full MPC expansion pack (no sequences, no additional programs)
- Does not replicate the TB-303's internal sequencer behavior

## 4. Target Platform

- Akai MPC OS 3.7.1+ (MPC One, MPC Live, MPC X, MPC Key 61/37, Akai Force)
- XPM File Version: 2.1
- Compatible with MPC 2 Desktop Software

## 5. TB-303 Technical Reference

### 5.1 Oscillator (VCO)
- Single saw-core VCO; square wave derived via transistor waveshaping
- Bass range: C1 (65.41 Hz) base pitch, ~1 octave sequencer range
- Monophonic, no keyboard tracking to filter

### 5.2 Filter (VCF)
- 4-pole diode ladder (2SC536F transistors as diodes), effectively ~18 dB/oct
- Pole 1 uses 0.18 uF capacitor vs 0.33 uF for poles 2-4 (the defining "flaw")
- Cutoff range: ~210 Hz to ~2.5 kHz (knob only), up to ~4 kHz with envelope
- Does NOT self-oscillate; high resonance produces overdrive/saturation instead
- No keyboard tracking (stock unit)

### 5.3 Envelopes
- **Filter Envelope (MEG)**: ~3ms attack, 200ms-2000ms decay (normal), fixed 200ms (accented), no sustain
- **Volume Envelope (VEG)**: Instant attack, fixed ~3-4 second decay, ~16ms note-end

### 5.4 Accent
- Binary (on/off per step), not velocity
- Shortens filter decay to 200ms, boosts VCA, sweeps filter cutoff up
- Consecutive accents stack (capacitor charge accumulation)

### 5.5 Slide
- Fixed 60ms constant-time portamento in pitch-scale (logarithmic)
- Anticipatory: begins sliding into next step before trigger

### 5.6 Distortion
- Soft clipping in VCA/output amplifier, level-dependent
- Volume knob position controls saturation amount

## 6. TB-303 → MPC Parameter Mapping

### 6.1 Envelope Time Normalization

MPC XPM uses 0.0-1.0 normalized values for envelope times. The conversion formula (from ConvertWithMoss):

```
normalized = ln(seconds / 0.001) / ln(100000)
```

Reference values:
| Physical Time | Normalized |
|---|---|
| 0.001s (min) | 0.000 |
| 0.003s (303 filter attack) | 0.095 |
| 0.060s (303 slide) | 0.366 |
| 0.200s (303 accent decay) | 0.460 |
| 0.300s | 0.496 |
| 2.000s (303 max filter decay) | 0.661 |
| 3.500s (303 VCA decay) | 0.710 |
| 100.0s (max) | 1.000 |

### 6.2 Complete Parameter Table

| TB-303 Parameter | TB-303 Value | XPM Tag | XPM Value | Rationale |
|---|---|---|---|---|
| VCO Sawtooth | Single-cycle 44.1kHz/16-bit | Layer 1 SampleFile | TB303_Saw.WAV | Root note C3 (MIDI 60), 169 samples |
| VCO Square | Single-cycle 44.1kHz/16-bit | Layer 2 SampleFile | TB303_Square.WAV | Muted by default (Active=0), switchable |
| VCF Type | 4-pole diode ladder ~18dB/oct | FilterType | 3 (Low 4) | 4-pole 24dB/oct LP, closest MPC approximation |
| VCF Cutoff | ~500Hz (midpoint) | Cutoff | 0.250000 | Normalized, mid-range starting point |
| VCF Resonance | Moderate, no self-oscillation | Resonance | 0.400000 | Reduced to compensate for 24dB/oct being steeper than 303's ~18dB/oct |
| VCF Env Amount | Heavy positive modulation | FilterEnvAmt | 0.700000 | Increased for stronger squelch |
| Filter Attack | ~3ms | FilterAttack | 0.095000 | normalize_env_time(0.003) = 0.095 for 3ms |
| Filter Hold | 0 | FilterHold | 0.000000 | No hold stage |
| Filter Decay | ~300ms (mid-range) | FilterDecay | 0.500000 | Log-normalized, adjustable sweet spot |
| Filter Sustain | 0 (no sustain) | FilterSustain | 0.000000 | 303 filter envelope has no sustain |
| Filter Release | ~200ms | FilterRelease | 0.460000 | Matches accent decay time |
| VCA Attack | Instant | VolumeAttack | 0.000000 | Immediate gate open |
| VCA Hold | 0 | VolumeHold | 0.000000 | No hold stage |
| VCA Decay | ~3.5 seconds | VolumeDecay | 0.720000 | Long gate-like decay |
| VCA Sustain | 0.7 | VolumeSustain | 0.700000 | Held level during gate |
| VCA Release | ~200ms | VolumeRelease | 0.460000 | Quick release |
| Accent → Filter | Velocity-mapped | VelocityToFilter | 0.400000 | More prominent accent effect, harder velocity = brighter |
| Voice Mode | Monophonic | Mono | True | 303 is single-voice |
| Program Polyphony | 1 voice | Program_Polyphony | 1 | Enforces mono at program level |
| Slide/Portamento | 60ms constant-time | _(manual setup)_ | _(see 10.5)_ | Must be set manually on MPC (XPM 2.1 portamento tags undocumented) |
| Filter Keytrack | None (stock 303) | FilterKeytrack | 0.000000 | 303 has no filter keyboard tracking |
| Filter Decay Curve | RC circuit (exponential) | FilterDecayCurve | 0.700000 | Convex/exponential curve for RC character |
| Filter Release Curve | RC circuit (exponential) | FilterReleaseCurve | 0.700000 | Convex/exponential curve for RC character |
| VCA Decay Curve | Gradual taper | VolumeDecayCurve | 0.600000 | Smooth exponential VCA decay |
| VCA Velocity Sens | Accent boosts VCA | VelocitySensitivity | 0.600000 | VCA boost on accented (high velocity) notes |
| Accent → Filter Env | Deeper sweep on accent | VelocityToFilterEnvelope | 0.250000 | Velocity increases filter envelope depth |
| LFO Shape | Sine | LFO_Shape | Sine | Default sine, off by default |
| LFO Rate | Slow | LFO_Rate | 0.100000 | Low rate, user-configurable |
| LFO → Pitch | Off | LFO_PitchDepth | 0.000000 | All LFO depths off by default |
| LFO → Cutoff | Off | LFO_CutoffDepth | 0.000000 | User-configurable modulation target |
| LFO → Volume | Off | LFO_VolumeDepth | 0.000000 | User-configurable modulation target |

### 6.3 Q-Link Assignments

| Q-Link | CC | Parameter |
|---|---|---|
| Q1 | 94 | Cutoff |
| Q2 | 71 | Resonance |
| Q3 | — | Unassigned |
| Q4 | — | Unassigned |
| Q5 | 7 | Volume |
| Q6 | 10 | Pan |
| Q7 | — | Unassigned |
| Q8 | — | Unassigned |

### 6.4 Program-Level Configuration

- **PadGroupMap**: 128 entries, all Group 0
- **AudioRoute**: InsertsEnabled=True (for post-load AIR FX insertion)
- **Program header**: Volume, Pan, and audio routing configuration included

### 6.5 Keygroup Configuration

- **1 keygroup** spanning full MIDI range (LowNote=0, HighNote=127)
- **Layer 1**: Sawtooth (Active=1, RootNote=60, full velocity range 0-127)
- **Layer 2**: Square (Active=0, muted, same mapping — user can switch)
- **Layers 3-4**: Empty
- **Loop**: Full single-cycle (LoopStart=0, LoopEnd=169) for seamless oscillator

## 7. Waveform Specifications

| Property | Value |
|---|---|
| Sample Rate | 44100 Hz |
| Bit Depth | 16-bit signed PCM |
| Channels | 1 (mono) |
| Root Frequency | 261.63 Hz (C3, MIDI 60) |
| Cycle Length | round(44100 / 261.63) = 169 samples |
| File Extension | .WAV (uppercase for MPC compatibility) |

### 7.1 Sawtooth Generation
Linear ramp from -1.0 to +1.0 over 169 samples:
```
sample[i] = -1.0 + 2.0 * (i / (cycle_len - 1))
```

### 7.2 Square Generation
Values of +0.95 / -0.95 with 50% duty cycle. 1-sample cosine taper at transitions to reduce aliasing:
```
sample[i] = +0.95 if i < cycle_len/2 else -0.95
```
With smooth taper at transition points.

## 8. XPM File Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MPCVObject>
  <Version>
    <File_Version>2.1</File_Version>
    <Application>MPC</Application>
    <Application_Version>3.7.1</Application_Version>
    <Platform>MPC</Platform>
  </Version>
  <Program type="Keygroup">
    <ProgramName>TB-303</ProgramName>
    <Instruments>
      <Instrument>
        <!-- Filter, Envelope, Layer configuration -->
      </Instrument>
    </Instruments>
  </Program>
</MPCVObject>
```

## 9. Output Directory Structure

```
output/TB-303/
├── Samples/
│   ├── TB303_Saw.WAV
│   └── TB303_Square.WAV
└── Programs/
    └── TB-303.xpm
```

## 10. Acceptance Criteria

1. **XPM Validity**: Generated XPM file is well-formed XML parseable by `xml.etree.ElementTree`
2. **XPM Structure**: Root element is `MPCVObject`, contains `Version` (File_Version=2.1) and `Program` (type=Keygroup)
3. **Parameter Ranges**: All normalized float parameters are within 0.0-1.0
4. **WAV Validity**: Generated WAV files are valid, parseable by Python `wave` module
5. **WAV Properties**: 44100 Hz, 16-bit, mono, 169 samples per file
6. **Sample References**: XPM `SampleFile` tags match actual generated WAV filenames
7. **Filter Configuration**: FilterType=3, Cutoff/Resonance/EnvAmt set to specified values
8. **Layer Configuration**: Layer 1 active (sawtooth), Layer 2 inactive (square), RootNote=60
9. **Mono Mode**: Program has Mono=True and Program_Polyphony=1
10. **Envelope Curves**: FilterDecayCurve=0.70, FilterReleaseCurve=0.70, VolumeDecayCurve=0.60 present
11. **Q-Link Assignments**: Q1 (Cutoff/CC94), Q2 (Resonance/CC71), Q5 (Volume/CC7), Q6 (Pan/CC10) mapped
12. **Filter Keytrack**: FilterKeytrack=0.0 explicitly set
13. **Velocity Routing**: VelocitySensitivity=0.60 and VelocityToFilterEnvelope=0.25 present
14. **Tests Pass**: All pytest tests pass with no failures
15. **CLI Runs**: `python src/main.py --output output/` completes without errors

### 10.5 Post-Load Manual Setup

The following parameters cannot be embedded in XPM 2.1 files and must be configured manually on the MPC after loading the program:

#### Portamento (Slide)
1. Navigate to **Program Edit > PORTA/MOD**
2. Set **Portamento Time = 30**
3. Set **Legato = On**
4. This approximates the 303's 60ms constant-time slide between notes

XPM 2.1 portamento tags are undocumented and not reliably parsed by MPC firmware.

#### Insert Effects (Saturation/Overdrive)
1. Open **Channel Mixer > Inserts** for the program's audio track
2. Add **AIR Tube Drive** effect:
   - Drive = 30%
   - Tone = 50%
   - Mix = 100%
3. This provides the 303's characteristic saturation and overdrive at high resonance settings

Insert effects cannot be embedded in XPM files; they are stored at the project/track level.

## 11. Known Limitations

- **Portamento**: Must be set manually after loading (see Section 10.5); XPM 2.1 portamento tags are undocumented
- **Insert effects**: AIR Tube Drive must be added manually for 303-style saturation (see Section 10.5); insert FX cannot be stored in XPM files
- **Filter slope**: MPC's Low 4 is 24dB/oct vs TB-303's effective ~18dB/oct; resonance reduced to 0.40 to compensate but no exact match available
- **Accent stacking**: The TB-303's capacitor-based accent accumulation across consecutive accented steps cannot be replicated via static XPM parameters; requires sequencer-level velocity programming
- **Filter keytrack**: Explicitly set to 0.0 to match the 303's lack of keyboard tracking

## 12. References

- [TB-303 Unique Characteristics — Robin Whittle](https://www.firstpr.com.au/rwi/dfish/303-unique.html)
- [Tim Stinchcombe — TB-303 Diode Ladder Filter](https://www.timstinchcombe.co.uk/index.php?pge=diode2)
- [MPCIC — MPC Keygroup Generator](https://github.com/plule/MPCIC)
- [ConvertWithMoss — Multi-sampler Converter](https://github.com/git-moss/ConvertWithMoss)
- [Akai MPC OS 3.7 User Guide](https://cdn.inmusicbrands.com/Software/37/MPC%20Standalone%20OS%20-%20User%20Guide%20-%20v3.7.pdf)
