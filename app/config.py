"""環境変数の読み込みと設定値の定義。

`.env`（ローカル）またはホスティング環境の環境変数から必須のシークレット類を読み込む。
未設定の場合は起動時に`KeyError`で即座に失敗させることで、
「キーが空のままAPIを呼んで原因不明のエラーになる」事態を防ぐ。
"""

import os

from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
