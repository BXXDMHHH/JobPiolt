# JobPilot

Windows 本地求职助手，使用 Python、Streamlit、SQLite 和 Playwright。目标是减少重复找岗位、筛选、匹配简历和记录投递结果的时间。

## 环境要求

- Windows 10/11
- Python 3.10 或更高版本

## 安装与启动

在 PowerShell 项目目录执行：

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m playwright install chromium
    .\.venv\Scripts\python.exe -m pytest
    .\.venv\Scripts\python.exe -m streamlit run app.py

通常可在 http://localhost:8501 打开本地应用。按 Ctrl+C 停止程序。

## 当前功能

- SQLite 岗位新增、查看、编辑、筛选、CSV 导入导出与去重
- 投递状态、状态变更历史
- 本地简历版本登记与下载：PDF、DOC、DOCX、TXT，单份最大 15 MB
- BOSS 直聘专用 Chromium 浏览器：用户手动登录并打开岗位，JobPilot 读取当前页面可见文本
- 结构化岗位字段建议：岗位名称、公司、城市、薪资、技能关键词；必须人工核对后保存
- 简历版本匹配：根据版本名称、目标岗位、备注与岗位 JD 做可解释的本地启发式评分
- 表单辅助：列出当前页面可见的普通输入框，用户逐项勾选后可填入；不会点击最终提交按钮
- 投递结果核实：记录“已确认成功 / 待核实 / 投递失败”、证据备注和页面 URL；确认成功必须提供证据
- 本地测试覆盖数据层、简历存储、字段提取、版本匹配与投递核实

## BOSS 页面读取流程

1. 在“BOSS 岗位读取”页面启动专用浏览器。
2. 在打开的 Chromium 中手动登录并打开目标岗位。
3. 回到 JobPilot，点击“读取当前 BOSS 页面”。
4. 检查自动识别字段并手动修正，再保存岗位。
5. 如需辅助填写，先检查页面字段，逐项勾选需要填写的普通输入框，再确认填写。
6. 回到浏览器核对填写结果；你本人完成提交操作后，再在 JobPilot 记录页面反馈作为证据。

页面结构和字段标签可能随 BOSS 直聘改版而变化。字段提取属于启发式识别，必须人工复核。遇到登录、验证码、访问限制时，请按平台正常流程处理；程序不绕过验证或访问控制。

## 简历匹配说明

当前版本不解析 PDF/DOC/DOCX 正文，只使用版本名称、目标岗位、备注以及岗位描述做本地规则评分。分数用于排序，不是录用概率；建议在版本备注中填写真实技能和项目重点，并人工检查推荐结果。

## 隐私和安全

- 简历、数据库和专用浏览器登录配置保存在本机。
- 不要将简历、账号密码、Cookie 或浏览器配置提交到公开仓库。
- 当前版本不自动点击最终投递按钮，不自动提交申请。
- 投递成功必须记录可核实的页面证据；单纯点击按钮不代表提交成功。

## 数据位置

- 岗位数据库：`data/jobpilot.db`
- 简历文件：`resumes/`
- BOSS 专用浏览器配置：`data/boss_browser_profile/`

请定期备份本地数据库和简历文件。