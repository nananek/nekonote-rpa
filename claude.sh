#!/usr/bin/env bash
# Claude Code ランチャー
# claude コマンドが見つからない場合、インストール方法を選択できる
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_DIR="$SCRIPT_DIR/.claude-local"
LOCAL_BIN="$LOCAL_DIR/node/bin"
LOCAL_CLAUDE="$LOCAL_DIR/node_modules/.bin/claude"

# ── ローカルインストール済みならそれを使う ──
if [[ -x "$LOCAL_CLAUDE" ]]; then
  export PATH="$LOCAL_BIN:$PATH"
  exec "$LOCAL_CLAUDE" "$@"
fi

# ── グローバルにインストール済みならそれを使う ──
if command -v claude &>/dev/null; then
  exec claude "$@"
fi

# ── 見つからない場合、選択肢を提示 ──
echo "Claude Code が見つかりません。"
echo ""
echo "  1) 自分でインストールする (手順を表示)"
echo "  2) このプロジェクト内にインストールする (.claude-local/)"
echo "  3) 終了"
echo ""
read -rp "選択してください [1-3]: " choice

case "$choice" in
  1)
    echo ""
    echo "=== インストール方法 ==="
    echo ""
    echo "  npm:"
    echo "    npm install -g @anthropic-ai/claude-code"
    echo ""
    echo "  Homebrew:"
    echo "    brew install claude-code"
    echo ""
    echo "  詳細: https://docs.anthropic.com/en/docs/claude-code"
    echo ""
    echo "インストール後、再度 ./claude.sh を実行してください。"
    exit 0
    ;;
  2)
    echo ""

    # Node.js の検出
    NODE_CMD=""
    if [[ -x "$LOCAL_BIN/node" ]]; then
      NODE_CMD="$LOCAL_BIN/node"
      NPM_CMD="$LOCAL_BIN/npm"
    elif command -v node &>/dev/null; then
      NODE_CMD="$(command -v node)"
      NPM_CMD="$(command -v npm)"
    fi

    if [[ -z "$NODE_CMD" ]]; then
      # Node.js もないのでダウンロードする
      echo "Node.js をダウンロードしています..."
      mkdir -p "$LOCAL_DIR"

      ARCH="$(uname -m)"
      case "$ARCH" in
        x86_64)  NODE_ARCH="x64" ;;
        aarch64|arm64) NODE_ARCH="arm64" ;;
        *) echo "未対応のアーキテクチャ: $ARCH"; exit 1 ;;
      esac

      OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
      case "$OS" in
        linux)  NODE_OS="linux" ;;
        darwin) NODE_OS="darwin" ;;
        *) echo "未対応の OS: $OS"; exit 1 ;;
      esac

      # 最新 LTS バージョンを取得
      NODE_VERSION="$(curl -fsSL https://nodejs.org/dist/index.json | grep -o '"v[0-9]*\.[0-9]*\.[0-9]*"' | head -1 | tr -d '"')"
      NODE_URL="https://nodejs.org/dist/${NODE_VERSION}/node-${NODE_VERSION}-${NODE_OS}-${NODE_ARCH}.tar.xz"

      echo "  Node.js ${NODE_VERSION} (${NODE_OS}-${NODE_ARCH})"
      curl -fsSL "$NODE_URL" | tar -xJ -C "$LOCAL_DIR"
      mv "$LOCAL_DIR/node-${NODE_VERSION}-${NODE_OS}-${NODE_ARCH}" "$LOCAL_DIR/node"

      NODE_CMD="$LOCAL_BIN/node"
      NPM_CMD="$LOCAL_BIN/npm"
    fi

    echo "Claude Code をインストールしています..."
    mkdir -p "$LOCAL_DIR"
    export PATH="$(dirname "$NODE_CMD"):$PATH"
    (cd "$LOCAL_DIR" && "$NPM_CMD" install --no-package-lock @anthropic-ai/claude-code)

    echo ""
    echo "インストール完了。起動します..."
    echo ""
    exec "$LOCAL_CLAUDE" "$@"
    ;;
  *)
    exit 0
    ;;
esac
