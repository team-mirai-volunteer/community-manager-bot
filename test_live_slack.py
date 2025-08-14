"""
実際のSlack環境での動作テストスクリプト

テストチャンネルでの実際の投稿を使って、
プラグインの動作を確認する。
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from main import CommunityManagerBot
from lib.slack_client import SlackClient


def test_slack_connection():
    """Slack接続テスト"""
    print("=== Slack接続テスト ===")
    
    token = os.getenv('SLACK_BOT_TOKEN')
    if not token:
        print("❌ SLACK_BOT_TOKEN が設定されていません")
        return False
    
    try:
        client = SlackClient(token)
        
        test_channel = "C093DQZS57S"
        channel_info = client.get_channel_info(test_channel)
        
        if channel_info:
            print(f"✅ チャンネル接続成功: #{channel_info.get('name', 'unknown')}")
            print(f"   チャンネルID: {test_channel}")
            return True
        else:
            print("❌ チャンネル情報の取得に失敗")
            return False
            
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        return False


def test_message_retrieval():
    """メッセージ取得テスト"""
    print("\n=== メッセージ取得テスト ===")
    
    try:
        bot = CommunityManagerBot()
        test_channel = "C093DQZS57S"
        
        since_time = datetime.now() - timedelta(hours=1)
        messages = bot.slack_client.get_channel_history(test_channel, since_time)
        
        print(f"✅ 過去1時間のメッセージ数: {len(messages)}")
        
        for i, msg in enumerate(messages[:3]):
            text = msg.get('text', '')[:50]
            user = msg.get('user', 'unknown')
            ts = msg.get('ts', '')
            print(f"   {i+1}. [{user}] {text}... (ts: {ts})")
        
        return len(messages) > 0
        
    except Exception as e:
        print(f"❌ メッセージ取得エラー: {e}")
        return False


def test_plugin_processing():
    """プラグイン処理テスト"""
    print("\n=== プラグイン処理テスト ===")
    
    try:
        bot = CommunityManagerBot()
        test_channel = "C093DQZS57S"
        
        test_messages = [
            {
                "text": "テスト: あいつは本当にバカだな",  # 誹謗中傷検出対象
                "user": "U_TEST_USER",
                "channel": test_channel,
                "ts": str(time.time())
            },
            {
                "text": "テスト: こちらをチェック https://bit.ly/test123 と https://evil.com も見て！無料プレゼント",  # URLスパム検出対象
                "user": "U_TEST_USER",
                "channel": test_channel,
                "ts": str(time.time() + 1)
            },
            {
                "text": "テスト: 今日はいい天気ですね",  # 正常メッセージ
                "user": "U_TEST_USER",
                "channel": test_channel,
                "ts": str(time.time() + 2)
            }
        ]
        
        context = {
            "channel_info": {"name": "test-channel"},
            "admin_users": bot.config.get('global', {}).get('admin_users', []),
            "moderator_channel": bot.config.get('global', {}).get('moderator_channel', test_channel)
        }
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- テストメッセージ {i} の処理 ---")
            print(f"内容: {message['text']}")
            
            matched_plugins = []
            actions_to_execute = []
            
            for plugin_name, plugin_info in bot.plugins.items():
                module = plugin_info['module']
                
                try:
                    if module.check(message, context):
                        matched_plugins.append(plugin_name)
                        print(f"✅ {plugin_name} がマッチしました")
                        
                        action_result = module.action(message, context)
                        actions_to_execute.append((plugin_name, action_result))
                        
                        print(f"   アクションタイプ: {action_result.get('type')}")
                        
                        if action_result.get('type') == 'multiple_actions':
                            print(f"   複数アクション数: {len(action_result.get('actions', []))}")
                        
                except Exception as e:
                    print(f"❌ {plugin_name} でエラー: {e}")
            
            if not matched_plugins:
                print("   マッチしたプラグインなし（正常メッセージ）")
            
            for plugin_name, action in actions_to_execute:
                print(f"   [{plugin_name}] 実行予定アクション:")
                if action.get('type') == 'post_message':
                    print(f"     → メッセージ投稿: {action.get('text', '')[:50]}...")
                elif action.get('type') == 'multiple_actions':
                    for j, sub_action in enumerate(action.get('actions', [])):
                        print(f"     → アクション{j+1}: {sub_action.get('type')}")
        
        return True
        
    except Exception as e:
        print(f"❌ プラグイン処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dry_run():
    """Dry-runモードでの実行テスト"""
    print("\n=== Dry-run実行テスト ===")
    
    try:
        import subprocess
        
        env = os.environ.copy()
        result = subprocess.run([
            sys.executable, 'main.py', 
            '--hours', '0.5', 
            '--dry-run'
        ], 
        capture_output=True, 
        text=True, 
        env=env,
        cwd=Path(__file__).parent
        )
        
        print(f"✅ Dry-run実行完了 (終了コード: {result.returncode})")
        
        if result.stdout:
            print("--- 標準出力 ---")
            print(result.stdout)
        
        if result.stderr:
            print("--- エラー出力 ---")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Dry-run実行エラー: {e}")
        return False


def main():
    """実際のSlack環境でのテストを実行"""
    print("🚀 実際のSlack環境での動作テスト開始\n")
    
    test_results = {}
    
    test_results['connection'] = test_slack_connection()
    
    test_results['message_retrieval'] = test_message_retrieval()
    
    test_results['plugin_processing'] = test_plugin_processing()
    
    test_results['dry_run'] = test_dry_run()
    
    print("\n" + "="*50)
    print("🏁 テスト結果サマリー")
    print("="*50)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 全てのテストが成功しました！")
        print("\n次のステップ:")
        print("1. 実際にテストチャンネルにメッセージを投稿")
        print("2. python main.py --hours 0.1 を実行")
        print("3. ボットの反応を確認")
    else:
        print("⚠️  一部のテストが失敗しました。")
        print("設定やトークンを確認してください。")
    
    print("\n📋 手動テスト手順:")
    print("1. テストチャンネル <#C093DQZS57S|> に以下を投稿:")
    print("   - '誹謗中傷テスト: あいつはバカだ'")
    print("   - 'URLテスト: https://bit.ly/spam123 と https://evil.com 無料プレゼント'")
    print("   - '正常テスト: 今日はいい天気ですね'")
    print("2. python main.py --hours 0.1 を実行")
    print("3. ボットの反応をSlackで確認")


if __name__ == "__main__":
    main()
