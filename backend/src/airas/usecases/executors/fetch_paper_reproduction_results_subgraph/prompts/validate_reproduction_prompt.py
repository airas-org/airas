# TODO: 今はパラメーター/メトリクスの突合もこのプロンプト経由で LLM に任せているが、
# 論文テキストと result.json からそれぞれ抽出して決定ロジックで突合する方が信頼性が高い。
validate_reproduction_prompt = """\
You are an independent auditor reviewing a paper-reproduction result. You are given the paper's text,
the reproduction's self-reported result.json, and a pre-computed deterministic pitfall checklist.
Deliver a final verdict.

# What to check
- Cross-check result.json's self-declared `parameters` against the paper text. Treat a value declared
  `source: "paper"` that does not match the paper as a likely false declaration (concern). `"assumed"`
  / `"substituted"` mismatches are fine if explained in `summary`.
- Cross-check result.json's `metrics` against the paper's reported values. Judge primarily whether the
  paper's claim (direction / relative magnitude of the improvement) holds — not whether absolute numbers
  match (a scaled-down/substituted reproduction legitimately shifts absolute values).
- Watch for: reverse-engineered parameters, hardcoded/mocked results, experiment not actually run,
  transcribed baseline values, undisclosed scale reduction. Use the pitfall checklist as input, but do
  not merely repeat it — focus on qualitative issues it cannot catch.

# reproduction_level
- "high"    = the paper's claim clearly holds (direction matches, improvement of comparable magnitude)
- "partial" = only some metrics hold, or the improvement partially supports the claim
- "low"     = performance could not be extracted, or the reproduction contradicts the paper's claim

# severity
- "ok" = no issues, "warning" = minor concern, "critical" = serious misconduct suspected

Return `severity`, `reproduction_level`, and `text` (2-5 sentences stating the basis for both).

# Paper text
{{ paper_text }}

# Reproduction result.json (self-reported)
{{ result }}

# Pre-computed pitfall checklist (deterministic — do not repeat, use as input)
{{ evidence }}
"""
