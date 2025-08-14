"""
プラグインのテスト実行スクリプト

各プラグインの動作を個別にテストできる。
実際のSlack APIを呼び出さずに、プラグインのロジックのみをテスト。
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent))

from plugins.defamatory_detection.plugin import check as defamatory_check, action as defamatory_action
from plugins.admin_channel_guard.plugin import check as admin_check, action as admin_action
from plugins.url_spam_detection.plugin import check as url_spam_check, action as url_spam_action


def test_defamatory_detection():
    """誹謗中傷検出プラグインのテスト"""
    print("=== 誹謗中傷検出プラグイン テスト ===")
    
    message1 = {
        "text": "あいつは本当にバカだな",
        "user": "U123456789",
        "channel": "C123456789",
        "ts": "1234567890.123456"
    }
    context1 = {}
    
    result1 = defamatory_check(message1, context1)
    print(f"テスト1 - 誹謗中傷メッセージ: {result1} (期待値: True)")
    
    if result1:
        action_result1 = defamatory_action(message1, context1)
        print(f"アクション結果: {action_result1['type']}")
        print(f"警告メッセージ: {action_result1['text'][:50]}...")
    
    message2 = {
        "text": "今日はいい天気ですね",
        "user": "U123456789",
        "channel": "C123456789",
        "ts": "1234567890.123456"
    }
    
    result2 = defamatory_check(message2, context1)
    print(f"テスト2 - 正常メッセージ: {result2} (期待値: False)")
    print()


def test_admin_channel_guard():
    """運営チャンネル監視プラグインのテスト"""
    print("=== 運営チャンネル監視プラグイン テスト ===")
    
    message1 = {
        "text": "質問があります",
        "user": "U987654321",  # 一般ユーザー
        "channel": "C123456789",
        "ts": "1234567890.123456"
    }
    context1 = {
        "channel_info": {"name": "運営-announcements"},
        "admin_users": ["U111111111", "U222222222"]  # 運営ユーザーリスト
    }
    
    result1 = admin_check(message1, context1)
    print(f"テスト1 - 運営チャンネルに一般ユーザー投稿: {result1} (期待値: True)")
    
    if result1:
        action_result1 = admin_action(message1, context1)
        print(f"アクション結果: {action_result1['type']}")
        print(f"アクション数: {len(action_result1['actions'])}")
    
    message2 = {
        "text": "重要なお知らせです",
        "user": "U111111111",  # 運営ユーザー
        "channel": "C123456789",
        "ts": "1234567890.123456"
    }
    
    result2 = admin_check(message2, context1)
    print(f"テスト2 - 運営チャンネルに運営ユーザー投稿: {result2} (期待値: False)")
    print()


def test_url_spam_detection():
    """URLスパム検出プラグインのテスト"""
    print("=== URLスパム検出プラグイン テスト ===")
    
    message1 = {
        "text": "こちらのサイトをチェック！ https://example.com と https://test.com も見てね",
        "user": "U123456789",
        "channel": "C123456789",
        "ts": "1234567890.123456"
    }
    context1 = {
        "channel_info": {"name": "general"},
        "moderator_channel": "C9876543210"
    }
    
    result1 = url_spam_check(message1, context1)
    print(f"テスト1 - 複数URLメッセージ: {result1} (期待値: True)")
    
    if result1:
        action_result1 = url_spam_action(message1, context1)
        print(f"アクション結果: {action_result1['type']}")
        print(f"検出URL数: {action_result1['metadata']['url_count']}")
    
    message2 = {
        "text": "無料プレゼント！今すぐクリック https://bit.ly/freebie123",
        "user": "U123456789",
        "channel": "C123456789",
        "ts": "1234567890.123456"
    }
    
    result2 = url_spam_check(message2, context1)
    print(f"テスト2 - 怪しいドメイン + 宣伝キーワード: {result2} (期待値: True)")
    
    message3 = {
        "text": "GitHubのドキュメントです https://docs.github.com",
        "user": "U123456789",
        "channel": "C123456789",
        "ts": "1234567890.123456"
    }
    
    result3 = url_spam_check(message3, context1)
    print(f"テスト3 - 正常なURL: {result3} (期待値: False)")
    print()


def main():
    """全プラグインのテストを実行"""
    print("コミュニティマネージャーボット プラグインテスト\n")
    
    test_defamatory_detection()
    test_admin_channel_guard()
    test_url_spam_detection()
    
    print("=== テスト完了 ===")
    print("注意: 実際のSlack APIは呼び出されていません。")
    print("プラグインのロジックのみをテストしています。")


if __name__ == "__main__":
    main()
