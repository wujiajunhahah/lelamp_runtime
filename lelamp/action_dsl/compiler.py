"""Lower constrained scenes into current motion/RGB dispatch events."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .schema import validate_scene

_GESTURE_RECORDINGS = {
    "nod": "nod",
    "greeting": "wake_up",
    "happy": "happy_wiggle",
    "happy_wiggle": "happy_wiggle",
    "curious": "curious",
    "sad": "sad",
    "shock": "shock",
    "shy": "shy",
    "worried": "headshake",
    "headshake": "headshake",
    "calm": "idle",
}
_LOOK_RECORDINGS = {
    "left": "curious",
    "right": "curious",
    "up": "wake_up",
    "down": "shy",
    "center": "idle",
}
_SETTLE_RECORDINGS = {
    "soft": "home_safe",
    "home": "home_safe",
    "idle": "idle",
    "off": "power_off",
    "power_off": "power_off",
    "wake": "wake_up",
    "wake_up": "wake_up",
}
_DEFAULT_LED_COUNT = 64


def compile_scene(scene: Mapping[str, Any]) -> dict[str, list[tuple[str, object]]]:
    validate_scene(scene)
    motion_events: list[tuple[str, object]] = []
    light_events: list[tuple[str, object]] = []
    has_visible_body_motion = False

    for node in scene.get("body", []):
        primitive = node["type"]
        if primitive == "pose":
            motion_events.append(("play", str(node["name"])))
            has_visible_body_motion = True
            continue
        if primitive == "gesture":
            recording = _GESTURE_RECORDINGS.get(str(node["name"]))
            if recording is None:
                raise ValueError(f"unsupported gesture: {node['name']!r}")
            repeats = int(node.get("repeats", 1))
            motion_events.extend([("play", recording)] * repeats)
            has_visible_body_motion = True
            continue
        if primitive == "look":
            recording = _LOOK_RECORDINGS.get(str(node["direction"]).lower())
            if recording is None:
                raise ValueError(f"unsupported look direction: {node['direction']!r}")
            motion_events.append(("play", recording))
            has_visible_body_motion = True
            continue
        if primitive == "sweep":
            motion_events.append(("play", "wake_up"))
            has_visible_body_motion = True
            continue
        if primitive == "settle":
            # AnimationService already interpolates non-idle recordings back to the
            # idle/home pose. Emitting a second explicit settle right after a
            # visible motion overrides the first playback too quickly to see it.
            if has_visible_body_motion:
                continue
            recording = _SETTLE_RECORDINGS.get(str(node["style"]).lower())
            if recording is None:
                raise ValueError(f"unsupported settle style: {node['style']!r}")
            motion_events.append(("play", recording))
            continue
        raise ValueError(f"unsupported primitive: {primitive!r}")

    for node in scene.get("light", []):
        primitive = node["type"]
        if primitive == "solid":
            light_events.append(("solid", tuple(node["rgb"])))
            continue
        palette = [tuple(color) for color in node["palette"]]
        if primitive == "gradient":
            light_events.append(("paint", _expand_gradient_palette(palette, led_count=_DEFAULT_LED_COUNT)))
            continue
        if primitive in {"pulse", "sparkle"}:
            light_events.append(("paint", _tile_palette(palette, led_count=_DEFAULT_LED_COUNT)))
            continue
        raise ValueError(f"unsupported primitive: {primitive!r}")

    return {"motion": motion_events, "light": light_events}


def _tile_palette(
    palette: list[tuple[int, int, int]],
    *,
    led_count: int,
) -> list[tuple[int, int, int]]:
    if not palette:
        return [(0, 0, 0)] * led_count
    return [palette[index % len(palette)] for index in range(led_count)]


def _expand_gradient_palette(
    palette: list[tuple[int, int, int]],
    *,
    led_count: int,
) -> list[tuple[int, int, int]]:
    if not palette:
        return [(0, 0, 0)] * led_count
    if len(palette) == 1:
        return [palette[0]] * led_count

    stops = len(palette) - 1
    colors: list[tuple[int, int, int]] = []
    for index in range(led_count):
        position = 0.0 if led_count <= 1 else index / (led_count - 1)
        segment_position = min(position * stops, float(stops))
        left_index = min(int(segment_position), stops - 1)
        right_index = left_index + 1
        blend = segment_position - left_index
        left = palette[left_index]
        right = palette[right_index]
        colors.append(
            tuple(
                int(round(left[channel] + (right[channel] - left[channel]) * blend))
                for channel in range(3)
            )
        )
    return colors
