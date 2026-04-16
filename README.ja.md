[![en](https://img.shields.io/badge/lang-English-blue.svg)](README.md)
[![ja](https://img.shields.io/badge/lang-日本語-red.svg)](README.ja.md)

![pixsize](https://capsule-render.vercel.app/api?type=candy&color=gradient&customColorList=12&text=pixsize&fontSize=42&fontColor=ffffff&animation=twinkling&fontAlignY=35&desc=%E3%82%AF%E3%83%AA%E3%82%A8%E3%82%A4%E3%82%BF%E3%83%BC%E5%90%91%E3%81%91%E3%83%90%E3%83%83%E3%83%81%E7%94%BB%E5%83%8F%E3%83%A1%E3%82%BF%E3%83%87%E3%83%BC%E3%82%BFCLI&descAlignY=55&descSize=16)

[![Python](https://img.shields.io/badge/Python-3.10+-for-the-badge?style=for-the-badge&logo=python&logoColor=white&color=3776AB)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-Pytest-for-the-badge?style=for-the-badge&logo=pytest&logoColor=white&color=0A9EDC)](https://pytest.org)
[![Coverage](https://img.shields.io/badge/Coverage-80%25+-for-the-badge?style=for-the-badge&logo=codecov&logoColor=white&color=F01F7A)](https://codecov.io)
[![License](https://img.shields.io/badge/License-MIT-for-the-badge?style=for-the-badge&logo=opensourceinitiative&logoColor=white&color=green)](LICENSE)
[![Linter](https://img.shields.io/badge/Linter-Ruff-for-the-badge?style=for-the-badge&logo=ruff&logoColor=white&color=D2FFED)](https://docs.astral.sh/ruff/)

**pixsize** はゲーム開発者・デザイナー・Web開発者向けの軽量CLIツールです。ImageMagickの重厚さなしに、画像のスキャン・検証・リサイズ・一括リネームができます。

## 特徴

- **`pixsize scan`** -- ディレクトリをスキャンし、寸法・フォーマット・アスペクト比でフィルタ
- **`pixsize check`** -- YAMLルールで画像を検証（スプライトシート、アイコンサイズ、Web仕様）
- **`pixsize resize`** -- プリセット（HD, 4K, アイコン, OG画像）またはカスタム寸法でバッチリサイズ
- **`pixsize rename`** -- パターンでリネーム（寸法、日付、インデックス）
- **複数出力形式** -- テーブル、JSON、CSV（パイプ対応）
- **API依存ゼロ** -- 純Python + Pillowのみ

## インストール

```bash
pip install pixsize
```

## クイックスタート

```bash
# カレントディレクトリの画像をスキャン
pixsize scan .

# フィルタ付きスキャン
pixsize scan ./sprites --min-width 32 --max-width 256 --square -o json

# ルールで検証
pixsize check ./icons --rules rules.yaml
pixsize check ./assets --min-width 100 --max-height 1000

# プリセットでリサイズ
pixsize resize ./photos -o ./resized --preset fhd
pixsize resize icon.png -w 32 -h 32 --no-keep-aspect

# パターンでリネーム
pixsize rename ./assets --pattern "{w}x{h}_{name}{ext}" --dry-run
pixsize rename ./assets --pattern "img_{i:03d}{ext}" --no-dry-run
```

## コマンド

### `pixsize scan`

ディレクトリをスキャンして画像メタデータを表示。

```bash
pixsize scan ディレクトリ [オプション]

オプション:
  -r, --recursive / --no-recursive   サブディレクトリをスキャン (デフォルト: true)
  --min-width INT                     最小幅フィルタ
  --max-width INT                     最大幅フィルタ
  --min-height INT                    最小高さフィルタ
  --max-height INT                    最大高さフィルタ
  --min-mp FLOAT                      最小メガピクセルフィルタ
  --max-mp FLOAT                      最大メガピクセルフィルタ
  --format TEXT                       フォーマットでフィルタ (繰り返し可)
  --square                            正方形のみ
  --landscape                         横長のみ
  --portrait                          縦長のみ
  -o, --output [table|json|csv]       出力形式 (デフォルト: table)
```

### `pixsize check`

寸法・フォーマットルールで画像を検証。

```bash
pixsize check パス... [オプション]

オプション:
  --rules FILE           YAMLルールファイル
  --min-width INT        最小幅
  --max-width INT        最大幅
  --min-height INT       最小高さ
  --max-height INT       最大高さ
  --square               正方形であること
  --max-size-mb FLOAT    最大ファイルサイズ (MB)
  --format TEXT          許可フォーマット (繰り返し可)
```

**ルールファイル例 (`rules.yaml`):**

```yaml
rules:
  - name: sprite-tile
    min_width: 16
    max_width: 256
    must_be_square: true
    allowed_formats: [PNG]

  - name: web-upload
    max_filesize_mb: 5.0
    max_width: 4096
    max_height: 4096
    allowed_formats: [PNG, JPEG, WEBP]
```

### `pixsize resize`

プリセットまたはカスタム寸法でリサイズ。

```bash
pixsize resize ソース... [オプション]

オプション:
  -o, --output-dir PATH       出力ディレクトリ
  -w, --width INT             目標幅
  -h, --height INT            目標高さ
  --max-dim INT               最大寸法 (アスペクト比維持)
  --preset PRESET             サイズプリセット
  --keep-aspect / --no-keep-aspect  アスペクト比維持 (デフォルト: true)
  --overwrite                 既存ファイルを上書き
```

**プリセット:** `hd`, `fhd`, `2k`, `4k`, `icon-16`, `icon-32`, `icon-64`, `icon-128`, `icon-256`, `icon-512`, `og-image`, `twitter-card`, `favicon`, `thumbnail`

### `pixsize rename`

パターントークンで画像をリネーム。

```bash
pixsize rename ディレクトリ [オプション]

オプション:
  -p, --pattern TEXT        リネームパターン (デフォルト: {name}_{w}x{h}{ext})
  --recursive / --no-recursive  サブディレクトリをスキャン (デフォルト: true)
  --dry-run / --no-dry-run  プレビューのみ (デフォルト: true)
```

**パターントークン:** `{w}` 幅, `{h}` 高さ, `{mp}` メガピクセル, `{fmt}` フォーマット, `{name}` 元の名前, `{ext}` 拡張子, `{date}` YYYYMMDD, `{i}` インデックス

## 開発

```bash
# クローン
git clone https://github.com/izag8216/pixsize.git
cd pixsize

# 開発依存を含めてインストール
pip install -e ".[dev]"

# テスト実行
pytest tests/ -v --cov=pixsize

# リント
ruff check src/ tests/
```

## ライセンス

MIT License -- 詳細は [LICENSE](LICENSE) を参照。

---

![footer](https://capsule-render.vercel.app/api?type=candy&color=gradient&customColorList=12&section=footer&fontSize=14&text=Made%20with%20pixsize&fontColor=ffffff)
