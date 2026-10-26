"""JobPilot 本地求职助手入口。学习重点：Streamlit 表单 + SQLite 持久化 + 可追踪的状态历史。"""
from pathlib import Path
import sys
from io import BytesIO
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.database import JOB_STATUSES, init_db, list_jobs, get_job, create_job, update_job, update_job_status, list_application_events, import_jobs, count_jobs
from services.matching_service import score_job

st.set_page_config(page_title="JobPilot 求职助手", page_icon="🎯", layout="wide")
init_db()
st.title("🎯 JobPilot 求职助手")
st.caption("Windows 本地运行 · 岗位管理、CSV 导入、投递状态与历史")

with st.sidebar:
    st.header("求职目标")
    target_role = st.text_input("目标岗位", value="软件测试开发")
    target_city = st.text_input("目标城市", value="")
    keywords_text = st.text_input("技能关键词（逗号分隔）", value="Python, SQL, 自动化测试")
    st.info("当前使用本地规则评分，不需要 AI API Key。")

jobs = list_jobs()
c1, c2, c3, c4 = st.columns(4)
c1.metric("岗位总数", count_jobs())
c2.metric("待投递", sum(j["status"] == "待投递" for j in jobs))
c3.metric("已投递", sum(j["status"] == "已投递" for j in jobs))
c4.metric("面试中", sum(j["status"] == "面试" for j in jobs))

tab_jobs, tab_import, tab_status, tab_history = st.tabs(["岗位管理", "CSV 批量导入/导出", "投递状态", "投递历史"])

with tab_jobs:
    st.subheader("新增岗位")
    with st.form("add_job_form", clear_on_submit=True):
        a, b = st.columns(2)
        title = a.text_input("岗位名称 *", placeholder="例如：软件测试工程师")
        company = b.text_input("公司名称 *", placeholder="例如：某某科技")
        a, b = st.columns(2)
        city = a.text_input("工作城市", value=target_city)
        salary = b.text_input("薪资范围", placeholder="例如：10-15K")
        url = st.text_input("岗位链接", placeholder="https://...")
        jd = st.text_area("岗位描述 / JD", height=120)
        initial_status = st.selectbox("初始状态", JOB_STATUSES)
        if st.form_submit_button("保存岗位", type="primary"):
            if not title.strip() or not company.strip():
                st.error("岗位名称和公司名称为必填项。")
            else:
                try:
                    create_job(title=title, company=company, city=city, salary=salary, url=url, jd=jd, status=initial_status)
                    st.success("岗位已保存。")
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))

    st.divider()
    st.subheader("岗位列表与编辑")
    search_text = st.text_input("搜索岗位 / 公司 / 技能 / 状态", key="job_search")
    current_jobs = list_jobs()
    keywords = [x.strip() for x in keywords_text.split(",") if x.strip()]
    visible = []
    for job in current_jobs:
        haystack = f"{job['title']} {job['company']} {job['city']} {job['jd']} {job['status']}".lower()
        if search_text.strip().lower() not in haystack:
            continue
        match = score_job(job, target_role=target_role, target_city=target_city, keywords=keywords)
        visible.append({"ID": job["id"], "岗位": job["title"], "公司": job["company"], "城市": job["city"], "薪资": job["salary"], "匹配分": match["score"], "状态": job["status"], "更新时间": job["updated_at"], "岗位链接": job["url"], "匹配说明": match["reason"]})
    if visible:
        st.dataframe(pd.DataFrame(visible), use_container_width=True, hide_index=True)
    else:
        st.info("没有匹配的岗位记录。")

    if current_jobs:
        choices = {f"#{j['id']} · {j['company']} · {j['title']}（{j['city'] or '城市未填'}）": j["id"] for j in current_jobs}
        selected = st.selectbox("选择要编辑的岗位", list(choices.keys()))
        job = get_job(choices[selected])
        if job:
            with st.form("edit_job_form"):
                a, b = st.columns(2)
                e_title = a.text_input("岗位名称", value=job["title"])
                e_company = b.text_input("公司名称", value=job["company"])
                a, b = st.columns(2)
                e_city = a.text_input("工作城市", value=job["city"])
                e_salary = b.text_input("薪资范围", value=job["salary"])
                e_url = st.text_input("岗位链接", value=job["url"])
                e_jd = st.text_area("岗位描述 / JD", value=job["jd"], height=120)
                if st.form_submit_button("保存岗位修改"):
                    if not e_title.strip() or not e_company.strip():
                        st.error("岗位名称和公司名称不能为空。")
                    else:
                        try:
                            update_job(job["id"], title=e_title, company=e_company, city=e_city, salary=e_salary, url=e_url, jd=e_jd)
                            st.success("岗位信息已更新。")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
    else:
        st.caption("新增岗位后，这里会出现编辑表单。")

with tab_import:
    st.subheader("CSV 批量导入")
    st.markdown("必需列：岗位名称、公司名称。可选列：城市、薪资、岗位链接、岗位描述、状态；也支持英文列名 title/company/city/salary/url/jd/status。")
    template = pd.DataFrame([{"岗位名称": "软件测试工程师", "公司名称": "示例科技", "城市": "上海", "薪资": "10-15K", "岗位链接": "https://example.com/job", "岗位描述": "Python、SQL、自动化测试", "状态": "待投递"}])
    st.download_button("下载 CSV 模板", template.to_csv(index=False).encode("utf-8-sig"), "jobpilot_jobs_template.csv", "text/csv")
    uploaded = st.file_uploader("选择岗位 CSV 文件", type=["csv"])
    if uploaded is not None:
        try:
            raw = uploaded.getvalue()
            try:
                df = pd.read_csv(BytesIO(raw), encoding="utf-8-sig").fillna("")
            except UnicodeDecodeError:
                df = pd.read_csv(BytesIO(raw), encoding="gb18030").fillna("")
            st.write("导入预览（最多显示前 20 行）")
            st.dataframe(df.head(20), use_container_width=True, hide_index=True)
            if st.button("确认导入岗位", type="primary"):
                result = import_jobs(df.to_dict(orient="records"))
                st.success(f"导入完成：新增 {result['imported']} 条，重复跳过 {result['skipped']} 条，缺少必填字段/失败 {result['failed']} 条。")
                st.rerun()
        except Exception as exc:
            st.error(f"CSV 读取失败，请检查文件编码和格式。详细信息：{exc}")
    export_rows = list_jobs()
    if export_rows:
        st.download_button("导出全部岗位 CSV", pd.DataFrame(export_rows).to_csv(index=False).encode("utf-8-sig"), "jobpilot_jobs_export.csv", "text/csv")
    else:
        st.caption("目前没有岗位可导出。")

with tab_status:
    st.subheader("修改投递状态")
    current_jobs = list_jobs()
    if not current_jobs:
        st.info("请先添加或导入岗位。")
    else:
        choices = {f"#{j['id']} · {j['company']} · {j['title']} · 当前：{j['status']}": j["id"] for j in current_jobs}
        chosen = st.selectbox("选择岗位", list(choices.keys()), key="status_job")
        job = get_job(choices[chosen])
        if job:
            st.write(f"**岗位：** {job['title']}　 **公司：** {job['company']}")
            with st.form("status_form"):
                new_status = st.selectbox("新状态", JOB_STATUSES, index=JOB_STATUSES.index(job["status"]))
                note = st.text_input("备注（可选）", placeholder="例如：页面显示投递成功")
                if st.form_submit_button("保存状态变化", type="primary"):
                    try:
                        update_job_status(job["id"], new_status, note)
                        st.success("状态与历史记录已更新。")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            if job["url"]:
                st.link_button("打开岗位链接", job["url"])

with tab_history:
    st.subheader("投递历史与状态变化")
    history_jobs = list_jobs()
    history_filter = st.selectbox("历史范围", ["全部岗位"] + [f"#{j['id']} · {j['company']} · {j['title']}" for j in history_jobs])
    history_id = None if history_filter == "全部岗位" else int(history_filter.split(" · ", 1)[0].replace("#", ""))
    events = list_application_events(history_id)
    if events:
        history_df = pd.DataFrame([{"时间": e["created_at"], "岗位": e["job_title"], "公司": e["company"], "原状态": e["old_status"] or "—", "新状态": e["new_status"], "备注": e["note"]} for e in events])
        st.dataframe(history_df, use_container_width=True, hide_index=True)
        st.download_button("导出历史 CSV", history_df.to_csv(index=False).encode("utf-8-sig"), "jobpilot_application_history.csv", "text/csv")
    else:
        st.info("暂无历史记录。创建岗位和修改状态后，历史会自动记录。")

st.divider()
st.caption("本地数据库默认保存在 data/jobpilot.db。不要把个人简历、账号密码、浏览器 Cookie 或真实个人信息提交到公开仓库。")
