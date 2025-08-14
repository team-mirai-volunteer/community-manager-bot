"""
メッセージ処理のユーティリティ関数
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


def extract_mentions(text: str) -> List[str]:
    """メッセージからユーザーメンションを抽出"""
    pattern = r'<@([A-Z0-9]+)>'
    return re.findall(pattern, text)


def extract_channel_mentions(text: str) -> List[str]:
    """メッセージからチャンネルメンションを抽出"""
    pattern = r'<#([A-Z0-9]+)\|[^>]+>'
    return re.findall(pattern, text)


def is_bot_message(message: Dict) -> bool:
    """ボットからのメッセージかどうか判定"""
    return message.get("subtype") == "bot_message" or "bot_id" in message


def is_thread_reply(message: Dict) -> bool:
    """スレッドへの返信かどうか判定"""
    return "thread_ts" in message and message.get("thread_ts") != message.get("ts")


def get_message_timestamp(message: Dict) -> datetime:
    """メッセージのタイムスタンプをdatetimeオブジェクトに変換"""
    ts = float(message.get("ts", 0))
    return datetime.fromtimestamp(ts)


def format_user_mention(user_id: str) -> str:
    """ユーザーIDをメンション形式に変換"""
    return f"<@{user_id}>"


def format_channel_mention(channel_id: str, channel_name: str) -> str:
    """チャンネルIDをメンション形式に変換"""
    return f"<#{channel_id}|{channel_name}>"


def clean_message_text(text: str) -> str:
    """メッセージテキストをクリーンアップ（メンション除去など）"""
    text = re.sub(r'<@[A-Z0-9]+>', '', text)
    text = re.sub(r'<#[A-Z0-9]+\|[^>]+>', '', text)
    text = re.sub(r'<https?://[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def contains_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> bool:
    """テキストに指定されたキーワードが含まれているかチェック"""
    if not case_sensitive:
        text = text.lower()
        keywords = [kw.lower() for kw in keywords]
    
    return any(keyword in text for keyword in keywords)
