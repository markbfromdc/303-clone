# TB-303 Emulation for Akai MPC

## Overview

Python tool that generates an Akai MPC-compatible XPM keygroup program file emulating the Roland TB-303 Bass Line synthesizer. Produces single-cycle WAV waveforms and an XML-based XPM file with TB-303 parameters mapped to MPC equivalents.

## Language & Dependencies

- Python 3.10+
- **No external runtime dependencies** — standard library only (`wave`, `struct`, `math`, `xml.etree.ElementTree`, `argparse`, `pathlib`)
- Test dependency: `pytest>=7.0`

## Commands

```bash
# Generate the TB-303 preset
python src/main.py --output output/

# Run tests
python -m pytest tests/ -v
```

## Architecture

```
src/
├── waveform_generator.py  — Generates single-cycle sawtooth/square WAV files
├── xpm_builder.py         — Builds XPM XML with TB-303 parameter mappings
└── main.py                — CLI entry point, orchestrates generation
```

**Flow**: `main.py` → calls `waveform_generator` to create WAV files → calls `xpm_builder` to create XPM referencing those WAVs → writes to output directory.

## Key Technical Notes

- **XPM format**: XML-based, File_Version 2.1. Reference implementations: [MPCIC](https://github.com/plule/MPCIC), [ConvertWithMoss](https://github.com/git-moss/ConvertWithMoss)
- **Parameter normalization**: XPM uses 0.0-1.0 floats. Envelope times use logarithmic normalization: `ln(seconds / 0.001) / ln(100000)`
- **Filter type 3** = Low Pass 4-pole (24dB/oct), closest to TB-303's diode ladder
- **WAV files** must use `.WAV` uppercase extension for MPC compatibility
- **Single-cycle waveforms**: 169 samples at 44100Hz, root note C3 (MIDI 60, 261.63Hz)
- **Looping**: LoopStart=0, LoopEnd=cycle_length for seamless oscillator behavior

## Conventions

- Type hints on all function signatures
- Docstrings on all public functions
- XPM parameter values documented with TB-303 mapping rationale as comments in code
- All generated output goes to `output/` directory (gitignored except .gitkeep)

## Project Structure

See `docs/PRD.md` for full product requirements and TB-303 parameter mapping table.

## Agents

- `prd-writer` — Researches and updates product requirements
- `code-generator` — Implements Python source code following PRD specs
- `tester` — Runs tests, validates XPM and WAV output

## Skills

- `/xpm-creator` — Generates the TB-303 XPM preset and reports results
