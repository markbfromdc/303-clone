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

# Sentinel value for unassigned Q-Link parameters in MPC XPM format
QLINK_UNASSIGNED: int = 2147483647


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
    # TB-303: 4-pole diode ladder, effectively ~18dB/oct due to mismatched
    # capacitor (pole 1: 0.18µF vs poles 2-4: 0.33µF). MPC has no 18dB mode.
    # Filter type 3 = Low Pass 4-pole (24dB/oct), closest available match.
    # We compensate for the steeper slope by reducing resonance slightly and
    # relying on the AIR Tube Drive insert for saturation character.
    filter_type: int = 3

    # TB-303: Cutoff range ~210Hz-2.5kHz, midpoint ~500Hz
    cutoff: float = 0.250000

    # TB-303: Does NOT self-oscillate — high resonance produces saturation/
    # overdrive instead. Reduced from 0.45 to compensate for 24dB/oct being
    # steeper than the 303's effective ~18dB/oct. Combined with AIR Tube Drive
    # insert, this avoids digital harshness while preserving squelch.
    resonance: float = 0.400000

    # TB-303: Heavy positive envelope-to-filter modulation is the core of
    # the "squelch" sound. Increased from 0.65 for stronger character.
    filter_env_amt: float = 0.700000

    # TB-303: Accent maps velocity to filter cutoff. Increased from 0.30
    # for more prominent accent filter sweep.
    velocity_to_filter: float = 0.400000

    # TB-303: Zero filter keyboard tracking on stock unit. The filter cutoff
    # does not follow pitch — lower notes sound darker, higher notes brighter.
    filter_keytrack: float = 0.000000

    # --- Filter Envelope (MEG) ---
    # TB-303: ~3ms attack. normalize_env_time(0.003) = 0.095.
    # Previously 0.012 which mapped to ~1.1ms — too fast.
    filter_attack: float = 0.095000

    filter_hold: float = 0.000000

    # TB-303: ~300ms decay (mid-range, adjustable 200ms-2000ms)
    filter_decay: float = 0.500000

    # TB-303: No sustain in filter envelope
    filter_sustain: float = 0.000000

    # TB-303: ~200ms release (matches accent decay)
    filter_release: float = 0.460000

    # --- Filter Envelope Curves ---
    # TB-303 uses RC circuit envelopes with exponential decay character.
    # Values > 0.5 = convex curve (fast initial decay, slow tail).
    filter_attack_curve: float = 0.500000   # Linear attack (snap)
    filter_decay_curve: float = 0.700000    # Convex — key 303 exponential decay
    filter_release_curve: float = 0.700000  # Convex release

    # --- Volume Envelope (VEG) ---
    # TB-303: Instant VCA attack
    volume_attack: float = 0.000000

    volume_hold: float = 0.000000

    # TB-303: Fixed ~3.5 second VCA decay (long gate). This creates the
    # characteristic "pluck from filter, sustain from VCA" behavior.
    volume_decay: float = 0.720000

    # TB-303: Held level during gate
    volume_sustain: float = 0.700000

    # TB-303: ~200ms release, quick close
    volume_release: float = 0.460000

    # --- Volume Envelope Curves ---
    volume_attack_curve: float = 0.500000   # Linear
    volume_decay_curve: float = 0.600000    # Slightly convex VCA
    volume_release_curve: float = 0.500000  # Linear

    # --- Pitch Envelope ---
    # TB-303: No dedicated pitch envelope; set neutral
    pitch_attack: float = 0.000000
    pitch_hold: float = 0.000000
    pitch_decay: float = 0.000000
    pitch_sustain: float = 0.500000
    pitch_release: float = 0.000000
    pitch_env_amount: float = 0.500000

    # --- Velocity / Accent Routing ---
    # TB-303 accent is binary (on/off) but maps naturally to MIDI velocity.
    # Accented notes: brighter (filter sweep) + louder (VCA boost) + deeper
    # envelope sweep simultaneously.
    velocity_sensitivity: float = 0.600000      # Velocity → amplitude (accent VCA boost)
    velocity_to_filter_env: float = 0.250000    # Velocity → filter env depth
    aftertouch_to_filter: float = 0.000000      # Not used on 303
    velocity_to_start: float = 0.000000
    velocity_to_filter_attack: float = 0.000000
    velocity_to_pitch: float = 0.000000
    velocity_to_volume_attack: float = 0.000000
    velocity_to_pan: float = 0.000000

    # --- LFO ---
    # Off by default. Available for user to enable via Q-Link for slow
    # filter sweeps or vibrato effects.
    lfo_type: str = "Sine"
    lfo_rate: float = 0.100000
    lfo_sync: int = 0
    lfo_reset: bool = False
    lfo_pitch: float = 0.000000
    lfo_cutoff: float = 0.000000
    lfo_volume: float = 0.000000
    lfo_pan: float = 0.000000

    # --- Voice Mode ---
    # TB-303 is monophonic with 60ms constant-time portamento (slide).
    mono: bool = True
    program_polyphony: int = 1

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
    program_volume: float = 0.707946   # ~-3dB
    inserts_enabled: bool = True        # Enable insert bus for AIR FX

    # Sawtooth WAV filename (MPC requires .WAV uppercase)
    saw_filename: str = "TB303_Saw.WAV"

    # Square WAV filename
    square_filename: str = "TB303_Square.WAV"

    # --- Q-Link Assignments ---
    # 16 entries of (parameter_id, momentary). MIDI CC mappings:
    # 94=Brightness/Cutoff, 71=Resonance, 7=Volume, 10=Pan.
    # QLINK_UNASSIGNED = unassigned (user can bind via Q-Link Learn on device).
    qlink_assignments: list[tuple[int, int]] = field(default_factory=lambda: [
        (94, 0),                # Q1: Cutoff
        (71, 0),                # Q2: Resonance
        (QLINK_UNASSIGNED, 0),  # Q3: unassigned (use Q-Link Learn for Filter Env Amt)
        (QLINK_UNASSIGNED, 0),  # Q4: unassigned (use Q-Link Learn for Filter Decay)
        (7, 0),                 # Q5: Volume
        (10, 0),                # Q6: Pan
        (QLINK_UNASSIGNED, 0),  # Q7-Q16: unassigned
        (QLINK_UNASSIGNED, 0),
        (QLINK_UNASSIGNED, 0),
        (QLINK_UNASSIGNED, 0),
        (QLINK_UNASSIGNED, 0),
        (QLINK_UNASSIGNED, 0),
        (QLINK_UNASSIGNED, 0),
        (QLINK_UNASSIGNED, 0),
        (QLINK_UNASSIGNED, 0),
        (QLINK_UNASSIGNED, 0),
    ])


def _add_text_element(parent: ET.Element, tag: str, text: str) -> ET.Element:
    """Add a child element with text content."""
    elem = ET.SubElement(parent, tag)
    elem.text = text
    return elem


def _add_float(parent: ET.Element, tag: str, value: float) -> ET.Element:
    """Add a child element with a formatted float value."""
    return _add_text_element(parent, tag, f"{value:.6f}")


def _add_version(root: ET.Element) -> None:
    """Add the Version block to the XPM root."""
    version = ET.SubElement(root, "Version")
    _add_text_element(version, "File_Version", "2.1")
    _add_text_element(version, "Application", "MPC")
    _add_text_element(version, "Application_Version", "3.7.1")
    _add_text_element(version, "Platform", "MPC")


def _build_program_header(program: ET.Element, params: TB303Params) -> None:
    """Add program-level settings between ProgramName and Instruments.

    Configures audio routing, insert effects bus, volume, pan,
    and monophonic voice mode for TB-303 emulation.
    """
    # Audio routing with insert effects bus enabled
    audio_route = ET.SubElement(program, "AudioRoute")
    _add_text_element(audio_route, "AudioRoute", "2")
    _add_text_element(audio_route, "AudioRouteSubIndex", "0")
    _add_text_element(audio_route, "AudioRouteChannelBitmap", "3")
    _add_text_element(audio_route, "InsertsEnabled", str(params.inserts_enabled))

    # Send levels (all off — user can route to FX sends on device)
    for i in range(1, 5):
        _add_float(program, f"Send{i}", 0.0)

    # Program master volume and pan
    _add_float(program, "Volume", params.program_volume)
    _add_text_element(program, "Mute", "False")
    _add_text_element(program, "Solo", "False")
    _add_float(program, "Pan", 0.500000)
    _add_text_element(program, "AutomationFilter", "1")
    _add_float(program, "Pitch", 0.0)
    _add_text_element(program, "TuneCoarse", "0")
    _add_text_element(program, "TuneFine", "0")

    # TB-303 is monophonic — set at program level (not keygroup level)
    # to avoid envelope retrigger issues per MPC forum guidance
    _add_text_element(program, "Mono", str(params.mono))
    _add_text_element(program, "Program_Polyphony", str(params.program_polyphony))


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
    _add_float(layer, "Volume", params.layer_volume)
    _add_float(layer, "Pan", params.layer_pan)
    _add_float(layer, "Pitch", 0.0)
    _add_float(layer, "TuneCoarse", 0.0)
    _add_float(layer, "TuneFine", 0.0)
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
    _add_float(layer, "Volume", 0.0)
    _add_float(layer, "Pan", 0.500000)
    _add_float(layer, "Pitch", 0.0)
    _add_float(layer, "TuneCoarse", 0.0)
    _add_float(layer, "TuneFine", 0.0)
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


def _build_lfo(parent: ET.Element, params: TB303Params) -> ET.Element:
    """Build LFO configuration element.

    LFO is off by default (all depth values 0.0) but available for
    the user to enable via Q-Link for slow filter sweeps.
    """
    lfo = ET.SubElement(parent, "LFO")
    _add_text_element(lfo, "Type", params.lfo_type)
    _add_float(lfo, "Rate", params.lfo_rate)
    _add_text_element(lfo, "Sync", str(params.lfo_sync))
    _add_text_element(lfo, "Reset", str(params.lfo_reset))
    return lfo


def _build_instrument(parent: ET.Element, params: TB303Params) -> ET.Element:
    """Build an Instrument (keygroup) element with TB-303 parameters.

    Single keygroup spanning full MIDI range (0-127) with:
    - Layer 1: Sawtooth (active) -- TB-303 primary waveform
    - Layer 2: Square (muted) -- TB-303 alternate waveform, user-switchable
    - Layers 3-4: Empty

    Includes filter with zero keytrack, exponential envelope curves,
    velocity-to-accent routing, and LFO section.
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
    # The 303's diode ladder is effectively ~18dB/oct due to mismatched C18.
    # MPC's Low 4 (24dB/oct) is the closest option. We compensate by:
    # 1. Reducing resonance (0.40 vs typical 0.45+) to avoid harsh digital peak
    # 2. Using convex envelope decay curves for exponential RC character
    # 3. Recommending AIR Tube Drive insert for saturation (see post-load setup)
    _add_text_element(instrument, "FilterType", str(params.filter_type))
    _add_float(instrument, "Cutoff", params.cutoff)
    _add_float(instrument, "Resonance", params.resonance)
    _add_float(instrument, "FilterEnvAmt", params.filter_env_amt)
    # TB-303: No filter keyboard tracking — cutoff is fixed regardless of pitch
    _add_float(instrument, "FilterKeytrack", params.filter_keytrack)
    # Velocity → filter cutoff (accent brightening)
    _add_float(instrument, "VelocityToFilter", params.velocity_to_filter)
    # Velocity → filter envelope depth (accented notes get deeper sweep)
    _add_float(instrument, "VelocityToFilterEnvelope", params.velocity_to_filter_env)

    # --- Filter Envelope: Fast attack, exponential decay, no sustain ---
    _add_float(instrument, "FilterAttack", params.filter_attack)
    _add_float(instrument, "FilterHold", params.filter_hold)
    _add_float(instrument, "FilterDecay", params.filter_decay)
    _add_float(instrument, "FilterSustain", params.filter_sustain)
    _add_float(instrument, "FilterRelease", params.filter_release)
    # Envelope curve shapes — convex (>0.5) for exponential RC decay character
    _add_float(instrument, "FilterAttackCurve", params.filter_attack_curve)
    _add_float(instrument, "FilterDecayCurve", params.filter_decay_curve)
    _add_float(instrument, "FilterReleaseCurve", params.filter_release_curve)

    # --- Volume Envelope: Instant attack, long decay (TB-303 VEG) ---
    # The VEG's ~3.5s decay means notes sustain long at VCA level while
    # the filter envelope creates the perceived "pluck" — timbral envelope
    # is fast and snappy while amplitude envelope is slow and gentle.
    _add_float(instrument, "VolumeAttack", params.volume_attack)
    _add_float(instrument, "VolumeHold", params.volume_hold)
    _add_float(instrument, "VolumeDecay", params.volume_decay)
    _add_float(instrument, "VolumeSustain", params.volume_sustain)
    _add_float(instrument, "VolumeRelease", params.volume_release)
    _add_float(instrument, "VolumeAttackCurve", params.volume_attack_curve)
    _add_float(instrument, "VolumeDecayCurve", params.volume_decay_curve)
    _add_float(instrument, "VolumeReleaseCurve", params.volume_release_curve)

    # --- Pitch Envelope: Neutral (no pitch modulation on stock 303) ---
    _add_float(instrument, "PitchAttack", params.pitch_attack)
    _add_float(instrument, "PitchHold", params.pitch_hold)
    _add_float(instrument, "PitchDecay", params.pitch_decay)
    _add_float(instrument, "PitchSustain", params.pitch_sustain)
    _add_float(instrument, "PitchRelease", params.pitch_release)
    _add_float(instrument, "PitchEnvAmount", params.pitch_env_amount)

    # --- Velocity / Accent Routing ---
    # TB-303 accent simultaneously: boosts VCA, sweeps filter, deepens envelope.
    # We map MIDI velocity to approximate this multi-path accent behavior.
    _add_float(instrument, "VelocitySensitivity", params.velocity_sensitivity)
    _add_float(instrument, "VelocityToStart", params.velocity_to_start)
    _add_float(instrument, "VelocityToFilterAttack", params.velocity_to_filter_attack)
    _add_float(instrument, "VelocityToPitch", params.velocity_to_pitch)
    _add_float(instrument, "VelocityToVolumeAttack", params.velocity_to_volume_attack)
    _add_float(instrument, "VelocityToPan", params.velocity_to_pan)
    _add_float(instrument, "AfterTouchToFilter", params.aftertouch_to_filter)

    # --- LFO ---
    # Depth controls (all off by default)
    _add_float(instrument, "LfoPitch", params.lfo_pitch)
    _add_float(instrument, "LfoCutoff", params.lfo_cutoff)
    _add_float(instrument, "LfoVolume", params.lfo_volume)
    _add_float(instrument, "LfoPan", params.lfo_pan)
    # LFO configuration
    _build_lfo(instrument, params)

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


def _build_qlink_assignments(parent: ET.Element, params: TB303Params) -> ET.Element:
    """Build Q-Link assignment configuration for real-time performance control.

    Q-Links 1-2: Cutoff and Resonance (core 303 controls)
    Q-Links 5-6: Volume and Pan
    Remaining: Unassigned (user can bind via Q-Link Learn on device for
    Filter Env Amount, Filter Decay, Accent Depth, etc.)
    """
    qlinks = ET.SubElement(parent, "QLinkAssignments")
    program_mode = ET.SubElement(qlinks, "ProgramMode")
    for i, (param_id, momentary) in enumerate(params.qlink_assignments, start=1):
        qlink = ET.SubElement(program_mode, "QLink")
        qlink.set("index", str(i))
        _add_text_element(qlink, "Parameter", str(param_id))
        _add_text_element(qlink, "Momentary", str(momentary))
    return qlinks


def _build_pad_group_map(parent: ET.Element) -> ET.Element:
    """Build the PadGroupMap section (128 entries, all Group 0)."""
    pad_group_map = ET.SubElement(parent, "PadGroupMap")
    for _ in range(128):
        pad_group = ET.SubElement(pad_group_map, "PadGroup")
        _add_text_element(pad_group, "Group", "0")
    return pad_group_map


def build_xpm(params: TB303Params | None = None) -> ET.Element:
    """Build the complete XPM XML tree for a TB-303 emulation program.

    Generates a fully configured MPC keygroup program with:
    - Monophonic voice mode
    - 4-pole LP filter with zero keytrack and exponential envelope curves
    - Multi-path velocity/accent routing (filter cutoff + VCA + envelope depth)
    - LFO section (off by default)
    - Q-Link performance mappings
    - Insert effects bus enabled for post-load AIR FX configuration

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

    # Program-level header (audio routing, mono mode, volume)
    _build_program_header(program, params)

    # Instruments (keygroups)
    instruments = ET.SubElement(program, "Instruments")
    _build_instrument(instruments, params)

    # Pad note map: 128 entries (pad index → MIDI note)
    pad_note_map = ET.SubElement(program, "PadNoteMap")
    for note in range(128):
        pad_note = ET.SubElement(pad_note_map, "PadNote")
        _add_text_element(pad_note, "Note", str(note))

    # Pad group map: 128 entries (all Group 0)
    _build_pad_group_map(program)

    # Program-level keygroup settings
    _add_float(program, "KeygroupMasterTranspose", 0.500000)
    _add_text_element(program, "KeygroupNumKeygroups", "1")
    _add_float(program, "KeygroupPitchBendRange", 0.500000)
    _add_float(program, "KeygroupWheelToLfo", 1.000000)
    _add_float(program, "KeygroupAftertouchToFilter", 0.000000)

    # Q-Link assignments for real-time performance control
    _build_qlink_assignments(program, params)

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
