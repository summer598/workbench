# 工作台部署指南 · 云端上线 + PWA + 真实数据

> 目标：部署到云端，手机访问链接，添加到主屏幕当APP用，热点/新闻/行情接入真实数据

---

## 架构说明

```
手机浏览器/PWA
    ↓ 读取 /data/*.json
前端 index.html + manifest.json + sw.js（静态托管）
    ↑ 定时生成JSON
后端 api_server.py（Python定时抓取真实数据）
    ↓ 抓取
新浪财经(行情) + 东方财富(新闻) + 头条(热搜)
```

**数据源（全部免费公开接口，已验证可用）：**

| 数据 | 源 | 状态 |
|---|---|---|
| A股指数(上证/深成/创业板) | 新浪财经 hq.sinajs.cn | ✅ 真实 |
| 黄金价格(COMEX期货+中国黄金) | 新浪财经 | ✅ 真实 |
| 财经新闻(20条快讯) | 东方财富 newsapi.eastmoney.com | ✅ 真实 |
| 全网热搜TOP15 | 头条热榜 toutiao.com | ✅ 真实 |
| 服饰电商数据 | 公开信息整理 | ⚠️ 模板，可接飞瓜/蝉妈妈 |

---

## 方案A：Vercel部署（推荐·免费·最简单）

### 前置条件
- 注册 [Vercel](https://vercel.com) 账号（GitHub登录即可）
- 安装 Node.js

### 步骤

1. **安装 Vercel CLI**
```bash
npm i -g vercel
```

2. **进入工作台目录**
```bash
cd /workspace
```

3. **部署**
```bash
vercel --prod
```
按提示操作（首次需登录），部署完成后会给你一个 `https://xxx.vercel.app` 链接。

4. **手机访问**
- 手机浏览器打开链接
- iOS Safari → 分享 → 添加到主屏幕
- Android Chrome → 菜单 → 添加到主屏幕

5. **定时数据更新**

Vercel的Cron Function免费版每天最少1次调用。对于更频繁更新，有两种方案：

**方案A1（简单）**：用Vercel的 `/api/fetch` 接口返回实时数据，前端改为调用API
- 已在 `api/fetch.py` 实现
- 每2小时Vercel Cron触发（需Vercel Pro）
- 免费版：每天1次，可手动访问 `/api/fetch` 触发

**方案A2（推荐）**：前端直接调用 `/api/fetch` 获取实时数据
- 修改前端 `loadRealData()` 改为 fetch `/api/fetch`
- 每次打开APP自动获取最新数据
- 不依赖定时任务

### 方案A的局限
- Vercel Serverless无持久文件系统，不能写JSON文件
- 需要前端改为直接调API（而非读静态JSON）
- 定时任务免费版受限

---

## 方案B：自有服务器/VPS部署（最灵活·推荐给需要定时更新的用户）

### 前置条件
- 一台云服务器（阿里云/腾讯云轻量服务器，月费几十元）
- Python 3.10+
- 域名（可选，用IP也行）

### 步骤

1. **上传文件到服务器**
```bash
# 将 /workspace 整个目录上传到服务器，例如 /opt/workbench
scp -r /workspace/* user@your-server:/opt/workbench/
```

2. **安装依赖**
```bash
cd /opt/workbench
pip3 install -r requirements.txt
```

3. **启动API Server（含定时抓取）**
```bash
# 前台测试
python3.11 data-server/api_server.py

# 后台常驻（用nohup）
nohup python3.11 data-server/api_server.py > server.log 2>&1 &

# 或用screen/tmux
screen -S workbench
python3.11 data-server/api_server.py
# Ctrl+A D 退出screen
```

4. **用Nginx反向代理（推荐，支持HTTPS）**
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 或IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. **配置HTTPS（手机PWA必须HTTPS）**
```bash
# 用certbot免费证书
sudo certbot --nginx -d your-domain.com
```

6. **设置开机自启（systemd）**
```bash
# /etc/systemd/system/workbench.service
[Unit]
Description=WorkBuddy Workbench API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/workbench
ExecStart=/usr/bin/python3 /opt/workbench/data-server/api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable workbench
sudo systemctl start workbench
```

7. **手机访问**
- `https://your-domain.com` 打开
- 添加到主屏幕 → 独立APP

### 方案B优势
- 定时抓取每2小时自动运行
- 数据持久化到JSON文件
- 可自定义抓取频率
- 支持HTTPS（PWA必须）

---

## 方案C：GitHub Pages部署（纯静态·无后端）

### 适用场景
- 不需要后端定时抓取
- 手动更新数据（本地跑fetch_data.py后上传JSON）

### 步骤

1. **创建GitHub仓库**
```bash
cd /workspace
git init
git add .
git commit -m "工作台部署"
git remote add origin https://github.com/你的用户名/workbench.git
git push -u origin main
```

2. **开启GitHub Pages**
- 仓库 Settings → Pages → Source: main branch
- 等待几分钟后得到 `https://你的用户名.github.io/workbench/`

3. **更新数据**
```bash
# 本地跑抓取脚本
cd /workspace/data-server
python3.11 fetch_data.py --once
# 把生成的JSON复制到data目录
cp public/data/*.json ../data/
# 提交推送
cd /workspace
git add data/
git commit -m "更新数据"
git push
```

4. **自动化更新（GitHub Actions）**
在 `.github/workflows/update-data.yml` 配置定时任务，详见下方。

### GitHub Actions 自动更新数据

创建 `.github/workflows/update-data.yml`：
```yaml
name: Update Data
on:
  schedule:
    - cron: "0 */6 * * *"  # 每6小时
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install requests
      - run: python data-server/fetch_data.py --once
      - run: |
          cp data-server/public/data/*.json data/
          git config user.name "GitHub Action"
          git config user.email "action@github.com"
          git add data/
          git diff --staged --quiet || git commit -m "auto: update data"
          git push
```

---

## 方案对比

| 维度 | Vercel | 自有服务器 | GitHub Pages |
|---|---|---|---|
| **费用** | 免费 | 服务器月费 | 免费 |
| **HTTPS** | 自动 | 需配置 | 自动 |
| **定时更新** | 受限(免费版) | 完全自由 | Actions(有限) |
| **部署难度** | ⭐ 最简单 | ⭐⭐⭐ 中等 | ⭐⭐ 简单 |
| **数据实时性** | 高(API直调) | 高(定时抓取) | 低(手动/Actions) |
| **适合场景** | 快速上线 | 长期稳定使用 | 纯展示 |

**我的建议：**
- **想最快上线** → 方案A（Vercel），5分钟搞定
- **长期认真用** → 方案B（自有服务器），数据定时自动更新
- **不想花钱** → 方案C（GitHub Pages）+ Actions，每6小时更新

---

## PWA安装说明（部署后操作）

### iPhone (Safari)
1. Safari打开部署链接
2. 底部「分享」→「添加到主屏幕」
3. 命名「我的工作台」→ 完成
4. 桌面图标点开全屏运行

### Android (Chrome)
1. Chrome打开链接
2. 菜单「⋮」→「添加到主屏幕」或「安装应用」
3. 桌面生成独立APP

### 注意事项
- **PWA必须HTTPS**（Vercel/GitHub Pages自动HTTPS，自有服务器需配置）
- 首次打开后Service Worker会缓存，之后离线也可打开
- 数据更新频率取决于后端定时任务设置

---

## 文件清单

```
/workspace/
├── index.html              # 前端主程序（PWA）
├── manifest.json           # PWA安装配置
├── sw.js                   # Service Worker离线缓存
├── data/                   # 前端读取的JSON数据
│   ├── stock.json          # A股行情
│   ├── gold.json           # 黄金行情
│   ├── news.json           # 财经新闻
│   ├── hot.json            # 热搜
│   └── ecom.json           # 电商数据
├── data-server/            # 后端
│   ├── api_server.py       # Flask API+定时抓取（方案B用）
│   ├── fetch_data.py       # 独立抓取脚本（cron用）
│   └── public/data/        # 抓取生成的JSON
├── api/
│   └── fetch.py            # Vercel Serverless Function（方案A用）
├── vercel.json             # Vercel部署配置
├── requirements.txt        # Python依赖
└── 部署指南_云端PWA版.md    # 本文档
```

---

## 后续优化

1. **数据源增强**：接入Tushare（A股详细数据）、付费黄金API
2. **电商真实数据**：接入飞瓜/蝉妈妈付费API
3. **推送通知**：PWA Push API，定时任务完成后推送
4. **数据图表**：接入ECharts画K线/资金流向图
5. **多设备同步**：API Server增加数据存储端点
