# JobPilot

Windows 本地求职助手。当前先建立可运行的 Python + Streamlit + SQLite 基础环境，逐步实现岗位管理、匹配评分、投递跟踪和 BOSS 直聘浏览器辅助自动化。

## 环境要求

- Windows 10/11
- Python 3.10 或更高版本
- 可正常使用的终端（PowerShell 或 Windows Terminal）

## 快速启动

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

如果 PowerShell 阻止激活虚拟环境，可以直接运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

浏览器默认会打开本地 Streamlit 页面。按 `Ctrl+C` 可停止程序。

## 运行测试

```powershell
python -m pytest
```

## 当前已实现

- Streamlit 本地仪表盘
- SQLite 数据库初始化和持久化
- 手动新增、查看和筛选岗位
- 按岗位方向、城市和技能关键词进行基础规则评分
- 疑似重复岗位拦截
- 初步匹配评分单元测试

## 后续开发

1. 完善岗位编辑、CSV 导入和投递状态更新
2. 增加简历版本管理和投递事件历史
3. 接入 BOSS 直聘网页的岗位读取
4. 逐步开发表单辅助填写和提交结果核实

浏览器自动化尚未接入，当前版本不会自动登录或提交求职申请。请勿将账号密码、浏览器 Cookie、个人简历或本地数据库提交到 GitHub。