import unittest

from lelamp.reply_sanitizer import sanitize_spoken_reply


class ReplySanitizerTests(unittest.TestCase):
    def test_sanitizes_light_narration_into_clean_dialogue(self) -> None:
        self.assertEqual(
            sanitize_spoken_reply("那我给你亮个节奏灯，你弹你的，我跟着晃。不过别太吵。"),
            "你弹你的，我陪着你。不过别太吵。",
        )

    def test_removes_bracketed_stage_directions(self) -> None:
        self.assertEqual(
            sanitize_spoken_reply("哼。(shock + 白光)你又来了？"),
            "哼。你又来了？",
        )

    def test_strips_follow_up_prompt_that_stalls_action_execution(self) -> None:
        self.assertEqual(
            sanitize_spoken_reply("好嘞！工作模式启动，灯光给你来个“元气满满”的开场！想先试试哪个动作？"),
            "好嘞！",
        )

    def test_strips_motion_narration_from_direct_execution_reply(self) -> None:
        self.assertEqual(
            sanitize_spoken_reply("好，家军你看——灯灯给你抬个头，害羞地晃一下～"),
            "好，家军你看。",
        )

    def test_strips_inline_express_tags_and_overwritten_clarification(self) -> None:
        self.assertEqual(
            sanitize_spoken_reply(
                "<express> calm </express> 嗯？你是在嘀咕什么悄悄话吗？灯灯没太听清，不过没关系，我就这样静静陪着你。"
            ),
            "嗯？你说啥？",
        )

    def test_strips_meta_narration_from_headshake_reply(self) -> None:
        self.assertEqual(
            sanitize_spoken_reply('好嘞，摇一下～灯灯给你晃个脑袋，像不像在说“不知道呀”？'),
            "好嘞。",
        )

    def test_strips_idle_state_stage_narration(self) -> None:
        self.assertEqual(
            sanitize_spoken_reply(
                "我呀，现在就是安安静静待着。灯光是暖黄的，轻轻晃一下，像个小毛球一样。你靠过来一点，我就这样陪着你，不说话也不乱动。"
            ),
            "我就在这儿陪你。",
        )

    def test_strips_babysitting_language_from_fatigue_prompt(self) -> None:
        self.assertEqual(
            sanitize_spoken_reply(
                "哎，你看起来有点累呢。是不是忙太久啦？要不要先歇一会儿，喝口水？灯灯在这儿陪着你呢。"
            ),
            "你该休息一下了，喝口水。",
        )


if __name__ == "__main__":
    unittest.main()
