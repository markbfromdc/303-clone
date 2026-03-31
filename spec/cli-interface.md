# CLI Interface Specification

> Version 1.0 | akai-303 v1.0.0 | 2026-03-31

## 1. Overview

The CLI is the only user-facing interface. It accepts optional parameter overrides, generates WAV and XPM files, and prints a summary to stdout.

Implementation: `src/main.py`

## 2. Invocation

```bash
# Direct execution
python src/main.py [OPTIONS]

# Module execution
python -m src.main [OPTIONS]

# Installed entry point (after pip install)
akai-303 [OPTIONS]
```

Both `python src/main.py` and `python -m src.main` are supported via a `sys.path` shim in `main.py`.

## 3. Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `--output` | Path | `output/` | Output directory. Creates `TB-303/Samples/` and `TB-303/Programs/` subdirectories. |
| `--cutoff` | float | `0.25` | Filter cutoff, overrides `TB303Params.cutoff` |
| `--resonance` | float | `0.40` | Filter resonance, overrides `TB303Params.resonance` |
| `--filter-env` | float | `0.70` | Filter envelope amount, overrides `TB303Params.filter_env_amt` |
| `--filter-decay` | float | `0.50` | Filter decay time, overrides `TB303Params.filter_decay` |
| `--no-mono` | flag | (mono enabled) | Disables mono mode, sets `Mono=False` and `Program_Polyphony=4` |
| `--accent-sensitivity` | float | `0.40` | Velocity-to-filter sensitivity, overrides `TB303Params.velocity_to_filter` |

All float arguments accept values in the 0.0-1.0 range. See Section 7 for validation behavior.

## 4. Output Directory Structure

```
{output}/TB-303/
├── Samples/
│   ├── TB303_Saw.WAV       (382 bytes)
│   └── TB303_Square.WAV    (382 bytes)
└── Programs/
    └── TB-303.xpm          (~24 KB)
```

Directories are created automatically. If the output directory already exists, files are overwritten without warning.

## 5. Console Output

```
  Generated: output/TB-303/Samples/TB303_Saw.WAV (382 bytes)
  Generated: output/TB-303/Samples/TB303_Square.WAV (382 bytes)
  Generated: output/TB-303/Programs/TB-303.xpm (24043 bytes)

TB-303 preset generated in: output/TB-303
  Voice: Mono
  Filter: type=3 cutoff=0.25 resonance=0.4 env_amt=0.7
  Accent: vel→filter=0.4 vel→amp=0.6 vel→env=0.25
  Curves: filter_decay=0.7 (convex/exponential)

  Post-load setup on MPC:
    1. Portamento: Program Edit > PORTA/MOD > Time=30, Legato=On
    2. Insert FX:  Channel Mixer > Inserts > AIR Tube Drive
       Drive=30%, Tone=50%, Mix=100%
```

## 6. Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success — files generated |
| `2` | Invalid arguments (argparse default behavior) |

Non-zero exit on argparse errors includes a usage message to stderr.

## 7. Known Gaps

**No float range validation**: CLI float arguments are not clamped to 0.0-1.0. Values like `--cutoff 5.0` or `--resonance -1.0` are passed through to `TB303Params` and written to the XPM without validation. The MPC firmware handles out-of-range values gracefully (clamps or ignores), but the generated XPM may not meet the 0.0-1.0 specification.

**No `--help` customization**: Uses argparse's default `--help` / `-h` behavior.

## 8. Idempotency

Running the tool twice with the same arguments produces identical output. Existing files are overwritten without error or confirmation.

## References

- `src/main.py` — Full CLI implementation
- `pyproject.toml` — `[project.scripts]` entry point: `akai-303 = "src.main:main"`
