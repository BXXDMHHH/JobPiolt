# JobPilot

Windows 本地求职助手，当前使用 Python、Streamlit 与 SQLite。先完成岗位管理闭环，再逐步接入 BOSS 直聘浏览器辅助自动化。

## 环境要求
- Windows 10/11
- Python 3.10 或更高版本

## 快速启动
在 PowerShell 项目目录中执行：

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m streamlit run app.py

浏览器会显示本地 Streamlit 地址，通常是 http://localhost:8501。按 Ctrl+C 停止程序。

## 已实现
- SQLite 本地岗位数据持久化
- 岗位新增、查看、编辑、关键词筛选
- CSV 岗位模板下载、批量导入、导出
- 基础岗位匹配评分
- 投递状态修改和状态变更历史
- CSV 导入重复检查及数据库单元测试

## CSV 格式
必需列：岗位名称、公司名称。可选列：城市、薪资、岗位链接、岗位描述、状态。也支持英文列名 title、company、city、salary、url、jd、status。

## 测试
    .\.venv\Scripts\python.exe -m pytest

## 数据与安全
本地数据库默认位于 data/jobpilot.db，已由 .gitignore 排除。不要把简历、账号密码、浏览器 Cookie 或真实个人信息提交到公开仓库。当前版本尚未接入 BOSS 直聘自动登录或自动提交功能。

## 后续路线
1. 完善简历版本管理和匹配规则
2. 接入 BOSS 直聘岗位读取
3. 对支持的页面实现表单辅助填写与结果核实
