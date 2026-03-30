"""Single-cycle waveform generator for TB-303 emulation.

Generates sawtooth and square WAV files tuned to C3 (MIDI 60, 261.63 Hz)
at 44100 Hz / 16-bit / mono. These single-cycle waveforms are designed to
be looped seamlessly in an MPC keygroup program to act as oscillators.
"""

import math
import struct
import wave
from pathlib import Path


# TB-303 VCO reference pitch: C3 (MIDI note 60)
DEFAULT_SAMPLE_RATE: int = 44100
DEFAULT_ROOT_FREQ: float = 261.63  # Hz, C3


def _calculate_cycle_length(sample_rate: int, root_freq: float) -> int:
    """Calculate the number of samples in one cycle of the waveform.

    Returns round(sample_rate / root_freq) which gives 169 samples for
    C3 at 44100 Hz.
    """
    return round(sample_rate / root_freq)


def _write_wav(filepath: Path, samples: list[int], sample_rate: int) -> Path:
    """Write 16-bit mono PCM samples to a WAV file.

    Args:
        filepath: Output path (should use .WAV extension for MPC compatibility).
        samples: List of 16-bit signed integer samples (-32768 to 32767).
        sample_rate: Sample rate in Hz.

    Returns:
        The filepath written to.
    """
    with wave.open(str(filepath), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(sample_rate)
        raw_data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(raw_data)
    return filepath


def generate_sawtooth(
    filepath: Path,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    root_freq: float = DEFAULT_ROOT_FREQ,
) -> Path:
    """Generate a single-cycle sawtooth waveform WAV file.

    The sawtooth ramps linearly from -1.0 to +1.0 over one cycle.
    This matches the TB-303's saw-core VCO which produces a rich
    harmonic spectrum with all harmonics present.

    Args:
        filepath: Output WAV file path.
        sample_rate: Sample rate in Hz (default 44100).
        root_freq: Root frequency in Hz (default 261.63, C3).

    Returns:
        The filepath written to.
    """
    cycle_len = _calculate_cycle_length(sample_rate, root_freq)
    samples = []
    for i in range(cycle_len):
        # Linear ramp from -1.0 to +1.0
        value = -1.0 + 2.0 * (i / (cycle_len - 1))
        samples.append(int(value * 32767))
    return _write_wav(filepath, samples, sample_rate)


def generate_square(
    filepath: Path,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    root_freq: float = DEFAULT_ROOT_FREQ,
    duty: float = 0.5,
) -> Path:
    """Generate a single-cycle square waveform WAV file.

    The TB-303's square wave is derived from the sawtooth via transistor
    waveshaping, producing an almost-but-not-exactly 50% duty cycle.
    We use a clean 50% duty cycle with 1-sample cosine tapers at
    transitions to reduce aliasing artifacts.

    Args:
        filepath: Output WAV file path.
        sample_rate: Sample rate in Hz (default 44100).
        root_freq: Root frequency in Hz (default 261.63, C3).
        duty: Duty cycle 0.0-1.0 (default 0.5).

    Returns:
        The filepath written to.
    """
    cycle_len = _calculate_cycle_length(sample_rate, root_freq)
    transition_point = int(cycle_len * duty)
    amplitude = 0.95  # Slight headroom to avoid clipping

    samples = []
    for i in range(cycle_len):
        if i == transition_point - 1:
            # Cosine taper at positive-to-negative transition
            value = amplitude * math.cos(math.pi / 2)
        elif i == transition_point:
            # Cosine taper at negative start
            value = -amplitude * math.cos(math.pi / 2)
        elif i < transition_point:
            value = amplitude
        else:
            value = -amplitude
        samples.append(int(value * 32767))
    return _write_wav(filepath, samples, sample_rate)


def generate_all_waveforms(output_dir: Path) -> list[Path]:
    """Generate all TB-303 waveforms into the specified directory.

    Creates TB303_Saw.WAV and TB303_Square.WAV in output_dir.

    Args:
        output_dir: Directory to write WAV files into (created if needed).

    Returns:
        List of generated file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # MPC requires uppercase .WAV extension
    saw_path = output_dir / "TB303_Saw.WAV"
    square_path = output_dir / "TB303_Square.WAV"

    paths = [
        generate_sawtooth(saw_path),
        generate_square(square_path),
    ]
    return paths
