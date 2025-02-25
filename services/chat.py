from langchain.schema import HumanMessage, SystemMessage
from deepseek_llm import DeepSeekChat
from dotenv import load_dotenv
from google_search import create_google_search_tool
from prompts import searcher_system_prompt_cn
from utils.logger import setup_logger
from utils.database import Database
from models.search_result import SearchResult
import os

# 设置日志
logger = setup_logger('chat')

# 全局变量
chat = None
search_tool = None
db = None

def init_services():
    global chat, search_tool, db
    
    # 加载环境变量
    load_dotenv()
    
    # 初始化数据库连接
    db = Database("postgresql+psycopg2://neondb_owner:npg_wgixrLkJB31N@ep-wandering-dawn-a8c402vl-pooler.eastus2.azure.neon.tech/neondb?sslmode=require")
    db.init_database()
    
    # 初始化 DeepSeek Chat 和 Google 搜索
    chat = DeepSeekChat(api_key=os.getenv("DEEPSEEK_API_KEY"))
    search_tool = create_google_search_tool()

def search_and_respond(query):
    global chat, search_tool, db
    if not all([chat, search_tool, db]):
        init_services()
    
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
    
    # 保存结果到数据库
    try:
        db.save_search_results(query, final_results)
        logger.info("搜索结果已保存到数据库")
    except Exception as e:
        logger.error(f"保存到数据库失败: {str(e)}")
    
    return final_results

if __name__ == "__main__":
    init_services()
    try:
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
    finally:
        # 确保关闭数据库连接
        db.close()