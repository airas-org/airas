# airas-loop policy

Operational choices for every research the loop runs. `airas loop` hands
this file to the agent at the start of each session, in place of the
questions "Settle once, up front" would otherwise ask.

- repository visibility: public (`is_private=False`)
- execution platform: seyval, BYO compute
  - workspace_id: <fill in>
  - compute_id: <fill in, resolve with list_computes each time>
- compute target: GB200 (aarch64), 1 GPU, time_limit 24h
- budget: park after a step has failed the same way twice
