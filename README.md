# Community Manager Bot

コミュニティマネージャーの業務を補佐するSlack botです。プラグイン式のアーキテクチャにより、様々なフィルタリングと自動処理を実現します。

## 概要

このボットは以下の機能を提供します：

1. **GitHub Actions**で直近のSlackメッセージを定期取得
2. **プラグインシステム**によるメッセージのフィルタリング
3. **自動処理**（警告メッセージ、チャンネル移動、削除など）

## アーキテクチャ

### プラグインシステム

各プラグインは独立したディレクトリを持ち、単一のファイルに`check`と`action`の2つのエントリーポイントを含みます：

```
plugins/
├── defamatory_detection/     # 誹謗中傷検出
│   └── plugin.py
├── admin_channel_guard/      # 運営チャンネル監視
│   └── plugin.py
└── your_plugin/              # 新しいプラグイン
    └── plugin.py
```

### プラグインの構造

```python
def check(message: Dict, context: Dict) -> bool:
    """
    メッセージがフィルタ条件にマッチするかチェック
    
    Args:
        message: Slackメッセージオブジェクト
        context: チャンネル情報、運営ユーザーリストなど
    
    Returns:
        bool: 処理対象の場合True
    """
    pass

def action(message: Dict, context: Dict) -> Dict:
    """
    マッチしたメッセージに対する処理を定義
    
    Args:
        message: Slackメッセージオブジェクト
        context: 追加のコンテキスト情報
    
    Returns:
        Dict: 実行するアクションの詳細
    """
    pass
```

### 共通ライブラリ

プラグイン間で共有される機能は`lib/`ディレクトリに配置：

- `lib/slack_client.py`: Slack API操作
- `lib/message_utils.py`: メッセージ処理ユーティリティ

## 設定

### プラグインの有効/無効

`config/plugins.yaml`でプラグインの設定を管理：

```yaml
plugins:
  defamatory_detection:
    enabled: true
    priority: 1
    
  admin_channel_guard:
    enabled: false
    priority: 2

global:
  admin_users:
    - "U1234567890"
  general_channel: "C1234567890"
```

### 環境変数

```bash
export SLACK_BOT_TOKEN=xoxb-your-bot-token
```

## 使用方法

### ローカル実行

```bash
# 過去1時間のメッセージを処理
python main.py --hours 1

# 設定ファイルを指定
python main.py --config custom_config.yaml
```

### GitHub Actions

30分ごとに自動実行されます。手動実行も可能です。

## プラグイン開発

### 新しいプラグインの作成

1. `plugins/your_plugin_name/`ディレクトリを作成
2. `plugin.py`ファイルに`check`と`action`関数を実装
3. `config/plugins.yaml`にプラグイン設定を追加

### 例：スパム検出プラグイン

```python
# plugins/spam_detection/plugin.py

def check(message: Dict, context: Dict) -> bool:
    text = message.get("text", "")
    # スパム判定ロジック
    return "spam_keyword" in text.lower()

def action(message: Dict, context: Dict) -> Dict:
    return {
        "type": "delete_message",
        "channel": message["channel"],
        "ts": message["ts"]
    }
```

## アクションタイプ

プラグインが返すアクションの種類：

- `post_message`: メッセージ投稿
- `delete_message`: メッセージ削除
- `multiple_actions`: 複数アクションの組み合わせ

## 既存プラグイン

### 誹謗中傷検出 (`defamatory_detection`)

誹謗中傷的なキーワードを含む投稿を検出し、警告メッセージを返信します。

### 運営チャンネル監視 (`admin_channel_guard`)

運営専用チャンネルに運営以外が投稿した場合、雑談チャンネルに移動して元メッセージを削除します。

## 開発者向け情報

### 依存関係

- `requests`: Slack API通信
- `pyyaml`: 設定ファイル読み込み
- `python-dotenv`: 環境変数管理

### テスト

```bash
# プラグインのテスト実行
python -c "
from plugins.defamatory_detection.plugin import check, action
message = {'text': 'テストメッセージ', 'user': 'U123', 'channel': 'C123', 'ts': '123'}
context = {}
print(check(message, context))
"
```

## 今後の拡張

- AI/LLMを活用した高度なコンテンツ分析
- Webダッシュボードでの設定管理
- より詳細なログとレポート機能
- 外部サービス連携（Discord、Teams等）

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
