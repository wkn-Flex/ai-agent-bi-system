# -*- coding: utf-8 -*-
"""
LLM调用封装：支持DeepSeek/Qwen/OpenAI
"""
from openai import OpenAI
from config import LLM_PROVIDER, DEEPSEEK_CONFIG, QWEN_CONFIG, OPENAI_CONFIG


class LLMClient:
    def __init__(self):
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
        self.client = OpenAI(api_key=cfg['api_key'], base_url=cfg['base_url'])

    def chat(self, system_prompt, user_prompt):
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


_llm_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient()
    return _llm_instance
