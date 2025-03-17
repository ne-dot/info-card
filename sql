

-- 启用UUID生成函数（MySQL示例）
SET GLOBAL log_bin_trust_function_creators = 1;
CREATE FUNCTION uuid_v7() RETURNS CHAR(36)
BEGIN
  SET @hex = HEX(UNHEX(CONCAT(
    LPAD(HEX(FLOOR(UNIX_TIMESTAMP(CURTIME(6)) / 1000)), 8, '0'),
    LPAD(HEX(MICROSECOND(CURTIME(6))), 5, '0'),
    LPAD(HEX(FLOOR(RAND() * 0xFFFF)), 4, '0'),
    LPAD(HEX(FLOOR(RAND() * 0xFFFF)), 4, '0'),
    LPAD(HEX(FLOOR(RAND() * 0xFFFFFFFF)), 8, '0')
  )));
  RETURN LOWER(CONCAT(
    SUBSTR(@hex, 1, 8), '-',
    SUBSTR(@hex, 9, 4), '-7',
    SUBSTR(@hex, 13, 3), '-',
    CONV(SUBSTR(@hex, 16, 1), 16, 10) & 0x3 | 0x8,
    SUBSTR(@hex, 17, 3), '-',
    SUBSTR(@hex, 20, 12)
  ));
END

CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT '用户唯一标识',
    -- 身份验证系统
    auth_type ENUM('email', 'anonymous', 'mobile', 'google', 'apple') NOT NULL DEFAULT 'anonymous',
    auth_id VARCHAR(255) COMMENT '第三方ID/手机号/匿名UUID',
    -- 认证补充字段
    mobile VARCHAR(20) GENERATED ALWAYS AS (
        CASE WHEN auth_type = 'mobile' THEN auth_id ELSE NULL END
    ) STORED UNIQUE COMMENT '手机号（仅mobile类型有效）',
    email VARCHAR(100) GENERATED ALWAYS AS (
        CASE WHEN auth_type = 'email' THEN auth_id ELSE NULL END
    ) STORED UNIQUE COMMENT '邮箱（仅email类型有效）',
    -- 安全信息
    password_hash VARCHAR(255) COMMENT '密码哈希（可选）',
    is_mobile_verified BOOLEAN DEFAULT FALSE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    -- 基础信息
    username VARCHAR(50) COMMENT '可编辑昵称',
    avatar_url VARCHAR(255),
    -- 时间信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    -- 状态管理
    account_status ENUM('active', 'locked', 'deleted') DEFAULT 'active',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '软删除标记',
    -- 索引
    UNIQUE INDEX uniq_auth (auth_type, auth_id),
    INDEX idx_mobile (mobile),
    INDEX idx_global_id (auth_id)
) COMMENT='统一用户身份系统';

-- 第三方登录详情表（扩展存储）
CREATE TABLE user_external_auths (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT,
    user_id INT UNSIGNED NOT NULL,
    provider ENUM('google', 'apple') NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    access_token VARCHAR(500) NOT NULL,
    refresh_token VARCHAR(500),
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE INDEX uniq_provider_user (provider, provider_user_id)
) COMMENT='第三方登录详情';

-- AI Agent核心表
CREATE TABLE ai_agents (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT,
    user_id INT UNSIGNED NOT NULL COMMENT '创建者',
    name VARCHAR(100) NOT NULL,
    description TEXT,
    -- 基础配置
    base_model VARCHAR(50) NOT NULL COMMENT '主模型标识',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens SMALLINT UNSIGNED DEFAULT 1000,
    -- 业务属性
    pricing DECIMAL(10,2) NOT NULL COMMENT '单价/月',
    visibility ENUM('public', 'private', 'organization') DEFAULT 'public',
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    -- 审计字段
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT(1) DEFAULT 0,
    -- 关联
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_creator (user_id),
    INDEX idx_public_agents (visibility, status)
) COMMENT='AI Agent核心配置';

-- Agent多模型配置表
CREATE TABLE agent_model_configs (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT,
    agent_id INT UNSIGNED NOT NULL,
    model_name VARCHAR(50) NOT NULL COMMENT '如gpt-4-turbo',
    weight DECIMAL(3,2) DEFAULT 1.0 COMMENT '流量分配权重',
    priority TINYINT UNSIGNED DEFAULT 1 COMMENT '降级优先级',
    is_enabled TINYINT(1) DEFAULT 1,
    config JSON COMMENT '模型特有参数',
    FOREIGN KEY (agent_id) REFERENCES ai_agents(id) ON DELETE CASCADE,
    INDEX idx_agent_models (agent_id, priority)
) COMMENT='Agent多模型配置';

-- Agent工具配置表
CREATE TABLE agent_tools (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT,
    agent_id INT UNSIGNED NOT NULL,
    tool_type VARCHAR(50) NOT NULL COMMENT '功能类型',
    config JSON NOT NULL COMMENT '工具配置',
    execution_order TINYINT UNSIGNED DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    FOREIGN KEY (agent_id) REFERENCES ai_agents(id) ON DELETE CASCADE,
    INDEX idx_tool_priority (agent_id, execution_order)
) COMMENT='Agent工具配置';

-- Agent提示词版本表
CREATE TABLE agent_prompts (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT,
    agent_id INT UNSIGNED NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    content TEXT NOT NULL COMMENT 'prompt模板内容',
    variables JSON COMMENT '可注入变量配置',
    is_production TINYINT(1) DEFAULT 0 COMMENT '是否生产环境',
    creator_id INT UNSIGNED NOT NULL COMMENT '修改者',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES ai_agents(id) ON DELETE CASCADE,
    FOREIGN KEY (creator_id) REFERENCES users(user_id),
    UNIQUE INDEX uniq_agent_version (agent_id, version)
) COMMENT='Prompt版本管理';

-- 用户订阅表
CREATE TABLE subscriptions (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT,
    user_id INT UNSIGNED NOT NULL,
    agent_id INT UNSIGNED NOT NULL,
    start_date DATE NOT NULL COMMENT '订阅起始日期',
    end_date DATE NOT NULL COMMENT '订阅结束日期',
    payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
    status ENUM('active', 'expired', 'cancelled') DEFAULT 'active',
    price DECIMAL(10,2) NOT NULL COMMENT '订阅时价格快照',
    renewal_count SMALLINT UNSIGNED DEFAULT 0 COMMENT '续订次数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted TINYINT(1) DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES ai_agents(id) ON DELETE CASCADE,
    INDEX idx_user_agent (user_id, agent_id),
    INDEX idx_expiry (end_date)
) COMMENT='用户订阅关系';


-- 1. Agent调用记录表（核心交互日志）
CREATE TABLE agent_invocations (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT '有序UUIDv7',
    user_id CHAR(36) NOT NULL COMMENT '触发用户',
    agent_id CHAR(36) NOT NULL COMMENT '调用的Agent',
    session_id CHAR(36) GENERATED ALWAYS AS (
        CASE WHEN input_params->"$.session_id" IS NOT NULL 
        THEN input_params->"$.session_id" 
        ELSE id END
    ) STORED COMMENT '会话ID（自动生成）',
    input_text TEXT NOT NULL,
    input_params JSON COMMENT '扩展参数',
    status ENUM('pending','processing','success','failed') DEFAULT 'pending',
    timestamps JSON NOT NULL COMMENT '{
        "start": "2024-03-20T12:34:56.789Z",
        "end": "2024-03-20T12:35:01.123Z"
    }',
    metrics JSON COMMENT '{
        "cost_time": 4321,
        "token_usage": {"total":1500,"prompt":300},
        "api_calls": 3
    }',
    error_logs JSON,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    INDEX idx_agent_user (agent_id, user_id),
    INDEX idx_time_range ( (CAST(timestamps->"$.start" AS DATETIME(6))) )
) COMMENT='Agent调用记录表' ROW_FORMAT=COMPRESSED;

-- 2. AI总结结果表（加工后数据）
CREATE TABLE ai_summaries (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT '有序UUIDv7',
    invocation_id CHAR(36) NOT NULL UNIQUE,
    content LONGTEXT NOT NULL,
    metadata JSON NOT NULL COMMENT '{
        "model": "gpt-4-1106",
        "quality_score": 0.87,
        "revision_history": ["v1","v2"]
    }',
    version_chain JSON COMMENT '版本链结构',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FULLTEXT INDEX ft_content (content) WITH PARSER ngram,
    CONSTRAINT fk_invocation
        FOREIGN KEY (invocation_id) 
        REFERENCES agent_invocations(id)
        ON DELETE CASCADE
) COMMENT='AI生成总结表' ROW_FORMAT=COMPRESSED;

-- 3. 搜索引擎原始数据表（第三方数据存档）
CREATE TABLE search_raw_data (
    id CHAR(36) PRIMARY KEY DEFAULT uuid_v7() COMMENT '有序UUIDv7',
    invocation_id CHAR(36) NOT NULL,
    engine_type VARCHAR(20) NOT NULL COMMENT 'google/bing等',
    request JSON NOT NULL COMMENT '{
        "query": "最新AI进展",
        "params": {"num":10,"lang":"zh-CN"}
    }',
    response LONGBLOB NOT NULL COMMENT '压缩后的原始响应',
    structured_data JSON COMMENT '结构化结果',
    cache_info JSON COMMENT '{
        "key": "cache_key",
        "hit": true,
        "ttl": 3600
    }',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    SPATIAL INDEX idx_geo ( (structured_data->"$.location") ),
    CONSTRAINT fk_search_invocation
        FOREIGN KEY (invocation_id) 
        REFERENCES agent_invocations(id)
        ON DELETE CASCADE
) COMMENT='搜索引擎数据表' 
ROW_FORMAT=COMPRESSED
KEY_BLOCK_SIZE=8;

-- 1. RSS订阅源表（支持多用户共享源）
CREATE TABLE rss_feeds (
    id CHAR(36) PRIMARY KEY COMMENT 'UUIDv7',
    feed_url VARCHAR(512) NOT NULL UNIQUE COMMENT 'RSS源地址',
    title VARCHAR(255) NOT NULL COMMENT '源标题',
    category ENUM('news', 'sports', 'tech', 'custom') DEFAULT 'news',
    language CHAR(2) DEFAULT 'zh' COMMENT 'ISO语言代码',
    etag VARCHAR(128) COMMENT 'HTTP缓存标识',
    last_modified DATETIME(6) COMMENT '最后更新时间戳',
    health_status JSON COMMENT '{
        "failure_count": 0,
        "last_success": "2024-03-20T09:00:00Z",
        "avg_interval": 3600
    }',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    INDEX idx_category_lang (category, language),
    INDEX idx_health_status ( (CAST(health_status->"$.failure_count" AS UNSIGNED)) )
) COMMENT='RSS订阅源库' ROW_FORMAT=COMPRESSED;


-- 2. RSS内容条目表（原子数据存储）
CREATE TABLE rss_entries (
    id CHAR(36) PRIMARY KEY,
    feed_id CHAR(36) NOT NULL,
    guid VARCHAR(512) NOT NULL COMMENT '条目唯一标识',
    title VARCHAR(1024) NOT NULL,
    content LONGTEXT COMMENT '完整内容（清洗后HTML）',
    summary TEXT COMMENT 'AI生成摘要',
    raw_data JSON COMMENT '原始元数据',
    links JSON COMMENT '{
        "alternate": "https://...",
        "image": "https://..."
    }',
    published_at DATETIME(6) NOT NULL COMMENT '条目发布时间',
    processed_at DATETIME(6) COMMENT '被Agent处理时间',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    FULLTEXT INDEX ft_content (title, content) WITH PARSER ngram,
    UNIQUE INDEX uniq_feed_entry (feed_id, guid),
    FOREIGN KEY (feed_id) REFERENCES rss_feeds(id) ON DELETE CASCADE
) COMMENT='RSS内容条目' ROW_FORMAT=COMPRESSED;


-- Agent-RSS订阅关联表（多对多）
CREATE TABLE agent_rss_feeds (
    id CHAR(36) PRIMARY KEY,
    agent_id CHAR(36) NOT NULL,
    feed_id CHAR(36) NOT NULL,
    custom_filter JSON COMMENT 'Agent专属过滤规则',
    priority TINYINT DEFAULT 1,
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    UNIQUE INDEX uniq_agent_feed (agent_id, feed_id),
    FOREIGN KEY (agent_id) REFERENCES ai_agents(id) ON DELETE CASCADE,
    FOREIGN KEY (feed_id) REFERENCES rss_feeds(id) ON DELETE CASCADE
) COMMENT='Agent与RSS源关联表';

-- 优化后的处理流水表（关联用户订阅）
CREATE TABLE agent_rss_processes (
    id CHAR(36) PRIMARY KEY,
    subscription_id CHAR(36) NOT NULL COMMENT '用户订阅记录',
    entry_id CHAR(36) NOT NULL COMMENT '处理的条目',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    process_chain JSON COMMENT '{
        "steps": ["fetch", "filter", "summarize"],
        "current_step": 2
    }',
    created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
    processed_at DATETIME(6),
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE,
    FOREIGN KEY (entry_id) REFERENCES rss_entries(id) ON DELETE CASCADE
) COMMENT='Agent处理流水表';