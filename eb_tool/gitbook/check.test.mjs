import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { checkRepository } from './check.mjs';

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'eb-gitbook-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const put = (name, content) => {
    fs.mkdirSync(path.dirname(path.join(root, name)), { recursive: true });
    fs.writeFileSync(path.join(root, name), content);
  };
  put('.gitbook.yaml', 'root: ./\nstructure:\n  readme: README.md\n  summary: SUMMARY.md\n');
  put('gitbook-docs.yaml', 'site:\n  title: Test\n  structure:\n    - type: space\n      key: test\n      title: Test\n      path: test\n      default: true\n      content:\n        directory: ./\n        language: zh\n');
  put('README.md', '# 简介\n');
  put('01 笔记/01 文档.md', '# 内容\n\n![图](../assets/pic.png)\n');
  put('assets/pic.png', 'test asset');
  put('SUMMARY.md', '# Summary\n\n- [简介](README.md)\n- [文档](<01 笔记/01 文档.md>)\n');
  return { root, put, codes: () => checkRepository(root).issues.map(issue => issue.code) };
}

test('Chinese and spaced filenames work; code examples do not become missing links', t => {
  const { root, put } = fixture(t);
  put('README.md', '# 简介\n\n`[example](missing.md)`\n\n```md\n![example](missing.png)\n```\n');
  const result = checkRepository(root);
  assert.deepEqual(result.issues, []);
  assert.equal(result.pages.length, 2);
  assert.equal(result.assets, 1);
});

test('rejects malformed navigation and duplicate pages', t => {
  const { put, codes } = fixture(t);
  put('SUMMARY.md', '# Summary\n\n- [简介](README.md)\n- [文档](01 笔记/01 文档.md)\n- [重复](README.md)\n');
  assert.ok(codes().includes('SUMMARY_SYNTAX'));
  assert.ok(codes().includes('DUPLICATE_PAGE'));
});

test('checks reference images and HTML assets and rejects local absolute paths', t => {
  const { put, codes } = fixture(t);
  put('README.md', '# 简介\n\n![image][missing]\n\n[missing]: assets/missing.png\n\n<img src="assets/missing2.png">\n\n![local](/Users/me/old.png)\n');
  assert.equal(codes().filter(code => code === 'MISSING_FILE').length, 2);
  assert.ok(codes().includes('ABSOLUTE_PATH'));
});

test('validates official schema and free site content mapping', t => {
  const { root, put, codes } = fixture(t);
  const config = fs.readFileSync(path.join(root, 'gitbook-docs.yaml'), 'utf8');
  put('gitbook-docs.yaml', config.replace('language: zh', 'language: zh-hans').replace('directory: ./', 'directory: ./docs'));
  assert.ok(codes().includes('SITE_SCHEMA'));
  assert.ok(codes().includes('CONTENT_ROOT'));
});

test('rejects generated content and links escaping the repository', t => {
  const { put, codes } = fixture(t);
  put('docs/index.html', '<p>legacy</p>');
  put('README.md', '# 简介\n\n[old](docs/index.html)\n\n[outside](../outside.md)\n');
  assert.ok(codes().includes('NON_CONTENT'));
  assert.ok(codes().includes('OUTSIDE_ROOT'));
});
