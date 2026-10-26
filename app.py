"""JobPilot 本地求职助手入口。

学习提示（按 28 法则）：
1. Streamlit 的核心是 st.title / st.text_input / st.button / st.dataframe。
2. 页面负责展示与接收输入，数据库操作放在 db/database.py。
3. 本地数据写入 SQLite，重启程序后仍然存在。
"""
from pathlib import Path
import sys

import streamlit as st

# 确保从项目根目录启动时可以导入 db/ 下的模块。
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.database import init_db, list_jobs, create_job, count_jobs
from services.matching_service import score_job

st.set_page_config(page_title="JobPilot 求职助手", page_icon="🎯", layout="wide")
init_db()

st.title("🎯 JobPilot 求职助手")
st.caption("Windows 本地运行 · 岗位管理与投递跟踪 · 初始开发版")

# 侧边栏：先做最重要的求职偏好，后续会保存到个人配置表。
with st.sidebar:
    st.header("求职目标")
    target_role = st.text_input("目标岗位", value="软件测试开发")
    target_city = st.text_input("目标城市", value="")
    keywords_text = st.text_input("技能关键词（逗号分隔）", value="Python, SQL, 自动化测试")
    st.info("当前版本先使用本地规则评分，不需要 AI API Key。")

jobs = list_jobs()
col1, col2, col3 = st.columns(3)
col1.metric("岗位总数", count_jobs())
col2.metric("待投递", sum(1 for job in jobs if job["status"] == "待投递"))
col3.metric("已投递", sum(1 for job in jobs if job["status"] == "已投递"))

st.subheader("新增岗位")
with st.form("add_job_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    title = c1.text_input("岗位名称 *", placeholder="例如：软件测试工程师")
    company = c2.text_input("公司名称 *", placeholder="例如：某某科技")
    c3, c4 = st.columns(2)
    city = c3.text_input("工作城市", value=target_city)
    salary = c4.text_input("薪资范围", placeholder="例如：10-15K")
    url = st.text_input("岗位链接", placeholder="https://...")
    jd = st.text_area("岗位描述 / JD", height=140, placeholder="粘贴岗位职责、任职要求等内容")
    submitted = st.form_submit_button("保存岗位", type="primary")
    if submitted:
        if not title.strip() or not company.strip():
            st.error("岗位名称和公司名称为必填项。")
        else:
            try:
                create_job(title=title.strip(), company=company.strip(), city=city.strip(), salary=salary.strip(), url=url.strip(), jd=jd.strip())
                st.success("岗位已保存到本地数据库。")
                st.rerun()
            except ValueError as exc:
                st.warning(str(exc))

st.subheader("岗位列表")
filter_text = st.text_input("搜索岗位 / 公司 / 技能", placeholder="输入关键词筛选")
if not jobs:
    st.info("还没有岗位。你可以先手动新增岗位，后续会增加 CSV 导入和 BOSS 直聘页面读取。")
else:
    keywords = [item.strip().lower() for item in keywords_text.split(",") if item.strip()]
    rows = []
    for job in jobs:
        searchable = f"{job['title']} {job['company']} {job['city']} {job['jd']}".lower()
        if filter_text.strip().lower() not in searchable:
            continue
        result = score_job(job, target_role=target_role, target_city=target_city, keywords=keywords)
        rows.append({"岗位": job["title"], "公司": job["company"], "城市": job["city"], "薪资": job["salary"], "匹配分": result["score"], "状态": job["status"], "链接": job["url"], "匹配说明": result["reason"]})
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.caption("没有找到符合筛选条件的岗位。")

st.divider()
st.caption("安全提示：不要把账号密码、浏览器 Cookie、个人简历或本地数据库上传到公开仓库。浏览器自动化尚未启用。")
