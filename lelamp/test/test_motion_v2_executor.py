from __future__ import annotations

from lelamp.motion_v2.executor import execute_compiled_program


def test_execute_compiled_program_expands_gradient_palette_to_led_count() -> None:
    class _Service:
        def __init__(self) -> None:
            self.calls = []
            self.led_count = 8

        def dispatch(self, event_type: str, payload: object) -> None:
            self.calls.append((event_type, payload))

    animation = _Service()
    rgb = _Service()

    result = execute_compiled_program(
        compiled={
            "decision": "exact",
            "frames": [{"base_pitch.pos": 40.0}, {"base_pitch.pos": 48.0}],
            "lighting": {
                "mode": "gradient",
                "palette": [(0, 0, 0), (70, 0, 0)],
            },
        },
        animation_service=animation,
        rgb_service=rgb,
    )

    assert result["motion_frame_count"] == 2
    assert animation.calls == [
        ("frames", [{"base_pitch.pos": 40.0}, {"base_pitch.pos": 48.0}])
    ]
    assert rgb.calls == [
        (
            "paint",
            [
                (0, 0, 0),
                (10, 0, 0),
                (20, 0, 0),
                (30, 0, 0),
                (40, 0, 0),
                (50, 0, 0),
                (60, 0, 0),
                (70, 0, 0),
            ],
        )
    ]
