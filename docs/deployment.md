# 部署说明

更新时间：2026-10-10（北京时间；初版 2026-10-09）。
适用范围：本公开归档副本（GitHub：`xu2005/economic-crisis`，整理提交 `0c42d01`「Prepare public project archive」）。

## 1. 副本定位

本仓库是网站源码的**公开剥离版**，与线上站点是两套不同的数据边界：

| 项目 | 线上站点 | 本公开副本 |
|---|---|---|
| 位置 | https://economic-crisis.xuhengyi.chatgpt.site （Sites 项目，当前版本 17 = V16.1） | 本仓库 `main` 分支 |
| 页面与交互代码 | V16.1 部署版（含 `#/studies/v161` 专题等新页面） | V16 公开剥离版；**尚未纳入 V16.1 新增页面**（`StudyPages`、`V161Evidence` 等） |
| 沪深300 15 年历史行情 | 随站点一起打包 | **已剥离**：`src/data/hs300-history.public-placeholder.json` 为空结构占位（`asset`/`sse` 为空数组） |
| 回测页表现 | 完整回测（图表、成交记录、下载） | 显示"原始行情序列未纳入公开仓库"的替代提示 |
| `public/backtest/` 下载文件 | 有 | 无 |
| `public/crisis-v32-cny/` 数据 | 有 | 有，且与线上**逐字节一致**（results.json sha256 `5250B3EF…`、product-disclosed-periods.csv sha256 `5323875F…`） |
| `favicon.svg` | 有 | 无（未随公开副本提供） |

依据：`UPLOAD_MANIFEST.md` 与 `docs/releases/V16_发布与线上验收记录.json`（`raw_series_public=false`）。

边界说明：同步核验为抽查性质（页面标记、CSS 规则、上述两个数据文件哈希）；**未**对托管档案做全量逐字节比对，因此不宣称本副本与线上完全等同，也不宣称可直接替换线上部署。2026-10-10 线上已发布 V16.1（平台版本 17），本副本源码仍停在 V16 公开剥离版，两者差异见上表。

## 2. 环境要求

- Node.js 18+（建议 20/22）与 npm；技术栈为 Vite 6 + TypeScript 5.8 + React 19，依赖已由 `package-lock.json` 锁定。
- 仅构建静态站点时不需要数据库：`server/`、`db/`、`drizzle/` 及 `scripts/*.py`（人民币研究管线）不参与前端构建。

## 3. 构建

```bash
npm ci
npx tsc -b
npx vite build
```

产物输出到 `dist/client/`。

注意：`package.json` 中的 `npm run build` 串联了 `scripts/clean-build.mjs` 与 `scripts/build_runtime.mjs`，这两个脚本以及 `tests/` 目录**未包含在本公开副本中**，因此 `npm run build`、`npm test` 无法直接运行；上面三条命令是等效的前端构建路径（跳过清理与 runtime 打包步骤）。

## 4. 部署方式

- 将 `dist/client/` 目录整体作为静态站点根目录托管即可。
- 站点使用 hash 路由（`#/models/...`），不需要服务端 history 回退配置。
- `vite.config.ts` 使用 `base: './'`，可部署在任意子路径下。
- 本地预览：`npx vite preview`，或用任意静态服务器指向 `dist/client/`。

## 5. 部署前检查清单

- HS300 回测页（`#/models/hs300/backtest`）将显示"原始行情序列未纳入公开仓库"提示，而非完整回测——这是公开副本的既定行为，不是故障。
- `/backtest/*`（csv/json）下载不存在。
- 页签图标 `favicon.svg` 缺失；如需可从线上取回或自行补充到 `public/`。
- 如需完整回测，须在本地自行准备经授权的行情数据并重建；本仓库不提供原始序列。

## 6. 发布记录索引

- `docs/releases/V15_发布与线上验收记录.json`：站点版本 15（提交 `7ca8d21`）
- `docs/releases/V16_发布与线上验收记录.json`：站点版本 16（提交 `e76ea39`）
- `docs/releases/V16.1_发布与线上验收记录.json`：站点版本 17（V16.1，提交 `105d126d`），当前线上
- `docs/research/V16.1正式研究与证据审计报告.md`、`docs/history/V16.1交接记录.md`：V16.1 研究与交接记录
- `docs/verification/v16.1/`：V16.1 发布期验收与校验记录（浏览器验收、构建验证、线上下载哈希、源码清单等，含 `acceptance/` 截图）；其中移动端自动验收未闭环、下载按钮事件未确认，按原始记录保留，未标记为通过
- 本副本的整理范围与排除清单见 `UPLOAD_MANIFEST.md`；阶段状态见 `docs/project-status.md`

## 7. 边界声明

本副本为研究资料归档，不构成投资建议。原始行情序列、内部交接文件与部署绑定配置未随仓库分发。测试与验收数字来自历史记录；本次归档与说明整理未重新运行构建、测试或站点部署。