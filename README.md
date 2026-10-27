# JobPilot

Windows 本地求职助手，使用 Python、Streamlit 与 SQLite。当前重点是岗位管理、简历版本管理和 BOSS 直聘岗位页面读取。

## 环境要求

- Windows 10/11
- Python 3.10 或更高版本

## 快速启动

在 PowerShell 项目目录中执行：

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m playwright install chromium
    .\.venv\Scripts\python.exe -m pytest
    .\.venv\Scripts\python.exe -m streamlit run app.py

浏览器会显示本地 Streamlit 地址，通常是 http://localhost:8501。按 Ctrl+C 停止程序。

## 当前功能

- SQLite 岗位新增、查看、编辑、筛选和去重
- CSV 岗位模板下载、批量导入、导出
- 投递状态更新、状态变更历史
- 简历版本登记：PDF、DOC、DOCX、TXT，单份最大 15 MB
- 简历文件保存在本机 `resumes/`，数据库保存版本名称、目标岗位、备注、哈希和创建时间
- BOSS 直聘页面读取：启动隔离的 Chromium 配置，由用户手动登录和打开岗位，再读取当前页面标题、URL、描述与可见文本；核对后可保存为岗位
- 基础岗位匹配评分

## BOSS 页面读取步骤

1. 安装依赖后运行 `python -m playwright install chromium`。
2. 在 JobPilot 的“BOSS 岗位读取”页面点击“启动 BOSS 专用浏览器”。
3. 在新打开的浏览器里手动登录 BOSS 直聘，并手动打开岗位详情页。
4. 回到 JobPilot 点击“读取当前 BOSS 页面”。
5. 检查页面文本，手动填写并核对岗位名称、公司、城市、薪资，再保存到岗位库。

如果页面显示登录、验证、访问限制或没有岗位详情，请在浏览器中按平台正常流程处理。程序不尝试绕过验证码或访问限制。

## 隐私和安全

- 简历文件、本地数据库、BOSS 专用浏览器配置均保存在本机。
- `data/jobpilot.db`、`data/boss_browser_profile/` 和 `resumes/` 均应保持在 Git 忽略范围内。
- 不要把简历、账号密码、Cookie 或浏览器配置提交到公开仓库。
- 当前 BOSS 集成只读取页面，不自动点击投递、不自动提交申请。
- 后续会在岗位读取稳定后，再开发表单辅助填写与提交结果核实。

## 测试

    .\.venv\Scripts\python.exe -m pytest
