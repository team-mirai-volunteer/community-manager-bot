"""
誹謗中傷検出プラグイン

メッセージが誹謗中傷的な内容を含んでいるかチェックし、
該当する場合は警告メッセージを返信する。
"""

from typing import Dict, Optional
from lib.message_utils import clean_message_text, contains_keywords


def check(message: Dict, context: Dict) -> bool:
    """
    メッセージが誹謗中傷的な内容を含んでいるかチェック
    
    Args:
        message: Slackメッセージオブジェクト
        context: 追加のコンテキスト情報（チャンネル情報など）
    
    Returns:
        bool: 誹謗中傷的な内容が検出された場合True
    """
    text = message.get("text", "")
    if not text:
        return False
    
    if message.get("subtype") == "bot_message" or "bot_id" in message:
        return False
    
    clean_text = clean_message_text(text)
    
    defamatory_keywords = [
        "バカ", "アホ", "死ね", "消えろ", "クズ", "ゴミ",
        "無能", "役立たず", "最低", "最悪", "うざい", "きもい"
    ]
    
    return contains_keywords(clean_text, defamatory_keywords, case_sensitive=False)


def action(message: Dict, context: Dict) -> Dict:
    """
    誹謗中傷的なメッセージに対するアクション
    
    Args:
        message: Slackメッセージオブジェクト
        context: 追加のコンテキスト情報
    
    Returns:
        Dict: 実行するアクションの詳細
    """
    channel = message.get("channel")
    thread_ts = message.get("ts")
    user = message.get("user")
    
    warning_text = (
        f"<@{user}> さん、投稿内容について確認させていただきます。\n"
        "コミュニティガイドラインに沿った建設的な議論をお願いします。\n"
        "詳細: https://example.com/community-guidelines"
    )
    
    return {
        "type": "post_message",
        "channel": channel,
        "text": warning_text,
        "thread_ts": thread_ts,
        "metadata": {
            "plugin": "defamatory_detection",
            "original_message_ts": thread_ts,
            "detected_user": user
        }
    }
