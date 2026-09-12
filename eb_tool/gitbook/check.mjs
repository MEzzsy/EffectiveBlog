import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from 'yaml';
import Ajv2020 from 'ajv/dist/2020.js';
import { fromMarkdown } from 'mdast-util-from-markdown';

const toolDirectory = path.dirname(fileURLToPath(import.meta.url));
const defaultRoot = path.resolve(toolDirectory, '../..');
const schema = parse(fs.readFileSync(path.join(toolDirectory, 'schemas/gitbook-docs.schema.yaml'), 'utf8'));
const ajv = new Ajv2020({ allErrors: true, strict: false });
ajv.addFormat('uri', value => {
  try { return Boolean(new URL(value).protocol); } catch { return false; }
});
ajv.addFormat('icon', true);
const validateSite = ajv.compile(schema);

function walk(node, visit) {
  visit(node);
  for (const child of node.children ?? []) walk(child, visit);
}

function inside(root, target) {
  const relative = path.relative(root, target);
  return relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}

export function checkRepository(repositoryRoot) {
  const root = fs.realpathSync(repositoryRoot);
  const issues = [];
  const pages = [];
  const assets = new Set();
  const add = (severity, code, file, line, message) => issues.push({ severity, code, file, line, message });
  const display = file => path.relative(root, file).split(path.sep).join('/');
  const readYaml = name => {
    try { return parse(fs.readFileSync(path.join(root, name), 'utf8')); }
    catch (error) { add('error', 'CONFIG', name, 1, error.message); return null; }
  };
  const site = readYaml('gitbook-docs.yaml');
  const config = readYaml('.gitbook.yaml');
  if (site && !validateSite(site)) {
    add('error', 'SITE_SCHEMA', 'gitbook-docs.yaml', 1, ajv.errorsText(validateSite.errors));
  }
  const nodes = site?.site?.structure;
  if (!Array.isArray(nodes) || nodes.length !== 1 || nodes[0]?.type !== 'space' || nodes[0]?.default !== true) {
    add('error', 'SITE_MAPPING', 'gitbook-docs.yaml', 1, '当前仓库的免费方案检查要求一个默认 space，目录层级由 SUMMARY.md 表达。');
  }
  if (nodes?.[0]?.content?.directory !== './') {
    add('error', 'CONTENT_ROOT', 'gitbook-docs.yaml', 1, '本仓库的 Markdown 源码位于 ./，不要指向构建产物目录。');
  }
  if (!config || config.root !== './' || config.structure?.readme !== 'README.md' || config.structure?.summary !== 'SUMMARY.md') {
    add('error', 'SPACE_CONFIG', '.gitbook.yaml', 1, '应设置 root: ./、structure.readme: README.md 和 structure.summary: SUMMARY.md。');
  }
  if (issues.some(issue => issue.severity === 'error')) return { pages, assets: 0, issues };

  function resolveReference(file, url, line, navigation = false) {
    // This check is offline: external URLs and platform-generated anchors are not fetched.
    if (/^(?:https?:|mailto:|tel:|data:|\/\/)/i.test(url)) return null;
    if (/^[a-z][a-z\d+.-]*:/i.test(url)) {
      add('error', 'LOCAL_PROTOCOL', display(file), line, `不能同步的本机或应用链接：${url}`);
      return null;
    }
    const pathname = url.split(/[?#]/, 1)[0];
    if (!pathname) return null;
    let decoded;
    try { decoded = decodeURIComponent(pathname); }
    catch { add('error', 'URL_ENCODING', display(file), line, `无效 URL 编码：${url}`); return null; }
    if (/^\/(?:Users|Applications|home|private|tmp)\//.test(decoded)) {
      add('error', 'ABSOLUTE_PATH', display(file), line, `本机绝对路径：${url}`);
      return null;
    }
    const target = path.resolve(decoded.startsWith('/') ? root : path.dirname(file), decoded.replace(/^\//, ''));
    if (!inside(root, target)) {
      add('error', 'OUTSIDE_ROOT', display(file), line, `引用超出同步目录：${url}`);
      return null;
    }
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
      add('error', 'MISSING_FILE', display(file), line, `目标文件不存在：${url}`);
      return null;
    }
    if (!inside(root, fs.realpathSync(target))) {
      add('error', 'OUTSIDE_ROOT', display(file), line, `符号链接指向同步目录外：${url}`);
      return null;
    }
    const relative = display(target);
    if (/^(?:docs|_book|build|dist|node_modules|eb_tool)\//.test(relative) || relative === 'AGENTS.md') {
      add('error', 'NON_CONTENT', display(file), line, `引用了构建产物、依赖或管理文件：${url}`);
      return null;
    }
    if (navigation && !/\.md$/i.test(target)) {
      add('error', 'NAVIGATION_FILE', display(file), line, `目录必须指向 Markdown 源文件：${url}`);
      return null;
    }
    if (!/\.md$/i.test(target)) assets.add(target);
    if (fs.statSync(target).size > 100 * 1024 * 1024) {
      add('error', 'FILE_SIZE', display(file), line, `文件超过 Git Sync 单文件 100 MB 限制：${url}`);
    }
    return target;
  }

  const summaryFile = path.join(root, config.structure.summary);
  let summary;
  try { summary = fs.readFileSync(summaryFile, 'utf8'); }
  catch (error) {
    add('error', 'SUMMARY', display(summaryFile), 1, error.message);
    return { pages, assets: 0, issues };
  }
  const tree = fromMarkdown(summary);
  const navigation = [];
  walk(tree, node => {
    if (node.type === 'link') navigation.push(node);
  });
  const expectedEntries = summary.split('\n').filter(line => /^\s*[-*+]\s+/.test(line)).length;
  if (!navigation.length || navigation.length !== expectedEntries) {
    add('error', 'SUMMARY_SYNTAX', 'SUMMARY.md', 1,
      `目录有 ${expectedEntries} 个条目，CommonMark 仅识别 ${navigation.length} 个链接；含空格的地址需要 <...> 或 %20。`);
  }
  const seen = new Set();
  for (const entry of navigation) {
    const target = resolveReference(summaryFile, entry.url, entry.position.start.line, true);
    if (!target) continue;
    if (seen.has(target)) {
      add('error', 'DUPLICATE_PAGE', 'SUMMARY.md', entry.position.start.line, `同一页面只能出现一次：${entry.url}`);
      continue;
    }
    seen.add(target);
    pages.push(display(target));
  }
  if (!seen.has(path.join(root, config.structure.readme))) {
    add('error', 'README', 'SUMMARY.md', 1, '目录中缺少根 README.md。');
  }
  const redirects = config.redirects ?? {};
  if (typeof redirects !== 'object' || Array.isArray(redirects)) {
    add('error', 'REDIRECTS', '.gitbook.yaml', 1, 'redirects 必须是旧地址到 Markdown 文件的映射。');
  } else {
    for (const destination of Object.values(redirects)) {
      if (typeof destination !== 'string') add('error', 'REDIRECTS', '.gitbook.yaml', 1, '重定向目标必须是字符串。');
      else resolveReference(path.join(root, '.gitbook.yaml'), destination, 1, true);
    }
  }
  for (const relative of pages) {
    const file = path.join(root, relative);
    const content = fs.readFileSync(file, 'utf8');
    const ast = fromMarkdown(content);
    const definitions = new Map();
    walk(ast, node => {
      if (node.type === 'definition') definitions.set(node.identifier, node.url);
    });
    walk(ast, node => {
      const line = node.position?.start.line ?? 1;
      let url;
      if (node.type === 'image' || node.type === 'link') url = node.url;
      if (node.type === 'imageReference' || node.type === 'linkReference') url = definitions.get(node.identifier);
      if (url) {
        const target = resolveReference(file, url, line);
        if (target?.endsWith('.md') && !seen.has(target)) {
          add('warning', 'UNLISTED_PAGE', relative, line, `链接指向未在 SUMMARY.md 中列出的页面：${url}`);
        }
      }
      if (node.type === 'html') {
        if (/<(?:img|iframe|script|style|table)\b|\bstyle\s*=/i.test(node.value)) {
          add('warning', 'HTML_REVIEW', relative, line, 'HTML 内容或内联样式需要在 GitBook 云端核对，不能保证保留原样式。');
        }
        for (const match of node.value.matchAll(/\b(?:src|href)\s*=\s*(["'])(.*?)\1/gi)) {
          resolveReference(file, match[2].replaceAll('&amp;', '&'), line);
        }
      }
      if (node.type === 'text' && /!?\[[^\]\n]+\]\([^\n]*\)/.test(node.value)) {
        add('warning', 'UNPARSED_LINK', relative, line, '看似链接的文本未被 CommonMark 识别，请检查空格和括号。');
      }
      if (node.type === 'text' && /\{%|\{\{/.test(node.value)) {
        add('warning', 'TEMPLATE_REVIEW', relative, line, '模板语法需由 GitBook 云端导入验证。');
      }
    });
  }
  return { pages, assets: assets.size, issues };
}

function main() {
  const args = process.argv.slice(2);
  if (args.includes('--help')) {
    console.log('node check.mjs [--root PATH] [--report FILE]\n本地检查配置、目录和文件引用；不登录、不上传、不渲染新版 GitBook 页面。');
    return;
  }
  let root = defaultRoot;
  let report = path.join(toolDirectory, 'reports/check.json');
  for (let i = 0; i < args.length; i++) {
    if (!['--root', '--report'].includes(args[i]) || !args[i + 1]) throw new Error(`未知或缺少值的参数：${args[i]}`);
    const option = args[i++];
    if (option === '--root') root = path.resolve(args[i]);
    else report = path.resolve(args[i]);
  }
  const result = checkRepository(root);
  const errors = result.issues.filter(issue => issue.severity === 'error');
  const warnings = result.issues.filter(issue => issue.severity === 'warning');
  if (report) {
    fs.mkdirSync(path.dirname(report), { recursive: true });
    fs.writeFileSync(report, JSON.stringify(result, null, 2) + '\n');
  }
  console.log(`本地内容检查：${result.pages.length} 页，${result.assets} 个实际存在的附件，${errors.length} 个错误，${warnings.length} 条待复核提示。`);
  for (const issue of errors) console.log(`ERROR ${issue.file}:${issue.line} [${issue.code}] ${issue.message}`);
  const codes = [...new Set(warnings.map(issue => issue.code))];
  for (const code of codes) console.log(`REVIEW ${code}: ${warnings.filter(issue => issue.code === code).length}`);
  if (report) console.log(`完整报告：${report}`);
  console.log('尚未验证：GitBook 云端导入、最终排版、页面锚点、外部链接与发布。');
  process.exitCode = errors.length ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { main(); } catch (error) { console.error(error.message); process.exitCode = 1; }
}
