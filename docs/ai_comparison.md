# AI assistant comparison: raw files vs governed metrics

**Question tested:** does giving an AI assistant governed, tested metric definitions change its answers?

**Method.** Two fresh Claude agents, neither had seen this project. Same five questions about 2023/24, asked identically.
- Agent A got only the raw HESA CSVs (no documentation).
- Agent B got only `metrics_long.csv` (governed values with definition, formula, source figure and caveat).
Answers below are recorded as found. One run each, so this shows what happened, not a statistical result.

## Results

| # | Question | Raw files | Governed table | Same? |
|---|---|---|---|---|
| 1 | Students enrolled | 2,904,425 (Figure 3) | 2,903,380 (Figure 4) | **No: 1,045 apart (0.04%)** |
| 2 | First-class rate | 28.8% (124,930 / 433,475) | 28.8% (124,930 / 433,480) | Yes |
| 3 | Non-UK domicile share | 25.2% (732,285 / 2,904,425) | 25.2% (732,285 / 2,904,425) | Yes |
| 4 | Postgraduate share | 29.2% (847,905 / 2,904,425) | 29.2% (847,845 / 2,903,380) | Yes at 1 dp |
| 5 | Full-time share | 80.5% (2,337,595 / 2,904,425) | 80.5% (2,337,270 / 2,903,380) | Yes at 1 dp |

## What I found

1. **The raw-file agent was very good.** It read the metadata lines, avoided double-counting aggregate rows, cross-checked totals across figures, and excluded further education colleges. It found the Figure 4 vs Figure 3 total difference on its own.
2. **The one headline disagreement is the enrolment total.** HESA's own figures give two different totals for the same year. The raw agent picked Figure 3; the governed table fixes Figure 4 as the single source and states why. Neither number is wrong, but without a stated choice two analysts can quote different numbers.
3. **Shares agreed to one decimal place.** The numerators and denominators differ slightly (different source figures), which only shows in the underlying counts.
4. **What governance added was not accuracy but explicitness:** every answer came with the source figure and a caveat (for example, "classified qualifiers only", "unknown domicile stays in the denominator"), and the answer to "which total?" is the same every time.

## Honest limits
- Five questions, one run each, one model: too small to claim a general effect.
- The raw HESA files are unusually clean and the questions are fairly direct. A messier source or vaguer questions would likely widen the gap; I have not tested that.
- The governed agent had an easier job (values already computed), so matching it is expected. The meaningful result is that the raw agent matched on four of five and differed on the total only because HESA itself publishes two totals.
