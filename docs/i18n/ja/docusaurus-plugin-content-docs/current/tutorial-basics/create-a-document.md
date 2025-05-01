---
sidebar_position: 2
---

# ドキュメントの作成

ドキュメントは以下を通じて接続された**ページのグループ**です：

- **サイドバー**
- **前/次のナビゲーション**
- **バージョン管理**

## 最初のドキュメントを作成する

`docs/hello.md`にMarkdownファイルを作成します：

```md title="docs/hello.md"
# こんにちは

これは私の**最初のDocusaurusドキュメント**です！
```

新しいドキュメントが[http://localhost:3000/docs/hello](http://localhost:3000/docs/hello)で利用可能になりました。

## サイドバーを設定する

Docusaurusは`docs`フォルダから自動的に**サイドバーを作成**します。

メタデータを追加して、サイドバーのラベルと位置をカスタマイズします：

```md title="docs/hello.md" {1-4}
---
sidebar_label: 'こんにちは！'
sidebar_position: 3
---

# こんにちは

これは私の**最初のDocusaurusドキュメント**です！
```

`sidebars.js`でサイドバーを明示的に作成することも可能です：

```js title="sidebars.js"
export default {
  tutorialSidebar: [
    'intro',
    // highlight-next-line
    'hello',
    {
      type: 'category',
      label: 'チュートリアル',
      items: ['tutorial-basics/create-a-document'],
    },
  ],
};
```
