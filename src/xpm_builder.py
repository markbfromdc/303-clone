"""XPM keygroup program builder for TB-303 emulation.

Builds an Akai MPC-compatible XPM (XML) file with TB-303 synthesizer
parameters mapped to MPC keygroup equivalents. The XPM file references
single-cycle WAV waveforms and configures filter, envelope, and layer
settings to approximate the TB-303 sound.

XPM format: XML-based, File_Version 2.1.
Reference implementations: MPCIC (github.com/plule/MPCIC),
ConvertWithMoss (github.com/git-moss/ConvertWithMoss).
"""

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path


def normalize_env_time(seconds: float, min_s: float = 0.001, max_s: float = 100.0) -> float:
    """Convert a time in seconds to MPC normalized 0.0-1.0 value.

    MPC XPM envelope times use logarithmic normalization:
        normalized = ln(seconds / min_s) / ln(max_s / min_s)

    This matches the formula from ConvertWithMoss.

    Args:
        seconds: Time value in seconds.
        min_s: Minimum time (default 0.001s = 1ms).
        max_s: Maximum time (default 100.0s).

    Returns:
        Normalized float between 0.0 and 1.0.
    """
    clamped = max(min_s, min(max_s, seconds))
    return math.log(clamped / min_s) / math.log(max_s / min_s)


@dataclass
class TB303Params:
    """TB-303 parameter values mapped to MPC XPM normalized ranges.

    All float values are normalized to 0.0-1.0 as required by XPM format.
    Each parameter is annotated with its TB-303 rationale.
    """

    # --- Filter (VCF) ---
    # TB-303: 4-pole diode ladder, effectively ~18dB/oct
    # MPC: Filter type 3 = Low Pass 4-pole (24dB/oct), closest match
    filter_type: int = 3

    # TB-303: Cutoff range ~210Hz-2.5kHz, midpoint ~500Hz
    cutoff: float = 0.250000

    # TB-303: Moderate resonance, does NOT self-oscillate
    resonance: float = 0.450000

    # TB-303: Heavy positive envelope-to-filter modulation (core "squelch")
    filter_env_amt: float = 0.650000

    # TB-303: Accent maps velocity to filter cutoff
    velocity_to_filter: float = 0.300000

    # --- Filter Envelope (MEG) ---
    # TB-303: ~3ms attack (fast snap)
    filter_attack: float = 0.012000

    filter_hold: float = 0.000000

    # TB-303: ~300ms decay (mid-range, adjustable 200ms-2000ms)
    filter_decay: float = 0.500000

    # TB-303: No sustain in filter envelope
    filter_sustain: float = 0.000000

    # TB-303: ~200ms release (matches accent decay)
    filter_release: float = 0.460000

    # --- Volume Envelope (VEG) ---
    # TB-303: Instant VCA attack
    volume_attack: float = 0.000000

    volume_hold: float = 0.000000

    # TB-303: Fixed ~3.5 second VCA decay (long gate)
    volume_decay: float = 0.720000

    # TB-303: Held level during gate
    volume_sustain: float = 0.700000

    # TB-303: ~200ms release, quick close
    volume_release: float = 0.460000

    # --- Pitch Envelope ---
    # TB-303: No dedicated pitch envelope; set neutral
    pitch_attack: float = 0.000000
    pitch_hold: float = 0.000000
    pitch_decay: float = 0.000000
    pitch_sustain: float = 0.500000
    pitch_release: float = 0.000000
    pitch_env_amount: float = 0.500000

    # --- Layer ---
    # Root note C3 (MIDI 60, 261.63 Hz)
    root_note: int = 60

    # Single-cycle loop length in samples (round(44100/261.63))
    cycle_length: int = 169

    # Layer volume (normalized, ~-3dB headroom)
    layer_volume: float = 0.708000

    # Center pan
    layer_pan: float = 0.500000

    # --- Program-level ---
    program_name: str = "TB-303"

    # Sawtooth WAV filename (MPC requires .WAV uppercase)
    saw_filename: str = "TB303_Saw.WAV"

    # Square WAV filename
    square_filename: str = "TB303_Square.WAV"


def _add_text_element(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Add a child element with text content."""
    elem = ET.SubElement(parent, tag)
    elem.text = text
    return elem


def _add_version(root: ET.Element) -> None:
    """Add the Version block to the XPM root."""
    version = ET.SubElement(root, "Version")
    _add_text_element(version, "File_Version", "2.1")
    _add_text_element(version, "Application", "MPC")
    _add_text_element(version, "Application_Version", "3.7.1")
    _add_text_element(version, "Platform", "MPC")


def _build_layer(
    parent: ET.Element,
    active: int,
    sample_name: str,
    sample_file: str,
    params: TB303Params,
) -> ET.Element:
    """Build a single Layer element within an Instrument.

    Args:
        parent: Parent Layers element.
        active: 1 for active, 0 for muted.
        sample_name: Sample display name (without extension).
        sample_file: Sample filename (with .WAV extension).
        params: TB303 parameters for root note, loop points, etc.

    Returns:
        The created Layer element.
    """
    layer = ET.SubElement(parent, "Layer")

    _add_text_element(layer, "Active", str(active))
    _add_text_element(layer, "Volume", f"{params.layer_volume:.6f}")
    _add_text_element(layer, "Pan", f"{params.layer_pan:.6f}")
    _add_text_element(layer, "Pitch", "0.000000")
    _add_text_element(layer, "TuneCoarse", "0.000000")
    _add_text_element(layer, "TuneFine", "0.000000")
    _add_text_element(layer, "RootNote", str(params.root_note))
    _add_text_element(layer, "KeyTrack", "1")
    _add_text_element(layer, "VelStart", "0")
    _add_text_element(layer, "VelEnd", "127")
    _add_text_element(layer, "SampleName", sample_name)
    _add_text_element(layer, "SampleFile", sample_file)
    _add_text_element(layer, "SliceIndex", "0")
    _add_text_element(layer, "SampleStart", "0")
    _add_text_element(layer, "SampleEnd", str(params.cycle_length))
    # Seamless looping: LoopStart=0, LoopEnd=cycle_length for oscillator behavior
    _add_text_element(layer, "LoopStart", "0")
    _add_text_element(layer, "LoopEnd", str(params.cycle_length))
    _add_text_element(layer, "LoopCrossfadeLength", "0")
    _add_text_element(layer, "LoopTune", "0")
    _add_text_element(layer, "Direction", "0")
    _add_text_element(layer, "Offset", "0")

    return layer


def _build_empty_layer(parent: ET.Element) -> ET.Element:
    """Build an empty/unused Layer element."""
    layer = ET.SubElement(parent, "Layer")
    _add_text_element(layer, "Active", "0")
    _add_text_element(layer, "Volume", "0.000000")
    _add_text_element(layer, "Pan", "0.500000")
    _add_text_element(layer, "Pitch", "0.000000")
    _add_text_element(layer, "TuneCoarse", "0.000000")
    _add_text_element(layer, "TuneFine", "0.000000")
    _add_text_element(layer, "RootNote", "60")
    _add_text_element(layer, "KeyTrack", "1")
    _add_text_element(layer, "VelStart", "0")
    _add_text_element(layer, "VelEnd", "127")
    _add_text_element(layer, "SampleName", "")
    _add_text_element(layer, "SampleFile", "")
    _add_text_element(layer, "SliceIndex", "0")
    _add_text_element(layer, "SampleStart", "0")
    _add_text_element(layer, "SampleEnd", "0")
    _add_text_element(layer, "LoopStart", "0")
    _add_text_element(layer, "LoopEnd", "0")
    _add_text_element(layer, "LoopCrossfadeLength", "0")
    _add_text_element(layer, "LoopTune", "0")
    _add_text_element(layer, "Direction", "0")
    _add_text_element(layer, "Offset", "0")
    return layer


def _build_instrument(parent: ET.Element, params: TB303Params) -> ET.Element:
    """Build an Instrument (keygroup) element with TB-303 parameters.

    Single keygroup spanning full MIDI range (0-127) with:
    - Layer 1: Sawtooth (active) — TB-303 primary waveform
    - Layer 2: Square (muted) — TB-303 alternate waveform, user-switchable
    - Layers 3-4: Empty
    """
    instrument = ET.SubElement(parent, "Instrument")

    # Full MIDI note range
    _add_text_element(instrument, "LowNote", "0")
    _add_text_element(instrument, "HighNote", "127")
    _add_text_element(instrument, "IgnoreBaseNote", "0")
    _add_text_element(instrument, "ZonePlay", "0")  # 0=All layers simultaneous
    _add_text_element(instrument, "TriggerMode", "0")
    _add_text_element(instrument, "OneShot", "0")

    # --- Filter: TB-303 4-pole diode ladder approximation ---
    _add_text_element(instrument, "FilterType", str(params.filter_type))
    _add_text_element(instrument, "Cutoff", f"{params.cutoff:.6f}")
    _add_text_element(instrument, "Resonance", f"{params.resonance:.6f}")
    _add_text_element(instrument, "FilterEnvAmt", f"{params.filter_env_amt:.6f}")
    _add_text_element(instrument, "VelocityToFilter", f"{params.velocity_to_filter:.6f}")

    # --- Filter Envelope: Fast attack, variable decay, no sustain ---
    _add_text_element(instrument, "FilterAttack", f"{params.filter_attack:.6f}")
    _add_text_element(instrument, "FilterHold", f"{params.filter_hold:.6f}")
    _add_text_element(instrument, "FilterDecay", f"{params.filter_decay:.6f}")
    _add_text_element(instrument, "FilterSustain", f"{params.filter_sustain:.6f}")
    _add_text_element(instrument, "FilterRelease", f"{params.filter_release:.6f}")

    # --- Volume Envelope: Instant attack, long decay (TB-303 VEG) ---
    _add_text_element(instrument, "VolumeAttack", f"{params.volume_attack:.6f}")
    _add_text_element(instrument, "VolumeHold", f"{params.volume_hold:.6f}")
    _add_text_element(instrument, "VolumeDecay", f"{params.volume_decay:.6f}")
    _add_text_element(instrument, "VolumeSustain", f"{params.volume_sustain:.6f}")
    _add_text_element(instrument, "VolumeRelease", f"{params.volume_release:.6f}")

    # --- Pitch Envelope: Neutral (no pitch modulation on stock 303) ---
    _add_text_element(instrument, "PitchAttack", f"{params.pitch_attack:.6f}")
    _add_text_element(instrument, "PitchHold", f"{params.pitch_hold:.6f}")
    _add_text_element(instrument, "PitchDecay", f"{params.pitch_decay:.6f}")
    _add_text_element(instrument, "PitchSustain", f"{params.pitch_sustain:.6f}")
    _add_text_element(instrument, "PitchRelease", f"{params.pitch_release:.6f}")
    _add_text_element(instrument, "PitchEnvAmount", f"{params.pitch_env_amount:.6f}")

    # --- Layers ---
    layers = ET.SubElement(instrument, "Layers")

    # Layer 1: Sawtooth (active) — TB-303 primary "buzzy" waveform
    saw_name = Path(params.saw_filename).stem
    _build_layer(layers, active=1, sample_name=saw_name,
                 sample_file=params.saw_filename, params=params)

    # Layer 2: Square (muted) — TB-303 alternate "hollow" waveform
    square_name = Path(params.square_filename).stem
    _build_layer(layers, active=0, sample_name=square_name,
                 sample_file=params.square_filename, params=params)

    # Layers 3-4: Empty (MPC expects 4 layers per keygroup)
    _build_empty_layer(layers)
    _build_empty_layer(layers)

    return instrument


def build_xpm(params: TB303Params | None = None) -> ET.Element:
    """Build the complete XPM XML tree for a TB-303 emulation program.

    Args:
        params: TB303 parameter values. Uses defaults if None.

    Returns:
        Root ET.Element of the XPM document.
    """
    if params is None:
        params = TB303Params()

    root = ET.Element("MPCVObject")

    # Version header
    _add_version(root)

    # Program
    program = ET.SubElement(root, "Program")
    program.set("type", "Keygroup")
    _add_text_element(program, "ProgramName", params.program_name)

    # Instruments (keygroups)
    instruments = ET.SubElement(program, "Instruments")
    _build_instrument(instruments, params)

    # Pad note map: 128 entries (pad index → MIDI note)
    pad_note_map = ET.SubElement(program, "PadNoteMap")
    for note in range(128):
        pad_note = ET.SubElement(pad_note_map, "PadNote")
        _add_text_element(pad_note, "Note", str(note))

    # Program-level keygroup settings
    _add_text_element(program, "KeygroupNumKeygroups", "1")
    _add_text_element(program, "KeygroupPitchBendRange", "0.500000")
    _add_text_element(program, "KeygroupWheelToLfo", "1.000000")

    return root


def write_xpm(root: ET.Element, filepath: Path) -> Path:
    """Write the XPM XML tree to a file.

    Args:
        root: Root ET.Element of the XPM document.
        filepath: Output file path.

    Returns:
        The filepath written to.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(str(filepath), encoding="UTF-8", xml_declaration=True)
    return filepath
