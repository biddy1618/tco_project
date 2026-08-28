# Agent runbook: dump `wps-diain` coverage for TC-026 / 027 / 034

You are a **runner**. Query Azure AI Search. Do not edit code, commit, or
install packages. Do not put a Search API key in the environment.

## Preconditions

```powershell
az account show --query "{name:name,id:id}" -o json
# name must be T332 - TCO
```

Wrong subscription: `az account set --subscription "T332 - TCO"`. No login:
`az login`, then stop if that fails. Same Python as slice 3 (repo root).

## Run (paste once, from repo root)

```powershell
python -c @"
from maf.search_client import WPS_INDEX, run_search

def dump(title, body):
    r = run_search(WPS_INDEX, body)
    vals = r.get('value') if isinstance(r, dict) else []
    print('===', title, 'hits=', len(vals), '===')
    for d in vals:
        print(' ', repr(d.get('line_class')), 'pwht=', repr(d.get('pwht')),
              'dia=', d.get('dia_in1'), '-', d.get('dia_in2'))

select = 'line_class,pwht,dia_in1,dia_in2'
for q in ['150H09', '150H21', '300H21', '300H21(A)', '300H21 (A)']:
    dump(q + ' keyword no filter', {
        'search': q, 'queryType': 'simple', 'searchFields': 'line_class',
        'select': select, 'top': 20,
    })
for q, dia in [('150H09', 4.0), ('150H09', 6.0), ('300H21(A)', 4.0),
               ('300H21 (A)', 4.0), ('150H21', 4.0), ('150H21', 6.0)]:
    dump('%s semantic dia=%s' % (q, dia), {
        'search': q, 'queryType': 'semantic',
        'semanticConfiguration': 'wps-diain-semantic-configuration',
        'filter': 'dia_in1 le %s and dia_in2 ge %s' % (dia, dia),
        'select': select, 'top': 6,
    })
"@
```

## Done when

Paste the full stdout. Do not interpret, do not re-run slice 3, do not open
Portal. If Search fails, paste the traceback and stop.

## Raw stdout:

```
=== 150H09 keyword no filter hits= 0 ===
=== 150H21 keyword no filter hits= 3 ===
  '150H21' pwht= 'N' dia= 14.0 - 48.0
  '150H21' pwht= 'Y' dia= 24.0 - 24.0
  '150H21' pwht= 'N' dia= 0.5 - 3.0
=== 300H21 keyword no filter hits= 6 ===
  '300H21 (B)' pwht= 'Y' dia= 24.0 - 48.0
  '300H21(A)' pwht= 'N' dia= 14.0 - 30.0
  '300H21(A)' pwht= 'Y' dia= 24.0 - 48.0
  '300H21 (B)' pwht= 'Y' dia= 14.0 - 30.0
  '300H21(A)' pwht= 'N' dia= 0.5 - 3.0
  '300H21 (B)' pwht= 'Y' dia= 0.5 - 3.0
=== 300H21(A) keyword no filter hits= 10 ===
  '300H21(A)' pwht= 'N' dia= 14.0 - 30.0
  '300H21(A)' pwht= 'Y' dia= 24.0 - 48.0
  '300H21(A)' pwht= 'N' dia= 0.5 - 3.0
  '150H25 (A)' pwht= 'Y' dia= 0.5 - 3.0
  '300H21 (B)' pwht= 'Y' dia= 24.0 - 48.0
  '150H25 (A)' pwht= 'Y' dia= 3.1 - 100.0
  '300H25 (A)' pwht= 'N' dia= 3.1 - 100.0
  '300H21 (B)' pwht= 'Y' dia= 14.0 - 30.0
  '300H25 (A)' pwht= 'N' dia= 0.5 - 3.0
  '300H21 (B)' pwht= 'Y' dia= 0.5 - 3.0
=== 300H21 (A) keyword no filter hits= 10 ===
  '300H21(A)' pwht= 'N' dia= 14.0 - 30.0
  '300H21(A)' pwht= 'Y' dia= 24.0 - 48.0
  '300H21(A)' pwht= 'N' dia= 0.5 - 3.0
  '150H25 (A)' pwht= 'Y' dia= 0.5 - 3.0
  '300H21 (B)' pwht= 'Y' dia= 24.0 - 48.0
  '150H25 (A)' pwht= 'Y' dia= 3.1 - 100.0
  '300H25 (A)' pwht= 'N' dia= 3.1 - 100.0
  '300H21 (B)' pwht= 'Y' dia= 14.0 - 30.0
  '300H25 (A)' pwht= 'N' dia= 0.5 - 3.0
  '300H21 (B)' pwht= 'Y' dia= 0.5 - 3.0
=== 150H09 semantic dia=4.0 hits= 0 ===
=== 150H09 semantic dia=6.0 hits= 0 ===
=== 300H21(A) semantic dia=4.0 hits= 2 ===
  '150H25 (A)' pwht= 'Y' dia= 3.1 - 100.0
  '300H25 (A)' pwht= 'N' dia= 3.1 - 100.0
=== 300H21 (A) semantic dia=4.0 hits= 2 ===
  '150H25 (A)' pwht= 'Y' dia= 3.1 - 100.0
  '300H25 (A)' pwht= 'N' dia= 3.1 - 100.0
=== 150H21 semantic dia=4.0 hits= 0 ===
=== 150H21 semantic dia=6.0 hits= 0 ===
```
