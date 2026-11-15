# Notices and attributions

**Licence:** our code, documentation and our own preference pairs are released under the
MIT licence ([`LICENSE`](LICENSE)). Third-party material keeps its own licence, as listed
below. In particular, the advisory facts from the GitHub Advisory Database stay CC BY 4.0
and need the attribution below wherever they're reused.

## Advisory data (CC BY 4.0)

`data/sources/osv/` holds copies of advisory records fetched from the
[OSV API](https://osv.dev). All of them are **GitHub Advisory Database** records (GHSA ids),
licensed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
(© GitHub, Inc. and contributors; https://github.com/github/advisory-database). They are
unmodified. The facts our preference pairs state about advisories (ids, aliases, affected
and patched versions, severity) come from these records, and every pair cites its advisory
URL in `source_url`. Version lookups also query OSV, whose PyPI records come from the
PyPA Advisory Database (CC BY 4.0, https://github.com/pypa/advisory-database).

## NVD data (truth source)

`truth-sources/cve-cvss/` reads NVD CVE records (a US government work) through the NVD CVE
API 2.0 and CIRCL Vulnerability-Lookup's mirror of the NVD feed. "This product uses NVD data
but is not endorsed or certified by the NVD." Saved test fixtures are trimmed NVD responses.

## Reused software and models

| Component | Used for | License |
|---|---|---|
| [telegraph-wasm-baseline](https://github.com/telegraphprotocol/telegraph-wasm-baseline) @ `1ed063e` | training, export, Stage 1 check, executor, remote-check client (used unmodified, fetched by `scripts/setup_kit.sh`, not vendored in git) | MIT |
| [telegraph-foundation](https://github.com/telegraphprotocol/telegraph-foundation) `modernbert-base-lora16-v1` | Foundation Model graph, engine, tokenizer (fetched, hash-checked) | see that repo |
| [answerdotai/ModernBERT-base](https://huggingface.co/answerdotai/ModernBERT-base) | base model for training and PyTorch scoring | Apache-2.0 |
| PyTorch, Hugging Face Transformers, PEFT, tokenizers, safetensors, packaging | training and scoring (pip dependencies) | BSD-3 / Apache-2.0 |
| Foundry `cast` | local signing of pool uploads and registration (user's machine) | MIT / Apache-2.0 |
| Google Fonts (Bricolage Grotesque, Instrument Sans, JetBrains Mono) | demo page and figure typography (loaded from fonts.googleapis.com) | SIL OFL 1.1 |
| [Anatomy skill](https://github.com/wheresryan22/anatomy) (wheresryan22) | isometric kit used to draw `docs/assets/adversarialeval-anatomy.png` (`docs/assets/anatomy-figure/`) | MIT |

## AI assistance

This project was built with substantial help from an AI coding assistant (Claude): code,
documentation and the first drafts of the hand-written preference pairs. Commits it
co-authored carry a `Co-Authored-By: Claude` trailer. Every advisory fact is checked against
OSV by `tools/fetch_sources.py`, `tools/check_ids.py` and `tools/verify_generated.py`. Pool
rows are uploaded only after a human `approve` (`tools/review_pool.py`), and the headline
test set is written by independent human reviewers.
