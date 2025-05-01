---
sidebar_position: 3
---

# ブログ投稿の作成

Docusaurusは**各ブログ投稿ごとにページ**を作成するだけでなく、**ブログインデックスページ**、**タグシステム**、**RSSフィード**なども作成します。

## 最初の投稿を作成する

`blog/2021-02-28-greetings.md`というファイルを作成します：

```md title="blog/2021-02-28-greetings.md"
---
slug: greetings
title: ご挨拶！
authors:
  - name: Joel Marcey
    title: Docusaurus 1の共同作成者
    url: https://github.com/JoelMarcey
    image_url: https://github.com/JoelMarcey.png
  - name: Sébastien Lorber
    title: Docusaurusメンテナー
    url: https://sebastienlorber.com
    image_url: https://github.com/slorber.png
tags: [greetings]
---

おめでとうございます！最初の投稿ができました！

自由にこの投稿を編集して、好きなだけ遊んでみてください。
```

新しいブログ投稿が[http://localhost:3000/blog/greetings](http://localhost:3000/blog/greetings)で利用可能になりました。
