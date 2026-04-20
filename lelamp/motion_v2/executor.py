from __future__ import annotations

from typing import Any

_DEFAULT_LED_COUNT = 64


def execute_compiled_program(
    *,
    compiled: dict[str, Any],
    animation_service: Any = None,
    rgb_service: Any = None,
) -> dict[str, Any]:
    frames = [_normalize_frame(frame) for frame in compiled.get("frames", [])]
    lighting = compiled.get("lighting")

    if animation_service is not None and frames:
        animation_service.dispatch("frames", frames)

    light_event_count = 0
    if rgb_service is not None and isinstance(lighting, dict):
        mode = lighting.get("mode")
        if mode == "solid" and isinstance(lighting.get("rgb"), (list, tuple)):
            rgb_service.dispatch("solid", tuple(lighting["rgb"]))
            light_event_count = 1
        elif mode == "gradient" and isinstance(lighting.get("palette"), list):
            led_count = int(getattr(rgb_service, "led_count", _DEFAULT_LED_COUNT))
            palette = [tuple(color) for color in lighting["palette"]]
            rgb_service.dispatch(
                "paint",
                _expand_gradient_palette(palette, led_count=max(1, led_count)),
            )
            light_event_count = 1

    return {
        "decision": compiled.get("decision", "exact"),
        "motion_frame_count": len(frames),
        "light_event_count": light_event_count,
    }


def _normalize_frame(frame: Any) -> dict[str, float]:
    if not isinstance(frame, dict):
        return {}
    normalized: dict[str, float] = {}
    for joint_name, value in frame.items():
        key = str(joint_name)
        if not key.endswith(".pos"):
            key = f"{key}.pos"
        normalized[key] = float(value)
    return normalized


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
