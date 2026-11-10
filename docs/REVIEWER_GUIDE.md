# Guide for independent reviewers: writing test pairs

Thank you for helping. You'll write a small set of **test questions** for a security-review
judge model. Each question gets a **better** and a **worse** answer. Your pairs become the
**frozen test set**: the only data used for the headline accuracy number. They are never
used to train or tune the model.

**Time:** about 2–3 hours for 20 pairs. **What you need:** security review experience
(AppSec, pentesting, dependency triage or secure code review).

## Independence rules (please read)

1. **Don't look at our training or validation data** (`data/public/`, `data/validation/`,
   `data/authoring/`) before or while you write. Your value is that you write *differently*
   from us.
2. Write in your own voice and your own formats, the way you'd actually answer a colleague
   or how a tool would report.
3. Write your own questions; don't paraphrase public CTF write-ups or benchmarks. Real-world
   situations you've seen, anonymised, are ideal.
4. Your pairs stay out of the public training set and are never uploaded to the Telegraph
   evaluation pool.

## What one pair looks like

| Field | What to write |
|---|---|
| `prompt` | A realistic security-review request: a code snippet, a dependency list, a config, or a scanner alert to triage. Keep it under about 1,200 characters. |
| `better` | The answer a careful senior reviewer would give. **Every fact must be correct.** Use a verdict of `Secure`, `Needs changes` or `Insecure`, give a count, and name the issues (CVE / GHSA / CWE ids where relevant). |
| `worse` | An answer that **sounds plausible but is wrong**, in a way a real reviewer or tool might get wrong. Keep it about the same length and style as `better`. |
| `what_is_wrong` | One sentence: why `worse` is worse. |
| `source_url` | A public page that backs the better answer (a GHSA/NVD/OSV advisory, a CWE page, or vendor docs). |

### Example

> **prompt:** Our Node API does `res.redirect(req.query.next)` after login. express 4.21.0. Severity?
>
> **better:** Needs changes, 1 issue: CWE-601 open redirect (medium). An attacker can send users to a phishing site after a real login. Allow only relative paths starting with a single `/`.
>
> **worse:** Insecure, 1 issue: critical remote code execution. `res.redirect` evaluates the URL, so a `javascript:` value runs code on the server. Take the route offline.
>
> **what_is_wrong:** It inflates a client-side open redirect into server-side RCE.

## Variety we need

Aim for this mix across your 20 pairs. Exact counts don't matter.

- **About ⅓ where the right verdict is `Secure`**: code that *looks* risky but is safe
  (parameterised queries, auto-escaping templates, constant arguments, dev-only dependencies).
  The worse answer raises a false alarm.
- **About ⅓ obvious-but-easy-to-miss bugs**: the worse answer misses the critical issue,
  calls vulnerable code safe, or hedges when the evidence is clear.
- **About ⅓ subtle errors**: wrong version range, wrong advisory id, wrong severity,
  a fix that doesn't fix, or verdict/count fields that contradict each other.
- Mix answer styles: prose, bullet points, JSON, terse scanner output.
- In some pairs make the **worse** answer the longer or more "security-sounding" one.

## Accuracy rules

- If you cite an advisory, check the id and the affected versions on
  [GitHub Advisories](https://github.com/advisories) or [OSV](https://osv.dev).
- Scope your claims. Say "not affected by GHSA-…", never "this version has no
  vulnerabilities". New advisories appear all the time.
- When in doubt, leave the pair out. One wrong label hurts more than one missing pair.

## How to submit

Fill in [`templates/test_pairs_template.csv`](../templates/test_pairs_template.csv)
(spreadsheet-friendly) and send it to the project lead, or open a PR adding it under
`data/authoring/security_review/test/`. We convert it with
`python tools/import_reviewer_csv.py <file.csv> --author <your-handle>`. Your handle is
recorded with each pair so you're credited in the dataset card. Tell us if you'd rather
stay anonymous.
