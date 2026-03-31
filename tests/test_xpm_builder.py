"""Tests for XPM keygroup program builder."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from src.xpm_builder import (
    QLINK_UNASSIGNED,
    TB303Params,
    build_xpm,
    normalize_env_time,
    write_xpm,
)


class TestNormalizeEnvTime:
    def test_minimum_time(self) -> None:
        """0.001s (minimum) should normalize to 0.0."""
        assert normalize_env_time(0.001) == pytest.approx(0.0, abs=0.001)

    def test_maximum_time(self) -> None:
        """100.0s (maximum) should normalize to 1.0."""
        assert normalize_env_time(100.0) == pytest.approx(1.0, abs=0.001)

    def test_303_filter_attack(self) -> None:
        """3ms (TB-303 filter attack) should normalize to ~0.095."""
        assert normalize_env_time(0.003) == pytest.approx(0.095, abs=0.01)

    def test_303_accent_decay(self) -> None:
        """200ms (TB-303 accent decay) should normalize to ~0.460."""
        assert normalize_env_time(0.200) == pytest.approx(0.460, abs=0.01)

    def test_303_max_filter_decay(self) -> None:
        """2000ms (TB-303 max filter decay) should normalize to ~0.661."""
        assert normalize_env_time(2.0) == pytest.approx(0.661, abs=0.01)

    def test_303_vca_decay(self) -> None:
        """3500ms (TB-303 VCA decay) should normalize to ~0.710."""
        assert normalize_env_time(3.5) == pytest.approx(0.710, abs=0.01)

    def test_clamps_below_minimum(self) -> None:
        """Values below minimum should clamp to 0.0."""
        assert normalize_env_time(0.0001) == pytest.approx(0.0, abs=0.001)

    def test_clamps_above_maximum(self) -> None:
        """Values above maximum should clamp to 1.0."""
        assert normalize_env_time(1000.0) == pytest.approx(1.0, abs=0.001)


class TestBuildXpm:
    @pytest.fixture
    def xpm_root(self) -> ET.Element:
        return build_xpm()

    def test_root_element(self, xpm_root: ET.Element) -> None:
        """Root element should be MPCVObject."""
        assert xpm_root.tag == "MPCVObject"

    def test_file_version(self, xpm_root: ET.Element) -> None:
        """File_Version should be 2.1."""
        version = xpm_root.find("Version/File_Version")
        assert version is not None
        assert version.text == "2.1"

    def test_program_type(self, xpm_root: ET.Element) -> None:
        """Program type should be Keygroup."""
        program = xpm_root.find("Program")
        assert program is not None
        assert program.get("type") == "Keygroup"

    def test_program_name(self, xpm_root: ET.Element) -> None:
        """ProgramName should be TB-303."""
        name = xpm_root.find("Program/ProgramName")
        assert name is not None
        assert name.text == "TB-303"

    def test_filter_type(self, xpm_root: ET.Element) -> None:
        """FilterType should be 3 (Low 4-pole 24dB/oct LP)."""
        ft = xpm_root.find("Program/Instruments/Instrument/FilterType")
        assert ft is not None
        assert ft.text == "3"

    def test_float_params_in_range(self, xpm_root: ET.Element) -> None:
        """All float parameters should be between 0.0 and 1.0."""
        float_tags = [
            "Cutoff", "Resonance", "FilterEnvAmt", "VelocityToFilter",
            "FilterKeytrack", "VelocityToFilterEnvelope",
            "FilterAttack", "FilterHold", "FilterDecay", "FilterSustain", "FilterRelease",
            "FilterAttackCurve", "FilterDecayCurve", "FilterReleaseCurve",
            "VolumeAttack", "VolumeHold", "VolumeDecay", "VolumeSustain", "VolumeRelease",
            "VolumeAttackCurve", "VolumeDecayCurve", "VolumeReleaseCurve",
            "PitchAttack", "PitchHold", "PitchDecay", "PitchSustain", "PitchRelease",
            "PitchEnvAmount",
            "VelocitySensitivity", "VelocityToStart", "VelocityToFilterAttack",
            "VelocityToPitch", "VelocityToVolumeAttack", "VelocityToPan",
            "AfterTouchToFilter",
            "LfoPitch", "LfoCutoff", "LfoVolume", "LfoPan",
        ]
        instrument = xpm_root.find("Program/Instruments/Instrument")
        assert instrument is not None
        for tag in float_tags:
            elem = instrument.find(tag)
            assert elem is not None, f"Missing tag: {tag}"
            val = float(elem.text)
            assert 0.0 <= val <= 1.0, f"{tag}={val} out of range"

    def test_sample_references(self, xpm_root: ET.Element) -> None:
        """Layer sample files should match expected WAV filenames."""
        layers = xpm_root.findall("Program/Instruments/Instrument/Layers/Layer")
        assert len(layers) == 4

        # Layer 1: Sawtooth
        assert layers[0].find("SampleFile").text == "TB303_Saw.WAV"
        # Layer 2: Square
        assert layers[1].find("SampleFile").text == "TB303_Square.WAV"

    def test_root_note(self, xpm_root: ET.Element) -> None:
        """RootNote should be 60 (C3, MIDI note 60)."""
        layers = xpm_root.findall("Program/Instruments/Instrument/Layers/Layer")
        assert layers[0].find("RootNote").text == "60"

    def test_layer1_active(self, xpm_root: ET.Element) -> None:
        """Layer 1 (sawtooth) should be active."""
        layers = xpm_root.findall("Program/Instruments/Instrument/Layers/Layer")
        assert layers[0].find("Active").text == "1"

    def test_layer2_inactive(self, xpm_root: ET.Element) -> None:
        """Layer 2 (square) should be muted/inactive."""
        layers = xpm_root.findall("Program/Instruments/Instrument/Layers/Layer")
        assert layers[1].find("Active").text == "0"

    def test_loop_points(self, xpm_root: ET.Element) -> None:
        """Loop should span full single-cycle waveform (0 to 169)."""
        layer = xpm_root.findall("Program/Instruments/Instrument/Layers/Layer")[0]
        assert layer.find("LoopStart").text == "0"
        assert layer.find("LoopEnd").text == "169"

    def test_pad_note_map(self, xpm_root: ET.Element) -> None:
        """PadNoteMap should have 128 entries."""
        pad_notes = xpm_root.findall("Program/PadNoteMap/PadNote")
        assert len(pad_notes) == 128

    def test_pad_note_map_values(self, xpm_root: ET.Element) -> None:
        """PadNoteMap entries should map 0-127."""
        pad_notes = xpm_root.findall("Program/PadNoteMap/PadNote")
        for i, pn in enumerate(pad_notes):
            assert pn.find("Note").text == str(i)

    def test_custom_params(self) -> None:
        """Custom parameters should be reflected in the XPM."""
        params = TB303Params(cutoff=0.5, resonance=0.8)
        root = build_xpm(params)
        instrument = root.find("Program/Instruments/Instrument")
        assert float(instrument.find("Cutoff").text) == pytest.approx(0.5)
        assert float(instrument.find("Resonance").text) == pytest.approx(0.8)


class TestMonoMode:
    @pytest.fixture
    def xpm_root(self) -> ET.Element:
        return build_xpm()

    def test_mono_program_level(self, xpm_root: ET.Element) -> None:
        """Program-level Mono should be True for 303 monophonic emulation."""
        mono = xpm_root.find("Program/Mono")
        assert mono is not None
        assert mono.text == "True"

    def test_program_polyphony(self, xpm_root: ET.Element) -> None:
        """Program_Polyphony should be 1 for single-voice behavior."""
        poly = xpm_root.find("Program/Program_Polyphony")
        assert poly is not None
        assert poly.text == "1"

    def test_poly_mode_custom(self) -> None:
        """Disabling mono should set Mono=False."""
        params = TB303Params(mono=False, program_polyphony=4)
        root = build_xpm(params)
        assert root.find("Program/Mono").text == "False"
        assert root.find("Program/Program_Polyphony").text == "4"


class TestFilterKeytrack:
    def test_filter_keytrack_zero(self) -> None:
        """FilterKeytrack should be 0.0 — 303 has no filter keytrack."""
        root = build_xpm()
        fkt = root.find("Program/Instruments/Instrument/FilterKeytrack")
        assert fkt is not None
        assert float(fkt.text) == pytest.approx(0.0)


class TestEnvelopeCurves:
    @pytest.fixture
    def xpm_root(self) -> ET.Element:
        return build_xpm()

    def test_all_curve_params_in_range(self, xpm_root: ET.Element) -> None:
        """All envelope curve parameters should be between 0.0 and 1.0."""
        curve_tags = [
            "FilterAttackCurve", "FilterDecayCurve", "FilterReleaseCurve",
            "VolumeAttackCurve", "VolumeDecayCurve", "VolumeReleaseCurve",
        ]
        instrument = xpm_root.find("Program/Instruments/Instrument")
        for tag in curve_tags:
            elem = instrument.find(tag)
            assert elem is not None, f"Missing tag: {tag}"
            val = float(elem.text)
            assert 0.0 <= val <= 1.0, f"{tag}={val} out of range"

    def test_filter_decay_curve_convex(self, xpm_root: ET.Element) -> None:
        """FilterDecayCurve should be convex (>0.5) for 303 exponential RC decay."""
        fdc = xpm_root.find("Program/Instruments/Instrument/FilterDecayCurve")
        assert fdc is not None
        assert float(fdc.text) > 0.5

    def test_filter_release_curve_convex(self, xpm_root: ET.Element) -> None:
        """FilterReleaseCurve should be convex (>0.5) for exponential release."""
        frc = xpm_root.find("Program/Instruments/Instrument/FilterReleaseCurve")
        assert frc is not None
        assert float(frc.text) > 0.5


class TestVelocityRouting:
    @pytest.fixture
    def xpm_root(self) -> ET.Element:
        return build_xpm()

    def test_velocity_sensitivity(self, xpm_root: ET.Element) -> None:
        """VelocitySensitivity should be set for accent VCA boost."""
        vs = xpm_root.find("Program/Instruments/Instrument/VelocitySensitivity")
        assert vs is not None
        assert 0.0 < float(vs.text) <= 1.0

    def test_velocity_to_filter_envelope(self, xpm_root: ET.Element) -> None:
        """VelocityToFilterEnvelope should be set for accent sweep depth."""
        vtfe = xpm_root.find("Program/Instruments/Instrument/VelocityToFilterEnvelope")
        assert vtfe is not None
        assert float(vtfe.text) > 0.0

    def test_aftertouch_not_used(self, xpm_root: ET.Element) -> None:
        """AfterTouchToFilter should be 0 — not used on 303."""
        atf = xpm_root.find("Program/Instruments/Instrument/AfterTouchToFilter")
        assert atf is not None
        assert float(atf.text) == pytest.approx(0.0)


class TestLFO:
    @pytest.fixture
    def xpm_root(self) -> ET.Element:
        return build_xpm()

    def test_lfo_section_exists(self, xpm_root: ET.Element) -> None:
        """LFO section should exist within Instrument."""
        lfo = xpm_root.find("Program/Instruments/Instrument/LFO")
        assert lfo is not None
        assert lfo.find("Type").text == "Sine"
        assert lfo.find("Rate") is not None

    def test_lfo_cutoff_default_zero(self, xpm_root: ET.Element) -> None:
        """LfoCutoff should default to 0 (off) — user enables via Q-Link."""
        lfo_cutoff = xpm_root.find("Program/Instruments/Instrument/LfoCutoff")
        assert lfo_cutoff is not None
        assert float(lfo_cutoff.text) == pytest.approx(0.0)

    def test_all_lfo_depths_zero(self, xpm_root: ET.Element) -> None:
        """All LFO depth controls should default to 0."""
        instrument = xpm_root.find("Program/Instruments/Instrument")
        for tag in ["LfoPitch", "LfoCutoff", "LfoVolume", "LfoPan"]:
            elem = instrument.find(tag)
            assert elem is not None, f"Missing: {tag}"
            assert float(elem.text) == pytest.approx(0.0)


class TestQLinkAssignments:
    @pytest.fixture
    def xpm_root(self) -> ET.Element:
        return build_xpm()

    def test_qlink_section_exists(self, xpm_root: ET.Element) -> None:
        """QLinkAssignments section should exist."""
        qlinks = xpm_root.find("Program/QLinkAssignments")
        assert qlinks is not None

    def test_qlink_has_16_entries(self, xpm_root: ET.Element) -> None:
        """Should have 16 Q-Link entries."""
        qlinks = xpm_root.findall("Program/QLinkAssignments/ProgramMode/QLink")
        assert len(qlinks) == 16

    def test_qlink1_cutoff(self, xpm_root: ET.Element) -> None:
        """Q-Link 1 should be assigned to cutoff (parameter 94)."""
        qlinks = xpm_root.findall("Program/QLinkAssignments/ProgramMode/QLink")
        q1 = qlinks[0]
        assert q1.get("index") == "1"
        assert q1.find("Parameter").text == "94"

    def test_qlink2_resonance(self, xpm_root: ET.Element) -> None:
        """Q-Link 2 should be assigned to resonance (parameter 71)."""
        qlinks = xpm_root.findall("Program/QLinkAssignments/ProgramMode/QLink")
        q2 = qlinks[1]
        assert q2.get("index") == "2"
        assert q2.find("Parameter").text == "71"

    def test_unassigned_qlinks(self, xpm_root: ET.Element) -> None:
        """Unassigned Q-Links should have parameter QLINK_UNASSIGNED."""
        qlinks = xpm_root.findall("Program/QLinkAssignments/ProgramMode/QLink")
        q3 = qlinks[2]
        assert q3.find("Parameter").text == str(QLINK_UNASSIGNED)


class TestPadGroupMap:
    @pytest.fixture
    def xpm_root(self) -> ET.Element:
        return build_xpm()

    def test_pad_group_map_exists(self, xpm_root: ET.Element) -> None:
        """PadGroupMap should have 128 entries."""
        groups = xpm_root.findall("Program/PadGroupMap/PadGroup")
        assert len(groups) == 128

    def test_all_group_zero(self, xpm_root: ET.Element) -> None:
        """All pad groups should be Group 0."""
        groups = xpm_root.findall("Program/PadGroupMap/PadGroup")
        for g in groups:
            assert g.find("Group").text == "0"


class TestInsertsEnabled:
    def test_inserts_enabled(self) -> None:
        """InsertsEnabled should be True to allow AIR FX insert effects."""
        root = build_xpm()
        ie = root.find("Program/AudioRoute/InsertsEnabled")
        assert ie is not None
        assert ie.text == "True"

    def test_audio_route_exists(self) -> None:
        """AudioRoute section should exist with routing config."""
        root = build_xpm()
        ar = root.find("Program/AudioRoute")
        assert ar is not None
        assert ar.find("AudioRoute") is not None


class TestWriteXpm:
    def test_writes_valid_xml(self, tmp_path: Path) -> None:
        """Written XPM should be parseable XML."""
        root = build_xpm()
        filepath = write_xpm(root, tmp_path / "test.xpm")
        assert filepath.exists()
        parsed = ET.parse(str(filepath))
        assert parsed.getroot().tag == "MPCVObject"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Should create parent directories if they don't exist."""
        root = build_xpm()
        filepath = write_xpm(root, tmp_path / "deep" / "nested" / "test.xpm")
        assert filepath.exists()

    def test_file_has_xml_declaration(self, tmp_path: Path) -> None:
        """Written file should start with XML declaration."""
        root = build_xpm()
        filepath = write_xpm(root, tmp_path / "test.xpm")
        content = filepath.read_text(encoding="UTF-8")
        assert content.startswith("<?xml")

    def test_roundtrip_preserves_structure(self, tmp_path: Path) -> None:
        """XPM written to disk should match in-memory structure."""
        root = build_xpm()
        filepath = write_xpm(root, tmp_path / "test.xpm")
        parsed = ET.parse(str(filepath)).getroot()
        # Check key values survive roundtrip
        assert parsed.find("Version/File_Version").text == "2.1"
        assert parsed.find("Program").get("type") == "Keygroup"
        assert parsed.find("Program/ProgramName").text == "TB-303"
        assert parsed.find("Program/Mono").text == "True"
