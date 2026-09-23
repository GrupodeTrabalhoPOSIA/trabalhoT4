"""Congela fontes permitidas, parâmetros públicos e entradas; nunca inclui .env."""
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'BACKEND'))
from app.services.final_delivery import canonical_bytes, digest, runtime_configuration


def freeze():
    release = ROOT / 'BACKEND/release'
    public = ROOT / 'FRONTEND/public/entregas/t6'
    frontend_manifest = ROOT / 'FRONTEND/src/features/t6/releaseManifest.json'
    patterns = [
        'BACKEND/app/**/*.py', 'BACKEND/prompts/**/*.txt', 'BACKEND/knowledge/*.txt',
        'BACKEND/tests/**/*.py', 'BACKEND/evaluation/*.py', 'BACKEND/database/**/*.sql',
        'BACKEND/pyproject.toml', 'BACKEND/Dockerfile', 'BACKEND/.dockerignore', 'BACKEND/.env.example',
        'FRONTEND/src/**/*.ts', 'FRONTEND/src/**/*.tsx', 'FRONTEND/src/**/*.css', 'FRONTEND/src/**/*.json', 'FRONTEND/src/**/*.csv',
        'FRONTEND/public/entregas/**/*.pdf', 'FRONTEND/public/entregas/**/*.docx', 'FRONTEND/public/entregas/**/*.md', 'FRONTEND/public/entregas/**/*.svg',
        'FRONTEND/package*.json', 'FRONTEND/tsconfig*.json', 'FRONTEND/*.config.*', 'FRONTEND/index.html', 'FRONTEND/.env.example',
        'README.md', 'INTEGRACOES.md', 'render.yaml', '.gitignore',
    ]
    paths = sorted({p for pattern in patterns for p in ROOT.glob(pattern) if p.is_file() and p != frontend_manifest})
    contents = {p.relative_to(ROOT).as_posix(): canonical_bytes(p) for p in paths}
    cases = json.loads((ROOT / 'FRONTEND/src/features/t5/cases.json').read_text(encoding='utf-8'))
    fixtures = {name: (ROOT / 'FRONTEND/public/entregas/t5' / name).read_bytes() for name in sorted({c['fixture'] for c in cases if c.get('fixture')})}
    identity = {'files': {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}, 'configuration': runtime_configuration(), 'cases_sha256': digest(cases), 'fixtures': {name: hashlib.sha256(content).hexdigest() for name, content in fixtures.items()}}
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip() or 'not-available'
    manifest = {**identity, 'release_id': 't6-' + digest(identity)[:24], 'created_at': datetime.now(timezone.utc).isoformat(), 'source_commit': commit}
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2).encode()
    for path in [release / 'manifest.json', public / 'manifest.json', frontend_manifest]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(serialized)
    (release / 'cases.json').write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding='utf-8')
    (release / 'fixtures').mkdir(exist_ok=True)
    for name, content in fixtures.items(): (release / 'fixtures' / name).write_bytes(content)
    (release / 'docs').mkdir(exist_ok=True)
    for path in public.iterdir():
        if path.suffix in {'.md', '.svg'}: (release / 'docs' / path.name).write_bytes(canonical_bytes(path))
    # Artefatos derivados são incluídos no fonte para executá-lo após a extração.
    contents['FRONTEND/src/features/t6/releaseManifest.json'] = serialized
    contents['FRONTEND/public/entregas/t6/manifest.json'] = serialized
    for path in release.rglob('*'):
        if path.is_file() and path.name not in {'source.zip', 'source.sha256'}:
            contents[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    with zipfile.ZipFile(release / 'source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(contents.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED)
    (release / 'source.sha256').write_text(hashlib.sha256((release / 'source.zip').read_bytes()).hexdigest(), encoding='ascii')
    print(f"{manifest['release_id']} | {len(paths)} arquivos | {len(cases)} casos | {len(fixtures)} documentos")


if __name__ == '__main__':
    freeze()
