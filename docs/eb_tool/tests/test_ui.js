const test = require("node:test");
const assert = require("node:assert/strict");
const { topLevelPaths, canMovePaths, titleWithoutNumber, visibleRows } = require("../ui/app.js");

test("批量移动折叠父子选择并排除自身、后代和原目录", () => {
  assert.deepEqual(topLevelPaths(["a", "a/one.md", "a/inner/two.md", "b.md", "a"]), ["a", "b.md"]);
  assert.equal(canMovePaths(["a"], "a/inner"), false);
  assert.equal(canMovePaths(["a"], ""), false);
  assert.equal(canMovePaths(["a/file.md", "b/file.md"], "a"), false);
  assert.equal(canMovePaths(["a/file.md", "a/inner"], "b"), true);
  assert.equal(canMovePaths(["a/file.md"], ""), true);
  assert.equal(canMovePaths([], "b"), false);
});

test("名称输入只显示标题，编号由后端处理", () => {
  assert.equal(titleWithoutNumber("01 标题"), "标题");
  assert.equal(titleWithoutNumber("07-标题"), "标题");
  assert.equal(titleWithoutNumber("1 标题"), "标题");
  assert.equal(titleWithoutNumber("2024 年度总结"), "2024 年度总结");
  assert.equal(titleWithoutNumber("README"), "README");
  assert.equal(titleWithoutNumber("未编号"), "未编号");
  assert.equal(titleWithoutNumber(""), "");
});

const outlineEntries = [
  { path: "02 目录", parent: "", name: "02 目录", kind: "directory" },
  { path: "01 目录/README.md", parent: "01 目录", name: "README.md", kind: "file" },
  { path: "01 根文档.md", parent: "", name: "01 根文档.md", kind: "file" },
  { path: "01 目录/01 子目录/01 笔记.md", parent: "01 目录/01 子目录", name: "01 笔记.md", kind: "file" },
  { path: "01 目录/01 子目录", parent: "01 目录", name: "01 子目录", kind: "directory" },
  { path: "01 目录", parent: "", name: "01 目录", kind: "directory" },
  { path: "02 目录/README.md", parent: "02 目录", name: "README.md", kind: "file" },
];

test("列表按目录层级展开，折叠时隐藏所有后代并保留相邻项目", () => {
  assert.deepEqual(visibleRows(outlineEntries, "", new Set()).map(row => row.path),
    ["01 目录", "02 目录", "01 根文档.md"]);
  assert.deepEqual(visibleRows(outlineEntries, "", new Set(["01 目录", "01 目录/01 子目录"]))
    .map(row => [row.path, row.depth]), [
      ["01 目录", 0], ["01 目录/01 子目录", 1], ["01 目录/01 子目录/01 笔记.md", 2],
      ["01 目录/README.md", 1], ["02 目录", 0], ["01 根文档.md", 0],
    ]);
  assert.deepEqual(visibleRows(outlineEntries, "", new Set(["01 目录/01 子目录"])).map(row => row.path),
    ["01 目录", "02 目录", "01 根文档.md"]);
  assert.deepEqual(visibleRows(outlineEntries, "01 目录", new Set()).map(row => [row.name, row.depth]),
    [["01 子目录", 0], ["README.md", 0]]);
});

test("搜索跨越折叠目录，同名结果保留路径并以平面列表展示", () => {
  const result = visibleRows(outlineEntries, "01 目录", new Set(), "readme");
  assert.deepEqual(result.map(row => [row.path, row.depth]),
    [["01 目录/README.md", 0], ["02 目录/README.md", 0]]);
  assert.deepEqual(visibleRows(outlineEntries, "", new Set(), "子目录/01 笔记").map(row => row.path),
    ["01 目录/01 子目录/01 笔记.md"]);
  assert.equal(visibleRows(outlineEntries, "", new Set(), "不存在").length, 0);
});
