"""First-pass synchronous manager implementation."""

from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lelamp.runtime_config import RuntimeSettings


_DEMO_RECORDINGS = (
    "happy_wiggle",
    "excited",
    "scanning",
    "curious",
    "nod",
    "headshake",
    "shy",
    "shock",
    "sad",
    "wake_up",
    "idle",
)
_RECORDING_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("狂野", "excited"),
    ("疯狂", "excited"),
    ("激动", "excited"),
    ("扫描", "scanning"),
    ("扫一圈", "scanning"),
    ("东张西望", "scanning"),
    ("好奇", "curious"),
    ("点头", "nod"),
    ("摇头", "headshake"),
    ("害羞", "shy"),
    ("震惊", "shock"),
    ("惊讶", "shock"),
    ("难过", "sad"),
)
_LIGHT_STEPS = {
    "happy_wiggle": {"type": "sparkle", "palette": [[255, 180, 70], [255, 120, 40], [70, 255, 120]]},
    "excited": {"type": "sparkle", "palette": [[255, 80, 60], [255, 220, 90], [255, 255, 255]]},
    "scanning": {"type": "gradient", "palette": [[90, 170, 255], [220, 245, 255]]},
    "curious": {"type": "gradient", "palette": [[220, 235, 255], [140, 180, 255]]},
    "nod": {"type": "solid", "rgb": [255, 175, 90]},
    "headshake": {"type": "solid", "rgb": [255, 140, 70]},
    "shy": {"type": "solid", "rgb": [255, 200, 90]},
    "shock": {"type": "solid", "rgb": [255, 255, 255]},
    "sad": {"type": "solid", "rgb": [255, 90, 60]},
    "wake_up": {"type": "gradient", "palette": [[255, 170, 70], [255, 235, 180]]},
    "idle": {"type": "solid", "rgb": [255, 200, 135]},
}
_GENERAL_SEQUENCE_PRESETS: tuple[tuple[str, ...], ...] = (
    ("happy_wiggle", "excited", "scanning"),
    ("curious", "nod", "headshake"),
    ("wake_up", "curious", "excited"),
    ("shy", "shock", "sad"),
)
_NOVEL_SEQUENCE_PRESETS: tuple[tuple[str, ...], ...] = (
    ("curious", "headshake", "shock"),
    ("shy", "nod", "sad"),
    ("wake_up", "curious", "headshake"),
)
_SHOWCASE_PALETTES: dict[str, tuple[tuple[list[int], ...], ...]] = {
    "playful": (
        ([255, 160, 80], [255, 225, 120], [120, 255, 190]),
        ([255, 120, 70], [255, 210, 110], [90, 170, 255]),
    ),
    "sequence": (
        ([120, 180, 255], [255, 255, 255], [255, 190, 120]),
        ([100, 220, 255], [210, 240, 255], [255, 170, 110]),
    ),
    "novel": (
        ([255, 110, 80], [255, 250, 240], [140, 220, 255]),
        ([255, 210, 90], [255, 130, 120], [120, 255, 210]),
        ([190, 150, 255], [255, 245, 220], [120, 220, 255]),
    ),
}


class GLMManager:
    def __init__(self, *, settings: "RuntimeSettings") -> None:
        self._settings = settings

    @property
    def settings(self) -> "RuntimeSettings":
        return self._settings

    def process(
        self,
        *,
        items: list[dict[str, Any]],
        previous_snapshot: dict[str, Any] | None,
    ) -> dict[str, Any]:
        del previous_snapshot
        last_user_turn = next(
            (item for item in reversed(items) if item.get("kind") == "conversation.user_turn"),
            None,
        )
        text = str((((last_user_turn or {}).get("payload") or {}).get("text", "")) or "").strip()
        profile_summary = f"Recent user theme: {text}".strip()
        action_program = _action_program_for_text(text)
        scene_proposal = _scene_proposal_for_text(text) if action_program is None else None
        scene_priors = {}
        if action_program is not None:
            scene_priors = {action_program["intent"]: list(action_program["priors"])}
        elif scene_proposal is not None:
            scene_priors = {scene_proposal["intent"]: list(scene_proposal["priors"])}

        result = {
            "profile_summary": profile_summary,
            "preference_hints": [],
            "scene_priors": scene_priors,
            "banned_patterns": ["repeat same scene twice in a row"],
            "updated_at_ms": int(time.time() * 1000),
        }
        if action_program is not None:
            result["_action_program"] = {
                "summary": action_program["summary"],
                "program": action_program["program"],
                "source_item_id": (last_user_turn or {}).get("item_id"),
            }
        if scene_proposal is not None:
            result["_scene_proposal"] = {
                "summary": scene_proposal["summary"],
                "scene": scene_proposal["scene"],
                "source_item_id": (last_user_turn or {}).get("item_id"),
            }
        return result


def _action_program_for_text(text: str) -> dict[str, Any] | None:
    lowered = text.lower()
    if _contains_any(
        lowered,
        text,
        "头部",
        "只动头",
        "只要头",
        "head only",
    ) and (
        _contains_any(
            lowered,
            text,
            "看一下",
            "来看一下",
            "看我",
            "look",
            "看过来",
        )
        or _matches_any(
            text,
            r"头.?部.*看一下",
            r"只要头.*看一下",
        )
    ):
        return _build_head_only_action_program(text)

    if _contains_any(lowered, text, "抬头", "仰头", "look up", "往上看", "向上看") or _matches_any(
        text,
        r"抬.?头",
        r"头抬.?一下",
    ):
        return {
            "intent": "proud_look_up",
            "priors": ["cool gradient", "upward sweep"],
            "summary": "User requested a confident upward attention shift.",
            "program": {
                "version": "v2",
                "intent": "proud_look_up",
                "why": "User asked the lamp to look up.",
                "expression": {
                    "attention": "up",
                    "attitude": "confident",
                    "emotion": "warm",
                    "novelty": 0.62,
                },
                "style": {
                    "exaggeration": 0.74,
                    "smoothness": 0.38,
                    "tension": 0.52,
                    "tempo": 1.0,
                    "symmetry_break": 0.18,
                },
                "settle_policy": {
                    "return_to_home_bias": 0.55,
                    "preserve_attention_heading": True,
                },
                "phases": [
                    {
                        "name": "prepare",
                        "duration_ms": 140,
                        "easing": "ease_out",
                        "joints": {
                            "base_pitch": {"target": -0.12, "role": "lead"},
                            "elbow_pitch": {"target": 0.06, "role": "support"},
                        },
                    },
                    {
                        "name": "accent",
                        "duration_ms": 220,
                        "easing": "ease_in_out",
                        "joints": {
                            "base_pitch": {"target": 0.70, "role": "lead"},
                            "wrist_pitch": {"target": 0.14, "role": "support"},
                            "wrist_roll": {"target": 0.06, "role": "accent"},
                        },
                    },
                ],
                "lighting": {
                    "mode": "gradient",
                    "palette": [[120, 180, 255], [255, 255, 255]],
                },
            },
        }

    explicit_recordings = _extract_exact_recording_mentions(text)
    if explicit_recordings and _matches_any(
        text,
        r"来.*(动作|一遍|一组)",
        r"(动作|录制|pose).*(来|做|放)",
    ):
        return None

    if _contains_any(
        lowered,
        text,
        "完全没有做过",
        "没做过",
        "没玩过",
        "没见过",
        "新的动作",
        "新动作",
        "给我个新动作",
        "新一点",
        "换一组",
        "换个组合",
        "别老那几个",
        "不一样",
        "动作看看",
    ):
        return _build_showcase_action_program(
            text=text,
            intent="novel_showcase",
            summary="User requested a novel motion showcase.",
            priors=["novel motion_v2 phrasing", "fresh lighting cadence"],
            flavor="novel",
            attention="forward",
            attitude="playful",
            emotion="mischievous",
            phase_count=4,
            novelty_range=(0.84, 0.96),
        )

    if _contains_any(
        lowered,
        text,
        "连续",
        "多个动作",
        "几个动作",
        "一组动作",
        "组合动作",
        "串起来",
        "别只来一个",
        "多来几个",
        "灯光也变",
        "灯光也切换",
    ):
        return _build_showcase_action_program(
            text=text,
            intent="sequence_showcase",
            summary="User requested a multi-step motion showcase.",
            priors=["multi-phase motion_v2 sequence", "coordinated gradient lighting"],
            flavor="sequence",
            attention="forward",
            attitude="confident",
            emotion="bright",
            phase_count=4,
            novelty_range=(0.72, 0.84),
        )

    if _contains_any(
        lowered,
        text,
        "跳舞",
        "舞蹈",
        "跳个舞",
        "舞给我看",
        "dance",
        "摇摆",
        "摇一摇",
        "来个动作",
        "玩个动作",
        "随便来一个",
        "狂野的动作",
        "动作看看",
        "直接执行",
        "直接做",
        "用动作来表示",
        "动作来表示",
        "酷一点",
    ) or _matches_any(
        text,
        r"来.?个动作",
        r"玩.?个动作",
        r"随便来.?个",
    ):
        return _build_showcase_action_program(
            text=text,
            intent="playful_showcase",
            summary="User requested a playful motion showcase.",
            priors=["playful motion_v2 phrasing", "warm energetic lighting"],
            flavor="playful",
            attention="forward",
            attitude="confident",
            emotion="warm",
            phase_count=3,
            novelty_range=(0.62, 0.78),
        )

    return None


def _build_head_only_action_program(text: str) -> dict[str, Any]:
    fingerprint = _text_fingerprint(text)
    side = _side_sign(fingerprint)
    pitch = _vary(fingerprint, salt=21, low=0.08, high=0.18)
    yaw = _vary(fingerprint, salt=22, low=0.14, high=0.24)
    novelty = _vary(fingerprint, salt=23, low=0.66, high=0.8)
    return {
        "intent": "head_only_glance",
        "priors": ["head-only motion_v2 phrasing", "compact lighting cue"],
        "summary": "User requested a head-only glance.",
        "program": {
            "version": "v2",
            "intent": "head_only_glance",
            "why": text,
            "expression": {
                "attention": "forward",
                "attitude": "precise",
                "emotion": "cool",
                "novelty": round(novelty, 3),
            },
            "style": {
                "exaggeration": 0.34,
                "smoothness": 0.62,
                "tension": 0.28,
                "tempo": 1.08,
                "symmetry_break": 0.12,
            },
            "settle_policy": {
                "return_to_home_bias": 0.74,
                "preserve_attention_heading": False,
            },
            "phases": [
                {
                    "name": "prepare",
                    "duration_ms": 110,
                    "easing": "ease_out",
                    "joints": {
                        "base_pitch": {"target": round(-pitch * 0.4, 3), "role": "lead"},
                    },
                },
                {
                    "name": "peek",
                    "duration_ms": 180,
                    "easing": "ease_in_out",
                    "joints": {
                        "base_pitch": {"target": round(pitch, 3), "role": "lead"},
                        "base_yaw": {"target": round(side * yaw, 3), "role": "support"},
                    },
                },
                {
                    "name": "settle",
                    "duration_ms": 140,
                    "easing": "ease_out",
                    "joints": {
                        "base_yaw": {"target": round(side * yaw * 0.35, 3), "role": "lead"},
                    },
                },
            ],
            "lighting": {
                "mode": "gradient",
                "palette": [[150, 210, 255], [255, 255, 255]],
            },
        },
    }


def _build_showcase_action_program(
    *,
    text: str,
    intent: str,
    summary: str,
    priors: list[str],
    flavor: str,
    attention: str,
    attitude: str,
    emotion: str,
    phase_count: int,
    novelty_range: tuple[float, float],
) -> dict[str, Any]:
    return {
        "intent": intent,
        "priors": priors,
        "summary": summary,
        "program": _build_showcase_program(
            text=text,
            intent=intent,
            flavor=flavor,
            attention=attention,
            attitude=attitude,
            emotion=emotion,
            phase_count=phase_count,
            novelty_range=novelty_range,
        ),
    }


def _build_showcase_program(
    *,
    text: str,
    intent: str,
    flavor: str,
    attention: str,
    attitude: str,
    emotion: str,
    phase_count: int,
    novelty_range: tuple[float, float],
) -> dict[str, Any]:
    fingerprint = _text_fingerprint(text)
    side = _side_sign(fingerprint)
    exaggeration = _vary(fingerprint, salt=1, low=0.58, high=0.76)
    smoothness = _vary(fingerprint, salt=2, low=0.34, high=0.64)
    tension = _vary(fingerprint, salt=3, low=0.42, high=0.72)
    tempo = _vary(fingerprint, salt=4, low=0.92, high=1.14)
    symmetry_break = _vary(fingerprint, salt=5, low=0.18, high=0.46)
    novelty = _vary(fingerprint, salt=6, low=novelty_range[0], high=novelty_range[1])
    lift = _vary(fingerprint, salt=7, low=0.34, high=0.66)
    yaw = _vary(fingerprint, salt=8, low=0.16, high=0.34)
    elbow = _vary(fingerprint, salt=9, low=0.08, high=0.22)
    wrist_pitch = _vary(fingerprint, salt=10, low=0.10, high=0.24)
    roll = _vary(fingerprint, salt=11, low=0.05, high=0.12)
    palette = _palette_for_text(flavor=flavor, fingerprint=fingerprint)
    phases = [
        {
            "name": "windup",
            "duration_ms": int(_vary(fingerprint, salt=12, low=120, high=180)),
            "easing": "ease_out",
            "joints": {
                "base_yaw": {"target": round(-side * yaw * 0.55, 3), "role": "lead"},
                "elbow_pitch": {"target": round(elbow * 0.45, 3), "role": "support"},
                "wrist_roll": {"target": round(side * roll * 0.8, 3), "role": "accent"},
            },
        },
        {
            "name": "lift",
            "duration_ms": int(_vary(fingerprint, salt=13, low=180, high=260)),
            "easing": "ease_in_out",
            "joints": {
                "base_pitch": {"target": round(lift, 3), "role": "lead"},
                "wrist_pitch": {"target": round(wrist_pitch, 3), "role": "support"},
                "wrist_roll": {"target": round(side * roll, 3), "role": "accent"},
            },
        },
        {
            "name": "switch",
            "duration_ms": int(_vary(fingerprint, salt=14, low=150, high=230)),
            "easing": "ease_in_out",
            "joints": {
                "base_yaw": {"target": round(side * yaw, 3), "role": "lead"},
                "elbow_pitch": {"target": round(elbow, 3), "role": "support"},
                "wrist_roll": {"target": round(-side * roll, 3), "role": "accent"},
            },
        },
    ]
    if phase_count >= 4:
        phases.append(
            {
                "name": "accent",
                "duration_ms": int(_vary(fingerprint, salt=15, low=180, high=280)),
                "easing": "ease_out",
                "joints": {
                    "base_pitch": {"target": round(lift * 0.88, 3), "role": "lead"},
                    "base_yaw": {"target": round(side * yaw * 0.4, 3), "role": "support"},
                    "wrist_pitch": {
                        "target": round(wrist_pitch * 0.7, 3),
                        "role": "accent",
                    },
                },
            }
        )

    return {
        "version": "v2",
        "intent": intent,
        "why": text,
        "expression": {
            "attention": attention,
            "attitude": attitude,
            "emotion": emotion,
            "novelty": round(novelty, 3),
        },
        "style": {
            "exaggeration": round(exaggeration, 3),
            "smoothness": round(smoothness, 3),
            "tension": round(tension, 3),
            "tempo": round(tempo, 3),
            "symmetry_break": round(symmetry_break, 3),
        },
        "settle_policy": {
            "return_to_home_bias": round(_vary(fingerprint, salt=16, low=0.42, high=0.68), 3),
            "preserve_attention_heading": phase_count <= 3,
        },
        "phases": phases,
        "lighting": {"mode": "gradient", "palette": palette},
    }


def _palette_for_text(*, flavor: str, fingerprint: int) -> list[list[int]]:
    palettes = _SHOWCASE_PALETTES.get(flavor) or _SHOWCASE_PALETTES["playful"]
    palette = palettes[fingerprint % len(palettes)]
    return [list(color) for color in palette]


def _text_fingerprint(text: str) -> int:
    total = 0
    for index, char in enumerate(text, start=1):
        total += index * ord(char)
    return total or 1


def _vary(fingerprint: int, *, salt: int, low: float, high: float) -> float:
    bucket = ((fingerprint * (salt * 37 + 11)) % 1000) / 999.0
    return low + (high - low) * bucket


def _side_sign(fingerprint: int) -> float:
    return -1.0 if fingerprint % 2 else 1.0


def _scene_proposal_for_text(text: str) -> dict[str, Any] | None:
    lowered = text.lower()
    explicit_recordings = _extract_exact_recording_mentions(text)
    if explicit_recordings and _matches_any(text, r"来.*(动作|一遍|一组)", r"(动作|录制|pose).*(来|做|放)"):
        return _build_recording_sequence_proposal(
            explicit_recordings,
            intent="custom_sequence",
            summary="User requested a custom motion sequence.",
        )
    if _contains_any(
        lowered,
        text,
        "完全没有做过",
        "没做过",
        "没玩过",
        "没见过",
        "新的动作",
        "新一点",
        "换一组",
        "换个组合",
        "别老那几个",
        "不一样",
    ):
        return _build_recording_sequence_proposal(
            _pick_sequence_preset(text, presets=_NOVEL_SEQUENCE_PRESETS),
            intent="novel_sequence",
            summary="User requested a fresh motion sequence.",
        )
    if _contains_any(
        lowered,
        text,
        "连续",
        "多个动作",
        "几个动作",
        "一组动作",
        "组合动作",
        "串起来",
        "别只来一个",
        "多来几个",
        "灯光也变",
        "灯光也切换",
    ):
        return _build_recording_sequence_proposal(
            _select_demo_recordings(text),
            intent="playful_sequence",
            summary="User requested a multi-step motion demo.",
        )
    if _contains_any(
        lowered,
        text,
        "跳舞",
        "舞蹈",
        "跳个舞",
        "舞给我看",
        "dance",
        "摇摆",
        "摇一摇",
        "来个动作",
        "玩个动作",
        "随便来一个",
        "狂野的动作",
        "直接执行",
        "直接做",
        "用动作来表示",
        "动作来表示",
    ) or _matches_any(
        text,
        r"来.?个动作",
        r"玩.?个动作",
        r"随便来.?个",
    ):
        return {
            "intent": "playful",
            "priors": ["sparkle palette", "happy wiggle"],
            "summary": "User requested a playful dance response.",
            "scene": {
                "body": [{"type": "gesture", "name": "happy", "intensity": 0.8, "repeats": 2}],
                "light": [{"type": "sparkle", "palette": [[255, 120, 40], [255, 220, 90], [70, 255, 120]]}],
            },
        }
    if _contains_any(lowered, text, "仰头", "仰个头", "抬头", "往上看", "向上看", "look up"):
        return {
            "intent": "look_up",
            "priors": ["cool gradient", "upward sweep"],
            "summary": "User requested an upward look response.",
            "scene": {
                "body": [{"type": "look", "direction": "up"}, {"type": "settle", "style": "soft"}],
                "light": [{"type": "gradient", "palette": [[120, 180, 255], [255, 255, 255]]}],
            },
        }
    if _contains_any(lowered, text, "低头", "往下看", "向下看", "look down"):
        return {
            "intent": "look_down",
            "priors": ["soft amber", "downward tilt"],
            "summary": "User requested a downward look response.",
            "scene": {
                "body": [{"type": "look", "direction": "down"}, {"type": "settle", "style": "soft"}],
                "light": [{"type": "solid", "rgb": [255, 190, 120]}],
            },
        }
    if _contains_any(lowered, text, "往左看", "向左看", "看左边", "look left"):
        return {
            "intent": "look_left",
            "priors": ["cool side sweep", "left glance"],
            "summary": "User requested a leftward look response.",
            "scene": {
                "body": [{"type": "look", "direction": "left"}, {"type": "settle", "style": "soft"}],
                "light": [{"type": "gradient", "palette": [[90, 170, 255], [200, 235, 255]]}],
            },
        }
    if _contains_any(lowered, text, "往右看", "向右看", "看右边", "look right"):
        return {
            "intent": "look_right",
            "priors": ["warm side sweep", "right glance"],
            "summary": "User requested a rightward look response.",
            "scene": {
                "body": [{"type": "look", "direction": "right"}, {"type": "settle", "style": "soft"}],
                "light": [{"type": "gradient", "palette": [[255, 180, 120], [255, 235, 200]]}],
            },
        }
    if _contains_any(lowered, text, "点头", "nod"):
        return {
            "intent": "affirm",
            "priors": ["warm nod", "amber highlight"],
            "summary": "User requested a nod response.",
            "scene": {
                "body": [{"type": "gesture", "name": "nod", "intensity": 0.55, "repeats": 1}],
                "light": [{"type": "solid", "rgb": [255, 175, 90]}],
            },
        }
    return None


def _contains_any(lowered: str, original: str, *needles: str) -> bool:
    return any(needle in lowered or needle in original for needle in needles)


def _matches_any(text: str, *patterns: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _extract_requested_recordings(text: str) -> list[str]:
    lowered = text.lower()
    located: list[tuple[int, str]] = []
    for recording_name in _DEMO_RECORDINGS:
        index = lowered.find(recording_name.lower())
        if index >= 0:
            located.append((index, recording_name))
    for keyword, recording_name in _RECORDING_KEYWORDS:
        index = text.find(keyword)
        if index >= 0:
            located.append((index, recording_name))
    located.sort(key=lambda entry: entry[0])
    ordered: list[str] = []
    for _, recording_name in located:
        if recording_name not in ordered:
            ordered.append(recording_name)
    return ordered[:4]


def _extract_exact_recording_mentions(text: str) -> list[str]:
    lowered = text.lower()
    located: list[tuple[int, str]] = []
    for recording_name in _DEMO_RECORDINGS:
        index = lowered.find(recording_name.lower())
        if index >= 0:
            located.append((index, recording_name))
    located.sort(key=lambda entry: entry[0])
    ordered: list[str] = []
    for _, recording_name in located:
        if recording_name not in ordered:
            ordered.append(recording_name)
    return ordered[:4]


def _select_demo_recordings(text: str) -> list[str]:
    requested = _extract_requested_recordings(text)
    if requested:
        return requested
    lowered = text.lower()
    if _contains_any(lowered, text, "狂野", "疯狂", "炸裂", "high energy", "excited"):
        return ["excited", "happy_wiggle", "shock"]
    if _contains_any(lowered, text, "扫描", "扫一圈", "东张西望", "scanning"):
        return ["scanning", "curious", "nod"]
    return _pick_sequence_preset(text, presets=_GENERAL_SEQUENCE_PRESETS)


def _build_recording_sequence_proposal(
    recording_names: list[str],
    *,
    intent: str,
    summary: str,
) -> dict[str, Any]:
    body = [{"type": "pose", "name": name} for name in recording_names]
    light = [_LIGHT_STEPS[name] for name in recording_names if name in _LIGHT_STEPS]
    return {
        "intent": intent,
        "priors": [f"recording:{name}" for name in recording_names],
        "summary": summary,
        "scene": {
            "body": body,
            "light": light,
        },
    }


def _pick_sequence_preset(
    text: str,
    *,
    presets: tuple[tuple[str, ...], ...],
) -> list[str]:
    if not presets:
        return ["happy_wiggle", "excited", "scanning"]
    fingerprint = sum(ord(char) for char in text)
    return list(presets[fingerprint % len(presets)])
