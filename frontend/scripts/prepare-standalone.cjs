const fs = require('node:fs');
fs.cpSync('.next/static', '.next/standalone/.next/static', {recursive: true});
if (fs.existsSync('public')) fs.cpSync('public', '.next/standalone/public', {recursive: true});
