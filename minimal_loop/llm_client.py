# -*- coding: utf-8 -*-
"""
LLM调用封装模块
支持DeepSeek、通义千问、OpenAI三种API（均使用OpenAI兼容格式）
"""
from openai import OpenAI
from config import LLM_PROVIDER, DEEPSEEK_CONFIG, QWEN_CONFIG, OPENAI_CONFIG


class LLMClient:
    """LLM客户端，统一封装不同提供商的API调用"""

    def __init__(self):
        # 根据配置选择提供商
        if LLM_PROVIDER == 'deepseek':
            cfg = DEEPSEEK_CONFIG
        elif LLM_PROVIDER == 'qwen':
            cfg = QWEN_CONFIG
        elif LLM_PROVIDER == 'openai':
            cfg = OPENAI_CONFIG
        else:
            raise ValueError(f'不支持的LLM提供商: {LLM_PROVIDER}')

        self.model = cfg['model']
        self.temperature = cfg['temperature']
        self.max_tokens = cfg['max_tokens']

        # 初始化OpenAI兼容客户端
        self.client = OpenAI(
            api_key=cfg['api_key'],
            base_url=cfg['base_url'],
        )

        print(f'[LLM] 初始化成功: provider={LLM_PROVIDER}, model={self.model}')

    def chat(self, system_prompt, user_prompt):
        """
        发送聊天请求，返回LLM的文本回复

        Args:
            system_prompt: 系统提示词（角色设定+任务描述）
            user_prompt: 用户提示词（具体问题+上下文）

        Returns:
            str: LLM生成的文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content.strip()

    def chat_with_history(self, messages):
        """
        带历史对话的聊天请求（用于self-correction等多轮场景）

        Args:
            messages: 消息列表，格式 [{'role': 'system'/'user'/'assistant', 'content': '...'}, ...]

        Returns:
            str: LLM生成的文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content.strip()


# 单例模式，全局共享一个LLM客户端实例
_llm_instance = None

def get_llm():
    """获取LLM客户端单例"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient()
    return _llm_instance
