from services.resume_matching import match_resume_to_job


def test_resume_matching_prefers_relevant_version():
    job = {"title": "软件测试开发工程师", "jd": "要求 Python SQL 自动化测试", "city": "上海"}
    resumes = [
        {"id": 1, "display_name": "通用版", "target_role": "", "notes": ""},
        {"id": 2, "display_name": "测试开发校招版", "target_role": "软件测试开发", "notes": "Python SQL 自动化测试项目"},
    ]
    result = match_resume_to_job(job, resumes, target_role="软件测试开发", keywords=["Python", "SQL", "自动化测试"])
    assert result[0]["resume_id"] == 2
    assert result[0]["score"] > result[1]["score"]
