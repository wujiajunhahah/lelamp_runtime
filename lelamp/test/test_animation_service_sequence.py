from __future__ import annotations

from lelamp.service.motors.animation_service import AnimationService


def test_handle_sequence_concatenates_recordings_into_one_playback():
    service = AnimationService(
        port="/dev/null",
        lamp_id="lelamp",
        fps=30,
        duration=0.2,
        idle_recording="idle",
        home_recording="home_safe",
        use_home_pose_relative=False,
    )
    service.robot = object()
    service._current_state = {"base_pitch.pos": 0.0}
    service._load_recording = lambda name: {
        "happy_wiggle": [{"base_pitch.pos": 0.1}, {"base_pitch.pos": 0.2}],
        "excited": [{"base_pitch.pos": 0.3}],
        "scanning": [{"base_pitch.pos": 0.4}, {"base_pitch.pos": 0.5}],
    }[name]

    service._handle_sequence(["happy_wiggle", "excited", "scanning"])

    assert service._current_recording == "sequence:happy_wiggle,excited,scanning"
    assert service._current_actions == [
        {"base_pitch.pos": 0.1},
        {"base_pitch.pos": 0.2},
        {"base_pitch.pos": 0.3},
        {"base_pitch.pos": 0.4},
        {"base_pitch.pos": 0.5},
    ]
    assert service._current_frame_index == 0
    assert service._interpolation_target == {"base_pitch.pos": 0.1}
    assert service._interpolation_frames == int(service.duration * service.fps)
