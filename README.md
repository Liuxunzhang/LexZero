# LexZero

一个基于 Textual 的 Volatility3 TUI（终端用户界面）工具，用于内存取证分析。

## 功能特性

- **侧边栏菜单**：左侧分类显示插件（进程、网络、内核模块、文件系统等）
- **命令行界面**：顶部命令行支持自动补全
- **实时过滤**：在查看进程列表时支持搜索
- **列排序**：按任意列升序/降序排序（按 S 键）
- **列移动**：左右移动列调整显示顺序（方向键）
- **可视化展示**：以表格形式展示内存镜像分析结果
- **缓存机制**：插件结果自动缓存，避免重复执行（提升性能）

## 安装

```bash
pip install -r requirements.txt
```

或使用开发模式安装：

```bash
pip install -e .
```

## 使用方法

```bash
# 启动 TUI（不加载镜像）
python -m lexzero.app

# 启动并加载内存镜像
python -m lexzero.app dumps/dump.raw
```

## 快捷键

- `Ctrl+L`: 聚焦到命令行
- `Ctrl+F`: 聚焦到过滤框
- `Ctrl+S`: 聚焦到侧边栏
- `Ctrl+E`: 导出当前结果
- `Ctrl+R`: 刷新当前插件���清除缓存重新运行）
- `S`: 按当前列排序（切换升序/降序）
- `Left/Right`: 左右移动当前列
- `Q` 或 `Ctrl+C`: 退出

### 命令

- `load <path>`: 加载内存镜像
- `clear`: 清空结果
- `clearcache`: 清除所有缓存
- `export [csv|json|txt]`: 导出结果（默认 CSV）
- `help`: 显示帮助
- `<plugin_name>`: 运行指定插件（使用完整路径，如 `linux.pslist.PsList`）

## ���用示例

```bash
# 启动应用
python -m lexzero.app dumps/dump.raw

# 在命令行中输入：
load /path/to/memory.dump

# 运行 Linux 插件（使用完整路径）：
linux.pslist.PsList
linux.lsmod.Lsmod
linux.bash.Bash

# 或者点击侧边栏中的插件名称
```

## 缓存机制

- 插件执行结果会自动缓存
- 再次运行相同插件时直接返回缓存结果（0秒 vs 7秒）
- 使用 `Ctrl+R` 或 `clearcache` 命令清除缓存
- 加载新镜像时自动清除所有缓存

## 支持的 Linux 插件

LexZero 支持 57 个 Linux 内存取证插件，分为 8 大类：

- **进程相关** (6个): pslist, psscan, pstree, psaux, envars, kthreads
- **文件/模块** (8个): lsof, lsmod, elfs, library_list, mountinfo 等
- **网络相关** (4个): sockstat, netfilter, ip.Addr, ip.Link
- **内存/恶意代码** (6个): malfind, proc.Maps, vmaregexscan, pagecache 等
- **安全检查/Rootkit** (9个): check_syscall, check_afinfo, check_idt, ebpf 等
- **系统信息/调试** (8个): bash, kmsg, boottime, kallsyms 等
- **追踪/调试** (5个): ftrace, tracepoints, perf_events, ptrace 等
- **Malware专项** (11个): 各类恶意软件检测插件

## 项目结构

```
lexzero/
├── core/              # 核心功能
│   ├── volatility_wrapper_v2.py  # Volatility3 封装（使用 vol 命令行）
│   └── __init__.py
├── ui/                # UI 组件
│   ├── sidebar.py     # 侧边栏
│   ├── command_input.py  # 命令输入
│   ├── filter_input.py   # 过滤输入
│   ├── filterable_table.py  # 可过滤表格
│   ├── status_bar.py     # 状态栏
│   └── __init__.py
├── utils/             # 工具函数
│   ├── exporter.py    # 导出工具
│   └── __init__.py
└── app.py             # 主应用
```

## 技术实现

- 使用 `vol` 命令行工具执行插件（CSV 输出）
- 异步执行避免 UI 阻塞
- 内存缓存提升性能
- 支持超时控制（120秒）

## 开发计划

- [x] 基础 TUI 框架
- [x] 侧边栏插件分类
- [x] 命令行自动补全
- [x] 实时过滤功能
- [x] 结果导出（CSV/JSON/TXT）
- [x] Volatility3 插件执行（使用 vol 命令行）
- [x] 结果缓存机制
- [x] 列排序功能
- [x] 列移动功能
- [ ] 支持多标签页
- [ ] 插件参数配置

## 故障排除

如果遇到 "Plugin requirements not satisfied" 或其他错误，请查看：

- 日志文件：`/tmp/lexzero.log`

常见问题：
- 确保使用 Linux 内存镜像（不是 Windows/Mac）
- 确保镜像文件路径正确
- 可能需要下载对应的符号表文件

## 许可证

MIT License
