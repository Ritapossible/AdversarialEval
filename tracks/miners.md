# Miners track: not entered yet

**Not pursued for this submission (decided 28 Nov).** No miner is registered from this repository.
The notes below record what was gathered, for later.

## Candidate: `CODE_PATCH_VERIFY_GENERAL`

Whether a given commit or pull request passed CI is specialist intelligence in the sense
Telegraph describes: a general model can't know it, and the CI provider's API can prove it. The
intent asks for `patch` (a repository and a commit, pull request or CI run) and returns
`conclusion`, `passed`, and the commit and pipeline checked.

The intent already has 23 miners (checked 22 Nov 2026), most of them generic wrappers whose
compatibility note says they declare no field for `patch`, and a few serious ones. So the plan
measures before it builds ([`PLAN.md`](../PLAN.md), Phase P):

1. A benchmark of the existing miners, with CI truth read from the providers' APIs and frozen
   before any call.
2. A free check for CI answers, in the style of Verified Ask.
3. Evaluation pairs for the intent.
4. A miner, only if steps 1 and 2 show a gap the existing miners leave.

Registration facts gathered so far (current Diamond, `registerMiner` arguments, activation,
grace period) are in [`PLAN.md`](../PLAN.md).
