"""
コミュニティマネージャーボット メイン処理

GitHub Actionsから実行され、直近のSlackメッセージを取得して
プラグインによる処理を実行する。
"""

import os
import sys
import yaml
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse

from lib.slack_client import SlackClient
from lib.message_utils import get_message_timestamp


class CommunityManagerBot:
    """コミュニティマネージャーボットのメインクラス"""
    
    def __init__(self, config_path: str = "config/plugins.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.slack_client = SlackClient(os.getenv("SLACK_BOT_TOKEN"))
        self.plugins = self._load_plugins()
        
    def _load_config(self) -> Dict:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {self.config_path}")
            return {"plugins": {}, "global": {}}
    
    def _load_plugins(self) -> Dict:
        """有効なプラグインを動的に読み込み"""
        plugins = {}
        plugins_dir = Path("plugins")
        
        for plugin_name, plugin_config in self.config.get("plugins", {}).items():
            if not plugin_config.get("enabled", False):
                print(f"プラグイン {plugin_name} は無効です")
                continue
                
            plugin_path = plugins_dir / plugin_name / "plugin.py"
            if not plugin_path.exists():
                print(f"プラグインファイルが見つかりません: {plugin_path}")
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{plugin_name}.plugin", 
                    plugin_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'check') and hasattr(module, 'action'):
                    plugins[plugin_name] = {
                        "module": module,
                        "config": plugin_config,
                        "priority": plugin_config.get("priority", 999)
                    }
                    print(f"プラグイン {plugin_name} を読み込みました")
                else:
                    print(f"プラグイン {plugin_name} に check または action 関数がありません")
                    
            except Exception as e:
                print(f"プラグイン {plugin_name} の読み込みに失敗: {e}")
        
        return dict(sorted(plugins.items(), key=lambda x: x[1]["priority"]))
    
    def _get_context(self, channel_id: str) -> Dict:
        """プラグイン実行用のコンテキストを構築"""
        try:
            channel_info = self.slack_client.get_channel_info(channel_id)
            return {
                "channel_info": channel_info,
                "admin_users": self.config.get("global", {}).get("admin_users", []),
                "general_channel": self.config.get("global", {}).get("general_channel"),
                "excluded_channels": self.config.get("global", {}).get("excluded_channels", [])
            }
        except Exception as e:
            print(f"コンテキスト取得エラー: {e}")
            return {}
    
    def _execute_action(self, action_result: Dict) -> bool:
        """プラグインのアクション結果を実行"""
        try:
            action_type = action_result.get("type")
            
            if action_type == "post_message":
                self.slack_client.post_message(
                    channel=action_result["channel"],
                    text=action_result["text"],
                    thread_ts=action_result.get("thread_ts")
                )
                print(f"メッセージを投稿しました: {action_result['channel']}")
                
            elif action_type == "delete_message":
                self.slack_client.delete_message(
                    channel=action_result["channel"],
                    ts=action_result["ts"]
                )
                print(f"メッセージを削除しました: {action_result['ts']}")
                
            elif action_type == "multiple_actions":
                for action in action_result.get("actions", []):
                    self._execute_action(action)
                    
            else:
                print(f"未知のアクションタイプ: {action_type}")
                return False
                
            return True
            
        except Exception as e:
            print(f"アクション実行エラー: {e}")
            return False
    
    def process_messages(self, hours_back: int = 1) -> None:
        """指定時間内のメッセージを処理"""
        print(f"過去 {hours_back} 時間のメッセージを処理開始")
        
        now = datetime.now()
        oldest = (now - timedelta(hours=hours_back)).timestamp()
        
        try:
            test_channels = ["C1234567890"]  # テスト用チャンネルID
            
            for channel_id in test_channels:
                if channel_id in self.config.get("global", {}).get("excluded_channels", []):
                    print(f"チャンネル {channel_id} は除外対象です")
                    continue
                
                print(f"チャンネル {channel_id} を処理中...")
                
                messages = self.slack_client.get_channel_history(
                    channel_id=channel_id,
                    oldest=str(oldest)
                )
                
                context = self._get_context(channel_id)
                
                for message in messages:
                    self._process_single_message(message, context)
                    
        except Exception as e:
            print(f"メッセージ処理エラー: {e}")
    
    def _process_single_message(self, message: Dict, context: Dict) -> None:
        """単一メッセージに対してプラグインを実行"""
        message_ts = message.get("ts")
        user = message.get("user", "unknown")
        
        for plugin_name, plugin_info in self.plugins.items():
            try:
                module = plugin_info["module"]
                
                if module.check(message, context):
                    print(f"プラグイン {plugin_name} がメッセージ {message_ts} (user: {user}) にマッチしました")
                    
                    action_result = module.action(message, context)
                    
                    if self._execute_action(action_result):
                        print(f"プラグイン {plugin_name} のアクションを実行しました")
                    else:
                        print(f"プラグイン {plugin_name} のアクション実行に失敗しました")
                        
            except Exception as e:
                print(f"プラグイン {plugin_name} の実行エラー: {e}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="コミュニティマネージャーボット")
    parser.add_argument("--hours", type=int, default=1, help="処理対象の時間範囲（時間）")
    parser.add_argument("--config", default="config/plugins.yaml", help="設定ファイルパス")
    
    args = parser.parse_args()
    
    if not os.getenv("SLACK_BOT_TOKEN"):
        print("エラー: SLACK_BOT_TOKEN 環境変数が設定されていません")
        sys.exit(1)
    
    bot = CommunityManagerBot(config_path=args.config)
    bot.process_messages(hours_back=args.hours)
    
    print("処理完了")


if __name__ == "__main__":
    main()
