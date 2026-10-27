"""BOSS 直聘页面读取辅助：仅读取当前可见页面，不自动投递、不绕过登录或验证码。"""
from pathlib import Path
import subprocess
import time

ROOT_DIR = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT_DIR / "data" / "boss_browser_profile"
DEBUG_PORT = 9222
DEFAULT_URL = "https://www.zhipin.com/web/geek/job?query=软件测试开发"


def launch_browser(url: str = DEFAULT_URL) -> str:
    """启动隔离的 Chromium 用户配置；登录由用户本人手动完成。"""
    from playwright.sync_api import sync_playwright
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        executable = p.chromium.executable_path
    command = [executable, f"--remote-debugging-port={DEBUG_PORT}",
               f"--user-data-dir={PROFILE_DIR}", "--no-first-run",
               "--no-default-browser-check", url or DEFAULT_URL]
    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        raise RuntimeError(f"无法启动 Chromium：{exc}. 请先运行 playwright install chromium。") from exc
    time.sleep(1.5)
    return "已尝试启动专用浏览器。请手动登录 BOSS 直聘并打开目标岗位。"


def read_current_page() -> dict[str, str]:
    """通过本机 CDP 读取当前标签页的标题、URL、描述和可见文本。"""
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}", timeout=5000)
        except PlaywrightError as exc:
            raise RuntimeError("未发现 JobPilot 专用浏览器。请先点击“启动 BOSS 浏览器”。") from exc
        try:
            pages = [page for context in browser.contexts for page in context.pages]
            page = next((page for page in reversed(pages) if "zhipin.com" in page.url), None)
            if page is None:
                raise RuntimeError("当前没有打开 BOSS 直聘页面，请在专用浏览器中打开岗位详情页。")
            data = page.evaluate("""() => ({
                title: document.title || '',
                url: location.href || '',
                description: document.querySelector('meta[name="description"]')?.content || '',
                text: (document.body?.innerText || '').slice(0, 12000)
            })""")
            return {k: str(v or "") for k, v in data.items()}
        finally:
            browser.close()



def inspect_visible_form_fields() -> list[dict[str, str]]:
    """只检查当前 BOSS 页面可见、可编辑的表单控件，不读取密码字段。"""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}", timeout=5000)
        try:
            pages = [page for context in browser.contexts for page in context.pages]
            page = next((page for page in reversed(pages) if "zhipin.com" in page.url), None)
            if page is None:
                raise RuntimeError("没有打开 BOSS 直聘页面。")
            return page.evaluate("""() => Array.from(document.querySelectorAll('input, textarea, select'))
                .filter(el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' &&
                           !el.disabled && !el.readOnly &&
                           !['password','hidden','file','submit','button','checkbox','radio'].includes((el.type || '').toLowerCase());
                }).slice(0, 80).map((el, i) => ({
                    index: String(i),
                    tag: el.tagName.toLowerCase(),
                    type: el.type || '',
                    label: (el.labels && Array.from(el.labels).map(x => x.innerText).join(' ')) ||
                           el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.name || '',
                    placeholder: el.getAttribute('placeholder') || '',
                    value: (el.value || '').slice(0, 120)
                }))""")
        finally:
            browser.close()


def fill_visible_fields(values: dict[str, str]) -> dict[str, object]:
    """按用户勾选后的 index 填写可见字段；绝不提交表单。"""
    from playwright.sync_api import sync_playwright
    allowed = {}
    for key, value in values.items():
        if not str(key).isdigit():
            continue
        allowed[int(key)] = str(value)[:2000]
    if not allowed:
        return {"filled": 0, "fields": []}
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}", timeout=5000)
        try:
            pages = [page for context in browser.contexts for page in context.pages]
            page = next((page for page in reversed(pages) if "zhipin.com" in page.url), None)
            if page is None:
                raise RuntimeError("没有打开 BOSS 直聘页面。")
            result = page.evaluate("""(values) => {
                const els = Array.from(document.querySelectorAll('input, textarea, select'))
                  .filter(el => {
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' &&
                           !el.disabled && !el.readOnly &&
                           !['password','hidden','file','submit','button','checkbox','radio'].includes((el.type || '').toLowerCase());
                  }).slice(0, 80);
                const filled = [];
                for (const [key, value] of Object.entries(values)) {
                  const el = els[Number(key)];
                  if (!el || !['INPUT','TEXTAREA'].includes(el.tagName)) continue;
                  const setter = Object.getOwnPropertyDescriptor(
                    el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype, 'value'
                  )?.set;
                  if (!setter) continue;
                  setter.call(el, value);
                  el.dispatchEvent(new Event('input', {bubbles:true}));
                  el.dispatchEvent(new Event('change', {bubbles:true}));
                  filled.push({index:key, label:el.getAttribute('aria-label') || el.placeholder || el.name || '', value:value.slice(0,120)});
                }
                return filled;
            }""", {str(k): v for k, v in allowed.items()})
            return {"filled": len(result), "fields": result, "submitted": False}
        finally:
            browser.close()
