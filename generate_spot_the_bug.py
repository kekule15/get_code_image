#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import argparse
import html
import tempfile
import re


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html, body {
    background: #0d1117;
}

body {
    padding: 48px;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

.window {
    width: 900px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.55);
}

.titlebar {
    min-height: 62px;
    background: #21262d;
    border-bottom: 1px solid #30363d;
    display: flex;
    align-items: center;
    padding: 0 22px;
    gap: 10px;
}

.dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    flex: 0 0 14px;
}

.red {
    background: #ff5f56;
}

.yellow {
    background: #ffbd2e;
}

.green {
    background: #27c93f;
}

.title {
    margin-left: 12px;
    color: #e6edf3;
    font-family:
        "SF Mono",
        "Fira Code",
        "JetBrains Mono",
        Menlo,
        Consolas,
        monospace;
    font-size: 15px;
    font-weight: 700;
}

.badge {
    margin-left: auto;
    background: #da3633;
    color: #ffffff;
    padding: 7px 12px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.8px;
}

.code-wrapper {
    padding: 30px;
    background: #0d1117;
}

pre {
    margin: 0;
    padding: 26px 28px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    overflow: hidden;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    word-break: break-word;
}

code {
    display: block;
    color: #e6edf3;
    font-family:
        "SF Mono",
        "Fira Code",
        "JetBrains Mono",
        Menlo,
        Consolas,
        monospace;
    font-size: 15px;
    line-height: 1.65;
}

.code-line {
    display: flex;
    min-height: 25px;
}

.line-number {
    flex: 0 0 42px;
    color: #484f58;
    text-align: right;
    padding-right: 18px;
    user-select: none;
}

.line-content {
    flex: 1;
    min-width: 0;
    color: #e6edf3;
}

.keyword {
    color: #ff7b72;
}

.string {
    color: #a5d6ff;
}

.number {
    color: #79c0ff;
}

.function {
    color: #d2a8ff;
}

.comment {
    color: #8b949e;
}

.boolean {
    color: #ff7b72;
}

.property {
    color: #79c0ff;
}

.operator {
    color: #ff7b72;
}

.hint {
    padding: 14px 24px;
    background: #0d1117;
    border-top: 1px solid #30363d;
    color: #8b949e;
    text-align: center;
    font-size: 12px;
}
</style>

</head>

<body>

<div class="window">

    <div class="titlebar">

        <div class="dot red"></div>
        <div class="dot yellow"></div>
        <div class="dot green"></div>

        <div class="title">
            __TITLE__
        </div>

        <div class="badge">
            SPOT THE BUG
        </div>

    </div>

    <div class="code-wrapper">

        <pre><code>
__CODE__
        </code></pre>

    </div>

    <div class="hint">
        Something here will hurt in production.
    </div>

</div>

</body>
</html>
"""


ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "cs": "csharp",
    "c#": "csharp",
    "jsx": "javascript",
    "tsx": "typescript",
}


KEYWORDS = {
    "javascript": {
        "const", "let", "var", "function", "async", "await",
        "return", "if", "else", "for", "while", "do",
        "new", "throw", "try", "catch", "finally",
        "class", "extends", "import", "from", "export",
        "default", "of", "in", "typeof", "instanceof",
        "switch", "case", "break", "continue",
        "true", "false", "null", "undefined"
    },

    "typescript": {
        "const", "let", "var", "function", "async", "await",
        "return", "if", "else", "for", "while", "do",
        "new", "throw", "try", "catch", "finally",
        "class", "extends", "import", "from", "export",
        "default", "of", "in", "typeof", "instanceof",
        "switch", "case", "break", "continue",
        "true", "false", "null", "undefined",
        "interface", "type", "public", "private",
        "protected", "readonly", "implements"
    },

    "python": {
        "def", "return", "if", "else", "elif",
        "for", "while", "in", "import", "from",
        "as", "class", "try", "except", "finally",
        "with", "async", "await", "lambda",
        "yield", "raise", "and", "or", "not",
        "is", "None", "True", "False",
        "pass", "break", "continue"
    },

    "csharp": {
        "public", "private", "protected", "internal",
        "class", "static", "async", "await", "return",
        "var", "new", "if", "else", "for",
        "foreach", "while", "try", "catch", "finally",
        "using", "Task", "string", "int", "bool",
        "void", "null", "true", "false"
    },

    "dart": {
        "class", "extends", "implements", "void",
        "final", "const", "var", "return",
        "if", "else", "for", "while",
        "async", "await", "import",
        "required", "late", "null", "true", "false"
    },

    "sql": {
        "SELECT", "FROM", "WHERE", "INSERT", "INTO",
        "VALUES", "UPDATE", "SET", "DELETE",
        "CREATE", "TABLE", "PRIMARY", "KEY",
        "FOREIGN", "REFERENCES", "UNIQUE", "NOT",
        "NULL", "ORDER", "BY", "GROUP", "LIMIT",
        "OFFSET", "JOIN", "LEFT", "RIGHT",
        "INNER", "ON", "AS", "AND", "OR",
        "DESC", "ASC", "DEFAULT", "ALTER", "INDEX"
    },
}


def highlight_line(line: str, language: str) -> str:
    """
    Local syntax highlighting.

    No Highlight.js CDN or external JavaScript is used.
    This means the generator works without internet access.
    """

    language = ALIASES.get(
        language.lower(),
        language.lower()
    )

    keywords = KEYWORDS.get(language, set())

    token_pattern = re.compile(
        r"""
        (//[^\n]*)
        |(#[^\n]*)
        |(--[^\n]*)
        |(/\*[\s\S]*?\*/)
        |("(?:\\.|[^"\\])*")
        |('(?:\\.|[^'\\])*')
        |(`(?:\\.|[^`\\])*`)
        |(\b\d+(?:\.\d+)?\b)
        |(\b[A-Za-z_][A-Za-z0-9_]*\b)
        """,
        re.VERBOSE
    )

    output = []
    last = 0

    for match in token_pattern.finditer(line):

        if match.start() > last:
            output.append(
                html.escape(
                    line[last:match.start()]
                )
            )

        token = match.group(0)
        safe = html.escape(token)

        if token.startswith("//"):
            output.append(
                f'<span class="comment">{safe}</span>'
            )

        elif token.startswith("#"):
            output.append(
                f'<span class="comment">{safe}</span>'
            )

        elif token.startswith("--"):
            output.append(
                f'<span class="comment">{safe}</span>'
            )

        elif token.startswith("/*"):
            output.append(
                f'<span class="comment">{safe}</span>'
            )

        elif token.startswith(("\"", "'", "`")):
            output.append(
                f'<span class="string">{safe}</span>'
            )

        elif token[0].isdigit():
            output.append(
                f'<span class="number">{safe}</span>'
            )

        elif token in keywords:
            output.append(
                f'<span class="keyword">{safe}</span>'
            )

        elif token in {
            "true",
            "false",
            "True",
            "False",
            "null",
            "None",
            "undefined",
        }:
            output.append(
                f'<span class="boolean">{safe}</span>'
            )

        else:
            remainder = line[match.end():]

            if remainder.lstrip().startswith("("):
                output.append(
                    f'<span class="function">{safe}</span>'
                )
            else:
                output.append(safe)

        last = match.end()

    if last < len(line):
        output.append(
            html.escape(line[last:])
        )

    return "".join(output) or "&nbsp;"


def build_code_html(code: str, language: str) -> str:

    rendered_lines = []

    for line_number, line in enumerate(
        code.split("\n"),
        start=1
    ):

        rendered_lines.append(
            '<div class="code-line">'
            f'<span class="line-number">{line_number:>2}</span>'
            f'<span class="line-content">'
            f'{highlight_line(line, language)}'
            '</span>'
            '</div>'
        )

    return "\n".join(rendered_lines)


def generate_spot_the_bug(
    code: str,
    lang: str = "python",
    title: str = "Spot the Bug",
    output: str = "spot_the_bug.png"
):

    code_html = build_code_html(
        code,
        lang
    )

    page_html = (
        HTML_TEMPLATE
        .replace(
            "__TITLE__",
            html.escape(title)
        )
        .replace(
            "__CODE__",
            code_html
        )
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8"
    ) as f:

        f.write(page_html)
        html_path = f.name

    with sync_playwright() as p:

        browser = p.chromium.launch()

        page = browser.new_page(
            viewport={
                "width": 1000,
                "height": 1000,
            },
            device_scale_factor=2,
        )

        # Important:
        # We intentionally do NOT wait for external resources.
        # This HTML has no external resources, so generation
        # works completely offline.
        page.goto(
            f"file://{html_path}",
            wait_until="domcontentloaded",
            timeout=10000,
        )

        page.wait_for_timeout(150)

        window = page.query_selector(".window")

        if window is None:
            browser.close()
            raise RuntimeError(
                "Could not find .window in generated HTML."
            )

        window.screenshot(
            path=output
        )

        browser.close()

    print(
        f"✅ Spot the Bug image saved → {output}"
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate Spot the Bug code images "
            "for X posts."
        )
    )

    parser.add_argument(
        "--lang",
        default="python",
        help=(
            "Programming language: "
            "javascript, typescript, python, "
            "csharp, dart, sql, etc."
        ),
    )

    parser.add_argument(
        "--title",
        default="Spot the Bug",
    )

    parser.add_argument(
        "--output",
        default="spot_the_bug.png",
    )

    parser.add_argument(
        "--code",
        required=True,
        help=(
            "Code snippet. Use \\\\n "
            "for new lines."
        ),
    )

    args = parser.parse_args()

    code = args.code.replace(
        "\\n",
        "\n"
    )

    generate_spot_the_bug(
        code=code,
        lang=args.lang,
        title=args.title,
        output=args.output,
    )


if __name__ == "__main__":
    main()
