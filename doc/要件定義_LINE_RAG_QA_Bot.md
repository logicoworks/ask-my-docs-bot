# 要件定義：LINE × RAG ドキュメントQA Bot

## 1. プロジェクト概要

### プロジェクト名
LINE × RAG ドキュメントQA Bot

### 目的
LINEにPDFやテキストファイルを送信すると内容を記憶し、自然言語で質問すると文書の内容に基づいて回答するBotを開発する。

### ゴール
- RAG（Retrieval-Augmented Generation）の実装スキルを習得する
- GitHubポートフォリオとして公開できる品質のプロダクトを完成させる
- 将来的に副業・案件獲得につなげられる実績を作る

### 開発者プロフィール
- 20年超のエンジニア経験（Java / JavaScript / PHP）
- Salesforce認定上級Platformデベロッパー
- iPaaSによるSaaS統合（HubSpot / SVF Cloud / CloudSign / Kickflow）の設計・構築経験
- CI/CD整備（CircleCI / GitHub Actions）、AWS ECS上でのバッチ自動化経験
- Pythonは新規習得

---

## 2. システム構成

### アーキテクチャ概要

```
[ユーザー] → [LINE] → [LINE Messaging API]
                            ↓
                      [Webhook / FastAPI]
                        ↓            ↓
              [PDF受信・テキスト抽出]  [質問受信]
                        ↓            ↓
              [チャンク分割]     [ベクトル検索（ChromaDB）]
                        ↓            ↓
              [Embedding生成]   [関連チャンク取得]
                        ↓            ↓
              [ChromaDB保存]    [LLM API（Claude）で回答生成]
                                     ↓
                              [LINE返信]
```

### 技術スタック

| カテゴリ | 技術 | 選定理由 |
|---------|------|---------|
| 言語 | Python 3.11+ | AI/RAG系ライブラリの充実 |
| Webフレームワーク | FastAPI | 非同期対応・型安全・軽量 |
| LLM API | Claude API（Anthropic） | 日本語性能・コストパフォーマンス |
| Embedding | OpenAI Embeddings API or Sentence Transformers | ベクトル検索用（後者なら無料） |
| ベクトルDB | ChromaDB | ローカル動作・無料・Python親和性が高い |
| PDF解析 | pdfplumber | テーブル含むPDF対応 |
| LINE連携 | LINE Messaging API + line-bot-sdk-python | 公式SDK |
| ホスティング | Render（Free Tier） | 無料・GitHub連携デプロイ |
| バージョン管理 | Git / GitHub | ポートフォリオ公開先 |

### コスト見積もり

| 項目 | 月額目安 |
|------|---------|
| LINE Messaging API | 無料（Free プラン） |
| Claude API（従量課金） | ～500円（個人利用想定） |
| Render Free Tier | 無料 |
| ChromaDB | 無料（ローカル） |
| **合計** | **～500円/月** |

---

## 3. 機能要件

### Phase 1：土台構築（1週目）

**目標：** LINEで話しかけたらAIが返事するBotを動かす

| # | 機能 | 詳細 |
|---|------|------|
| 1-1 | Python環境構築 | Python 3.11+、venv、依存パッケージ管理（requirements.txt） |
| 1-2 | LINE Echo Bot | LINE Messaging APIのWebhook受信 → オウム返し |
| 1-3 | Claude API疎通 | テキストメッセージ受信 → Claude API → 回答をLINE返信 |
| 1-4 | ローカル開発環境 | ngrokによるローカルWebhookトンネリング |

**完了条件：** LINEでテキストを送信し、Claude APIによる応答がLINEに返ってくること

---

### Phase 2：RAGコア実装（2〜3週目）

**目標：** PDFを送ると記憶し、質問に文書ベースで回答する

| # | 機能 | 詳細 |
|---|------|------|
| 2-1 | PDF受信 | LINEからPDFファイルを受信・一時保存 |
| 2-2 | テキスト抽出 | pdfplumberでPDFからテキストを抽出 |
| 2-3 | チャンク分割 | テキストを意味的なまとまり（500〜1000トークン程度）に分割 |
| 2-4 | Embedding生成 | 各チャンクのベクトル表現を生成 |
| 2-5 | ChromaDB保存 | ベクトル+メタデータ（ファイル名・ページ番号等）を保存 |
| 2-6 | ベクトル検索 | 質問文をEmbedding化し、類似チャンクを上位3〜5件検索 |
| 2-7 | RAG回答生成 | 関連チャンク+質問文をClaude APIに渡し、文書に基づく回答を生成 |
| 2-8 | ドキュメント管理 | 登録済み文書の一覧表示・削除 |

**完了条件：** PDFをLINEに送信後、その内容に関する質問にPDFの情報を根拠とした回答が返ること

---

### Phase 3：仕上げ・ポートフォリオ整備（4週目）

**目標：** GitHub公開に耐える品質に仕上げる

| # | 項目 | 詳細 |
|---|------|------|
| 3-1 | エラーハンドリング | API障害・PDF解析失敗・ファイルサイズ超過等への対応 |
| 3-2 | ユーザーフィードバック | 処理中メッセージ、エラー時の案内メッセージ |
| 3-3 | README（日英） | プロジェクト概要・アーキテクチャ図・セットアップ手順・デモ |
| 3-4 | デモ素材 | スクリーンショット or 動画GIF |
| 3-5 | コード品質 | Linter（ruff）、型ヒント、docstring |
| 3-6 | GitHub整備 | .gitignore、.env.example、LICENSE、ディレクトリ構成 |

---

## 4. 非機能要件

| 項目 | 要件 |
|------|------|
| レスポンス | LINE返信まで10秒以内（目安） |
| 対応ファイル | PDF（Phase 2）。テキストファイル対応は将来拡張 |
| ファイルサイズ上限 | 10MB以下（LINE APIの制限に準拠） |
| 同時ユーザー | 個人利用想定（1ユーザー） |
| セキュリティ | APIキーは環境変数管理、.envはgit管理外 |
| 可用性 | Render Free Tierのため、スリープ許容 |

---

## 5. ディレクトリ構成（想定）

```
line-rag-qa-bot/
├── README.md
├── README_ja.md
├── LICENSE
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── main.py            # FastAPIエントリーポイント
│   ├── config.py           # 環境変数・設定管理
│   ├── line/
│   │   ├── handler.py      # LINE Webhook処理
│   │   └── messages.py     # LINE返信メッセージ定義
│   ├── rag/
│   │   ├── pdf_parser.py   # PDF解析・テキスト抽出
│   │   ├── chunker.py      # テキストチャンク分割
│   │   ├── embeddings.py   # Embedding生成
│   │   ├── vectorstore.py  # ChromaDB操作
│   │   └── qa.py           # 質問応答（検索+LLM呼び出し）
│   └── llm/
│       └── claude.py       # Claude API クライアント
├── tests/
│   ├── test_chunker.py
│   ├── test_pdf_parser.py
│   └── test_qa.py
└── docs/
    ├── architecture.md
    └── demo/
        └── screenshot.png
```

---

## 6. 将来拡張（Phase 3完了後に検討）

- テキストファイル（.txt / .md）対応
- 複数ドキュメントの横断検索
- 回答時のソース引用（ページ番号表示）
- Webダッシュボード（Streamlit）でのドキュメント管理
- Docker化
- ユーザーごとのドキュメント管理（マルチテナント化）
- Render有料プラン or AWS Lambda への移行

---

## 7. スケジュール

| 期間 | フェーズ | マイルストーン |
|------|---------|--------------|
| Week 1 | Phase 1：土台構築 | LINE × Claude APIで会話できるBotが動作 |
| Week 2-3 | Phase 2：RAGコア | PDF送信 → 質問応答のRAGパイプライン完成 |
| Week 4 | Phase 3：仕上げ | README・デモ整備、GitHub公開 |

---

## 8. 開発ルール

- **スコープ厳守：** Phase 1〜3の範囲を守り、機能追加は完了後に検討する
- **小さく動かす：** 各Phaseの完了条件を満たしてから次に進む
- **Git運用：** feature branchで開発 → mainにマージ、こまめにコミット
- **環境変数：** APIキー等の秘匿情報は.envで管理し、リポジトリには含めない
