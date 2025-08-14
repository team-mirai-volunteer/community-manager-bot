# 実際のSlack環境での動作テスト手順

テストチャンネル: <#C093DQZS57S|>

## 事前準備

### 1. Slack Bot Token の設定

```bash
# 環境変数を設定
export SLACK_BOT_TOKEN=xoxb-your-actual-bot-token

# または .env ファイルを作成
echo "SLACK_BOT_TOKEN=xoxb-your-actual-bot-token" > .env
```

### 2. テストチャンネルIDの確認と設定

```bash
# テストチャンネルID: C093DQZS57S
# config/plugins.yaml の設定を一時的に更新
```

<str_replace path="/home/ubuntu/repos/community-manager-bot/config/plugins.yaml">
<old_str>global:
  admin_users:
    - "U1234567890"  # 例: 運営メンバー1
    - "U0987654321"  # 例: 運営メンバー2
  
  general_channel: "C1234567890"
  
  excluded_channels:
    - "C9999999999"  # 例: テストチャンネル</old_str>
<new_str>global:
  admin_users:
    - "U1234567890"  # 例: 運営メンバー1
    - "U0987654321"  # 例: 運営メンバー2
  
  general_channel: "C093DQZS57S"  # テストチャンネル
  moderator_channel: "C093DQZS57S"  # テストチャンネル（モデレーター通知用）
  
  excluded_channels:
    - "C9999999999"  # 例: 除外チャンネル</new_str>
</str_replace>

### 3. 依存関係のインストール

```bash
cd /home/ubuntu/repos/community-manager-bot
pip install -r requirements.txt
```

## テスト実行手順

### Phase 1: 基本動作確認

#### 1-1. ボット接続テスト

```bash
# Slack APIの接続確認
python -c "
import os
from lib.slack_client import SlackClient
client = SlackClient(os.getenv('SLACK_BOT_TOKEN'))
result = client.get_channel_info('C093DQZS57S')
print('チャンネル情報:', result)
"
```

#### 1-2. メッセージ履歴取得テスト

```bash
# 過去1時間のメッセージを取得
python main.py --hours 1 --dry-run
```

### Phase 2: プラグイン個別テスト

#### 2-1. 誹謗中傷検出プラグインテスト

**テスト投稿1**: 誹謗中傷キーワードを含む投稿
```
テストチャンネルに投稿: "あいつは本当にバカだな"
```

**期待動作**:
- プラグインが検出
- 警告メッセージがスレッドで返信される

**確認コマンド**:
```bash
python main.py --hours 0.1
```

#### 2-2. URLスパム検出プラグインテスト

**テスト投稿2**: 複数URLを含む投稿
```
テストチャンネルに投稿: "こちらをチェック https://example.com と https://test.com も見てね"
```

**テスト投稿3**: 怪しいドメイン + 宣伝キーワード
```
テストチャンネルに投稿: "無料プレゼント！今すぐクリック https://bit.ly/freebie123"
```

**期待動作**:
- URLスパム検出
- ユーザーへの警告メッセージ
- モデレーターチャンネルへの通知

#### 2-3. 運営チャンネル監視プラグインテスト

**事前設定**: チャンネル名を「運営-test」に変更するか、プラグインの条件を調整

**テスト投稿4**: 運営チャンネルに一般ユーザーが投稿
```
運営チャンネルに投稿: "質問があります"
```

**期待動作**:
- 一般ユーザーの投稿を検出
- 雑談チャンネルに転載
- 元メッセージを削除
- ユーザーに説明メッセージ

### Phase 3: 正常メッセージテスト

#### 3-1. 正常投稿の確認

**テスト投稿5**: 正常なメッセージ
```
テストチャンネルに投稿: "今日はいい天気ですね"
```

**期待動作**:
- どのプラグインも反応しない
- メッセージがそのまま残る

### Phase 4: 統合テスト

#### 4-1. 複数メッセージの一括処理

```bash
# 複数のテストメッセージ投稿後、一括処理
python main.py --hours 1
```

#### 4-2. プラグイン優先度テスト

複数の条件にマッチするメッセージで優先度順の処理を確認

## テスト結果の確認方法

### 1. ログ出力の確認

```bash
# 詳細ログ付きで実行
python main.py --hours 1 --verbose
```

### 2. Slackでの確認ポイント

- ✅ 警告メッセージが適切なスレッドに投稿されているか
- ✅ モデレーター通知が正しいチャンネルに送信されているか
- ✅ メッセージ削除が実行されているか
- ✅ チャンネル間移動が正常に動作しているか

### 3. エラー処理の確認

```bash
# 無効なトークンでのエラーハンドリング確認
SLACK_BOT_TOKEN=invalid python main.py --hours 1
```

## トラブルシューティング

### よくある問題と解決方法

1. **Bot Token エラー**
   ```
   エラー: "invalid_auth"
   解決: SLACK_BOT_TOKEN の値を確認
   ```

2. **チャンネルアクセスエラー**
   ```
   エラー: "channel_not_found"
   解決: ボットをテストチャンネルに招待
   ```

3. **権限エラー**
   ```
   エラー: "missing_scope"
   解決: ボットに必要な権限を付与
   ```

### 必要なSlackボット権限

- `channels:history` - チャンネル履歴の読み取り
- `chat:write` - メッセージの投稿
- `chat:write.public` - パブリックチャンネルへの投稿
- `channels:read` - チャンネル情報の取得

## 安全な本番環境テスト

### 1. Dry-run モードの使用

```bash
# 実際のアクションを実行せずにテスト
python main.py --hours 1 --dry-run
```

### 2. 段階的な有効化

```yaml
# config/plugins.yaml で段階的にプラグインを有効化
plugins:
  defamatory_detection:
    enabled: true  # まずこれだけ有効化
  admin_channel_guard:
    enabled: false  # 後で有効化
  url_spam_detection:
    enabled: false  # 最後に有効化
```

### 3. 監視とロールバック

```bash
# 問題が発生した場合の緊急停止
# GitHub Actions の workflow_dispatch で手動停止
# または設定ファイルで全プラグインを無効化
```

## 継続的な監視

### 1. ログ監視

```bash
# GitHub Actions のログを定期確認
# エラー率や処理時間の監視
```

### 2. 誤検出の確認

```bash
# 定期的に処理結果をレビュー
# 必要に応じてフィルタ条件を調整
```

### 3. パフォーマンス監視

```bash
# 処理時間とAPI呼び出し回数の監視
# レート制限への対応
```
