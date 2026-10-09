# LINE RAG QA Bot

LINE に PDF を送ると内容を登録し、テキストで質問すると登録済み文書の内容に基づいて回答する Bot です。

## 使い方（LINE 上の操作）

| 送信内容 | 動作 |
| --- | --- |
| PDF ファイル | テキストを抽出してチャンク分割し、ベクトル DB に登録する。同名ファイルは上書き |
| `一覧` | 登録済みの文書名とチャンク数を返す |
| `削除 <ファイル名>` | 指定した文書を削除する |
| 上記以外のテキスト | 登録済み文書を検索し、その内容を根拠に回答する |

- PDF 以外のファイルは受け付けません
- 画像のみの PDF などテキストを抽出できないものは登録されません

## 仕組み

```
PDF 受信 → pdfplumber でページごとにテキスト抽出 → チャンク分割（800 文字・重複 100 文字）
        → OpenAI text-embedding-3-small で埋め込み → ChromaDB に保存

質問受信 → 質問を埋め込み → ChromaDB から上位 5 件を検索
        → 検索結果（ファイル名・ページ番号付き）をプロンプトに入れて Claude で回答生成
```

## 技術スタック

- Python 3.12 / uv
- FastAPI + Uvicorn（Webhook サーバー）
- LINE Messaging API（line-bot-sdk v3）
- ChromaDB（ローカル永続化、`chroma_db/` に保存）
- OpenAI Embeddings（`text-embedding-3-small`）
- Anthropic Claude（`claude-sonnet-5`）
- pdfplumber

## ディレクトリ構成

```
app/
├── main.py            # FastAPI アプリ。POST /callback で Webhook を受ける
├── config.py          # 環境変数の読み込み
├── line/handler.py    # LINE のメッセージ処理（PDF 登録・一覧・削除・質問）
├── llm/claude.py      # Claude API 呼び出し
└── rag/
    ├── pdf_parser.py  # PDF からページごとのテキストを抽出
    ├── chunker.py     # チャンク分割
    ├── embeddings.py  # 埋め込み生成
    ├── vectorstore.py # ChromaDB への登録・検索・一覧・削除
    └── qa.py          # 検索結果からプロンプトを組み立てて回答生成
doc/                   # 要件定義
render.yaml            # Render のデプロイ設定
```

## セットアップ

### 1. 環境変数

`.env.example` をコピーして `.env` を作成し、値を設定します。

```bash
cp .env.example .env
```

| 変数名 | 内容 |
| --- | --- |
| `LINE_CHANNEL_SECRET` | LINE チャネルシークレット |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE チャネルアクセストークン |
| `ANTHROPIC_API_KEY` | Anthropic API キー |
| `OPENAI_API_KEY` | OpenAI API キー（埋め込み生成用） |

### 2. 依存関係のインストール

```bash
uv sync
```

### 3. 起動

```bash
uv run uvicorn app.main:app --reload
```

LINE Developers コンソールで、Webhook URL に `https://<ホスト>/callback` を設定します。

## デプロイ（Render）

`render.yaml` に Render 用の設定があります。環境変数 4 つは Render のダッシュボードで設定します。

- ビルド: `pip install uv && uv sync --frozen`
- 起動: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
