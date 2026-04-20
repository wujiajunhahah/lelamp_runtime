from __future__ import annotations

import getpass
import os


_DEFAULT_MIXER_CONTROLS = ("PCM", "Line", "Line DAC", "HP", "HP DAC")
_PLAYBACK_SWITCH_CONTROLS = frozenset({"Line", "HP"})
_FIXED_GAIN_CONTROLS = frozenset({"PCM", "Line DAC", "HP DAC"})


def build_amixer_volume_commands(
    *,
    audio_user: str,
    card_index: int,
    volume_percent: int,
    controls: tuple[str, ...] = _DEFAULT_MIXER_CONTROLS,
) -> list[list[str]]:
    current_user = getpass.getuser()
    should_use_sudo = os.geteuid() == 0 and current_user != audio_user
    command_prefix = ["sudo", "-u", audio_user] if should_use_sudo else []

    commands: list[list[str]] = []
    for control in controls:
        target_volume = 100 if control in _FIXED_GAIN_CONTROLS else volume_percent
        commands.append(
            command_prefix
            + ["amixer", "-c", str(card_index), "sset", control, f"{target_volume}%"]
        )
        if control in _PLAYBACK_SWITCH_CONTROLS:
            commands.append(
                command_prefix
                + ["amixer", "-c", str(card_index), "sset", control, "unmute"]
            )
    return commands
