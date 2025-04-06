from fastapi import APIRouter, Depends, Request
from utils.logger import setup_logger
from utils.response_utils import success_response, error_response, ErrorCode
from dependencies.auth import get_current_user
from models.user import UserResponse
from models.suggestion import SuggestionGenerateRequest
from dao.agent_dao import AgentDAO
from dao.suggestion_dao import SuggestionDAO

logger = setup_logger('suggestion_controller')
router = APIRouter(tags=["建议"], include_in_schema=True)

# 全局变量存储DAO实例
agent_dao = None
suggestion_dao = None

def init_controller(db):
    """初始化控制器，设置全局DAO实例"""
    global agent_dao, suggestion_dao
    agent_dao = AgentDAO(db)
    suggestion_dao = SuggestionDAO(db)
    logger.info("建议控制器初始化完成")

@router.post("/suggestions/generate")
async def generate_suggestions(
    request_data: SuggestionGenerateRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """生成AI查询建议"""
    try:
        # 获取agent服务
        agent_service = request.app.state.agent_service
        
        # 获取语言设置
        lang = request.state.lang if hasattr(request.state, 'lang') else 'zh'
        
        # 从请求模型中获取参数
        query = request_data.query
        agent_id = request_data.agent_id
        
        # 如果没有提供agent_id，则查找name='建议agent'的agent
        if not agent_id:
            suggestion_agent = agent_dao.get_agent_by_name('建议agent')
            if not suggestion_agent:
                return error_response("未找到建议agent，请先创建", ErrorCode.NOT_FOUND)
            agent_id = suggestion_agent.key_id
        
        # 触发agent获取建议
        result = await agent_service.trigger_agent(
            agent_id=agent_id,
            user_id=current_user.user_id,
            lang=lang,
            query=query
        )
        
        # 返回结果
        return success_response(result)
    except Exception as e:
        logger.error(f"生成建议失败: {str(e)}")
        return error_response(f"生成建议失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

@router.get("/suggestions")
async def get_suggestions(
    agent_id: str = None,
    language: str = None,
    limit: int = 5,
    request: Request = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取建议列表"""
    try:
        # 如果没有提供agent_id，则查找name='建议agent'的agent
        if not agent_id:
            suggestion_agent = agent_dao.get_agent_by_name('建议agent')
            if suggestion_agent:
                agent_id = suggestion_agent.key_id
        
        # 获取语言设置
        if not language:
            language = request.state.lang if hasattr(request.state, 'lang') else 'zh'
        
        # 获取建议列表
        suggestions = await suggestion_dao.get_suggestions_by_agent(
            agent_id=agent_id,
            user_id=current_user.user_id,
            language=language,
            limit=limit
        )
        
        # 格式化建议列表
        suggestion_list = []
        for suggestion in suggestions:
            suggestion_list.append({
                'id': suggestion.id,
                'content': suggestion.content,
                'context': suggestion.context,
                'language': suggestion.language,
                'created_at': suggestion.created_at
            })
        
        # 返回结果
        return success_response(suggestion_list)
    except Exception as e:
        logger.error(f"获取建议列表失败: {str(e)}")
        return error_response(f"获取建议列表失败: {str(e)}", ErrorCode.UNKNOWN_ERROR)

def _parse_suggestions(result: str):
    """解析AI生成的推荐问题
    
    Args:
        result: AI生成的回复
        
    Returns:
        List[str]: 推荐问题列表
    """
    import json
    import re
    
    try:
        # 确保result是字符串
        if not isinstance(result, str):
            result = str(result)
        
        # 尝试解析JSON字符串
        try:
            data = json.loads(result)
            
            # 如果JSON中包含suggestions字段
            if isinstance(data, dict) and 'suggestions' in data and isinstance(data['suggestions'], list):
                suggestions = []
                for item in data['suggestions']:
                    if isinstance(item, str) and 3 <= len(item) <= 200:
                        suggestions.append(item)
                
                return suggestions
            else:
                # 尝试从其他可能的字段中提取建议
                for key in ['questions', 'recommendations', 'follow_up', 'follow_up_questions']:
                    if key in data and isinstance(data[key], list):
                        suggestions = []
                        for item in data[key]:
                            if isinstance(item, str) and 3 <= len(item) <= 200:
                                suggestions.append(item)
                        
                        if suggestions:
                            return suggestions
        except json.JSONDecodeError:
            # 如果不是有效的JSON，尝试从文本中提取问题
            logger.info("AI回复不是有效的JSON格式，尝试从文本中提取问题")
        
        # 如果不是JSON或没有找到有效的建议，尝试从文本中提取问题
        lines = result.strip().split('\n')
        suggestions = []
        
        for line in lines:
            # 尝试匹配常见的列表格式
            line = line.strip()
            if not line:
                continue
            
            # 匹配数字编号的列表项
            if re.match(r'^\d+[\.\)]\s*', line):
                question = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
                if 3 <= len(question) <= 200:
                    suggestions.append(question)
            # 匹配破折号或星号开头的列表项
            elif re.match(r'^[-*]\s*', line):
                question = re.sub(r'^[-*]\s*', '', line).strip()
                if 3 <= len(question) <= 200:
                    suggestions.append(question)
            # 匹配引号包围的问题
            elif re.match(r'^["\']', line) and re.search(r'["\']$', line):
                question = line.strip('"\'').strip()
                if 3 <= len(question) <= 200:
                    suggestions.append(question)
            # 匹配问号结尾的行
            elif line.endswith('?'):
                if 3 <= len(line) <= 200:
                    suggestions.append(line)
        
        # 如果找到了建议，返回它们
        if suggestions:
            return suggestions
        
        # 如果仍然没有找到建议，将整个结果作为一个建议返回
        if 3 <= len(result.strip()) <= 200:
            return [result.strip()]
        
        # 如果结果太长，将其分割成多个建议
        sentences = re.split(r'[.!?]', result)
        suggestions = []
        for sentence in sentences:
            sentence = sentence.strip()
            if 3 <= len(sentence) <= 200:
                suggestions.append(sentence)
        
        return suggestions
            
    except Exception as e:
        logger.error(f"解析推荐问题失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # 如果解析失败，返回原始结果
        return [result] 