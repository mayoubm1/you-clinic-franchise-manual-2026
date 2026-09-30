# -*- coding: utf-8 -*-
"""Deterministic internal link check for the generated portal.

Scans the browser-facing generated HTML (index.html, master.html,
chapters/*.html) for href/src/url() references and fails if any *relative*
(internal) target is missing on disk. External URLs, fragments,
mailto:/tel:/data:/javascript: placeholders and the template are ignored.

Optional as-built 3D models referenced via data-gltf-src are reported as
informational when absent (the viewer falls back to a procedural model until a
real .gltf is dropped into assets/models/).

Run:  python tools/check_links.py
Exit code 0 = all internal references resolve; 1 = broken reference(s) found.
"""
import io
import glob
import os
import re
import sys
from itertools import chain

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGET = re.compile(r'(?<![\w-])(?:href|src)=["\']([^"\']+)["\']')
OPTIONAL = re.compile(r'data-gltf-src=["\']([^"\']+)["\']')
SKIP_PREFIX = ('#', 'javascript:', 'data:', 'mailto:', 'tel:')


def _unref(base, u):
    low = u.lower()
    if not u or u.startswith(SKIP_PREFIX) or re.match(r'[a-z][a-z0-9+.-]*:', low):
        return None
    if '{{' in u or '*/__' in u:
        return None
    p = u.split('#', 1)[0].split('?', 1)[0]
    if not p:
        return None
    return os.path.normpath(os.path.join(base, p))


def main():
    files = [os.path.join(ROOT, 'index.html'), os.path.join(ROOT, 'master.html')]
    files += sorted(glob.glob(os.path.join(ROOT, 'chapters', '*.html')))

    broken = []
    optional_missing = []
    for f in files:
        d = io.open(f, encoding='utf-8', errors='replace').read()
        base = os.path.dirname(f)
        for m in chain(TARGET.finditer(d), re.compile(r'url\(([^)]+)\)').finditer(d)):
            t = _unref(base, m.group(1).strip().strip('"\''))
            if t is not None and not os.path.exists(t):
                broken.append((os.path.relpath(f, ROOT), os.path.relpath(t, ROOT)))
        for m in OPTIONAL.finditer(d):
            t = _unref(base, m.group(1).strip().strip('"\''))
            if t is not None and not os.path.exists(t):
                optional_missing.append((os.path.relpath(f, ROOT), os.path.relpath(t, ROOT)))

    print('internal link check: scanned %d generated html files' % len(files))
    for src, tgt in optional_missing:
        print('  optional (ok, procedural fallback): %s -> %s' % (src, tgt))
    if broken:
        print('BROKEN references:')
        for src, tgt in broken:
            print('  %s -> %s  (MISSING)' % (src, tgt))
        return 1
    print('OK: all required internal references resolve')
    return 0


if __name__ == '__main__':
    sys.exit(main())