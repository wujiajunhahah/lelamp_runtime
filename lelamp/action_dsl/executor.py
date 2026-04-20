"""Execute compiled DSL events through existing services."""

from __future__ import annotations

from typing import Any

from .compiler import compile_scene


def execute_compiled_scene(
    compiled: dict[str, list[tuple[str, object]]],
    *,
    animation_service: Any = None,
    rgb_service: Any = None,
) -> dict[str, list[tuple[str, object]]]:
    motion_events = list(compiled.get("motion", []))
    light_events = list(compiled.get("light", []))

    if animation_service is not None:
        if len(motion_events) > 1 and all(event_type == "play" for event_type, _ in motion_events):
            animation_service.dispatch("sequence", [payload for _, payload in motion_events])
        else:
            for event_type, payload in motion_events:
                animation_service.dispatch(event_type, payload)
    if rgb_service is not None:
        if len(light_events) > 1:
            rgb_service.dispatch("sequence", light_events)
        else:
            for event_type, payload in light_events:
                rgb_service.dispatch(event_type, payload)
    return compiled


def execute_scene(
    scene: dict[str, object],
    *,
    animation_service: Any = None,
    rgb_service: Any = None,
) -> dict[str, list[tuple[str, object]]]:
    compiled = compile_scene(scene)
    return execute_compiled_scene(
        compiled,
        animation_service=animation_service,
        rgb_service=rgb_service,
    )
