"""从 BOSS 页面可见文本做启发式字段提取；结果必须由用户核对。"""
import re

SKILL_TERMS = [
    "Python", "Java", "C++", "JavaScript", "TypeScript", "SQL", "MySQL",
    "Linux", "Git", "pytest", "Selenium", "Playwright", "Appium",
    "自动化测试", "接口测试", "性能测试", "软件测试", "测试开发",
    "Docker", "Jenkins", "Redis", "Postman", "计算机网络",
]
CITY_TERMS = [
    "北京", "上海", "广州", "深圳", "杭州", "南京", "苏州", "成都",
    "武汉", "西安", "重庆", "天津", "郑州", "长沙", "合肥", "厦门",
    "青岛", "无锡", "宁波", "东莞", "佛山", "珠海", "福州", "济南",
]


def extract_job_fields(page: dict[str, str]) -> dict[str, object]:
    """从标题、URL 和可见文本中尽力提取字段，并返回置信度提示。"""
    title = (page.get("title") or "").strip()
    text = (page.get("text") or "").replace("\r", "\n")
    combined = title + "\n" + text
    lines = [re.sub(r"\s+", " ", line).strip() for line in combined.splitlines()]
    lines = [line for line in lines if line]
    clean_title = re.sub(r"\s*[-_|｜].*(BOSS直聘|BOSS).*?$", "", title, flags=re.I).strip()
    role = ""
    role_pattern = re.compile(r"([^\n]{2,40}?(?:工程师|测试开发|开发工程师|测试|研发|实习生|产品经理|运维|算法|前端|后端)[^\n]{0,15})")
    for line in lines[:40]:
        match = role_pattern.search(line)
        if match:
            candidate = match.group(1).strip(" -|｜")
            if not any(x in candidate for x in ["BOSS直聘", "登录", "扫码", "职位描述"]):
                role = candidate[:80]
                break
    if not role and clean_title and "BOSS直聘" not in clean_title:
        role = clean_title[:80]

    salary = ""
    salary_pattern = re.compile(r"(?<!\d)(?:\d{1,3}(?:\.\d+)?\s*[-~—至]\s*)?\d{1,3}(?:\.\d+)?\s*[万千kK](?:\s*[-~—至]\s*\d{1,3}(?:\.\d+)?\s*[万千kK])?(?:\s*[·/ ]\s*\d{1,2}薪)?")
    for line in lines:
        m = salary_pattern.search(line)
        if m:
            salary = re.sub(r"\s+", "", m.group(0))
            break

    city = ""
    for line in lines[:80]:
        for candidate in CITY_TERMS:
            if candidate in line and any(mark in line for mark in ["·", "|", "｜", "市", "区"]):
                city = candidate
                break
        if city:
            break
    if not city:
        for candidate in CITY_TERMS:
            if candidate in combined:
                city = candidate
                break

    skills = []
    lower_text = combined.lower()
    for skill in SKILL_TERMS:
        if skill.lower() in lower_text and skill.lower() not in [s.lower() for s in skills]:
            skills.append(skill)
    company = ""
    company_markers = ("有限公司", "股份有限公司", "科技", "集团", "信息技术", "网络技术")
    for line in lines[:100]:
        if len(line) <= 45 and any(marker in line for marker in company_markers):
            if not any(skip in line for skip in ["岗位职责", "任职要求", "职位描述", "公司介绍", "工作职责"]):
                company = line[:80]
                break

    confidence = {
        "岗位名称": "中" if role else "低",
        "公司名称": "中" if company else "低",
        "城市": "中" if city else "低",
        "薪资": "中" if salary else "低",
        "技能要求": "中" if skills else "低",
    }
    return {
        "title": role, "company": company, "city": city, "salary": salary,
        "skills": skills, "jd": text[:12000], "url": page.get("url", ""),
        "confidence": confidence,
    }
