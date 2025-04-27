# -*- coding: utf-8 -*-
# @Time    : 2024/8/21 17:56
# @Author  : nongbin
# @FileName: bot.py
# @Software: PyCharm
# @Affiliation: tfswufe.edu.cn
from typing import Literal, TypeAlias, List

from config.config import Config
# from lang_chain.poetry_game import GameMode, PoetryGame
from QA.custom_tool_calling.interaction import chat_libai as chat_libai_by_custom_agent
# from QA.supported_tool_calling.interaction import chat_libai as chat_libai_by_supported_agent
from utils.singleton import Singleton

Parser: TypeAlias = Literal['custom']


class ChatBot(object, metaclass=Singleton):
    """
    聊天机器人,供gradio调用
    """

    def __init__(self):
        self.question_parser: Parser = (
            Config.get_instance().get_with_nested_params("lang-chain", "question_parse"))
        self.game_mode = None

    def chat(self,
             message: str,
             history: List[List[str] | None] | None = None,
             ):


        if self.question_parser == 'custom':
            yield from chat_libai_by_custom_agent(message, history)



        else:
            raise ValueError(f"{self.question_parser} is not supported for question parser")
