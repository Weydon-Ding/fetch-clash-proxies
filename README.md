# fetch clash proxies

从 [socks5-proxy.github.io](https://socks5-proxy.github.io/) 抓取免费代理，并生成 Clash/mihomo 可用的配置文件。

生成的订阅文件不会提交到 `main` 分支；GitHub Actions 会把最新版发布为固定 `latest` GitHub Release 的资产文件。

## 快速使用

直接运行：

```bash
python fetch_clash_proxies.py
```

指定输出文件：

```bash
python fetch_clash_proxies.py -o clash.yaml
```

指定代理列表来源：

```bash
python fetch_clash_proxies.py --url https://socks5-proxy.github.io/ -o clash.yaml
```

运行成功后，会在指定路径生成 Clash/mihomo 配置文件。

## Clash 订阅地址

如果仓库是公开仓库，推荐订阅 GitHub Release asset：

- 宽松版：[`clash-free-proxies.yaml`](https://github.com/Weydon-Ding/fetch-clash-proxies/releases/download/latest/clash-free-proxies.yaml)
- 严格规则版：[`clash-free-proxies-strict.yaml`](https://github.com/Weydon-Ding/fetch-clash-proxies/releases/download/latest/clash-free-proxies-strict.yaml)

## 规则策略

生成的 YAML 使用 `rule-providers` 引用 `Loyalsoldier/clash-rules` 的远程规则：

```text
https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/<规则文件>.txt
```

默认生成两个配置文件：

- `clash-free-proxies.yaml`：宽松版，未命中的未知流量默认走 `PROXY`，可用性更好；
- `clash-free-proxies-strict.yaml`：严格规则版，未命中的未知流量默认走 `DIRECT`，隐私暴露范围更小，但部分站点可能需要补充规则。

两种配置都会采用以下规则：

- 内网、局域网和中国大陆流量直连；
- 广告和追踪域名拒绝；
- Google、常见代理域名、Telegram 走 `PROXY`。

## 自动更新

项目包含 GitHub Actions workflow：

```text
.github/workflows/update-proxies.yml
```

它会：

- 每天北京时间约 04:00 自动运行一次；
- 也可以在 GitHub Actions 页面手动触发；
- 生成 `publish/clash-free-proxies.yaml` 和 `publish/clash-free-proxies-strict.yaml`；
- 上传并覆盖固定 tag `latest` 的 GitHub Release assets。

如果 Release 发布失败，请检查仓库设置：

```text
Settings → Actions → General → Workflow permissions → Read and write permissions
```

## 注意事项

- 免费代理的稳定性和可用性无法保证。
- 源站页面结构变化时，脚本可能解析失败。
- 如果仓库是私有仓库，Clash/mihomo 客户端通常不能直接读取 GitHub Release asset。
- 如果本次自动生成或发布失败，GitHub Release 中已有的上一版订阅文件会继续保留。
- 如果客户端无法访问 `raw.githubusercontent.com`，远程规则更新可能失败。
