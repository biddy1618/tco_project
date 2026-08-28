# Slice 3 Tracker log

2026-08-28, subscription **T332 - TCO**, `python -m maf.slice3`.
Inputs are Tracker IDs (`maf/tracker_cases.json` deducted prompts).
Use a fresh `history.json` per case. Electric tracing: reply
`I&E Job Pack YY-NNNN` (same placeholder as ID003).

33 job packs. 3 WPS table misses (TC-026, TC-027, TC-034).
See `docs/azure-environment.md` §5 for the index ranges.

```bash
python -m maf.slice3 TC-001
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

## TC-001  (EWO 22-0294, TLR single-removal)

```bash
python -m maf.slice3 TC-001
```

pack  (WPS No, NDE No, CS)

## TC-002  (EWO 22-0430, TLR single-removal)

```bash
python -m maf.slice3 TC-002
```

pack  (WPS No, NDE No, CS)

## TC-003  (22-0385, TLR single-removal)

```bash
python -m maf.slice3 TC-003
```

pack  (WPS No, NDE No, CS)

## TC-004  (23-0474, Pipe section repl.)

```bash
python -m maf.slice3 TC-004
```

pack  (WPS Yes, NDE No, CS)

## TC-005  (25-0048, Pipe section repl.)

```bash
python -m maf.slice3 TC-005
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-006  (25-0046, TLR single-removal)

```bash
python -m maf.slice3 TC-006
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-007  (25-0047, Pipe extension)

```bash
python -m maf.slice3 TC-007
```

pack (Site/PSSR from template; ID003 Site was empty)

## TC-008  (25-0049, Flange replacement)

```bash
python -m maf.slice3 TC-008
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-009  (25-0050, Flange replacement)

```bash
python -m maf.slice3 TC-009
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-010  (23-0060, TLR multi-removal)

```bash
python -m maf.slice3 TC-010
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-011  (25-0068, Flange replacement)

```bash
python -m maf.slice3 TC-011
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-012  (25-0071, Pipe section repl.)

```bash
python -m maf.slice3 TC-012
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-013  (25-0072, TLR single-removal)

```bash
python -m maf.slice3 TC-013
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-014  (25-0073, TLR single-removal)

```bash
python -m maf.slice3 TC-014
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-015  (25-0078, TLR single-removal)

```bash
python -m maf.slice3 TC-015
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-016  (25-0079, Elbow replacement)

```bash
python -m maf.slice3 TC-016
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-017  (25-0085, TLR single-removal)

```bash
python -m maf.slice3 TC-017
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-018  (25-0086, TLR single-removal)

```bash
python -m maf.slice3 TC-018
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-019  (25-0087, TLR multi-removal)

```bash
python -m maf.slice3 TC-019
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-020  (25-0088, TLR single-removal)

```bash
python -m maf.slice3 TC-020
```

pack  (WPS No, NDE No, CS)

## TC-021  (25-0093, TLR single-removal)

```bash
python -m maf.slice3 TC-021
```

pack  (WPS No, NDE No, CS)

## TC-022  (25-0112, TLR single-removal)

```bash
python -m maf.slice3 TC-022
```

pack  (WPS No, NDE No, CS)

## TC-023  (25-0114, TLR single-removal)

```bash
python -m maf.slice3 TC-023
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-024  (25-0120, TLR single-removal)

```bash
python -m maf.slice3 TC-024
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-025  (25-0464, TLR multi-removal)

```bash
python -m maf.slice3 TC-025
```

pack  (WPS No, NDE No, CS)

## TC-026  (25-0542, Pipe section repl.)

```bash
python -m maf.slice3 TC-026
```

WPS miss — 150H09 not in wps-diain

## TC-027  (EWO-2180860, Tee/branch repl.)

```bash
python -m maf.slice3 TC-027
python -m maf.slice3 --history history.json "Tee replacement. Replace the pipe section."
```

WPS miss — 300H21(A) has 0.5–3 and 14–30, not 4″

## TC-028  (EWO-1381685, Flange replacement)

```bash
python -m maf.slice3 TC-028
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
python -m maf.slice3 --history history.json "Flange replacement."
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS Yes, NDE No, CS)

## TC-029  (EWO-1924975, Pipe section repl.)

```bash
python -m maf.slice3 TC-029
```

pack  (WPS No, NDE No, CS)

## TC-030  (EWO-2013037, Section + support)

```bash
python -m maf.slice3 TC-030
```

pack  (WPS No, NDE No, CS)

## TC-031  (EWO-2029651, Flange replacement)

```bash
python -m maf.slice3 TC-031
python -m maf.slice3 --history history.json "Flange replacement. Insulated. Diameter 2 inch."
```

pack  (WPS No, NDE Yes, SS)

## TC-032  (EWO-2029652, Flange replacement)

```bash
python -m maf.slice3 TC-032
python -m maf.slice3 --history history.json "Flange replacement. Insulated."
```

pack  (WPS No, NDE Yes, SS)

## TC-033  (EWO-2107378, Pipe section repl.)

```bash
python -m maf.slice3 TC-033
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
python -m maf.slice3 --history history.json "Replace the pipe section."
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS No, NDE No, CS)

## TC-034  (EWO-2126781, Pipe section repl.)

```bash
python -m maf.slice3 TC-034
```

WPS miss — 150H21 has 0.5–3 and 14–48, not 6″

## TC-035  (EWO-2127713, Pipe section repl.)

```bash
python -m maf.slice3 TC-035
python -m maf.slice3 --history history.json "Replace the pipe section."
python -m maf.slice3 --history history.json "I&E Job Pack YY-NNNN"
```

pack  (WPS Yes, NDE No, CS)

## TC-036  (EWO-2127910, Flange replacement)

```bash
python -m maf.slice3 TC-036
python -m maf.slice3 --history history.json "Insulated."
```

pack  (WPS No, NDE Yes, SS)
