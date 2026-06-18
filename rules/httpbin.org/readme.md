# httpbin.org

## 规则使用方法

本规则用于演示 mitmproxy 代理工具的基本请求/响应头修改功能。

### 代理链路

```
浏览器 → Proxy1 (127.0.0.1:8081) → Proxy2 (127.0.0.1:8082) → httpbin.org
```

### 脚本说明

| 脚本 | 位置 | 功能 |
|------|------|------|
| proxy1.py | 解密端 | 在请求进入 Proxy1 后、转发前，添加/修改/删除请求头 |
| proxy2.py | 加密端 | 在响应返回前，添加/修改/删除响应头（当前为空模板） |

### 使用步骤

1. 在工具中启用 httpbin.org 规则（勾选 proxy1 和/或 proxy2）
2. 启动对应代理实例
3. 配置浏览器代理为 `127.0.0.1:8081`（或对应端口）
4. 访问 `https://httpbin.org/headers` 验证请求头是否被修改

### 自定义修改

编辑 `proxy1.py` 中的配置字典即可自定义头修改行为：

- `REQUEST_HEADERS` — 要添加或覆盖的请求头
- `REMOVE_REQUEST_HEADERS` — 要删除的请求头
- `RESPONSE_HEADERS` — 要添加或覆盖的响应头
- `REMOVE_RESPONSE_HEADERS` — 要删除的响应头

## 加解密分析

### HTTPS 拦截原理

httpbin.org 使用 HTTPS 协议。mitmproxy 通过以下流程实现中间人代理：

```
┌─────────┐     TLS(mitmproxy)     ┌─────────┐     TLS(httpbin.org)     ┌──────────────┐
│  浏览器  │ ◄──────────────────────► │ Proxy1  │ ◄──────────────────────► │ Proxy2       │ ──► httpbin.org
└─────────┘                         └─────────┘                         └──────────────┘
  客户端证书                          mitmproxy CA 证书                   真实服务器证书
```

### 解密阶段 (Proxy1)

1. 浏览器发起 CONNECT 请求到 Proxy1
2. Proxy1 使用 mitmproxy 自签 CA 证书与浏览器完成 TLS 握手
3. 浏览器发送的加密请求在 Proxy1 处被解密为明文
4. `proxy1.py` 的 `request()` 函数在明文请求上执行，可读取/修改 URL、请求头、请求体
5. 修改后的请求转发至 Proxy2

### 加密阶段 (Proxy2)

1. Proxy2 接收来自 Proxy1 的明文请求
2. `proxy2.py` 的 `request()` 函数可对明文请求做进一步处理
3. Proxy2 与目标服务器 httpbin.org 建立真实的 TLS 连接
4. 请求以标准 HTTPS 加密发送至 httpbin.org
5. 收到响应后，`proxy2.py` 的 `response()` 函数处理明文响应
6. 响应经 Proxy1 → 浏览器链路返回，由 mitmproxy CA 证书重新加密

### 本例加解密要点

| 阶段 | 操作 | 数据状态 |
|------|------|----------|
| 浏览器 → Proxy1 | TLS 解密（mitmproxy 证书） | 明文 |
| Proxy1 request() | 添加 X-Custom-Header、Authorization | 明文修改 |
| Proxy2 → httpbin.org | TLS 加密（真实证书） | 密文 |
| httpbin.org → Proxy2 | TLS 解密（真实证书） | 明文 |
| Proxy1 → 浏览器 | TLS 加密（mitmproxy 证书） | 密文 |

### 安全说明

- 本规则仅用于本地开发调试，请勿在生产环境使用
- mitmproxy CA 证书需在客户端设备上手动信任
- 敏感请求头（如 Authorization）的修改仅在本地代理链路中可见
