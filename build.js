// build.js — compatibility shim (ESM, since the repo package.json sets "type":"module").
// The single source of truth for the build is build_portal.py (Python 3).
// This wrapper lets the GitHub Actions workflow (and Node users) run `node build.js`
// exactly as the original plan described, while executing the real Python builder.
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const py = process.platform === 'win32' ? 'python' : 'python3';

const res = spawnSync(py, [path.join(__dirname, 'build_portal.py')], {
  stdio: 'inherit'
});
if (res.status !== 0) {
  console.error('build failed');
  process.exit(res.status || 1);
}
console.log('build.js -> build_portal.py completed');