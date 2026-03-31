"""Integration tests for TB-303 preset generation end-to-end."""

import wave
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import pytest

from src.main import main
from src.waveform_generator import generate_all_waveforms
from src.xpm_builder import build_xpm


class TestCLI:
    def test_main_generates_output(self, tmp_path: Path) -> None:
        """CLI main() should generate XPM and WAV files."""
        output_dir = tmp_path / "output"
        with patch("sys.argv", ["main", "--output", str(output_dir)]):
            main()
        base = output_dir / "TB-303"
        assert (base / "Samples" / "TB303_Saw.WAV").exists()
        assert (base / "Samples" / "TB303_Square.WAV").exists()
        assert (base / "Programs" / "TB-303.xpm").exists()

    def test_main_with_custom_params(self, tmp_path: Path) -> None:
        """CLI should accept and apply custom parameter flags."""
        output_dir = tmp_path / "output"
        with patch("sys.argv", [
            "main", "--output", str(output_dir),
            "--cutoff", "0.8", "--resonance", "0.6",
        ]):
            main()
        xpm_path = output_dir / "TB-303" / "Programs" / "TB-303.xpm"
        root = ET.parse(str(xpm_path)).getroot()
        instrument = root.find("Program/Instruments/Instrument")
        assert float(instrument.find("Cutoff").text) == pytest.approx(0.8)
        assert float(instrument.find("Resonance").text) == pytest.approx(0.6)


class TestXpmWavConsistency:
    def test_xpm_references_match_generated_wavs(self, tmp_path: Path) -> None:
        """XPM sample references should match actual generated WAV filenames."""
        wav_paths = generate_all_waveforms(tmp_path / "Samples")
        wav_names = {p.name for p in wav_paths}

        root = build_xpm()
        layers = root.findall("Program/Instruments/Instrument/Layers/Layer")
        xpm_refs = set()
        for layer in layers:
            sf = layer.find("SampleFile").text
            if sf:  # skip empty layers
                xpm_refs.add(sf)

        assert xpm_refs == wav_names

    def test_xpm_loop_end_matches_wav_length(self, tmp_path: Path) -> None:
        """XPM LoopEnd should equal actual WAV frame count."""
        wav_paths = generate_all_waveforms(tmp_path / "Samples")
        root = build_xpm()

        saw_path = [p for p in wav_paths if "Saw" in p.name][0]
        with wave.open(str(saw_path), "rb") as wf:
            actual_frames = wf.getnframes()

        layer = root.findall("Program/Instruments/Instrument/Layers/Layer")[0]
        loop_end = int(layer.find("LoopEnd").text)
        assert loop_end == actual_frames
