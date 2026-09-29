# TGSOU 部署方案 — Cloudflare Pages

> 目标：把本地 tgsou 站点发布到 Cloudflare Pages，绑定 tgsou.net，每次 `git push` 自动重建搜索索引并上线。
> 当前规模核对：1710 个文件 / 51MB / 单文件最大 ~350KB —— 全部在 Cloudflare Pages 免费额度内（20000 文件、25MB/文件、流量不限）。

---

## 架构总览

```
GitHub 仓库 (tgsou/tgsou.github.io)
   │  git push
   ▼
Cloudflare Pages 构建机
   │  构建命令: python3 build-search-index.py   ← 重建搜索索引
   │  输出目录: /（仓库根，纯静态）
   ▼
Cloudflare 全球 CDN  ←── tgsou.net（CNAME 接入）
   │                        tgsou.pages.dev（默认域名）
   ▼
访客（零服务器、零运维、流量不限量）
```

**构建时自动做的事**：`build-search-index.py` 重新扫描 `detail/` 生成 `search/search-index.json` 与分块——收录变更后无需手动重建索引。

---

## 第一步：推送到 GitHub

本地仓库当前 remote 还指向原站（tgnav/tgnav.github.io），需要换成你自己的新仓库。

1. 在 GitHub 新建仓库（建议名 `tgsou`，**Private 也可以**，Pages 构建在 Cloudflare 侧进行）
2. 执行（在 `tgnav/` 目录下）：

```bash
git remote remove origin
git remote add origin https://github.com/<你的用户名>/tgsou.git
git add -A
git commit -m "TGSOU: rebrand, local search, local avatars, stats removed"
git branch -M main
git push -u origin main
```

> 提交前注意：901 个文件有改动（品牌替换/搜索/头像/清理的全部成果）。`avatars/`（19MB）一并入库——部署后由 CDN 分发。

---

## 第二步：接入 Cloudflare Pages

1. 登录 [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
2. 授权 GitHub 并选择 `tgsou` 仓库
3. 构建配置（**关键三行**）：

| 配置项 | 值 |
|---|---|
| Project name | `tgsou`（决定默认域名 tgsou.pages.dev） |
| Production branch | `main` |
| Build command | `python3 build-search-index.py` |
| Build output directory | `/` |
| Root directory | （留空） |

4. **环境变量**（可选但推荐）：无强制需求；如需钉住 Python 版本可加 `PYTHON_VERSION=3.11`
5. 点 **Save and Deploy**，约 2-3 分钟后上线：`https://tgsou.pages.dev`

> Pages 构建机自带 Python3，`build-search-index.py` 只用标准库，无需依赖安装步骤。

---

## 第三步：绑定 tgsou.net

### 3a. 域名托管到 Cloudflare（推荐）

1. Cloudflare 控制台 → **Add a domain** → 输入 `tgsou.net` → 选 Free 计划
2. Cloudflare 给出两个 NS 服务器地址（如 `xxx.ns.cloudflare.com`）
3. 去域名注册商（你在哪买的就在哪）→ 修改 **Nameservers** 为 Cloudflare 的两个 NS
4. 等待生效（几分钟到几小时）

### 3b. Pages 绑定自定义域名

1. Pages 项目 → **Custom domains** → **Set up a custom domain**
2. 输入 `tgsou.net` → Continue
3. 按提示添加记录（域名已在 Cloudflare 时基本自动完成）：

| 类型 | 名称 | 目标 |
|---|---|---|
| CNAME | `www` | `tgsou.pages.dev` |
| CNAME（或 Redirect） | `@`（根域） | `tgsou.pages.dev` |

> 根域 CNAME：Cloudflare 支持 CNAME flattening，根域可直接 CNAME；若注册商不支持，用 A 记录或让 Cloudflare 做 301 跳转到 www。
4. 勾选两个域名（apex + www），SSL/TLS 模式用默认 **Full** —— 证书自动签发，几分钟生效
5. 验证：`https://tgsou.net` 与 `https://www.tgsou.net` 均返回站点

### 3c. 上线前一致性检查

站点内所有 URL 已在品牌改造时统一为 tgsou.net（og:url、canonical、sitemap），域名生效即自洽，无需再改代码。

---

## 第四步：日常更新流程

### 收录新频道/群组/机器人

```bash
# 1. 生成新详情页（手动复制模板或未来的 add-channel.py）
# 2. 在对应分类页/首页加入口链接
# 3. 重建索引（本地预览验证）
python3 build-search-index.py

# 4. 抓取新条目头像（清单自动跳过已有）
python3 fetch-avatars.py --method scrape

# 5. 提交推送 → Cloudflare 自动重建索引并发布
git add -A && git commit -m "收录: @username（分类）" && git push
```

### 修改任意页面

直接改 HTML → `git push` → 自动上线。构建命令每次都会重跑索引生成（幂等，无副作用）。

---

## 备选：GitHub Actions 构建（可选增强）

若想把"索引构建"从 Pages 构建机挪到 GitHub Actions（构建日志更清晰、可做校验），在仓库加：

```yaml
# .github/workflows/deploy.yml
name: Build & Deploy
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python3 build-search-index.py
      - uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy . --project-name=tgsou
```

需要在 GitHub 仓库 Settings → Secrets 添加 `CLOUDFLARE_API_TOKEN`（Cloudflare 面板创建，权限：Cloudflare Pages Edit）和 `CLOUDFLARE_ACCOUNT_ID`。

**建议**：起步阶段直接用「Pages Git 集成」（第二步）就够了，Actions 方案等需要多环境预览时再上。

---

## Cloudflare Pages 限额核对（当前 51MB / 1710 文件）

| 限额 | 值 | 当前用量 | 状态 |
|---|---|---|---|
| 单项目文件数 | 20,000 | 1,710 | 8% ✅ |
| 单文件大小 | 25 MB | ≤350KB | ✅ |
| 带宽 | 不限量 | — | ✅ |
| 构建/月 | 500 次 | 按需 | ✅ |
| 收录容量预估 | — | ~2.5 万条时到 2 万文件，届时拆分头像到 R2/子域 | 远期 |

---

## 常见问题

**Q: 国内访问慢/被墙？**
Cloudflare 免费版走海外节点，国内直连可用但速度一般（TGNAV 原站同样情况）。不影响可用性；备案域名可后续换国内方案。

**Q: avatars 目录以后越来越大怎么办？**
超过几万张后把 `avatars/` 迁到 Cloudflare R2（免费 10GB），改 `migrate-avatars.py` 里的前缀为 R2 公开域名即可，页面代码零改动。

**Q: 搜索索引会构建失败吗？**
`build-search-index.py` 只依赖标准库且幂等；万一失败，Pages 会保留上一次成功部署，线上不受影响。

**Q: 如何回滚？**
Pages 项目 → Deployments → 选历史版本 → **Rollback to this deployment**，秒级回滚。
