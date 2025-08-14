"""
運営チャンネル監視プラグイン

運営専用チャンネルに運営以外のユーザーが投稿した場合、
雑談チャンネルに転載して元メッセージを削除する。
"""

from typing import Dict, Optional
from lib.message_utils import format_user_mention


def check(message: Dict, context: Dict) -> bool:
    """
    運営チャンネルに運営以外が投稿したかチェック
    
    Args:
        message: Slackメッセージオブジェクト
        context: 追加のコンテキスト情報（チャンネル情報など）
    
    Returns:
        bool: 運営以外の投稿が検出された場合True
    """
    if message.get("subtype") == "bot_message" or "bot_id" in message:
        return False
    
    channel_info = context.get("channel_info", {})
    channel_name = channel_info.get("name", "")
    
    admin_channel_patterns = ["運営", "admin", "staff", "管理"]
    is_admin_channel = any(pattern in channel_name for pattern in admin_channel_patterns)
    
    if not is_admin_channel:
        return False
    
    user_id = message.get("user")
    admin_users = context.get("admin_users", [])
    
    return user_id not in admin_users


def action(message: Dict, context: Dict) -> Dict:
    """
    運営チャンネルの不適切な投稿に対するアクション
    
    Args:
        message: Slackメッセージオブジェクト
        context: 追加のコンテキスト情報
    
    Returns:
        Dict: 実行するアクションの詳細
    """
    user_id = message.get("user")
    original_text = message.get("text", "")
    original_channel = message.get("channel")
    original_ts = message.get("ts")
    
    channel_info = context.get("channel_info", {})
    channel_name = channel_info.get("name", "unknown")
    
    transfer_text = (
        f"📝 {format_user_mention(user_id)} さんからの投稿を #{channel_name} から移動しました:\n\n"
        f"> {original_text}\n\n"
        f"運営チャンネルへの投稿は運営メンバーのみとなっております。"
    )
    
    return {
        "type": "multiple_actions",
        "actions": [
            {
                "type": "post_message",
                "channel": "C1234567890",  # 雑談チャンネルのID（設定で管理）
                "text": transfer_text
            },
            {
                "type": "delete_message",
                "channel": original_channel,
                "ts": original_ts
            },
            {
                "type": "post_message",
                "channel": original_channel,
                "text": f"{format_user_mention(user_id)} さん、こちらは運営専用チャンネルです。投稿内容を雑談チャンネルに移動させていただきました。"
            }
        ],
        "metadata": {
            "plugin": "admin_channel_guard",
            "original_message_ts": original_ts,
            "transferred_user": user_id,
            "original_channel": original_channel
        }
    }
