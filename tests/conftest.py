"""テスト全体の前提設定。

`app.config` は必須の環境変数が未設定だと import 時に `KeyError` で失敗する。
テストでは外部APIを呼ばないため、ダミー値を入れて import を通す。
"""

import os

os.environ.setdefault("LINE_CHANNEL_SECRET", "test-secret")
os.environ.setdefault("LINE_CHANNEL_ACCESS_TOKEN", "test-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
