# 错误码对照表

## API 错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 0 | 成功 | - |
| -1 | 通用错误 | 检查请求参数和网络连接 |
| -2 | 参数错误 | 检查请求参数格式 |
| -3 | 设备不在线 | 检查设备网络状态 |
| -4 | Token 过期 | 重新登录获取新 Token |
| -5 | 无权限 | 检查账号权限设置 |
| -6 | 设备不支持该操作 | 检查设备是否支持此功能 |
| -7 | 操作过于频繁 | 降低操作频率 |
| -8 | 设备响应超时 | 重试或检查设备状态 |
| -9 | 设备忙碌 | 等待后重试 |
| -10 | 安全锁定 | 多次失败后需等待解锁 |

## HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 502 | 网关错误 |
| 503 | 服务不可用 |

## 认证错误

| 错误信息 | 说明 |
|----------|------|
| "Need verify" | 需要二次验证 |
| "Invalid username or password" | 用户名或密码错误 |
| "Account locked" | 账号被锁定 |
| "OAuth token expired" | OAuth Token 已过期 |
| "Invalid OAuth code" | OAuth 授权码无效 |

## 设备控制错误

| 错误信息 | 说明 |
|----------|------|
| "Device offline" | 设备离线 |
| "Device not found" | 设备不存在 |
| "Property not exist" | 属性不存在 |
| "Value out of range" | 值超出范围 |
| "Device busy" | 设备忙碌中 |
| "Control failed" | 控制失败 |

## 网络错误

| 错误信息 | 说明 |
|----------|------|
| "Connection timeout" | 连接超时 |
| "Connection refused" | 连接被拒绝 |
| "Network unreachable" | 网络不可达 |
| "DNS resolution failed" | DNS 解析失败 |
