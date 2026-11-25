"""Smoke test for Qwen-Agent's web UI (qwen_agent.gui.WebUI): build the real app, serve it on
localhost, and request its page and config. No model is called (the LLM key is a dummy and no
message is sent). Exit code 0 and a JSON line {"ok": true, ...} mean the app builds and serves.

    <venv>/bin/python deploycheck/apps/qwen_agent_webui.py
"""
import json
import socket
import sys
import urllib.request


def free_port() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def main() -> int:
    out = {"ok": False}
    try:
        import gradio as gr
        from qwen_agent.agents import Assistant
        from qwen_agent.gui import WebUI
        out["gradio"] = gr.__version__
        launched = {}
        real_launch = gr.Blocks.launch

        def launch(self, *a, **k):  # serve without blocking, on a free local port
            k.update(prevent_thread_lock=True, server_name="127.0.0.1", server_port=launched.setdefault("port", free_port()),
                     share=False, quiet=True)
            launched["app"] = self
            return real_launch(self, *a, **k)
        gr.Blocks.launch = launch
        bot = Assistant(llm={"model": "qwen-max", "model_server": "dashscope", "api_key": "dummy-not-used"},
                        name="Smoke", description="build-and-serve check")
        WebUI(bot).run()
        base = f"http://127.0.0.1:{launched['port']}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        page = opener.open(base + "/", timeout=30)
        cfg = json.loads(opener.open(base + "/config", timeout=30).read())
        out.update(ok=page.status == 200 and bool(cfg.get("components")), http=page.status,
                   components=len(cfg.get("components", [])))
        launched["app"].close()
    except Exception as e:  # report, don't hide
        out["error"] = f"{type(e).__name__}: {e}"[:600]
    print(json.dumps(out))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
