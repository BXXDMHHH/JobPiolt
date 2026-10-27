"""本地可解释的岗位-简历版本匹配，不读取或解析简历文件正文。"""


def match_resume_to_job(job: dict, resumes: list[dict], target_role: str = "", keywords: list[str] | None = None) -> list[dict]:
    """依据版本名称、目标岗位、备注与岗位 JD 评分；不是录用概率。"""
    keywords = [str(k).strip() for k in (keywords or []) if str(k).strip()]
    job_text = " ".join(str(job.get(k, "")) for k in ("title", "jd", "salary", "city")).lower()
    results = []
    for resume in resumes:
        role = str(resume.get("target_role", ""))
        label = str(resume.get("display_name", ""))
        notes = str(resume.get("notes", ""))
        resume_text = f"{role} {label} {notes}".lower()
        score = 0
        reasons = []
        if target_role and target_role.lower() in (str(job.get("title", "")) + " " + job_text):
            score += 20
            reasons.append("岗位与当前求职目标相关 +20")
        if role and any(token in (str(job.get("title", "") + " " + job_text)) for token in [x for x in role.lower().replace("、", " ").replace("/", " ").split() if len(x) > 1]):
            score += 35
            reasons.append("简历目标岗位与职位描述相关 +35")
        elif role:
            reasons.append("简历目标岗位未明显命中职位文本")
        else:
            reasons.append("该简历版本未设置目标岗位")
        note_hits = [token for token in keywords if token.lower() in resume_text and token.lower() in job_text]
        if keywords:
            points = round(35 * len(note_hits) / len(keywords))
            score += points
            reasons.append(f"版本备注与岗位技能共同命中 {len(note_hits)}/{len(keywords)} +{points}")
        else:
            overlap = [token for token in ("python", "sql", "自动化测试", "接口测试", "selenium", "playwright", "linux") if token in resume_text and token in job_text]
            points = min(35, 10 * len(overlap))
            score += points
            if overlap:
                reasons.append("版本备注与岗位技能命中：" + "、".join(overlap))
            else:
                reasons.append("版本备注未提供足够技能信息")
        if notes.strip():
            score += 10
            reasons.append("存在版本备注，可辅助人工判断 +10")
        results.append({
            "resume_id": resume.get("id"), "display_name": label,
            "target_role": role, "score": min(score, 100),
            "reason": "；".join(reasons),
        })
    return sorted(results, key=lambda item: item["score"], reverse=True)
