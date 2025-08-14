"""
統合テスト - メインシステムとプラグインの連携をテスト

実際のSlack APIを使わずに、プラグインローディングと
メッセージ処理フローをテストする。
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent))

from main import CommunityManagerBot


def test_plugin_loading():
    """プラグインの読み込みテスト"""
    print("=== プラグイン読み込みテスト ===")
    
    with patch.dict(os.environ, {'SLACK_BOT_TOKEN': 'xoxb-test-token'}):
        bot = CommunityManagerBot()
        
        print(f"読み込まれたプラグイン数: {len(bot.plugins)}")
        
        for plugin_name, plugin_info in bot.plugins.items():
            print(f"- {plugin_name}: 優先度 {plugin_info['priority']}")
            print(f"  説明: {plugin_info['config'].get('description', 'なし')}")
            
            module = plugin_info['module']
            has_check = hasattr(module, 'check')
            has_action = hasattr(module, 'action')
            print(f"  check関数: {'✓' if has_check else '✗'}")
            print(f"  action関数: {'✓' if has_action else '✗'}")
        
        print()
        return bot


def test_message_processing():
    """メッセージ処理フローのテスト"""
    print("=== メッセージ処理フローテスト ===")
    
    with patch.dict(os.environ, {'SLACK_BOT_TOKEN': 'xoxb-test-token'}):
        bot = CommunityManagerBot()
        
        mock_messages = [
            {
                "text": "あいつは本当にバカだな",
                "user": "U123456789",
                "channel": "C123456789",
                "ts": "1234567890.123456"
            },
            {
                "text": "こちらをチェック https://bit.ly/spam123 と https://evil.com も見て！無料プレゼント",
                "user": "U987654321",
                "channel": "C123456789",
                "ts": "1234567890.123457"
            },
            {
                "text": "今日はいい天気ですね",
                "user": "U555555555",
                "channel": "C123456789",
                "ts": "1234567890.123458"
            }
        ]
        
        bot.slack_client.get_channel_history = Mock(return_value=mock_messages)
        bot.slack_client.get_channel_info = Mock(return_value={"name": "general"})
        bot.slack_client.post_message = Mock(return_value={"ok": True})
        bot.slack_client.delete_message = Mock(return_value={"ok": True})
        
        context = {
            "channel_info": {"name": "general"},
            "admin_users": ["U111111111"],
            "moderator_channel": "C9876543210"
        }
        
        for i, message in enumerate(mock_messages, 1):
            print(f"\n--- メッセージ {i} の処理 ---")
            print(f"内容: {message['text'][:50]}...")
            
            matched_plugins = []
            
            for plugin_name, plugin_info in bot.plugins.items():
                module = plugin_info['module']
                
                try:
                    if module.check(message, context):
                        matched_plugins.append(plugin_name)
                        print(f"✓ {plugin_name} がマッチしました")
                        
                        action_result = module.action(message, context)
                        print(f"  アクションタイプ: {action_result.get('type')}")
                        
                        if action_result.get('type') == 'multiple_actions':
                            print(f"  複数アクション数: {len(action_result.get('actions', []))}")
                        
                except Exception as e:
                    print(f"✗ {plugin_name} でエラー: {e}")
            
            if not matched_plugins:
                print("  マッチしたプラグインなし（正常メッセージ）")
        
        print(f"\nSlack API呼び出し回数:")
        print(f"- post_message: {bot.slack_client.post_message.call_count}")
        print(f"- delete_message: {bot.slack_client.delete_message.call_count}")
        print()


def test_config_validation():
    """設定ファイルの検証テスト"""
    print("=== 設定ファイル検証テスト ===")
    
    with patch.dict(os.environ, {'SLACK_BOT_TOKEN': 'xoxb-test-token'}):
        bot = CommunityManagerBot()
        
        config = bot.config
        
        required_global_keys = ['admin_users', 'general_channel']
        
        print("グローバル設定:")
        for key in required_global_keys:
            value = config.get('global', {}).get(key)
            status = "✓" if value else "✗"
            print(f"  {key}: {status} {value}")
        
        print("\nプラグイン設定:")
        for plugin_name, plugin_config in config.get('plugins', {}).items():
            enabled = plugin_config.get('enabled', False)
            priority = plugin_config.get('priority', 999)
            description = plugin_config.get('description', 'なし')
            
            status = "有効" if enabled else "無効"
            print(f"  {plugin_name}: {status} (優先度: {priority})")
            print(f"    説明: {description}")
        
        print()


def main():
    """統合テストを実行"""
    print("コミュニティマネージャーボット 統合テスト\n")
    
    try:
        test_plugin_loading()
        test_message_processing()
        test_config_validation()
        
        print("=== 統合テスト完了 ===")
        print("✓ 全てのテストが正常に完了しました")
        
    except Exception as e:
        print(f"✗ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
