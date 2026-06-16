import html
import re


def clean_text(value: str) -> str:
    if not value:
        return ""

    value = value.replace("&nbsp;", " ")
    value = value.replace("&nbsp", " ")
    value = html.unescape(value)
    value = value.replace("\xa0", " ")

    value = re.sub(r"\(\s+", "(", value)
    value = re.sub(r"\s+\)", ")", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\s*\n\s*", "\n", value)
    value = re.sub(r"\n{2,}", "\n", value)

    return value.strip()
    