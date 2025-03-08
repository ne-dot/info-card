from typing import Dict, Optional
import json
import os
from utils.logger import setup_logger

logger = setup_logger('i18n_utils')

# 支持的语言列表
SUPPORTED_LANGUAGES = ['zh', 'en']
DEFAULT_LANGUAGE = 'en'

# 语言文件缓存
_translations: Dict[str, Dict[str, str]] = {}

def load_translations():
    """加载所有语言的翻译文件"""
    global _translations
    
    i18n_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'i18n')
    if not os.path.exists(i18n_dir):
        os.makedirs(i18n_dir)
        
    for lang in SUPPORTED_LANGUAGES:
        lang_file = os.path.join(i18n_dir, f'{lang}.json')
        
        # 如果语言文件不存在，创建一个空的
        if not os.path.exists(lang_file):
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        
        try:
            with open(lang_file, 'r', encoding='utf-8') as f:
                _translations[lang] = json.load(f)
            logger.info(f"已加载语言文件: {lang}")
        except Exception as e:
            logger.error(f"加载语言文件失败 {lang}: {str(e)}")
            _translations[lang] = {}

def get_text(key: str, lang: Optional[str] = None) -> str:
    """获取指定语言的文本"""
    if not _translations:
        load_translations()
    
    # 如果未指定语言或语言不支持，使用默认语言
    if not lang or lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    
    # 尝试获取翻译，如果不存在则返回键名
    return _translations.get(lang, {}).get(key, key)

def set_text(key: str, value: str, lang: str):
    """设置指定语言的文本"""
    if not _translations:
        load_translations()
    
    if lang not in SUPPORTED_LANGUAGES:
        logger.warning(f"不支持的语言: {lang}")
        return False
    
    _translations[lang][key] = value
    
    # 保存到文件
    i18n_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'i18n')
    lang_file = os.path.join(i18n_dir, f'{lang}.json')
    
    try:
        with open(lang_file, 'w', encoding='utf-8') as f:
            json.dump(_translations[lang], f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存语言文件失败 {lang}: {str(e)}")
        return False

# 初始化时加载翻译
load_translations()