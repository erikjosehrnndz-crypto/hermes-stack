import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic';

type TreeNode = { name: string; type: 'file' | 'directory'; children?: TreeNode[] };

function walk(dir: string, depth: number): TreeNode[] {
  if (depth > 3) return [];
  const entries: TreeNode[] = [];
  try {
    for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
      if (item.name.startsWith('.')) continue;
      const fullPath = path.join(dir, item.name);
      entries.push(
        item.isDirectory()
          ? { name: item.name, type: 'directory', children: walk(fullPath, depth + 1) }
          : { name: item.name, type: 'file' }
      );
    }
  } catch { /* ignore permission errors */ }
  return entries;
}

export async function GET() {
  return NextResponse.json(walk('/host-root', 0));
}
