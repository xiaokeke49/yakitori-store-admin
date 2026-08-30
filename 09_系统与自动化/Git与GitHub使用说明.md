# Git 与 GitHub 使用说明

## 0. 本项目使用什么

本项目使用 **Git + GitHub CLI（`gh`）** 管理 GitHub，不需要安装 GitHub Desktop。

| 工具 | 用途 | 当前情况 |
|---|---|---|
| Git | 在本机记录修改、提交、拉取和上传 | 本机已使用 |
| GitHub CLI（`gh`） | 登录 GitHub、管理仓库和 Pull Request | 本机已安装 |
| GitHub Desktop | 图形界面工具 | 本项目不需要安装 |

## GitHub CLI 登录

### 检查当前登录状态

```bash
gh auth status
```

当前电脑已登录 GitHub 账号 `xiaokeke49`，Git 操作使用 HTTPS。账号凭据由 macOS 钥匙串保存，不要把 Token 写进项目文件。

### 首次登录或重新登录

```bash
gh auth login --web --clipboard
```

按终端提示操作：

1. 选择 `GitHub.com`。
2. Git 协议选择 `HTTPS`。
3. 浏览器打开 GitHub 登录页面。
4. 粘贴一次性验证码并授权 GitHub CLI。
5. 回到终端，再执行 `gh auth status` 确认登录成功。

如需退出当前账号：

```bash
gh auth logout
```

## 你的 GitHub 仓库

| 用途 | 地址 |
|---|---|
| 浏览器查看仓库 | [xiaokeke49/yakitori-store-admin](https://github.com/xiaokeke49/yakitori-store-admin) |
| 克隆/下载地址 | `https://github.com/xiaokeke49/yakitori-store-admin.git` |

### 用 `gh` 下载这个仓库

```bash
gh repo clone xiaokeke49/yakitori-store-admin
cd yakitori-store-admin
```

如果项目已经在电脑里，不需要重新克隆。进入现有项目目录后用 `git status` 检查即可。

## 每次的操作流程

```text
git pull → 修改文件 → git status/diff → git add → git commit → git push
```

> 注意：`git commit` 只是保存到本机；完成 `git push` 后才算上传到 GitHub。

## 1. Git 和 GitHub 是什么

| 名称 | 用途 |
|---|---|
| Git | 在本机记录文件的每次修改 |
| GitHub | 把 Git 仓库放到网上，用于备份和协作 |
| Commit | 一次带说明的版本保存 |
| Push | 把本地提交上传到 GitHub |
| Pull | 把 GitHub 的新版本拉到本地 |

## 2. 第一次配置 Git

```bash
git config --global user.name "你的名字"
git config --global user.email "你的GitHub邮箱"
```

检查配置：

```bash
git config --global --list
```

## 3. 把现有文件夹放进 Git

进入项目文件夹：

```bash
cd "你的项目路径"
```

初始化 Git：

```bash
git init
```

先创建 `.gitignore`，至少排除：

```gitignore
.env
.DS_Store
.venv/
__pycache__/
*.pyc
```

检查文件：

```bash
git status
```

精确添加要保存的文件：

```bash
git add -- "README.md"
git add -- "其他文件或文件夹"
```

创建第一次提交：

```bash
git commit -m "Initial commit"
```

## 4. 把本地 Git 连接到自己的 GitHub

### 在 GitHub 新建仓库

1. 登录 GitHub。
2. 点击 `New repository`。
3. 填写仓库名称。
4. 有店铺资料时建议选择 `Private`。
5. 本地已有 README 时，GitHub 页面不要再创建 README。
6. 创建仓库并复制 HTTPS 地址。

### 连接远程仓库

将下面的地址换成你自己的仓库：

```bash
git remote add origin https://github.com/用户名/仓库名.git
git remote -v
git branch -M main
git push -u origin main
```

如果提示没有登录，执行 `gh auth login --web --clipboard`，按浏览器提示授权。

### 更换已有的 GitHub 仓库地址

```bash
git remote -v
git remote set-url origin https://github.com/用户名/新仓库名.git
git remote -v
```

## 5. 以后每次的固定流程

### 第1步：开始工作前拉取更新

```bash
git status --short
git pull --ff-only
```

如果 `git status` 显示已有未提交修改，先不要 pull，先处理现有修改。

### 第2步：正常修改文件

编辑、新增或删除文件。

### 第3步：检查改动

```bash
git status --short
git diff
```

### 第4步：只添加本次要提交的文件

```bash
git add -- "文件1"
git add -- "文件2"
```

不要在没有检查时盲目使用 `git add .`。

### 第5步：确认将要提交的内容

```bash
git diff --cached
```

### 第6步：提交

```bash
git commit -m "说清这次改了什么"
```

例如：

```bash
git commit -m "Update store information"
git commit -m "Add employee template"
git commit -m "Fix menu prices"
```

### 第7步：上传到 GitHub

```bash
git push
```

### 一行记住日常流程

```text
pull → 修改 → status/diff → add → diff --cached → commit → push
```

## 6. 多人协作时使用分支

新建分支：

```bash
git switch -c update-store-info
```

完成后提交并上传：

```bash
git add -- "需要提交的文件"
git commit -m "Update store information"
git push -u origin update-store-info
```

然后到 GitHub 创建 Pull Request，检查完内容再合并到 `main`。

## 7. 在新电脑下载自己的仓库

```bash
git clone https://github.com/用户名/仓库名.git
cd 仓库名
```

以后每次进入该文件夹，执行日常流程即可。

## 8. 常用命令

| 命令 | 用途 |
|---|---|
| `git status --short` | 查看哪些文件变了 |
| `git diff` | 查看未暂存的修改 |
| `git diff --cached` | 查看准备提交的内容 |
| `git log --oneline -10` | 查看最近10次提交 |
| `git remote -v` | 查看连接的 GitHub 仓库 |
| `git branch --show-current` | 查看当前分支 |
| `gh auth status` | 检查 GitHub CLI 登录状态 |
| `gh repo view --web` | 在浏览器打开当前 GitHub 仓库 |
| `gh pr create` | 为当前分支创建 Pull Request |

## 9. 撤销操作

取消某个文件的暂存，但保留文件内容：

```bash
git restore --staged -- "文件路径"
```

撤销一次已经共享的提交：

```bash
git revert <提交ID>
```

不清楚后果时不要使用：

```text
git reset --hard
git push --force
```

## 10. 不能提交到 GitHub 的内容

- `.env`、AK/SK、Token、账号密码。
- 员工身份证、银行卡、薪资和合同。
- 顾客电话、微信和会员信息。
- 财务明细和银行对账资料。
- 未获授权的人物照片或录像。
- 大型图片、视频、安装包和缓存；这些更适合放 OSS。

## 11. 最简单的记忆方式

第一次：

```text
init → 设置 .gitignore → add → commit → 连接 GitHub → push
```

以后每次：

```text
pull → 修改 → 检查 → add → commit → push
```
