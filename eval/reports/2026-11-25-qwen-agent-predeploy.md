# Is Qwen-Agent safe to deploy? An independent pre-deployment check (2026-11-25)

The scenario Telegraph asked for (Alibaba thread, and the 24 Nov guidance): before an enterprise
deploys software built on Qwen or Alibaba Cloud, independently establish whether its dependencies
are malicious, compromised or vulnerable, whether reported vulnerabilities actually affect it,
whether the proposed fixes work without breaking it, and decide DEPLOY or HOLD with evidence.

**Application:** Qwen-Agent, Alibaba's own agent framework (github.com/QwenLM/Qwen-Agent), latest
release on PyPI (0.0.34), installed with its web UI exactly as its README tells users:
`pip install "qwen-agent[gui]"`.

**Method:** `python -m deploycheck deploycheck/scenarios/qwen_agent.json` (code in `deploycheck/`,
tests in `tests/test_deploycheck.py`). Every finding comes from installing and running the app in a
fresh sandbox, OSV, the package registry, or a reviewed rule matched against the app's own source
code. None comes from a model's opinion. Run 09:04 to 09:10 UTC at commit `ec10d31`; full output
`bench/out/deploycheck-qwen-agent/report.md` and `report.json`.

## Decision

| Candidate | Imports | Serves its web UI | Advisories that apply | Decision |
|---|---|---|---|---|
| As shipped | **no** | no | 5 CRITICAL, 37 HIGH and more (68 reachable or conditional) | **HOLD** |
| Fix 1: add the missing package | yes | yes | same 68 | HOLD |
| Fix 2: Fix 1 + Gradio 5.50.0 | yes | yes | 67 (Pillow stays capped below 12) | HOLD |
| Fix 3: Fix 1 + Gradio 6.32.0 | **no** | no | (app breaks) | HOLD |
| Fix 4: Fix 3 + modelscope-studio 2.1.2 | **no** | no | (app breaks) | HOLD |
| **Fix 5: Fix 2 + Pillow 13.0.0 + Starlette 1.3.1, forced** | yes | yes | **2, both conditional** | **DEPLOY WITH CONDITIONS** |

## What we found

1. **The latest release doesn't start after the documented install.** `qwen_agent/utils/utils.py`
   imports `soundfile` at load time, and no dependency of `qwen-agent[gui]` provides it:
   `from qwen_agent.agents import Assistant` fails with `No module named 'soundfile'`. Without the
   GUI extra it's worse: a plain `pip install qwen-agent==0.0.34` also lacks `numpy`, `tqdm` and
   `python-dateutil` (checked by hand in a fresh environment, same method).
2. **Its web UI pins a vulnerable Gradio.** `qwen-agent[gui]` pins `gradio==5.23.1`: 9 distinct
   advisories (17 OSV records). Checked against Qwen-Agent's own code, 6 need features it never
   uses (FileExplorer, `gr.load`, OAuth login, flagging). 3 apply: a CORS bypass (low; fixed by
   Gradio 5.50), a path traversal that needs **Windows with Python 3.13+** (HIGH), and a weak audio
   cache key that needs **local access** (low). Evidence: `qwen_agent/gui/web_ui.py:210` serves the
   app; it uses `gr.Audio`.
3. **The bigger exposure is underneath.** Gradio 5 caps Pillow below 12, so every Gradio 5
   configuration runs `pillow 11.3.0`: **60 advisories, 5 CRITICAL and 36 HIGH**, all fixed by
   13.0.0. Qwen-Agent decodes images it downloads (`qwen_agent/tools/image_zoom_in_qwen3vl.py:145`,
   `Image.open(BytesIO(response.content))`), so image-decoder flaws are reachable. `starlette
   0.52.1`, the web server under Gradio, adds 5 more (2 HIGH), fixed in 1.x.
4. **The clean upgrade breaks the app.** Gradio 6 fixes everything Gradio-related and allows Pillow
   13, but Qwen-Agent's UI is built on `modelscope_studio`'s `legacy` components: version 1.1.7
   requires Gradio below 6, and 2.x (which supports Gradio 6) removed those components. No
   dependency-only change gives a supported, fully fixed web UI. That needs a code change in
   Qwen-Agent (moving its UI off the legacy components).
5. **A working, much safer configuration exists.** Fix 5 forces Pillow 13 and Starlette 1.3.1 under
   Gradio 5.50. The real web UI still builds and serves, and only 2 conditional advisories remain.
   It runs versions above Gradio's declared caps (`pip check` reports both), so it's a stopgap
   that needs the app's own regression tests, not a supported release.

**Recommendation:** HOLD the shipped release. If the web UI must ship before Qwen-Agent moves off
the legacy components, deploy Fix 5 on Linux (or Windows without Python 3.13), with the four
missing packages pinned, and test the image and audio paths before release.

## Telegraph specialist answers (paid, checked before use)

| Package | Telegraph answer (Telegraph Verity Intelligence) | Verified Ask | Cost | Receipt |
|---|---|---|---|---|
| `qwen-agent` 0.0.34 | Secure, 0 advisories | verified | $0.01 | `0xf8228220673cb1e7af…` |
| `gradio` 5.23.1 | Insecure, 17 | verified | $0.01 | `0xa3a983a865faf3feb8…` |
| `gradio` 5.50.0 | Insecure, 14 | verified | $0.01 | `0x2db6f51bfdb91ad264…` |
| `gradio` 6.32.0 | Secure, 0 | verified | $0.01 | `0x6890e12dcb26ffcc7c…` |

All four paid answers were correct and verified against OSV. They also show the gap this check
closes: "qwen-agent 0.0.34: Secure, 0 advisories" is true for known vulnerabilities, yet that
release doesn't import after a normal install, and its real exposure (Pillow, Starlette) sits two
levels down. Only installing, running and tracing the app finds those.

## Limits

- One application, one release, one day's OSV data.
- Reachability rules are written per advisory from its text and matched against source code; a
  match shows the feature is used, not that an exploit was demonstrated. "Unknown" is treated as
  reachable.
- The smoke test builds and serves the real web UI without calling a model; it is not a full
  functional test of Fix 5.
- Sandbox: Linux, Python 3.13, fresh virtual environments.
