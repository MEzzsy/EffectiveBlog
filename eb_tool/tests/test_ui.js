const test = require("node:test");
const assert = require("node:assert/strict");
const { topLevelPaths, canMovePaths, titleWithoutNumber, visibleRows, remapPath, reorderProposal, rowDropIntent } = require("../ui/app.js");

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

const reorderEntries = [
  ...outlineEntries,
  ...["01 甲.md", "02 乙.md", "03 丙.md", "04 丁.md"].map(name => ({
    path: "01 目录/" + name, parent: "01 目录", name, kind: "file"
  })),
];

test("同级多选排序保持原有相对顺序，支持前插、后插并忽略无变化的落点", () => {
  const first = "01 目录/01 甲.md", second = "01 目录/02 乙.md", third = "01 目录/03 丙.md", last = "01 目录/04 丁.md";
  assert.deepEqual(reorderProposal(reorderEntries, [last, second, second], first, "before"),
    { paths: [second, last], anchor: first, position: "before" });
  assert.deepEqual(reorderProposal(reorderEntries, [first], last, "after"),
    { paths: [first], anchor: last, position: "after" });
  assert.equal(reorderProposal(reorderEntries, [second, third], first, "after"), null);
  assert.equal(reorderProposal(reorderEntries, [first], second, "before"), null);
  assert.deepEqual(reorderProposal(reorderEntries, ["01 目录", first], "02 目录", "after"),
    { paths: ["01 目录"], anchor: "02 目录", position: "after" });
});

test("排序排除混合类型、跨目录、README、自身参照和不合法落点", () => {
  for (const [paths, anchor, position] of [
    [["01 目录/README.md"], "01 目录/01 甲.md", "before"],
    [["01 目录/01 甲.md"], "01 目录/README.md", "after"],
    [["01 根文档.md"], "01 目录/01 甲.md", "before"],
    [["01 目录"], "01 根文档.md", "after"],
    [["01 目录"], "01 目录", "before"],
    [["missing"], "01 目录", "before"],
    [["01 目录"], "missing", "before"],
    [["01 目录"], "02 目录", "invalid"],
    [[], "02 目录", "before"],
  ]) assert.equal(reorderProposal(reorderEntries, paths, anchor, position), null);
});

test("目录边缘排序、中间移入，搜索和跨目录文件行不触发排序", () => {
  assert.deepEqual(rowDropIntent(reorderEntries, ["02 目录"], "01 目录", 0.1),
    { action: "reorder", payload: { paths: ["02 目录"], anchor: "01 目录", position: "before" } });
  assert.deepEqual(rowDropIntent(reorderEntries, ["02 目录"], "01 目录", 0.5),
    { action: "move", payload: { paths: ["02 目录"], target: "01 目录" } });
  assert.equal(rowDropIntent(reorderEntries, ["02 目录"], "01 目录", 0.1, false), null);
  assert.equal(rowDropIntent(reorderEntries, ["01 根文档.md"], "01 目录/01 甲.md", 0.5), null);
  assert.equal(rowDropIntent(reorderEntries, ["01 目录/01 甲.md"], "01 目录", 0.5), null);
  assert.deepEqual(rowDropIntent(reorderEntries, ["01 目录/01 甲.md"], "01 目录/04 丁.md", 0.9),
    { action: "reorder", payload: { paths: ["01 目录/01 甲.md"], anchor: "01 目录/04 丁.md", position: "after" } });
});

test("编号互换只映射一次，按最长原路径匹配以保留展开目录和焦点", () => {
  const mapping = [
    { from: "01 目录", to: "02 目录" }, { from: "02 目录", to: "01 目录" },
    { from: "01 目录/01 子目录", to: "02 目录/02 子目录" },
  ];
  assert.equal(remapPath("01 目录/README.md", mapping), "02 目录/README.md");
  assert.equal(remapPath("02 目录", mapping), "01 目录");
  assert.equal(remapPath("01 目录/01 子目录/01 笔记.md", mapping), "02 目录/02 子目录/01 笔记.md");
  assert.equal(remapPath("01 目录的其他名称", mapping), "01 目录的其他名称");
  assert.equal(remapPath("", mapping), "");
  assert.equal(remapPath(null, mapping), null);
});

test("未编号中文项目采用后端顺序，显示顺序与拖拽判断保持一致", () => {
  const entries = [
    { name: "阿.md", sortOrder: 2 }, { name: "波.md", sortOrder: 1 }, { name: "中.md", sortOrder: 0 },
  ].map(entry => ({ ...entry, path: entry.name, parent: "", kind: "file" }));
  assert.deepEqual(visibleRows(entries, "", new Set()).map(row => row.path), ["中.md", "波.md", "阿.md"]);
  assert.deepEqual(reorderProposal(entries, ["阿.md"], "中.md", "before"),
    { paths: ["阿.md"], anchor: "中.md", position: "before" });
  assert.equal(reorderProposal(entries, ["中.md"], "波.md", "before"), null);
});
