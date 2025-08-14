"""
URL スパム検出プラグイン

短時間に複数のURLを含む投稿や、怪しいドメインのURLを検出し、
警告メッセージを投稿してモデレーターに通知する。

このプラグインはハッカソン参加者向けのサンプルとして、
以下の機能を実装している：
- 複数のフィルタ条件の組み合わせ
- 複数のアクションの実行
- 設定可能なパラメータの使用
- メタデータの活用
"""

import re
from typing import Dict, List
from datetime import datetime, timedelta
from lib.message_utils import clean_message_text, extract_mentions, is_bot_message


def check(message: Dict, context: Dict) -> bool:
    """
    URLスパムの可能性があるメッセージかチェック
    
    検出条件：
    1. メッセージに2個以上のURLが含まれている
    2. 怪しいドメインのURLが含まれている
    3. ボットメッセージは除外
    
    Args:
        message: Slackメッセージオブジェクト
        context: 追加のコンテキスト情報
    
    Returns:
        bool: スパムの可能性がある場合True
    """
    text = message.get("text", "")
    if not text:
        return False
    
    if is_bot_message(message):
        return False
    
    url_pattern = r'https?://[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    
    if len(urls) >= 2:
        return True
    
    suspicious_domains = [
        "bit.ly", "tinyurl.com", "t.co", "goo.gl",
        "ow.ly", "short.link", "tiny.cc", "is.gd",
        "clickhere.com", "freebie.com", "win-now.com"
    ]
    
    for url in urls:
        for domain in suspicious_domains:
            if domain in url:
                return True
    
    if urls:
        promotional_keywords = [
            "無料", "限定", "今すぐ", "クリック", "登録",
            "プレゼント", "当選", "特別価格", "お得"
        ]
        
        clean_text = clean_message_text(text)
        for keyword in promotional_keywords:
            if keyword in clean_text:
                return True
    
    return False


def action(message: Dict, context: Dict) -> Dict:
    """
    URLスパムに対するアクション
    
    実行内容：
    1. 元メッセージにスレッドで警告を投稿
    2. モデレーター用チャンネルに詳細レポートを送信
    3. メタデータでログ記録
    
    Args:
        message: Slackメッセージオブジェクト
        context: 追加のコンテキスト情報
    
    Returns:
        Dict: 実行するアクションの詳細
    """
    channel = message.get("channel")
    thread_ts = message.get("ts")
    user = message.get("user")
    text = message.get("text", "")
    
    url_pattern = r'https?://[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    
    warning_text = (
        f"<@{user}> さん、投稿内容を確認しています。\n"
        f"複数のURLまたは外部リンクが検出されました。\n"
        f"スパムではない場合は、この返信を無視してください。\n"
        f"コミュニティガイドライン: https://example.com/guidelines"
    )
    
    moderator_channel = context.get("moderator_channel", "C9876543210")
    channel_info = context.get("channel_info", {})
    channel_name = channel_info.get("name", "unknown")
    
    report_text = (
        f"🚨 **URL スパム検出レポート**\n\n"
        f"**ユーザー:** <@{user}>\n"
        f"**チャンネル:** #{channel_name} (<#{channel}>)\n"
        f"**検出URL数:** {len(urls)}\n"
        f"**検出URL:**\n"
    )
    
    for i, url in enumerate(urls[:5], 1):  # 最大5個まで表示
        report_text += f"  {i}. {url}\n"
    
    if len(urls) > 5:
        report_text += f"  ... 他 {len(urls) - 5} 個\n"
    
    report_text += (
        f"\n**元メッセージ:**\n"
        f"> {text[:200]}{'...' if len(text) > 200 else ''}\n\n"
        f"**アクション:** 警告メッセージを投稿しました\n"
        f"**タイムスタンプ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    return {
        "type": "multiple_actions",
        "actions": [
            {
                "type": "post_message",
                "channel": channel,
                "text": warning_text,
                "thread_ts": thread_ts
            },
            {
                "type": "post_message",
                "channel": moderator_channel,
                "text": report_text
            }
        ],
        "metadata": {
            "plugin": "url_spam_detection",
            "original_message_ts": thread_ts,
            "detected_user": user,
            "detected_urls": urls,
            "url_count": len(urls),
            "detection_time": datetime.now().isoformat(),
            "channel": channel,
            "action_type": "warning_and_report"
        }
    }
