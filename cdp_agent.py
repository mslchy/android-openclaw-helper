"""
CDP 远程控制手机 Chrome Demo
通过 Chrome DevTools Protocol 直接操作手机浏览器 DOM，无需截图+OCR
"""
import asyncio
import json
import websockets


CDP_HTTP = "http://127.0.0.1:9222"
CDP_WS = "ws://127.0.0.1:9222"


class ChromeCDP:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self._id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=10 * 1024 * 1024)
        print(f"[CDP] 已连接: {self.ws_url[:60]}...")

    async def send(self, method: str, params: dict = None) -> dict:
        self._id += 1
        msg = {"id": self._id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(msg))
        while True:
            resp = json.loads(await self.ws.recv())
            if resp.get("id") == self._id:
                if "error" in resp:
                    raise Exception(f"CDP error: {resp['error']}")
                return resp.get("result", {})

    async def evaluate(self, expression: str) -> any:
        """执行 JavaScript 并返回结果"""
        result = await self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
        })
        return result.get("result", {}).get("value")

    async def navigate(self, url: str):
        """导航到指定 URL"""
        await self.send("Page.navigate", {"url": url})
        await asyncio.sleep(2)
        print(f"[CDP] 已导航到: {url}")

    async def get_title(self) -> str:
        return await self.evaluate("document.title")

    async def get_text(self) -> str:
        """提取页面纯文本"""
        return await self.evaluate("document.body.innerText")

    async def query_text(self, selector: str) -> str:
        """用 CSS 选择器提取元素文本"""
        js = f"document.querySelector('{selector}')?.innerText || '未找到'"
        return await self.evaluate(js)

    async def click(self, selector: str):
        """用 CSS 选择器点击元素"""
        js = f"document.querySelector('{selector}')?.click()"
        await self.evaluate(js)
        print(f"[CDP] 已点击: {selector}")

    async def close(self):
        if self.ws:
            await self.ws.close()


async def get_tabs():
    """获取所有标签页"""
    import urllib.request
    resp = urllib.request.urlopen(f"{CDP_HTTP}/json")
    return json.loads(resp.read())


async def main():
    # 1. 列出所有标签页
    tabs = await get_tabs()
    print("=== 手机 Chrome 标签页 ===")
    for i, tab in enumerate(tabs):
        if tab["type"] == "page":
            print(f"  [{i}] {tab['title'][:40]}  ->  {tab['url'][:60]}")

    # 2. 连接第一个标签页
    page_tab = next(t for t in tabs if t["type"] == "page")
    cdp = ChromeCDP(page_tab["webSocketDebuggerUrl"])
    await cdp.connect()

    # 3. 获取当前页面标题
    title = await cdp.get_title()
    print(f"\n=== 当前页面: {title} ===")

    # 4. 导航到知乎创作者中心活动页
    await cdp.navigate("https://www.zhihu.com/creator/activity")
    title = await cdp.get_title()
    print(f"=== 导航后: {title} ===")

    # 5. 提取页面文本内容
    text = await cdp.get_text()
    print(f"\n=== 页面文本 (前 1000 字) ===")
    print(text[:1000] if text else "无内容")

    # 6. 用 JS 提取结构化数据示例
    activity_js = """
    (() => {
        const items = document.querySelectorAll('.ActivityCard, [class*="activity"], [class*="Activity"]');
        if (items.length === 0) return '未找到活动卡片元素，页面文本已在上方输出';
        return Array.from(items).map(el => el.innerText.trim()).join('\\n---\\n');
    })()
    """
    activities = await cdp.evaluate(activity_js)
    print(f"\n=== 活动卡片 ===")
    print(activities or "未匹配到特定选择器，参考上方页面文本")

    await cdp.close()
    print("\n[CDP] 连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
