from services.matching_service import score_job


def test_exact_role_city_and_keywords_score_100():
    job = {"title": "软件测试开发工程师", "city": "上海", "jd": "Python SQL 自动化测试"}
    result = score_job(job, target_role="软件测试开发", target_city="上海", keywords=["Python", "SQL", "自动化测试"])
    assert result["score"] == 100
    assert "技能关键词命中 3/3" in result["reason"]


def test_missing_keywords_scores_lower():
    job = {"title": "销售", "city": "北京", "jd": "客户沟通"}
    result = score_job(job, target_role="软件测试开发", target_city="上海", keywords=["Python", "SQL"])
    assert 0 <= result["score"] < 100
