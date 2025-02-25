from langchain.schema import HumanMessage, SystemMessage
from deepseek_llm import DeepSeekChat
from dotenv import load_dotenv
from google_search import create_google_search_tool
from prompts import searcher_system_prompt_cn
from utils.logger import setup_logger
import os
from suggestion_generator import generate_suggestions_with_search

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
    search_result = search_tool.run(query)
    
    # 创建消息列表
    tool_info = f"- Google Search: {search_tool.description}"
    system_prompt = searcher_system_prompt_cn.format(tool_info=tool_info)
    
    logger.info("构建系统提示和对话消息")
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"搜索结果：{search_result}\n\n当前问题：{query}")
    ]
    
    # 获取响应
    logger.info("开始调用 AI 模型生成回答")
    response = chat.invoke(messages)
    
    # 生成相关建议
    logger.info("正在生成相关建议...")
    suggestions = generate_suggestions_with_search(
        chat_history=f"Question: {query}\nAnswer: {response.content}",
        chat_model=chat,
        search_tool=search_tool
    )
    
    # 格式化输出
    result = {
        'answer': response.content,
        'suggestions': suggestions
    }
    
    return result

if __name__ == "__main__":
    query = "最新的量子计算机研究进展"
    result = search_and_respond(query)
    print("\n=== 主要回答 ===")
    print(result['answer'])
    print("\n=== 相关建议 ===")
    for item in result['suggestions']:
        print(f"\n建议: {item['suggestion']}")
        print(f"搜索结果: {item['search_result'][:200]}...")