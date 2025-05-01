---
sidebar_position: 5
---

# サイトのデプロイ

Docusaurusは**静的サイトジェネレーター**（**[Jamstack](https://jamstack.org/)**とも呼ばれます）です。

サイトをシンプルな**静的HTML、JavaScript、CSSファイル**としてビルドします。

## サイトのビルド

**本番用**のサイトをビルドします：

```bash
npm run build
```

静的ファイルは`build`フォルダに生成されます。

## サイトのデプロイ

本番ビルドをローカルでテストします：

```bash
npm run serve
```

`build`フォルダが[http://localhost:3000/](http://localhost:3000/)で提供されるようになりました。

これで`build`フォルダを**ほぼどこにでも**、**無料**または非常に低コストで簡単にデプロイできます（**[デプロイガイド](https://docusaurus.io/docs/deployment)**を参照してください）。
