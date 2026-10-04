from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[1]
for line in (root/'SHA256SUMS.txt').read_text().splitlines():
    digest,name=line.split('  ',1)
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
print('Integridad verificada')
