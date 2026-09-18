analyze_experiment_prompt = """\
You are analysing a preregistered study. Before any run, its hypothesis was \
frozen together with numbered claims; each claim declared a criterion (a \
falsification line on one metric), a predicted interval for the observed \
difference, and the runs that would decide it. The runs have executed and \
the verdicts below were derived mechanically from the criteria. Your job is \
the interpretation the mechanics cannot give: what held, what did not, and \
what that means for the hypothesis.

Rules:
- Do not invent numbers. Every value you mention must be one of the observed \
  differences or metrics listed below, named as `<run_id>.<metric>`.
- A refuted claim is a negative result. Report it as one; never reword a \
  claim to fit the data.
- Where an observed difference falls outside its predicted interval (in \
  either direction), say so and what it suggests.
- Weigh the stated assumptions: which ones the results lean on, which ones \
  the results cannot confirm.
- Distinguish what the claims together establish about the hypothesis from \
  what remains open, and name alternative explanations worth ruling out.
- Write in the language of the hypothesis statement.

{% for h in hypotheses %}
## Hypothesis {{ h.id }}
{{ h.statement }}
{% if h.assumptions %}
Assumptions:
{% for a in h.assumptions %}- {{ a }}
{% endfor %}{% endif %}{% if h.notes %}
Notes from preregistration:
{% for n in h.notes %}- {{ n }}
{% endfor %}{% endif %}
### Claims
{% for c in h.claims %}
{{ c.id }}: {{ c.statement }}
- Rationale: {{ c.rationale }}
{% if c.criterion %}- Criterion: {{ c.criterion }}
- Predicted interval: [{{ c.prediction.low }}, {{ c.prediction.high }}] ({{ c.prediction.basis }})
- Observed difference: {{ "%g"|format(c.observed) if c.observed is not none else "not available" }}\
{% if c.observed is not none %} ({{ "inside" if c.in_prediction else "outside" }} the predicted interval){% endif %}
{% endif %}- Verdict: {{ c.verdict or "pending" }}
{% endfor %}{% endfor %}
## Metrics per run
{% if metrics %}{{ metrics }}{% else %}NONE PROVIDED — no run has a metrics file yet.{% endif %}

Write the analysis as prose a reader of the paper's Discussion could follow: \
per claim, then the hypothesis as a whole, then limitations and open questions.
"""
