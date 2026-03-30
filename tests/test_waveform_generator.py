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
