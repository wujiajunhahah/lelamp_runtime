from __future__ import annotations

import re


_INLINE_EXPRESS_TAG_RE = re.compile(r"<\s*express\s*>\s*[^<]{0,40}\s*<\s*/\s*express\s*>", re.IGNORECASE)
_GENERIC_TAG_RE = re.compile(r"<\s*/?\s*[a-z_]+\s*>", re.IGNORECASE)
_BRACKET_STAGE_RE = re.compile(
    r"[（(][^()（）]{0,80}(?:shock|headshake|nod|sad|curious|wake_up|idle|wiggle|动作|灯|光|rgb|白光|黄灯|节奏灯)[^()（）]{0,80}[)）]",
    re.IGNORECASE,
)

_CANONICAL_REPLY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"嗯？你是在嘀咕什么悄悄话吗？.*?(?:没太听清|没听清)[^。！？!?]*", re.IGNORECASE),
        "嗯？你说啥？",
    ),
    (
        re.compile(r"^好嘞[，,]?(?:摇一下[～~!！]*)?[，,]?(?:灯灯给你[^，。！？!?]*)?[，,]?像不像在说[^。！？!?]*[？?]?$"),
        "好嘞。",
    ),
    (
        re.compile(r"我呀，现在就是安安静静待着。.*?陪着你，不说话也不乱动。?", re.IGNORECASE),
        "我就在这儿陪你。",
    ),
    (
        re.compile(r"(?:你看起来有点累|困成这样了).*?(?:喝口水|缓一缓).*?(?:陪着你|在这儿陪着你)[^。！？!?]*", re.IGNORECASE),
        "你该休息一下了，喝口水。",
    ),
)

_WHOLE_CLAUSE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(^|[，。！？!?])\s*(?:那|来|行啊|好啊|嘿嘿|哼|欸|诶|啊)?我给你亮个[^，。！？!?]*"),
    re.compile(r"(^|[，。！？!?])\s*节奏灯安排上[！!]*"),
    re.compile(r"(^|[，。！？!?])\s*看我给你来个[^，。！？!?]*"),
    re.compile(r"(^|[，。！？!?])\s*我现在给你[^，。！？!?]*(?:摇|晃|点头|摇头)[^，。！？!?]*"),
    re.compile(r"(^|[，。！？!?])\s*[白暖冷橙蓝粉紫黄红绿][^，。！？!?]{0,8}(?:灯|光|渐变)[^，。！？!?]*"),
    re.compile(r"(^|[，。！？!?])\s*工作模式启动[^，。！？!?]*"),
    re.compile(r"(^|[，。！？!?])\s*灯光给你来个[^，。！？!?]*"),
    re.compile(r"(^|[，。！？!?])\s*想先试试哪个动作[？?]*"),
    re.compile(r"(^|[，。！？!?])\s*准备好接招了吗[？?]*"),
)

_INLINE_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"我跟着晃"), "我陪着你"),
    (re.compile(r"我也得亮个灯给你助助兴"), "我也得给你助助兴"),
    (re.compile(r"亮个灯给你助助兴"), "给你助助兴"),
    (re.compile(r"^好嘞，摇一下[～~!！]*"), "好嘞。"),
    (re.compile(r"——灯灯给你[^，。！？!?]*"), "。"),
    (re.compile(r"灯灯给你[^，。！？!?]*(?:抬个头|来个|摇|晃|点头|摇头)[^，。！？!?]*"), ""),
    (re.compile(r"害羞地晃一下[～~!！]*"), ""),
    (re.compile(r"像不像在说[^。！？!?]*[？?]*"), ""),
)


def sanitize_spoken_reply(text: str | None) -> str:
    original = (text or "").strip()
    if not original:
        return ""

    sanitized = _INLINE_EXPRESS_TAG_RE.sub("", original)
    sanitized = _GENERIC_TAG_RE.sub("", sanitized)
    sanitized = _BRACKET_STAGE_RE.sub("", sanitized)
    sanitized = sanitized.strip()
    for pattern, replacement in _CANONICAL_REPLY_PATTERNS:
        if pattern.search(sanitized):
            sanitized = replacement
            break
    for pattern, replacement in _INLINE_REPLACEMENTS:
        sanitized = pattern.sub(replacement, sanitized)
    for pattern in _WHOLE_CLAUSE_PATTERNS:
        sanitized = pattern.sub(r"\1", sanitized)

    sanitized = re.sub(r"\s+", "", sanitized)
    sanitized = re.sub(r"^[，,。！？!?]+", "", sanitized)
    sanitized = re.sub(r"[，,]{2,}", "，", sanitized)
    sanitized = re.sub(r"([。！？!?])[，,]+", r"\1", sanitized)
    sanitized = re.sub(r"[，,](?=[。！？!?]|$)", "", sanitized)
    sanitized = re.sub(r"([。！？!?]){2,}", r"\1", sanitized)

    return sanitized or original
