# Architecture Specification

> Version 1.0 | akai-303 v1.0.0 | 2026-03-31

## 1. Overview

akai-303 is a Python CLI tool that generates Akai MPC-compatible XPM keygroup program files emulating the Roland TB-303 Bass Line synthesizer. It produces single-cycle WAV waveforms and an XML-based XPM file, then exits. It is not a service, library, or plugin.

## 2. Module Map

```
src/
├── main.py                (94 lines)  CLI parsing, orchestration, stdout reporting
├── waveform_generator.py  (139 lines) Single-cycle WAV file generation
└── xpm_builder.py         (563 lines) XPM XML construction, TB303Params dataclass
```

| Module | Responsibility | Imports from |
|---|---|---|
| `main.py` | Parse CLI args, apply overrides, call generators, print summary | `waveform_generator`, `xpm_builder` |
| `waveform_generator.py` | Generate sawtooth and square WAV files | stdlib only |
| `xpm_builder.py` | Build XPM XML tree, normalize envelope times, write XML | stdlib only |

The two subsystems (WAV generation and XPM building) are **independent** — they share no state. The only coupling is filename conventions (`TB303_Saw.WAV`, `TB303_Square.WAV`) which `main.py` coordinates.

## 3. Data Flow

```
CLI args (argparse)
    │
    ▼
main.py
    ├──► generate_all_waveforms(samples_dir) ──► list[Path]
    │        Writes: TB303_Saw.WAV, TB303_Square.WAV
    │
    ├──► TB303Params(overrides...) ──► dataclass instance
    │
    ├──► build_xpm(params) ──► ET.Element (XML tree)
    │
    └──► write_xpm(root, filepath) ──► Path
             Writes: TB-303.xpm
```

Output directory structure:
```
{output}/TB-303/
├── Samples/
│   ├── TB303_Saw.WAV     (382 bytes)
│   └── TB303_Square.WAV  (382 bytes)
└── Programs/
    └── TB-303.xpm        (~24 KB)
```

## 4. Dependency Constraints

**Runtime**: Python 3.10+ standard library only.

| stdlib module | Used by | Purpose |
|---|---|---|
| `wave` | waveform_generator | WAV file writing |
| `struct` | waveform_generator | 16-bit PCM sample packing |
| `math` | waveform_generator, xpm_builder | cos(), log() |
| `xml.etree.ElementTree` | xpm_builder | XML construction and writing |
| `argparse` | main | CLI argument parsing |
| `pathlib` | all | File path handling |
| `dataclasses` | xpm_builder | TB303Params definition |
| `sys` | main | sys.path for dual invocation support |

**Test**: `pytest>=7.0` (the only external dependency).

## 5. Key Design Decisions

| Decision | Rationale |
|---|---|
| `TB303Params` as `@dataclass` | Enables type hints, IDE support, direct attribute override from CLI. Preferable to dict (no type safety) or config file (unnecessary complexity). |
| XML via `xml.etree.ElementTree` | Guarantees well-formed XML output. String templates risk malformed XML from special characters or formatting errors. |
| Single-cycle WAVs generated programmatically | Eliminates binary assets from version control. Ensures reproducibility. Any developer can verify the exact algorithm. |
| `QLINK_UNASSIGNED = 2147483647` | Sentinel value from MPC firmware (not arbitrary). Represents "no parameter assigned" in Q-Link configuration. |
| Mono mode at program level (not keygroup) | Per MPC forum guidance: setting mono at keygroup level causes envelope retrigger issues. Program-level mono avoids this. |
| No input validation on CLI floats | Follows project convention of not adding speculative error handling. MPC firmware ignores out-of-range values gracefully. |

## 6. What This Project Intentionally Excludes

- No configuration files (all params are CLI args or dataclass defaults)
- No external runtime dependencies
- No plugin system or extensibility hooks
- No real-time DSP or audio playback
- No network I/O, database, or persistence
- No build step beyond `python src/main.py`
- No deployment pipeline or containerization

## References

- `CLAUDE.md` — Project conventions and architecture overview
- `pyproject.toml` — Package metadata and entry point definition
- `src/` — All source modules
