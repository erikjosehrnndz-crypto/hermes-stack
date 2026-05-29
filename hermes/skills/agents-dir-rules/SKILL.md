---
name: agents-dir-rules
description: 按目录自动注入 AGENTS.md 规则到子 Agent。在 delegate_task 进入特定目录时，先检查该目录下有无 AGENTS.md/.hermes-rules，有则注入 context。
version: 1.0.0
author: Bryan (爪爪)
license: MIT
---

# AGENTS.md 目录级规则注入

## 场景

当需要子 Agent 进入特定项目目录执行任务时，该目录下的 AGENTS.md 或 .hermes-rules 文件定义了该目录的约定、规范、约束。在 delegate_task 前先读取这些规则并注入到 context 中，子 Agent 就能自动按该目录的规矩行事。

## 用法

### 1. 在项目目录创建规则文件

```bash
# AGENTS.md — 供 Hermes 子 Agent 读取
touch path/to/project/AGENTS.md

# .hermes-rules — 另一种命名风格，同样支持
touch path/to/project/.hermes-rules
```

AGENTS.md 内容示例：

```markdown
# 目录规则

## 编码规范
- 使用 TypeScript，严格模式
- 缩进 2 空格，行尾无分号
- 所有公共函数必须有 JSDoc 注释

## 测试
- 每个函数至少一个测试用例
- 测试文件放在 __tests__/ 目录
- 使用 vitest 运行

## 约束
- 不允许使用 any 类型
- 不允许引入 lodash，使用原生 JS 替代
- API 请求必须走 src/api/ 封装的客户端
```

### 2. 父 Agent 检查规则文件

标准流程（每次 delegate_task 调用前执行）：

```bash
# 先检查目录下 AGENTS.md 或 .hermes-rules
ls <target_dir>/AGENTS.md 2>/dev/null && cat <target_dir>/AGENTS.md
# 或
ls <target_dir>/.hermes-rules 2>/dev/null && cat <target_dir>/.hermes-rules
```

如果文件存在，将内容拼接到 delegate_task 的 context 参数中。

### 3. 完整调用示例

```python
# 伪代码逻辑
target_dir = "~/projects/my-app/src"

# 检查规则文件
rules = ""
if os.path.exists(f"{target_dir}/AGENTS.md"):
    with open(f"{target_dir}/AGENTS.md") as f:
        rules = f.read()
elif os.path.exists(f"{target_dir}/.hermes-rules"):
    with open(f"{target_dir}/.hermes-rules") as f:
        rules = f.read()

# 注入到 delegate_task
delegate_task(
    goal="在 src/ 下添加用户注册 API 路由",
    context=f"工作目录: {target_dir}\n\n目录规则:\n{rules}",
    toolsets=["terminal", "file"]
)
```

## 多级目录规则合并

当子 Agent 需要进入深层子目录时，按以下优先级合并规则（从近到远）：

1. 目标目录下的 AGENTS.md（最高优先级）
2. 目标目录的父目录下的 AGENTS.md
3. 项目根目录下的 AGENTS.md（最低优先级）

重复字段以最高优先级为准，不重复的字段全部保留。

## 配套 .hermes-agent.yaml

可以在项目根目录放 .hermes-agent.yaml 文件定义全局约定：

```yaml
# .hermes-agent.yaml — 整个项目的 Hermes 配置
agents:
  default_workdir: "~/projects/my-app"
  always_inject_rules: true
  rules_files:
    - AGENTS.md
    - .hermes-rules
```
