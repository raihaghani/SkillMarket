"""Package only source and submission files; exclude secrets, databases and tooling."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root=Path(__file__).resolve().parent.parent
folders=['config','marketplace','templates','assets','static','submission','.github']
files=['README.md','.env.example','.gitignore','manage.py','requirements.txt','requirements-lock.txt','package.json','package-lock.json','Procfile']
paths=[root/name for name in files]
for name in folders:
    paths.extend(p for p in (root/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.inspect.ndjson'))
paths.extend([root/'scripts/run_tests.py',root/'scripts/build_diagrams.py',root/'scripts/artifacts/build-workbooks.mjs',root/'scripts/package_submission.py'])
with ZipFile(root/'SkillMarket-submission.zip','w',ZIP_DEFLATED) as archive:
    for path in paths:
        archive.write(path,Path('SkillMarket')/path.relative_to(root))
print(f'Packaged {len(paths)} source and report files; credentials and local databases excluded.')
