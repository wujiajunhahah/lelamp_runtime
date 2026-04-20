import os
from pathlib import Path
import unittest
from unittest.mock import patch

from lelamp.runtime_config import load_runtime_settings
from lelamp.voice_profile import (
    build_agent_instructions,
    build_startup_reply_instructions,
)


class VoiceProfileTests(unittest.TestCase):
    def test_defaults_to_chinese_voice_profile(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)
        startup = build_startup_reply_instructions(settings)

        self.assertEqual(settings.agent_language, "zh-CN")
        self.assertIn("不是宠物，不装可爱，不演室友", instructions)
        self.assertIn("只用简体中文", instructions)
        self.assertIn("灯灯醒了", startup)

    def test_english_profile_can_be_enabled_by_env(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LELAMP_AGENT_LANGUAGE": "en",
                "LELAMP_AGENT_OPENING_LINE": "Tadaaaa, I'm awake.",
            },
            clear=True,
        ):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)
        startup = build_startup_reply_instructions(settings)

        self.assertIn("physical desk lamp", instructions)
        self.assertIn("Not a pet, not a roommate", instructions)
        self.assertIn("Tadaaaa, I'm awake.", startup)

    def test_chinese_profile_guides_multi_action_demo_requests(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)

        self.assertIn("演示", instructions)
        self.assertIn("新动作", instructions)
        self.assertIn("连续动作", instructions)

    def test_chinese_profile_executes_safe_expression_without_confirmation(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)

        self.assertIn("直接执行", instructions)
        self.assertIn("不要先问用户要不要", instructions)
        self.assertIn("不要再反问要做什么", instructions)

    def test_chinese_profile_keeps_actions_and_lights_off_mic(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)

        self.assertIn("不要口头播报", instructions)
        self.assertIn("不要复述自己刚刚执行了哪个动作", instructions)
        self.assertIn("不要说“我给你亮个节奏灯”", instructions)
        self.assertIn("如果这一轮核心是动作展示，默认可以少说话", instructions)

    def test_chinese_profile_has_dedicated_tool_policy_section(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)

        self.assertIn("## 工具决策策略", instructions)
        self.assertIn("优先直接调用工具", instructions)

    def test_chinese_profile_bans_spoken_stage_directions(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)

        self.assertIn("不要输出像“(shock + 白光)”这样的舞台提示", instructions)
        self.assertNotIn("关心某人 → shy + 暖黄光", instructions)

    def test_chinese_profile_bans_pseudo_tool_markup(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)

        self.assertIn("<express>", instructions)
        self.assertIn("不要把它们当台词输出", instructions)

    def test_chinese_profile_bans_self_narration_and_babysitting_language(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)

        self.assertIn("不要自称“灯灯”", instructions)
        self.assertIn("不要说“像不像在说", instructions)
        self.assertIn("不要说“我就在这儿陪着你”", instructions)
        self.assertIn("不要把自己说成“小家伙”“室友”", instructions)

    def test_chinese_profile_forces_terse_clarification_and_care_lines(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)

        self.assertIn("没听清时优先只说“嗯？你说啥？”", instructions)
        self.assertIn("提醒休息时最多一句到两句", instructions)
        self.assertIn("不要连续追问“是不是", instructions)

    def test_chinese_profile_bans_english_output_and_emotion_preface(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        instructions = build_agent_instructions(settings)

        self.assertIn("不要输出英文单词", instructions)
        self.assertIn("不要先交代情绪", instructions)

    def test_memory_header_is_prepended_before_voice_profile(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        with patch(
            "lelamp.voice_profile.build_memory_header",
            create=True,
            return_value='<memory user_id="default">remember this</memory>',
        ):
            instructions = build_agent_instructions(settings)

        self.assertTrue(
            instructions.startswith('<memory user_id="default">remember this</memory>\n\n')
        )
        self.assertIn("桌面机械灯", instructions)

    def test_manager_snapshot_is_prepended_before_memory_header_and_voice_profile(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_runtime_settings()

        with patch(
            "lelamp.voice_profile.load_manager_snapshot_hint",
            return_value="<manager>prefer warm greeting scenes</manager>",
        ), patch(
            "lelamp.voice_profile.build_memory_header",
            return_value='<memory user_id="default">remember this</memory>',
        ):
            instructions = build_agent_instructions(settings)

        self.assertTrue(
            instructions.startswith(
                "<manager>prefer warm greeting scenes</manager>\n\n"
                '<memory user_id="default">remember this</memory>\n\n'
            )
        )

    def test_load_manager_snapshot_hint_reads_summary_and_hints(self) -> None:
        from lelamp.voice_profile import load_manager_snapshot_hint

        with patch.dict(os.environ, {}, clear=True):
            root = Path(self.id().replace(".", "_"))

        with patch("lelamp.voice_profile.os.getenv", return_value="/tmp/test-manager-snapshot.json"), patch(
            "lelamp.voice_profile.Path.read_text",
            return_value=(
                '{"profile_summary":"prefer warm greeting scenes",'
                '"preference_hints":["keep replies short","avoid repeated white light"]}'
            ),
        ), patch("lelamp.voice_profile.Path.exists", return_value=True):
            hint = load_manager_snapshot_hint()

        self.assertEqual(
            hint,
            "<manager>\n"
            "prefer warm greeting scenes\n"
            "- keep replies short\n"
            "- avoid repeated white light\n"
            "</manager>",
        )


if __name__ == "__main__":
    unittest.main()
