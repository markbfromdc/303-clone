---
name: xpm-creator
description: Generates the TB-303 XPM preset and reports results
user_invocable: true
---

# XPM Creator Skill

Generate the TB-303 emulation XPM keygroup program file with accompanying WAV samples for Akai MPC.

## Steps

1. Run the generator:
```bash
python src/main.py --output output/ $ARGUMENTS
```

2. Verify the output files exist:
```bash
ls -la output/TB-303/Programs/TB-303.xpm output/TB-303/Samples/TB303_Saw.WAV output/TB-303/Samples/TB303_Square.WAV
```

3. Read the generated XPM and display key parameters (FilterType, Cutoff, Resonance, FilterEnvAmt, FilterDecay, VolumeDecay).

4. Report:
   - Success or failure status
   - File sizes for XPM and WAV files
   - Key TB-303 parameter values from the generated XPM
   - Output directory path

## Usage

- `/xpm-creator` — Generate with default TB-303 parameters
- `/xpm-creator --cutoff 0.3 --resonance 0.7` — Generate with custom parameter overrides
