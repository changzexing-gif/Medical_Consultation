# 医疗问诊多智能体协作系统

一个可本地运行的 Streamlit 医疗问诊教学原型。系统采用协调器 + 专职 Agent 架构，包含问诊、检索、用药、风险、分诊和随访 Agent，并提供可观测性与 RAG 评估页面。

> 本项目仅用于教学和技术验证，不能替代医生诊断。出现胸痛、呼吸困难、意识改变等危险信号时请立即拨打 120。

## 技术实现

- **RAG**：`BAAI/bge-small-zh-v1.5` + ChromaDB 持久化向量数据库；检索链未使用 LangChain。
- **历史对话**：问诊 Agent 使用 LangChain `InMemoryChatMessageHistory` 管理会话。
- **编排**：LangGraph 编排 6 个 Agent，并在最终节点实施风险优先、禁忌优先的冲突仲裁。
- **生产能力**：TTL 查询缓存、异步检索接口、SQLite 监控事件、成本/失败/反馈统计。
- **降级**：未配置 LLM 时使用确定性的医学规则；BGE 加载失败时明确报错，不伪装成向量检索。

## 快速开始

```powershell
conda create -n medical-agents python=3.11 -y
conda activate medical-agents
pip install -r requirements.txt
python -m streamlit run app.py
```

浏览器打开 <http://localhost:8501>。首次进入“知识库管理”或执行问诊时，系统会下载 BGE 模型并构建 Chroma 索引。

可选的真实 LLM 配置：

```powershell
$env:LLM_API_KEY="your-key"
$env:LLM_BASE_URL="https://api.openai.com/v1"
$env:LLM_MODEL="gpt-4o-mini"
$env:LLM_INPUT_COST_PER_1M="0.15"   # 按所选模型填写
$env:LLM_OUTPUT_COST_PER_1M="0.60"
```

如需离线预构建索引：

```powershell
python scripts/build_index.py
```

运行测试：

```powershell
python -m pytest -q
```

## 项目结构

```text
agents/       Agent 定义、结构化类型与协调器
core/         配置、LLM、历史会话、LangGraph、监控
rag/          BGE、Chroma、索引、缓存、异步检索、评估
data/         内置演示医学资料
pages/        Streamlit 功能页与监控面板
scripts/      索引构建脚本
tests/        规则、仲裁、监控与检索单元测试
```

## 数据与隐私

监控数据库默认位于 `.runtime/monitoring.db`，向量库位于 `.runtime/chroma`。请勿向演示环境输入真实姓名、身份证号、电话号码等个人敏感信息。部署到生产前必须补充身份认证、访问控制、数据加密、审计、临床验证和合规评审。
