# resolve: settling prediction markets on checked answers

Telegraph's `EVENT_OUTCOME_RESOLUTION_GENERAL` answers, checked against the official source a market
names before any money moves. The frozen rule is in `RULE.md`.

- `cases.json`: 24 markets, with the truth and its evidence from official sources (Coinbase, NHL,
  MLB, USGS).
- `sources.py`: one resolver per source.
- `run.py`: builds the paid jobs and scores the arms.
