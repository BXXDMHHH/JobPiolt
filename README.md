# JobPilot

Windows 本地求职助手。第一阶段使用 Python、Streamlit 与 SQLite，先完成岗位管理和投递记录，再逐步接入 BOSS 直聘浏览器辅助自动化。

## 快速启动

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 当前版本

- 本地 SQLite 数据持久化
- 岗位新增、查看、筛选
- 基础岗位匹配评分
- 投递状态记录

浏览器自动化将分阶段实现。请勿将账号密码、Cookie、个人简历或数据库文件提交到 GitHub。