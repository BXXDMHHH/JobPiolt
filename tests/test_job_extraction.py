from services.job_extraction import extract_job_fields


def test_extract_common_job_fields():
    result = extract_job_fields({
        "title": "软件测试开发工程师 - BOSS直聘",
        "url": "https://www.zhipin.com/job_detail/example",
        "text": "上海 · 10-15K · 经验不限\n示例科技有限公司\n岗位职责\n负责自动化测试，使用 Python、SQL、Playwright。",
    })
    assert "测试开发" in result["title"] or "测试" in result["title"]
    assert result["salary"] == "10-15K"
    assert result["city"] == "上海"
    assert "Python" in result["skills"]
    assert "SQL" in result["skills"]
    assert result["url"].startswith("https://")
