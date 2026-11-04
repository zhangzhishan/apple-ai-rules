# Apple AI Rules

供 **ShellCrash / Mihomo 与 Loon 共用**的 Apple Intelligence、Siri、Relay 域名规则集。

## 订阅地址

```text
https://raw.githubusercontent.com/zhangzhishan/apple-ai-rules/master/Apple-AI.list
```

仓库只维护 **一份** `Apple-AI.list`，两种客户端订阅同一个地址。规则文件不包含策略名、节点、账号、密码、订阅凭据或家庭网络地址。

## Loon 和 Mihomo 的规则相同吗？

**本仓库相同，可以直接共用。** 当前仅使用双方支持的 `DOMAIN,域名` 与 `DOMAIN-SUFFIX,域名` 基础语法。`DOMAIN` 是精确匹配；`DOMAIN-SUFFIX` 同时匹配域名自身及其子域名。

但这不代表任意 Loon / Clash / Mihomo 文件都能互换：Mihomo 的完整 YAML、`payload:` 包装、`.mrs` 二进制规则，以及客户端特有逻辑、脚本、重写、插件格式不应混用。这里故意采用无策略、无包装的纯文本规则集。[1][2]

## ShellCrash / Mihomo

参考 [`examples/mihomo-snippet.yaml`](examples/mihomo-snippet.yaml)。配置要点：

```yaml
rule-providers:
  apple-ai:
    type: http
    behavior: classical
    format: text
    url: https://raw.githubusercontent.com/zhangzhishan/apple-ai-rules/master/Apple-AI.list
    path: ./ruleset/apple-ai.list
    interval: 86400
    proxy: Apple Intelligence US

rules:
  - RULE-SET,apple-ai,Apple Intelligence US
  # 下面保留其他已有规则
```

- `Apple Intelligence US` 是示例策略组名；必须在配置里实际存在，并选用合适地区的节点。改用其他组名时，同步修改上面两处组名。
- `behavior: classical` 与 `format: text` 必须匹配本仓库的文件格式。[1]
- `interval` 是更新间隔，单位为秒；示例每天检查。`proxy` 指定规则文件下载使用的代理，与 `RULE-SET` 指定的业务分流策略是两件事。[1]
- `RULE-SET,apple-ai,...` 必须排在宽泛的 Apple / iCloud 直连规则及相关 Apple 规则集前面，避免先被直连命中。
- 将内容合并到现有唯一的顶层 `rule-providers:` / `rules:` 中，**不要简单追加重复顶层键，也不要用片段覆盖整个配置**。
- ShellCrash 应使用持久化覆写／受支持的最终配置钩子，不要修改下载生成的配置或 `ruleset/` 缓存。不同 ShellCrash 版本的合并方式不同，不能保证把整段复制进一个覆写文件就会自动正确合并。
- 部署前用当前核心校验最终配置；部署后核对 provider、规则顺序、策略组选择和实际连接匹配。**创建此仓库不等于已修改或接入任何路由器。**

## Loon

在 Loon 的规则订阅／远程规则中添加上面的 **同一条 Raw URL**，并在客户端给它选择合适的美国节点或策略组。无需转换 `.list`，无需在文件每行末尾补策略。[2]

**注意优先级：** Loon 官方手册说明，本地规则的优先级高于订阅规则；因此若已有本地 `DOMAIN-SUFFIX,apple.com,DIRECT`、`DOMAIN-SUFFIX,icloud.com,DIRECT` 等冲突规则，仅把本订阅移到远程规则列表顶部并不能覆盖它们。应先检查并有意识地处理冲突本地规则；不要不加区分地删除全部 Apple 直连规则。[3]

Loon 和 Mihomo 的策略组配置是各自独立的。在路由器上存在一个同名组，不代表 Loon 中也自动存在。

## 规则范围与局限

- 初始内容严格对应用户指定的 18 条域名规则，保持原拼写与精确／后缀匹配类型；不自动扩展为全部 `apple.com`、`icloud.com`、`cloudflare.com`。
- **这是用户指定的路由清单，不是 Apple 官方完整端点清单。** 部分域名还可能服务于其他 Apple 功能；本仓库不逐项声称其专属用途或持续可用性。
- 规则匹配成功只说明选择了某条路由；不证明出口 IP 的真实地理位置、TLS／应用可用性，也不能保证获得 Apple Intelligence 或 Siri AI 资格。
- 机型、系统版本、账号地区、所在地区、语言和服务端开放范围仍可能影响可用性。手机的蜂窝、IPv6、其他 VPN、按设备旁路也可能不经过同一核心。
- 本规则不需要 HTTPS 解密、根证书、脚本或 URL 重写。

## 维护与验证

直接编辑 `Apple-AI.list`，不要维护两份容易漂移的客户端副本。纯文本注释使用单独的 `#` 行；第一条规则不能粘在注释末尾。

```sh
python3 -m unittest discover -s tests -v
```

测试校验用户指定的基线条目、语法、匹配边界、唯一性、无策略字段和文档订阅地址一致性。GitHub Actions 使用固定提交版本的 GitHub 官方 actions，最小只读权限，不安装第三方 Python 依赖。

这些是仓库内容与格式测试，**不是声称已在真实 Loon 或 Mihomo 客户端加载本仓库文件**。此前对某台路由器旧规则的检查也不等于本仓库部署验收。

## Sources

[1] https://wiki.metacubex.one/config/rule-providers/

[2] https://github.com/loon0x00/loonmanual/blob/master/docs/cn/sub_rule.md

[3] https://github.com/loon0x00/loonmanual/blob/master/docs/cn/rule.md
