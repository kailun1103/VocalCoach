from __future__ import annotations

import html
from typing import Optional


def render_stt_form(
    transcript: Optional[str] = None,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
    show_success_notice: bool = False,
) -> str:
    """Render a simple HTML page for STT interactions."""
    safe_transcript = html.escape(transcript or "")
    transcript_section = ""
    if transcript:
        render_duration = (duration_ms or 0.0) / 1000.0
        transcript_section = f"""
            <section class="result">
                <h2>轉寫結果</h2>
                <p>處理時間：{render_duration:.2f} 秒</p>
                <textarea readonly>{safe_transcript}</textarea>
            </section>
        """
    elif error:
        transcript_section = f"""
            <section class="error">
                <strong>發生錯誤：</strong>
                <p>{html.escape(error)}</p>
            </section>
        """

    toast_snippet = (
        "<div id='stt-toast' class='toast'>轉寫完成，音訊已處理。</div>"
        "<script>"
        "window.addEventListener('DOMContentLoaded',function(){"
        "var toast=document.getElementById('stt-toast');"
        "if(!toast)return;"
        "toast.classList.add('show');"
        "setTimeout(function(){toast.classList.remove('show');},4000);"
        "});"
        "</script>"
    )

    return f"""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
        <meta charset="UTF-8" />
        <title>STT 測試介面</title>
        <style>
            :root {{
                color-scheme: light dark;
            }}
            body {{
                font-family: "Segoe UI", "Noto Sans TC", sans-serif;
                margin: 0;
                padding: 2rem;
                background: #f4f5f7;
                color: #1f2933;
            }}
            main {{
                max-width: 720px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                padding: 2rem;
                box-shadow: 0 0.75rem 2rem rgba(15, 23, 42, 0.08);
            }}
            h1 {{
                margin-top: 0;
                font-size: 1.75rem;
            }}
            form {{
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }}
            input[type="file"] {{
                font-size: 1rem;
            }}
            button {{
                align-self: flex-start;
                background: #2563eb;
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 10px;
                font-size: 1rem;
                cursor: pointer;
                transition: background 0.2s ease;
            }}
            button:hover {{
                background: #1d4ed8;
            }}
            .result, .error {{
                margin-top: 2rem;
                padding: 1.25rem;
                border-radius: 12px;
                background: #f1f5f9;
            }}
            .error {{
                background: #fee2e2;
                color: #991b1b;
            }}
            textarea[readonly] {{
                width: 100%;
                min-height: 140px;
                padding: 1rem;
                border-radius: 12px;
                border: 1px solid #d0d5dd;
                background: #f8fafc;
                font-family: "Fira Code", Consolas, monospace;
                font-size: 0.95rem;
                resize: vertical;
            }}
            .toast {{
                position: fixed;
                bottom: 24px;
                right: 24px;
                background: rgba(59, 130, 246, 0.95);
                color: white;
                padding: 1rem 1.25rem;
                border-radius: 12px;
                box-shadow: 0 1rem 2.5rem rgba(37, 99, 235, 0.25);
                font-weight: 500;
                opacity: 0;
                transform: translateY(10px);
                pointer-events: none;
                transition: opacity 0.3s ease, transform 0.3s ease;
            }}
            .toast.show {{
                opacity: 1;
                transform: translateY(0);
            }}
            @media (prefers-color-scheme: dark) {{
                body {{
                    background: #0f172a;
                    color: #e2e8f0;
                }}
                main {{
                    background: #111827;
                    box-shadow: none;
                }}
                textarea[readonly] {{
                    background: #0f172a;
                    color: inherit;
                }}
                .result {{
                    background: #1e293b;
                }}
            }}
        </style>
    </head>
    <body>
        <main>
            <h1>語音轉文字 (STT)</h1>
            <p>上傳音訊檔即可取得文本和處理時間。</p>
            <form method="post" action="/stt/form" enctype="multipart/form-data">
                <label for="audio">選擇音訊檔：</label>
                <input id="audio" name="file" type="file" accept="audio/*" required />
                <button type="submit">開始轉寫</button>
            </form>
            {transcript_section}
        </main>
        {toast_snippet if show_success_notice else ""}
    </body>
    </html>
    """
