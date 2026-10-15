"""Prepara plantilla empaquetable local; no conecta a AWS."""
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/'scripts/package_local.py'),run_name='__main__')
text=(ROOT/'template.yaml').read_text(encoding='utf-8')
(ROOT/'build/template.local.yaml').write_text(text.replace('CodeUri: src/','CodeUri: lambda.zip'),encoding='utf-8')
print('Plantilla empaquetable: build/template.local.yaml')
