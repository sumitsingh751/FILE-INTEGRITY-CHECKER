import os, sys, json, hashlib, time, argparse
from pathlib import Path
from datetime import datetime

def calc_hash(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(8192)
            if not b: break
            h.update(b)
    return h.hexdigest()

def scan(root):
    root = Path(root).expanduser().resolve()
    data = {}
    for r, d, f in os.walk(root):
        rel = str(Path(r).relative_to(root))
        if rel == '.': rel = root.name
        data[rel] = {}
        for name in f:
            full = Path(r) / name
            try:
                data[rel][name] = calc_hash(full)
            except Exception as e:
                data[rel][name] = str(e)
    return {'root': str(root), 'scanned_at': time.time(), 'data': data}

def save(f, d):
    with open(f, 'w', encoding='utf-8') as x:
        json.dump(d, x, indent=2, sort_keys=True)

def load(f):
    with open(f, 'r', encoding='utf-8') as x:
        return json.load(x)

def show(d):
    print('ROOT:', d['root'])
    print('SCANNED_AT:', datetime.fromtimestamp(d['scanned_at']).isoformat())
    print()
    for folder, files in sorted(d['data'].items()):
        print('Folder:', folder)
        for n, h in sorted(files.items()):
            print(' ', n, '→', h)
        print()

def compare(b, c):
    diff = {'added': [], 'removed': [], 'changed': []}
    for folder in c['data']:
        if folder not in b['data']:
            for n in c['data'][folder]:
                diff['added'].append(f'{folder}/{n}')
        else:
            for n in c['data'][folder]:
                if n not in b['data'][folder]:
                    diff['added'].append(f'{folder}/{n}')
                elif b['data'][folder][n] != c['data'][folder][n]:
                    diff['changed'].append(f'{folder}/{n}')
    for folder in b['data']:
        if folder not in c['data']:
            for n in b['data'][folder]:
                diff['removed'].append(f'{folder}/{n}')
        else:
            for n in b['data'][folder]:
                if n not in c['data'][folder]:
                    diff['removed'].append(f'{folder}/{n}')
    return diff

def main():
    p = argparse.ArgumentParser()
    p.add_argument('cmd', choices=['init','verify'])
    p.add_argument('path', nargs='?', default='.')
    p.add_argument('-b','--baseline', default='baseline.json')
    a = p.parse_args()

    if a.cmd == 'init':
        s = scan(a.path)
        save(a.baseline, s)
        print('Baseline created at', a.baseline)
        show(s)

    elif a.cmd == 'verify':
        if not os.path.exists(a.baseline):
            print('Baseline not found:', a.baseline)
            sys.exit(1)
        b = load(a.baseline)
        c = scan(b['root'])
        d = compare(b, c)
        if not any(d.values()):
            print('No changes found.')
        else:
            print('\nChanges detected:')
            for k,v in d.items():
                if v:
                    print(k.upper()+':')
                    for i in v:
                        print(' ', i)
                    print()
        print('\nCurrent structure:')
        show(c)

if __name__ == '__main__':
    main()
