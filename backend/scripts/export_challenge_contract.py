"""Regenerate the cross-language runtime contract fixture from trusted validators."""
import json
from pathlib import Path
from app.services.learning_challenges import DEFINITIONS, public_definition, execute, validate
root=Path(__file__).resolve().parents[2]
fixtures=json.loads((root/'backend/tests/fixtures/learning_challenges.json').read_text())
rows=[]
for id,d in DEFINITIONS.items():
    f=fixtures[id]
    rows.append({'definition':public_definition(d),'result':validate(d,f['circuit'],f['prediction'],execute(f['circuit']) if d['kind']=='circuit' else None,0)})
(root/'frontend/tests/fixtures/challenge-contract.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n')
