from langchain.schema import HumanMessage, SystemMessage
from deepseek_llm import DeepSeekChat
from dotenv import load_dotenv
from google_search import create_google_search_tool
from prompts import searcher_system_prompt_cn
from utils.logger import setup_logger
from models.search_result import SearchResult
import os

# 设置日志
logger = setup_logger('chat')

# 加载环境变量
load_dotenv()

# 初始化 DeepSeek Chat 和 Google 搜索
chat = DeepSeekChat(api_key=os.getenv("DEEPSEEK_API_KEY"))
search_tool = create_google_search_tool()

def search_and_respond(query):
    logger.info(f"接收到查询请求: {query}")
    
    # 执行 Google 搜索
    search_results = search_tool.run(query)
    
    # 将搜索结果转换为文本摘要
    search_summary = "\n".join([
        f"- {result['title']}\n  摘要: {result['snippet']}\n  来源: {result['link']}"
        for result in search_results
    ])
    
    # 创建消息列表
    tool_info = f"- Google Search: {search_tool.description}"
    system_prompt = searcher_system_prompt_cn.format(tool_info=tool_info)
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"搜索结果：{search_summary}\n\n当前问题：{query}")
    ]
    
    # 获取 GPT 响应
    gpt_response = chat.invoke(messages)
    
    # 构建最终返回结果
    final_results = []
    
    # 添加 GPT 响应结果
    final_results.append(SearchResult.from_gpt_response(gpt_response.content))
    
    # 添加 Google 搜索结果
    for result in search_results:
        final_results.append(SearchResult.from_google_result(result))
    
    return final_results

if __name__ == "__main__":
    query = "最新的量子计算机研究进展"
    results = search_and_respond(query)
    
    print("\n=== GPT 总结 ===")
    gpt_result = next(r for r in results if r.content is not None)
    print(f"ID: {gpt_result.id}")
    print(f"标题: {gpt_result.title}")
    print(f"内容: {gpt_result.content}")
    print(f"时间: {gpt_result.date}")
    
    print("\n=== Google 搜索结果 ===")
    google_results = [r for r in results if r.content is None]
    for result in google_results:
        print(f"\nID: {result.id}")
        print(f"标题: {result.title}")
        print(f"摘要: {result.snippet}")
        print(f"来源: {result.link}")
        print(f"时间: {result.date}")
        print("-" * 50)