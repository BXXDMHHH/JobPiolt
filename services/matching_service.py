"""简单、可解释的岗位匹配评分，不依赖外部 AI 服务。"""


def score_job(job: dict, *, target_role: str = "", target_city: str = "", keywords: list[str] | None = None) -> dict:
    """返回 0-100 分及理由。此版本是启发式排序，不代表真实录用概率。"""
    keywords = keywords or []
    title = str(job.get("title", ""))
    city = str(job.get("city", ""))
    jd = str(job.get("jd", ""))
    score = 0
    reasons = []

    if target_role.strip():
        if target_role.strip().lower() in title.lower():
            score += 40
            reasons.append("岗位名称匹配目标方向 +40")
        elif any(part and part.lower() in title.lower() for part in target_role.replace("开发", "").replace("工程师", "").split()):
            score += 20
            reasons.append("岗位名称存在部分匹配 +20")
        else:
            reasons.append("岗位名称与目标方向未明显匹配")
    else:
        score += 20
        reasons.append("未设置目标岗位，暂不扣分")

    if target_city.strip():
        if target_city.strip().lower() in city.lower():
            score += 20
            reasons.append("工作城市匹配 +20")
        else:
            reasons.append("工作城市不匹配或信息缺失")
    else:
        score += 20
        reasons.append("未设置目标城市，暂不扣分")

    text = f"{title} {jd}".lower()
    if keywords:
        matched = [word for word in keywords if word.lower() in text]
        points = round(40 * len(matched) / len(keywords))
        score += points
        reasons.append(f"技能关键词命中 {len(matched)}/{len(keywords)}，得分 +{points}")
    else:
        score += 40
        reasons.append("未设置技能关键词，暂不扣分")

    return {"score": min(100, score), "reason": "；".join(reasons)}
