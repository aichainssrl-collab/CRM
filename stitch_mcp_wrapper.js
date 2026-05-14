#!/usr/bin/env node

const { spawn } = require('child_process');

const mcp = spawn('npx', ['-y', '@_davideast/stitch-mcp@0.5.5', 'proxy'], {
  env: process.env
});

const readline = require('readline');
const rl = readline.createInterface({
  input: mcp.stdout,
  terminal: false
});

function resolveRefs(obj, defs) {
  if (Array.isArray(obj)) {
    return obj.map(item => resolveRefs(item, defs));
  } else if (obj !== null && typeof obj === 'object') {
    if (obj['$ref'] && obj['$ref'].startsWith('#/$defs/')) {
      const refName = obj['$ref'].replace('#/$defs/', '');
      if (defs && defs[refName]) {
        // Recursively resolve in case the def itself has refs, though usually we just copy it
        return resolveRefs(defs[refName], defs);
      }
    }
    const newObj = {};
    for (const key in obj) {
      if (key !== '$defs') {
        newObj[key] = resolveRefs(obj[key], defs);
      }
    }
    return newObj;
  }
  return obj;
}

rl.on('line', (line) => {
  try {
    const msg = JSON.parse(line);
    if (msg.id !== undefined && msg.result && msg.result.tools) {
      msg.result.tools = msg.result.tools.map(tool => {
        if (tool.inputSchema) {
          const defs = tool.inputSchema['$defs'] || {};
          tool.inputSchema = resolveRefs(tool.inputSchema, defs);
        }
        return tool;
      });
      process.stdout.write(JSON.stringify(msg) + '\n');
    } else {
      process.stdout.write(line + '\n');
    }
  } catch (e) {
    process.stdout.write(line + '\n');
  }
});

mcp.stderr.on('data', (data) => {
  process.stderr.write(data);
});

process.stdin.pipe(mcp.stdin);
