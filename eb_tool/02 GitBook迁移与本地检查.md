# 迁移状态

仓库已切换为新版 GitBook 的 Git Sync 源码工程，按免费方案使用一个默认内容空间。所有技术分类仍由根目录的 `SUMMARY.md` 组织，不需要拆成多个站点 section。

当前阶段完成本地配置与内容检查，尚未连接 GitBook 账户、上传或发布。新版 GitBook 的最终导入与页面效果还没有验证。

# 本地测试的范围

新版 `@gitbook/cli` 用于调用 GitBook API；它不提供旧版 GitBook 3.x 的本地 Markdown 静态构建流程。新版开源渲染器的官方开发方式也是读取已经发布的 GitBook 内容。本仓库提供配置、导航、附件和链接检查，页面效果需要导入 GitBook 后通过 Preview 验证。

本地检查使用 CommonMark 解析器，不等同于 GitBook 云端的导入器。外部链接可达性、最终页面锚点、模板语法、HTML 样式、云端导入及发布都需要后续复核。

# 配置文件

| 文件 | 作用 |
| --- | --- |
| 根目录 `.gitbook.yaml` | 指定 Markdown 源码根目录、首页与目录文件 |
| 根目录 `gitbook-docs.yaml` | 将唯一的默认空间映射到仓库根目录，语言为 `zh` |
| 根目录 `SUMMARY.md` | 保留原有中文导航与多级目录 |
| `gitbook/schemas/gitbook-docs.schema.yaml` | 从 GitBook 官方接口下载的 Schema 快照，用于离线验证站点配置 |

内容映射使用 `./`，Git Sync 直接读取根目录的 Markdown 和正文引用的附件。维护工具位于 `eb_tool/`，不列入 `SUMMARY.md`。

首次接入前可以选择空间的 `key`，接入后应保持 `effectiveblog` 不变。修改标题或目录时不要顺带改 key，否则 GitBook 会把它视为另一个空间。站点配置通过官方 Schema 验证不代表已经通过账户方案或云端导入验证。

# 旧工程清理

已删除下列旧版 GitBook 文件，原有文章目录和 `assets/` 保留：

| 路径 | 原用途 |
| --- | --- |
| `docs/` | 旧版生成并纳入版本管理的静态 HTML 站点 |
| `_book/` | 本机遗留的旧版构建产物 |
| 根目录 `node_modules/` | 旧版 GitBook 插件、主题及其依赖 |
| `book.json` | GitBook 3.2.3 的主题、插件和样式配置 |
| `auto_pull.sh` | 在旧服务器拉取代码并执行 `gitbook build` |

清理时未发现根目录 `build/` 或 `dist/`。`.gitignore` 与文档整理工具均排除这些目录及 `docs/`、`_book/`，防止产物再次入库或进入导航。各级 `node_modules/` 也已忽略。

工程不再执行 `gitbook install`、`gitbook build` 或 `gitbook serve`，也不再生成 `docs/` 静态站点。旧插件配置不会迁移到新版；主题和站点外观在 GitBook 内设置。今后的更新流程为：编辑 Markdown → 生成目录并检查 → 提交、推送 → Git Sync 同步 → GitBook 预览或发布。

已经纳入 Git 的旧文件可从清理前的提交历史中查阅；未纳入版本管理的 `_book/` 已作为生成产物删除。

# 运行检查

需要 Node.js 22 或以上版本。在仓库根目录执行：

```sh
npm --prefix eb_tool/gitbook ci --ignore-scripts
npm --prefix eb_tool/gitbook run check
```

首次安装依赖需要联网，安装完成后的检查可离线运行。检查器依赖安装在 `eb_tool/gitbook/node_modules/`，由该目录的 `package-lock.json` 锁定版本；根目录不再安装旧 GitBook 依赖。

完整结果写入 [check.json](gitbook/reports/check.json)，报告和检查依赖已加入 Git 忽略规则。退出码为 `0` 表示本地检查未发现错误；退出码为 `1` 表示存在缺失文件、无效配置等问题。待云端复核的 HTML 等内容单独列为提示，不等同于本地错误。

检查器针对当前仓库的单空间、根目录布局设计；未来若主动改变内容布局，需要同步调整检查器。它检查实际 Markdown 导航、已列入目录的文章以及其中的本地引用，不扫描整个硬盘，也不会访问外部链接。

重新生成目录仍使用：

```sh
python3 -B eb_tool/eb_tool.py --gen
```

目录生成器现在用尖括号包裹链接地址，使带空格的中文文件名符合 CommonMark。新增正文链接时也应使用这种形式：

```markdown
[文章](<../01 分类/01 文档.md>)
```

# 本次检查结果

本次已修正正文中 8 个能明确定位到现有文件的旧路径，并修正目录及正文链接中的裸空格。133 个目录条目全部可以被 CommonMark 解析，未发现目录指向的页面缺失或重复；站点配置通过官方 Schema 验证。

正文仍有 15 个历史引用错误，检查命令会如实返回失败：

| 类型 | 数量 | 说明 |
| --- | --- | --- |
| 缺失文档 | 5 | Java异常机制、KMP学习路径、OkHttp3、装饰模式、代理模式的旧链接 |
| 本机绝对图片路径 | 10 | 备份区 ClassLoader、热修复文章中的图片，当前仓库和原绝对路径均找不到原文件 |

实际可定位的附件有 124 个，另有 50 处 HTML 或内联样式需在云端核对。清理前已确认旧产物中没有上述 10 张缺失图片。没有删除缺失引用、编造替代图片或恢复 Git 历史中已删除的文章；这些问题的位置见生成的 JSON 报告。

计数为本次迁移时的结果，以重新运行检查后的报告为准。原生 GitBook 页面预览必须等后续导入内容后完成。

# 工具回归测试

```sh
npm --prefix eb_tool/gitbook test
python3 -B -m unittest discover -s eb_tool/tests -q
node --test eb_tool/tests/test_ui.js
```

Python HTTP 测试会监听本机临时端口。检查器测试使用临时目录，验证中文空格路径、无效目录链接、重复页面、缺失图片、代码示例排除及同步目录边界。

# 后续接入 GitBook

1. 在 GitBook 创建 Free 站点，打开 Git Sync，授权访问 `MEzzsy/EffectiveBlog`。
2. 将本地迁移修改提交并推送到要绑定的分支。当前开发分支为 `master`；首次同步方向选择 GitHub → GitBook。
3. Project directory 留空，使用仓库根目录，将内容空间映射到 `./`。
4. 核对 133 个页面的目录、图片、代码块和内部跳转，并处理本地报告中的遗留问题。
5. 在 GitBook 内配置主题，预览确认后再公开发布。

Git Sync 是双向的：GitBook 合并的更改也会写回绑定分支。后续首次接入可使用包含完整内容的测试分支。

# 官方资料

- [GitBook CLI](https://gitbook.com/docs/docs-as-code/gitbook-cli)
- [Git Sync 内容配置](https://gitbook.com/docs/docs-as-code/git-sync/content-configuration)
- [启用 GitHub Sync](https://gitbook.com/docs/docs-as-code/git-sync/enabling-github-sync)
- [站点配置 Schema](https://api.gitbook.com/gitbook-docs.yaml)，本地快照获取日期：2026-09-12
- [GitBook 开源渲染器](https://github.com/GitbookIO/gitbook)
- [Git Sync 故障排查与文件限制](https://gitbook.com/docs/docs-as-code/git-sync/troubleshooting)
