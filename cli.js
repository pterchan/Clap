#!/usr/bin/env node
const { spawn } = require('child_process');
const path = require('path');

const python = process.env.PYTHON || 'python3';
const script = path.join(__dirname, 'clap.py');

const child = spawn(python, [script, ...process.argv.slice(2)], {
  stdio: 'inherit',
  shell: false
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});
