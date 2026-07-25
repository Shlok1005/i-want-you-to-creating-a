#!/usr/bin/env node
/**
 * Deprecated: Fitness Gurukul now uses the Python backend only.
 * Run: python3 server.py
 * Or:  npm start
 */
console.error(`
Fitness Gurukul no longer uses the Node/Express server.

Use the Python backend instead:

  python3 server.py

Or:

  npm start

Admin and form APIs now live in server.py with SQLite storage.
`);
process.exit(1);
