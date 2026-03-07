import asyncio
import sys
import io
from dotenv import load_dotenv
from browser_use import Agent, BrowserSession, BrowserProfile, ChatGoogle

# 修复 Windows GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

load_dotenv()

browser = BrowserSession(
    browser_profile=BrowserProfile(
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )
)

llm = ChatGoogle(model="gemini-2.5-flash")


async def main():
    agent = Agent(
        task="去知乎创作者中心(https://www.zhihu.com/creator)，找到创作活动页面，汇总所有正在进行的活动信息，包括活动名称、时间、奖励等",
        llm=llm,
        browser=browser,
    )
    result = await agent.run()
    print("\n===== 结果 =====")
    print(result)


asyncio.run(main())
