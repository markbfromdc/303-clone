"""Tests for single-cycle waveform generator."""

import struct
import wave
from pathlib import Path

import pytest

from src.waveform_generator import (
    _calculate_cycle_length,
    generate_all_waveforms,
    generate_sawtooth,
    generate_square,
)


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    return tmp_path / "samples"


class TestCycleLength:
    def test_c3_cycle_length(self) -> None:
        """C3 at 44100 Hz should produce 169 samples."""
        assert _calculate_cycle_length(44100, 261.63) == 169

    def test_different_frequency(self) -> None:
        """A4 at 44100 Hz should produce 100 samples."""
        assert _calculate_cycle_length(44100, 440.0) == 100


class TestSawtooth:
    def test_generates_valid_wav(self, tmp_output: Path) -> None:
        """Generated sawtooth should be a valid WAV file."""
        tmp_output.mkdir(parents=True)
        path = generate_sawtooth(tmp_output / "test.WAV")
        assert path.exists()
        assert path.stat().st_size > 0

    def test_wav_properties(self, tmp_output: Path) -> None:
        """Sawtooth WAV should be 44100Hz, 16-bit, mono."""
        tmp_output.mkdir(parents=True)
        path = generate_sawtooth(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            assert wf.getframerate() == 44100
            assert wf.getsampwidth() == 2  # 16-bit
            assert wf.getnchannels() == 1  # mono
            assert wf.getnframes() == 169

    def test_sawtooth_ramps(self, tmp_output: Path) -> None:
        """Sawtooth samples should ramp from negative to positive."""
        tmp_output.mkdir(parents=True)
        path = generate_sawtooth(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = list(struct.unpack(f"<{169}h", raw))
        # First sample should be negative (near -32767)
        assert samples[0] < 0
        # Last sample should be positive (near +32767)
        assert samples[-1] > 0
        # Middle sample should be near zero
        mid = samples[len(samples) // 2]
        assert abs(mid) < 500

    def test_wav_extension(self, tmp_output: Path) -> None:
        """Output should use the provided .WAV extension."""
        tmp_output.mkdir(parents=True)
        path = generate_sawtooth(tmp_output / "TB303_Saw.WAV")
        assert path.suffix == ".WAV"

    def test_sawtooth_exact_endpoint_values(self, tmp_output: Path) -> None:
        """Sawtooth endpoints should be exactly -32767 and +32767."""
        tmp_output.mkdir(parents=True)
        path = generate_sawtooth(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = list(struct.unpack(f"<{169}h", raw))
        assert samples[0] == -32767
        assert samples[-1] == 32767


class TestSquare:
    def test_generates_valid_wav(self, tmp_output: Path) -> None:
        """Generated square should be a valid WAV file."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV")
        assert path.exists()
        assert path.stat().st_size > 0

    def test_wav_properties(self, tmp_output: Path) -> None:
        """Square WAV should be 44100Hz, 16-bit, mono."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            assert wf.getframerate() == 44100
            assert wf.getsampwidth() == 2
            assert wf.getnchannels() == 1
            assert wf.getnframes() == 169

    def test_square_values(self, tmp_output: Path) -> None:
        """Square wave should have values near +/- peak amplitude."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = list(struct.unpack(f"<{169}h", raw))
        # First half should be positive
        assert samples[0] > 30000
        # Second half should be negative
        assert samples[-1] < -30000

    def test_sample_count(self, tmp_output: Path) -> None:
        """Square wave should have exactly 169 samples."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            assert wf.getnframes() == 169

    def test_square_exact_plateau_values(self, tmp_output: Path) -> None:
        """Square wave plateau samples should be exactly int(0.95 * 32767)."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = list(struct.unpack(f"<{169}h", raw))
        expected_peak = int(0.95 * 32767)  # 31128
        assert samples[0] == expected_peak
        assert samples[-1] == -expected_peak


class TestSquareTaper:
    """Regression tests for the cosine taper at square wave transitions.

    The taper smooths the +amplitude → -amplitude transition to reduce
    aliasing. Previously used cos(π/2)≈0 which produced zero samples
    instead of smooth interpolation. Fixed to cos(π/4)≈0.7071.
    """

    def test_taper_samples_nonzero(self, tmp_output: Path) -> None:
        """Transition taper samples should NOT be zero."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = list(struct.unpack(f"<{169}h", raw))
        # transition_point = int(169 * 0.5) = 84
        assert samples[83] > 0, f"Taper at index 83 was {samples[83]}, expected positive nonzero"
        assert samples[84] < 0, f"Taper at index 84 was {samples[84]}, expected negative nonzero"

    def test_taper_values_between_zero_and_peak(self, tmp_output: Path) -> None:
        """Taper samples should be between zero and peak amplitude."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = list(struct.unpack(f"<{169}h", raw))
        peak = int(0.95 * 32767)
        assert 0 < samples[83] < peak
        assert -peak < samples[84] < 0

    def test_taper_symmetry(self, tmp_output: Path) -> None:
        """Positive and negative taper samples should be equal in magnitude."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV")
        with wave.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = list(struct.unpack(f"<{169}h", raw))
        assert samples[83] == -samples[84]


class TestSquareDutyCycle:
    def test_duty_75_percent(self, tmp_output: Path) -> None:
        """75% duty cycle should have more positive than negative samples."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV", duty=0.75)
        with wave.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        n = wf.getnframes()
        samples = list(struct.unpack(f"<{n}h", raw))
        positive = sum(1 for s in samples if s > 0)
        negative = sum(1 for s in samples if s < 0)
        assert positive > negative

    def test_duty_25_percent(self, tmp_output: Path) -> None:
        """25% duty cycle should have fewer positive than negative samples."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV", duty=0.25)
        with wave.open(str(path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        n = wf.getnframes()
        samples = list(struct.unpack(f"<{n}h", raw))
        positive = sum(1 for s in samples if s > 0)
        negative = sum(1 for s in samples if s < 0)
        assert positive < negative


class TestCustomParameters:
    def test_custom_sample_rate(self, tmp_output: Path) -> None:
        """Sawtooth at 48000 Hz should produce correct cycle length."""
        tmp_output.mkdir(parents=True)
        path = generate_sawtooth(tmp_output / "test.WAV", sample_rate=48000)
        with wave.open(str(path), "rb") as wf:
            assert wf.getframerate() == 48000
            expected_len = round(48000 / 261.63)
            assert wf.getnframes() == expected_len

    def test_custom_root_freq(self, tmp_output: Path) -> None:
        """Sawtooth at A4 (440 Hz) should produce 100 samples."""
        tmp_output.mkdir(parents=True)
        path = generate_sawtooth(tmp_output / "test.WAV", root_freq=440.0)
        with wave.open(str(path), "rb") as wf:
            assert wf.getnframes() == 100

    def test_square_custom_sample_rate(self, tmp_output: Path) -> None:
        """Square at 48000 Hz should have correct frame rate."""
        tmp_output.mkdir(parents=True)
        path = generate_square(tmp_output / "test.WAV", sample_rate=48000)
        with wave.open(str(path), "rb") as wf:
            assert wf.getframerate() == 48000


class TestGenerateAll:
    def test_generates_both_waveforms(self, tmp_output: Path) -> None:
        """Should generate both sawtooth and square WAV files."""
        paths = generate_all_waveforms(tmp_output)
        assert len(paths) == 2
        assert all(p.exists() for p in paths)

    def test_correct_filenames(self, tmp_output: Path) -> None:
        """Generated files should have correct MPC-compatible names."""
        paths = generate_all_waveforms(tmp_output)
        names = {p.name for p in paths}
        assert "TB303_Saw.WAV" in names
        assert "TB303_Square.WAV" in names

    def test_creates_directory(self, tmp_path: Path) -> None:
        """Should create output directory if it doesn't exist."""
        new_dir = tmp_path / "deep" / "nested" / "dir"
        paths = generate_all_waveforms(new_dir)
        assert new_dir.exists()
        assert len(paths) == 2
