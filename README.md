# 档案引文定位 API（Archive Quote Alignment）

基于 FastAPI 的引文定位服务：在档案原文中定位一组有序引文，返回每条引文在**原文中的原始字符偏移**。

## 启动

```bash
docker compose up --build
```

- 访问地址：**http://localhost:8000**（端口 **8000**）
- 交互式接口文档：http://localhost:8000/docs
- 健康检查：`GET http://localhost:8000/health` → `{"status": "ok"}`

依赖（FastAPI、Uvicorn）已写入 `requirements.txt`，在镜像构建阶段安装，随容器启动自动就绪，无需手动安装。

## 接口

### POST /quotes/align

请求体：

```json
{
  "text": "档案原文……",
  "quotes": ["引文一", "引文二"]
}
```

响应体（`results` 与 `quotes` 等长、顺序一一对应；无法定位的引文为 `null`）：

```json
{
  "results": [
    {"start": 0, "end": 12},
    null
  ]
}
```

`start`/`end` 为半开区间 `[start, end)`，即 `text[start:end]` 恰好是匹配到的原文片段。

示例：

```bash
curl -X POST http://localhost:8000/quotes/align \
  -H "Content-Type: application/json" \
  -d '{"text": "a   b\t\nc", "quotes": ["a b c", "不存在"]}'
# {"results":[{"start":0,"end":8},null]}
```

## 匹配与选择规则

1. **空白折叠匹配**：匹配时把原文与引文中任意连续空白（空格、制表符、换行等）视为一个空格；引文首尾空白忽略。返回的偏移始终指向**原文原始字符**，片段内部的空白按原文原样覆盖。
2. **多次出现**：同一引文可能在原文中出现多次，每次出现都是一个候选位置；完全无法定位的引文返回 `null`。
3. **联合选择**：从各引文的候选位置中联合挑选一组，要求互不重叠且保持引文数组的先后顺序，优化目标依次为：
   - 最大化成功定位的引文条数；
   - 最小化相邻已定位片段之间跳过的原文字符总数；
   - 仍并列时取偏移序列字典序最小的一组（同一位置上，已定位的偏移排在 `null` 之前）。

## 本地开发与测试

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
python -m pytest tests/    # 核心定位逻辑测试
```

## 项目结构

```
app/
  main.py        # FastAPI 应用：POST /quotes/align、GET /health
  alignment.py   # 核心定位算法（空白折叠、候选生成、动态规划联合选择）
tests/
  test_alignment.py
Dockerfile
docker-compose.yml
requirements.txt
```
