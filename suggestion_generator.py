from langchain.schema import HumanMessage, SystemMessage
from deepseek_llm import DeepSeekChat
from google_search import create_google_search_tool
from prompts import suggestion_generator_prompt
from utils.logger import setup_logger
import re

logger = setup_logger('suggestion_generator')

def extract_suggestions(text):
    """从文本中提取建议"""
    pattern = r'<suggestions>(.*?)</suggestions>'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        suggestions = [s.strip() for s in match.group(1).strip().split('\n') if s.strip()]
        return suggestions
    return []

def generate_suggestions_with_search(chat_history, chat_model, search_tool):
    """生成建议并进行搜索"""
    logger.info("开始生成建议...")
    
    # 生成建议
    messages = [
        SystemMessage(content="You are a helpful suggestion generator."),
        HumanMessage(content=suggestion_generator_prompt.format(chat_history=chat_history))
    ]
    
    response = chat_model.invoke(messages)
    suggestions = extract_suggestions(response.content)
    logger.info(f"生成了 {len(suggestions)} 个建议")
    
    # 为每个建议进行搜索
    enriched_suggestions = []
    for suggestion in suggestions:
        logger.info(f"正在搜索建议: {suggestion}")
        search_result = search_tool.run(suggestion)
        enriched_suggestions.append({
            'suggestion': suggestion,
            'search_result': search_result
        })
    
    return enriched_suggestions