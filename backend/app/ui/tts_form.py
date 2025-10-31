from __future__ import annotations

import html
from typing import Optional


def _format_float(value: Optional[float]) -> str:
    return f"{value:.3f}" if value is not None else ""


def render_tts_form(
    text_value: str = "",
    audio_data_uri: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    error: Optional[str] = None,
    show_success_notice: bool = False,
    voice_value: Optional[str] = None,
    length_scale_value: Optional[float] = None,
    noise_scale_value: Optional[float] = None,
    noise_w_value: Optional[float] = None,
) -> str:
    """Render a simple HTML page for TTS interactions with Piper prosody controls."""
    safe_text = html.escape(text_value or "", quote=True)
    safe_voice = html.escape(voice_value or "", quote=True)
    length_scale_str = _format_float(length_scale_value)
    noise_scale_str = _format_float(noise_scale_value)
    noise_w_str = _format_float(noise_w_value)

    feedback_section = ""
    if audio_data_uri:
        audio_safe = html.escape(audio_data_uri, quote=True)
        voice_display = safe_voice if safe_voice else "預設"
        length_display = length_scale_str or "預設"
        noise_display = noise_scale_str or "預設"
        noise_w_display = noise_w_str or "預設"
        feedback_section = f"""
            <section class="result">
                <h2>轉換結果</h2>
                <audio controls src="{audio_safe}"></audio>
                <p>耗時：{duration_seconds:.2f} 秒</p>
                <ul class="prosody-list">
                    <li>Voice：{voice_display}</li>
                    <li>Length Scale：{length_display}</li>
                    <li>Noise Scale：{noise_display}</li>
                    <li>Noise W：{noise_w_display}</li>
                </ul>
                <details>
                    <summary>Base64 音訊資料</summary>
                    <textarea readonly>{audio_safe}</textarea>
                </details>
            </section>
        """
    elif error:
        feedback_section = f"""
            <section class="error">
                <strong>發生錯誤</strong>
                <p>{html.escape(error)}</p>
            </section>
        """

    toast_snippet = (
        "<div id='tts-toast' class='toast'>語音合成完成</div>"
        "<script>"
        "window.addEventListener('DOMContentLoaded',function(){"
        "var toast=document.getElementById('tts-toast');"
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
        <title>TTS 測試工具</title>
        <style>
            :root {{
                color-scheme: light dark;
            }}
            body {{
                font-family: "Segoe UI", "Noto Sans TC", "PingFang TC", sans-serif;
                margin: 0;
                padding: 2rem;
                background: #f4f5f7;
                color: #1f2933;
            }}
            main {{
                max-width: 760px;
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
                gap: 1.5rem;
            }}
            textarea {{
                min-height: 140px;
                padding: 1rem;
                font-size: 1rem;
                border-radius: 12px;
                border: 1px solid #d0d5dd;
                resize: vertical;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                gap: 1rem;
            }}
            label {{
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
                font-size: 0.95rem;
            }}
            input[type="text"],
            input[type="number"] {{
                padding: 0.5rem 0.75rem;
                border-radius: 10px;
                border: 1px solid #d0d5dd;
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
            .prosody-list {{
                list-style: none;
                padding-left: 0;
                margin: 0.75rem 0 0;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                gap: 0.75rem;
            }}
            .error {{
                background: #fee2e2;
                color: #991b1b;
            }}
            textarea[readonly] {{
                font-family: "Fira Code", Consolas, monospace;
                font-size: 0.85rem;
                background: #f8fafc;
            }}
            details {{
                margin-top: 1rem;
            }}
            .toast {{
                position: fixed;
                bottom: 24px;
                right: 24px;
                background: rgba(34, 197, 94, 0.95);
                color: white;
                padding: 1rem 1.25rem;
                border-radius: 12px;
                box-shadow: 0 1rem 2.5rem rgba(15, 118, 110, 0.25);
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
                textarea {{
                    background: #0f172a;
                    color: inherit;
                }}
                input[type="text"],
                input[type="number"] {{
                    background: #0f172a;
                    color: inherit;
                    border-color: #334155;
                }}
                .result {{
                    background: #1e293b;
                }}
                textarea[readonly] {{
                    background: #0f172a;
                }}
            }}
        </style>
    </head>
    <body>
        <main>
            <h1>文字轉語音（TTS）測試</h1>
            <p>輸入文字並調整 Piper prosody 參數，直接在頁面中即時播放結果。</p>
            <form method="post" action="/tts/form">
                <label for="text">輸入欲合成的文字</label>
                <textarea id="text" name="text" placeholder="請輸入英文或支援語音模型的語言" required>{safe_text}</textarea>
                <div class="grid">
                    <label>
                        Voice ID
                        <input type="text" name="voice" value="{safe_voice}" placeholder="留白則使用預設" />
                    </label>
                    <label>
                        Length Scale
                        <input type="number" name="length_scale" step="0.05" min="0.1" value="{length_scale_str}" placeholder="預設 1.0" />
                    </label>
                    <label>
                        Noise Scale
                        <input type="number" name="noise_scale" step="0.05" min="0" value="{noise_scale_str}" placeholder="預設 0.667" />
                    </label>
                    <label>
                        Noise W
                        <input type="number" name="noise_w" step="0.05" min="0" value="{noise_w_str}" placeholder="預設 0.8" />
                    </label>
                </div>
                <button type="submit">送出合成</button>
            </form>
            {feedback_section}
        </main>
        {toast_snippet if show_success_notice else ""}
    </body>
    </html>
    """
