"""CLI entry point for TB-303 XPM preset generator.

Orchestrates waveform generation and XPM building to produce
an Akai MPC-compatible TB-303 emulation keygroup program.

Usage:
    python -m src.main --output output/
"""

import argparse
import sys
from pathlib import Path

# Support running as both `python -m src.main` and `python src/main.py`
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.waveform_generator import generate_all_waveforms
from src.xpm_builder import TB303Params, build_xpm, write_xpm


def main() -> None:
    """Generate the TB-303 XPM preset with accompanying WAV samples."""
    parser = argparse.ArgumentParser(
        description="Generate a TB-303 emulation XPM keygroup program for Akai MPC"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Output directory (default: output/)",
    )
    parser.add_argument("--cutoff", type=float, help="Filter cutoff 0.0-1.0")
    parser.add_argument("--resonance", type=float, help="Filter resonance 0.0-1.0")
    parser.add_argument("--filter-env", type=float, help="Filter envelope amount 0.0-1.0")
    parser.add_argument("--filter-decay", type=float, help="Filter decay 0.0-1.0")

    args = parser.parse_args()

    # Build output directory structure matching MPC expansion layout
    base_dir = args.output / "TB-303"
    samples_dir = base_dir / "Samples"
    programs_dir = base_dir / "Programs"

    # Generate single-cycle waveforms
    wav_paths = generate_all_waveforms(samples_dir)
    for p in wav_paths:
        print(f"  Generated: {p} ({p.stat().st_size} bytes)")

    # Build XPM with parameters (apply any CLI overrides)
    params = TB303Params()
    if args.cutoff is not None:
        params.cutoff = args.cutoff
    if args.resonance is not None:
        params.resonance = args.resonance
    if args.filter_env is not None:
        params.filter_env_amt = args.filter_env
    if args.filter_decay is not None:
        params.filter_decay = args.filter_decay

    xpm_root = build_xpm(params)
    xpm_path = write_xpm(xpm_root, programs_dir / "TB-303.xpm")
    print(f"  Generated: {xpm_path} ({xpm_path.stat().st_size} bytes)")

    print(f"\nTB-303 preset generated in: {base_dir}")
    print(f"  Filter: type={params.filter_type} cutoff={params.cutoff} "
          f"resonance={params.resonance} env_amt={params.filter_env_amt}")


if __name__ == "__main__":
    main()
