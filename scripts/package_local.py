"""Genera zip Lambda local; no sube archivos ni conecta a AWS."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'build'
out.mkdir(exist_ok=True)
with ZipFile(out/'lambda.zip','w',ZIP_DEFLATED) as archive:
    for path in sorted((ROOT/'src').glob('*.py')):
        archive.write(path,path.name)
print('Paquete local: build/lambda.zip')
