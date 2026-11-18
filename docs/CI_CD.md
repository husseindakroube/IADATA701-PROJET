# CI/CD — TGVision

## 自动执行的流程

工作流：`.github/workflows/ci.yml`。

1. 所有分支 push、面向 main 的 pull request、手动运行都会启动 CI。
2. 使用 `.python-version` 和 `uv.lock` 安装环境，uv 固定为 0.12.13。
3. Ruff 检查关键代码错误，检查 Python 语法，运行完整 pytest（含六页 Streamlit
   AppTest），测量 `app/` 和 `src/projet_kit_data/` 的行覆盖率，要求至少 **90.1%**。
   不通过缩小统计范围来满足门槛。当前检查并非完整格式/风格检查。
4. 无论测试成功或失败，都上传已有 JUnit、XML、HTML 覆盖率报告，保留 14 天。
5. CI 成功后构建 `linux/amd64` Docker 镜像，并真正启动容器检查健康状态。
6. 只有 main 的 push 或 main 的手动运行才发布到 GHCR；PR 不登录、不发布、不部署。
7. 配置部署开关后，将刚测试并发布的同一镜像按不可变 SHA-256 摘要部署到服务器。
   不使用 latest 作为生产部署依据。

## 首次配置 GitHub

在仓库 Settings → Environments 创建 **production**。

在 production 的 Secrets 中配置：

| Secret | 内容 |
|---|---|
| `DEPLOY_HOST` | Linux 服务器域名或 IPv4，不带协议 |
| `DEPLOY_USER` | 有 Docker 权限的专用 SSH 用户 |
| `DEPLOY_PORT` | SSH 端口；可不填，默认 22 |
| `DEPLOY_SSH_KEY` | SSH 私钥完整内容，对应公钥需预先放到服务器 |
| `DEPLOY_KNOWN_HOSTS` | 通过可信渠道核实的服务器 SSH 公钥记录；非 22 端口用 `[host]:port` 格式 |

在**仓库级** Settings → Secrets and variables → Actions → Variables 设置
`DEPLOY_ENABLED=true` 才会启用服务器部署。未设置时 CI 和 main 镜像发布照常运行，
服务器部署显示 skipped。不要把私钥发进聊天或提交进仓库。

GHCR 使用 GitHub 自动提供的 `GITHUB_TOKEN`，无需额外 registry 密钥。
若复用已有 GHCR package，应在 package 设置中允许本仓库 Actions 读写。
组织如禁止 Packages 写入，需要管理员调整权限。

可按团队需要给 production 设置审批规则，并在 main 的分支保护中要求
`Code, tests and coverage` 与 `Build and verify Docker image` 通过后才允许合并。

## 服务器准备

- Linux **x86-64/amd64**，Python 3，Docker Engine 和系统安装的 Compose v2
  （支持 `up --wait --wait-timeout`）。ARM 服务器需要先调整镜像架构配置。
- SSH 用户可以不经交互式 sudo 运行 Docker；Docker 权限等同高权限，应使用专用账户。
- GitHub 托管 runner 能通过 SSH 访问服务器，服务器可以拉取 GHCR 镜像。
- 部署文件位于 `~/.local/share/tgvision/`，使用文件锁防止同时更改。
- 应用仅绑定服务器 `127.0.0.1:8501`。已有 Nginx/Caddy 等反向代理应转发到此地址，
  配置域名、TLS 和 WebSocket。未配置代理前，不会自动产生公网网站。

Compose 中的容器以非 root 用户启动；不运行 Notebook、不训练模型。
镜像包含网站所需的代码、数据、报告、静态资源和可下载的 notebooks。
模型文件、开发虚拟环境、测试输出、旧首页 GIF 不进入镜像。

## 更新与失败恢复

`deploy.py` 校验输入、使用严格 SSH 主机验证，通过标准输入传输部署载荷。
远端拉取镜像后才替换服务。GHCR 登录信息保存在临时目录，结束时清除。
Compose 等待健康检查通过后才报告成功。

如果更新失败，输出容器日志并恢复原来的 compose 和镜像配置，再等待旧版健康。
即使回退成功，本次工作流仍显示失败。首次部署失败则停止并移除本次服务配置。
成功后保存 `compose.previous.yaml` 和 `.env.previous` 供人工回退：

```bash
cd ~/.local/share/tgvision
docker compose --project-directory "$PWD" --env-file .env.previous \
  -f compose.previous.yaml up -d --wait --wait-timeout 120
```

旧镜像仍在服务器本地时无需再次登录。若已被手动清理，则需要拥有该 package
读取权限的 GHCR 凭据。此方案为单实例更新，可能有短暂停机，不是零停机发布。

## 本地复现

```bash
uv sync --locked --dev
uv run --locked pytest -q --cov=src/projet_kit_data --cov=app --cov-fail-under=90.1
docker build -t tgvision:local .
TGVISION_IMAGE=tgvision:local docker compose up -d --wait
```

PowerShell 的最后一步改为：

```powershell
$env:TGVISION_IMAGE = 'tgvision:local'
docker compose up -d --wait
```

## 当前验证范围

重写时原有 147 项测试通过，`app/` 与 `src/projet_kit_data/` 行覆盖率 90.19%。
另外添加部署输入校验及回退逻辑的离线测试。Compose 配置可解析。
本机 Docker 引擎未启动，尚未完成真实镜像构建；GitHub Actions 尚未远端运行；
未提供服务器 Secrets，所以没有实际部署或确认公网访问。CI 会在首次运行时验证 Linux
镜像和健康检查，若 Linux 覆盖率低于门槛，也会如实失败。

参考：[Docker Actions](https://docs.docker.com/build/ci/github-actions/)、
[checkout](https://github.com/actions/checkout)、
[upload-artifact](https://github.com/actions/upload-artifact)。
