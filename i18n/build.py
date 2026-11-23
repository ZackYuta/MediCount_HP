#!/usr/bin/env python3
"""日本語のページ(index.html・privacy.html)から、各言語のページを作る。

    python3 i18n/build.py

- 日本語のページを型にして、文言だけを i18n/texts.py の訳に置き換える(構成は日本語のページと同じ)
- 出力: <言語>/index.html・<言語>/privacy.html(css・画像はルートのものを ../ で参照)
- App Store のバッジは badges/ の各言語のもの(Apple の公式。日本語はルートの既存のもの)
- すべてのページに言語の切り替えと hreflang を入れる(日本語のページにも書き戻す)
日本語のページを直したら、texts.py の該当する文を合わせて直し、このスクリプトを流し直す。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texts import LANGS, INDEX, PRIVACY, COMMON  # noqa: E402

JA_BADGE = "Download_on_the_App_Store_Badge_JP_RGB_blk_100317.svg"
LANG_NAMES = [("ja", "日本語"), ("en", "English"), ("pt-BR", "Português"), ("es-419", "Español"),
              ("zh-Hans", "简体中文"), ("ko", "한국어")]
SWITCH_START, SWITCH_END = "<!-- lang-switch -->", "<!-- /lang-switch -->"
ALT_START, ALT_END = "<!-- hreflang -->", "<!-- /hreflang -->"


def switcher(current, page, prefix):
    links = []
    for code, name in LANG_NAMES:
        href = prefix + ("" if code == "ja" else code + "/") + page
        attr = ' aria-current="page"' if code == current else ""
        links.append(f'<a href="{href}" hreflang="{code}" lang="{code}"{attr}>{name}</a>')
    return f'{SWITCH_START}<nav class="lang-switch" aria-label="Language">{" ".join(links)}</nav>{SWITCH_END}'


def alternates(page, prefix):
    tags = [f'<link rel="alternate" hreflang="{code}" href="{prefix}{"" if code == "ja" else code + "/"}{page}">'
            for code, _ in LANG_NAMES]
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{prefix}en/{page}">')
    return ALT_START + "".join(tags) + ALT_END


def strip_inserted(html):
    html = re.sub(re.escape(SWITCH_START) + ".*?" + re.escape(SWITCH_END) + r"\n?\s*", "", html, flags=re.S)
    return re.sub(re.escape(ALT_START) + ".*?" + re.escape(ALT_END) + r"\n?\s*", "", html, flags=re.S)


def insert(html, current, page, prefix):
    html = html.replace("</head>", "    " + alternates(page, prefix) + "\n</head>", 1)
    return html.replace('<div class="header-text">',
                        '<div class="header-text">\n                ' + switcher(current, page, prefix), 1)


def build(page, table):
    path = os.path.join(ROOT, page)
    ja = strip_inserted(open(path, encoding="utf-8").read())
    missing = [s for s in list(table) + list(COMMON) if s not in ja]
    if missing:
        sys.exit(f"{page}: 日本語のページに見つからない文があります(texts.py を直してください):\n  " + "\n  ".join(missing))
    open(path, "w", encoding="utf-8").write(insert(ja, "ja", page, ""))
    for i, lang in enumerate(LANGS):
        html = ja
        # 長い文から置き換える(短い文が長い文の一部のときに先に置き換わらないように)
        for source, targets in sorted(list(table.items()) + list(COMMON.items()), key=lambda kv: -len(kv[0])):
            html = html.replace(source, targets[i])
        html = html.replace('<html lang="ja">', f'<html lang="{lang["html"]}">')
        html = html.replace('href="styles.css"', 'href="../styles.css"')
        html = html.replace(f'src="{JA_BADGE}"', f'src="../badges/{lang["badge"]}"')
        html = re.sub(r'src="(?!\.\./|https?:)([^"]+\.(?:png|svg))"', r'src="../\1"', html)
        html = html.replace('href="privacy.html"', 'href="privacy.html"')
        left = re.findall(r"[ぁ-んァ-ヶ]+", html)
        if left:
            sys.exit(f"{lang['dir']}/{page}: 訳していない日本語が残っています: {sorted(set(left))[:10]}")
        os.makedirs(os.path.join(ROOT, lang["dir"]), exist_ok=True)
        open(os.path.join(ROOT, lang["dir"], page), "w", encoding="utf-8").write(insert(html, lang["dir"], page, "../"))
    print(f"{page}: {len(LANGS)} 言語を書き出しました")


build("index.html", INDEX)
build("privacy.html", PRIVACY)
