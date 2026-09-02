# AIRAS × Seyval 実行リファレンス（RIKYU / aarch64）

AIRAS の実験を RIKYU（BYO Slurm / GB200 / **aarch64**）で回すための手順と、
そこでしか踏まない落とし穴。`run-experiments` の step 0 で Seyval を選んだ
ときに読む。

前提が 3 つ。実行先は **aarch64**、Seyval は **prod（`https://api.seyval.dev`）**
のみ、そして実行は **seyval MCP を直接叩く**（`dispatch_experiment` は使わない）。
最初の 2 つが以降の判断のほぼ全てを決める。

## 目次

- [事前に済ませておくこと](#事前に済ませておくこと)
- [フロー](#フロー)
- [1. 実行先を解決する](#1-実行先を解決する)
- [2. コードを aarch64 で通る形にする](#2-コードを-aarch64-で通る形にする)
- [3. 実行環境を Dockerfile で固定する](#3-実行環境を-dockerfile-で固定する)
- [4. 起動する](#4-起動する)
- [5. 追跡して回収する](#5-追跡して回収する)
- [計算ノードから見える世界](#計算ノードから見える世界)
- [pip で入らないソフトウェアを持ち込む](#pip-で入らないソフトウェアを持ち込む)
- [失敗の切り分け](#失敗の切り分け)
- [見るものとツールの対応](#見るものとツールの対応)

## 事前に済ませておくこと

`SEYVAL_API_KEY` を `.env` に置く。**`~/.airas/credentials.json` は環境変数に優先する**
ので、`.env` を直したのに効かないときは、まずファイル側に古い値が残っていないか疑う。

実験リポジトリは push 済みであること。Seyval は GitHub からリポジトリを引くので、
手元にあるだけのコミットは実行できない。`prepare_repository` の既定は
`is_private=True` なので、新規作成分は private → GitHub App の導入が要る。

ワークスペースが複数ある場合、`register_repository` の `workspace_id` は**ユーザーに
訊く**。リポジトリはワークスペース全員に見え、**後から移せない**。

## フロー

```
list_computes             → 実行先の compute_id と run_profile を確認
（コードを書く）           → aarch64 wheel の実在を確認、Dockerfile を用意
register_repository       → pull_repository → get_analysis（未解析なら start_analysis）
start_run                 → 返る run_id を控える（step 5 で必須）
get_run                   → 終了まで追う
import_run_outputs        → execution_id に上の run_id を渡す
fetch_experiment_results  → リポジトリを読む
```

最後の 2 つの順序が重要で、`fetch_experiment_results` は**リポジトリしか見ない**。
Seyval の成果物は Seyval 側に残るので、`import_run_outputs` を挟まないと
「実験は成功したのに結果が空」になる。

## 1. 実行先を解決する

`list_computes` で**毎回**解決する。**ID を過去ログやドキュメントからコピペしない** —
BYO の ID はワークスペース単位でスコープされる。

BYO を選ぶなら `run_profile` を読む。ここを推測すると 400 で弾かれるだけなので、
値は必ず profile から取る。

- `resource_count` は `resource_options` の中の値で、**かつ `max_resource_count` 以下**。
  `resource_options` には上限を超える値が並んでいることがある
  （実例: options が `[1,2,3,4,8,12,16]` で上限が 4）
- 単位は `resource_unit`（`"gpu"` か `"node"`）
- `verification_status` は**自分の**認証情報の状態。null なら未接続で、
  `set_byo_credential` / `verify_byo_credential` が要る

投入前に `check_byo_availability` を**投入するのと同じ `compute_type` /
`resource_count` / `time_limit` で**叩く。違うパラメータで聞くと、投入しない
ジョブについて「空いている」と答えられるだけになる。

なお `start_run` に渡す `compute_type` は**要求**であって実機の種別ではない。
BYO では GPU 要求を導くための互換ティアとして扱われる。実際に何で走ったかは
`get_run` の `compute_type` を見る。

## 2. コードを aarch64 で通る形にする

**手元が x86 なら、ローカルの sanity run は「実行先で動く」証明にならない。**
ここが RIKYU で最も時間を溶かすポイントで、しかも失敗はビルド時まで出てこない。

`uv pip install --dry-run` が通っても入る保証にはならない。**解決は通っても対象
プラットフォームの wheel が存在しないことがある。**

実例: `triton==3.3.0` は x86_64 wheel しか公開しておらず、torch 2.7 系がこれを
ピンで引くため aarch64 ビルドで落ちる（torch 2.11 系が引く triton 3.6.0 には
aarch64 wheel がある）。`gemmi==0.7.1` も cp311/cp312 の aarch64 wheel を持たない。

**依存はロックファイルで固定する。`uv.lock` のコミットは必須。** Dockerfile は
`uv sync --frozen` だけで環境を作り、実行は `uv run --no-sync` で走る。どちらも
その場で依存を解決しないので、lock が無ければ**ビルドがそこで失敗する** — 黙って
解決にフォールバックはしない。裏を返せば、同じコミットが同じ環境で走ることを
保証しているのは lock ファイルだけである。

**`uv lock` の後に、lock 内の wheel URL を走査して aarch64 が無いパッケージを
洗い出す。** 数行のスクリプトで済み、ビルドを 1 往復させるより遥かに速い。

なお、ソースビルドできる依存なら Dockerfile 側で救える（gcc / g++ / cmake は入る）。
救えないのは wheel もソース配布も無いケース。

## 3. 実行環境を Dockerfile で固定する

AIRAS は**必ず自前の Dockerfile を使う**。`start_run(user_dockerfile_path=
"Dockerfile")` を渡すと、そのファイルがそのままビルドされる。渡さないと Seyval は
リポジトリの Dockerfile を無視して LLM に環境を再生成させ、それを抑止する手段は
無いので、**この引数は省略しない**。

ビルドコンテキストは常にリポジトリ root（`docker build -f <path> .` と同じ）。
ファイルが無い、または検証に落ちた場合は**黙って生成にフォールバックせず**
user 起因のエラーで落ちる。環境の定義がコミットと一緒にバージョン管理され、
コミットハッシュだけで実行環境が決まるのはこのためで、§2 のロックファイルと
セットで初めて成立する。

代償が 1 つある。**持ち込んだ Dockerfile の CMD はそのまま実行される**ので、
`parameters` による上書きが効かない（解析時の既定と違う値を渡すと 400）。
run と mode の切り替えは `command_args` で argv を自分で書く。

```python
command_args=[
    "uv", "run", "--no-sync", "python", "-u", "-m", "src.main",
    f"run={run_id}", "results_dir=.research/results", f"mode={mode}",
]
```

### コンテナ内で出来ないこと

```
リポジトリの Dockerfile → Kaniko ビルド → ECR
  → 計算ノードで Apptainer SIF として pull → apptainer run
```

作業ディレクトリは共有ストレージ上の `<job dir>/<run_id>/` で書き込み可能。

| 対象 | 可否 |
|---|---|
| gcc / g++ / cmake | Dockerfile で入る（ソースビルド可能） |
| micromamba | Dockerfile で入る。conda-forge / bioconda に到達できる |
| nvcc | ベースイメージを CUDA 付きに変える必要がある |
| **apptainer / singularity** | **恒久的に不可**。既に Apptainer の中にいるため nested になる |
| **srun / sbatch** | **不可**。Slurm クライアントはコンテナ内に無い |

「重い処理を `apptainer exec` で自前 SIF に委譲する」という設計は成立しない。

## 4. 起動する

`register_repository` は冪等で、**登録と同時にデフォルトブランチ HEAD の解析が
自動で始まる**。直後に `start_analysis` を呼ばないこと。押したコミットが別ブランチ
だったり、自動解析が失敗した場合にだけ明示的に呼ぶ。新しく push した内容を反映
するには `pull_repository` を挟む。

**コミットを変えるたびに解析からやり直し**になる。`get_analysis` が 404 なら
未解析という意味なので `start_analysis` を呼ぶ（3〜5 分）。

`start_run` に渡すのは **`analysis_id` と、`get_analysis` が返した `experiments`
の要素の `id`** の 2 つだけ。実験の定義そのものを送り返してはいけない（サーバが
解析結果から読む）。別コミットや過去の解析の id を使い回すと、UI に出ない
orphaned run になる。

```python
start_run(
    repository_id=..., commit_hash=..., analysis_id=..., experiment_id=...,
    compute_id="byo:<uuid>",          # 省略すると managed compute に飛ぶ
    compute_type=..., resource_count=..., time_limit=...,
    user_dockerfile_path="Dockerfile",
    command_args=[...],               # §3 参照
)
```

- **`compute_id` を省略すると managed compute に飛ぶ。** BYO で回したいなら明示する
- 解析器が返す `required_env_vars` は**警告どまりで run を止めない**。足りない鍵が
  あれば実行時に落ちる。**ダミー値を `set_env_var` して埋めない** — 実行環境が
  注入する変数を上書きして実験そのものを壊す

W&B を使う場合、**entity 名は当てずっぽうだと通らない。** `wandb.Api().default_entity`
で実際の値を引いてから config に書く。あわせて、`wandb.init` の失敗で実験ごと
落ちない作りにしておくこと。

## 5. 追跡して回収する

`get_run` で追う。Temporal から状態を更新するので、生の REST が返す古い `status`
（`running` のまま固まることがある）に引きずられない。`close_time` が入っていれば
終了している。

終了したら `import_run_outputs` で成果物をリポジトリへ取り込む。**`execution_id` に
`start_run` が返した `run_id` を必ず渡す。** 省略すると AIRAS は自分が dispatch した
ときの命名規則で run を探しに行き、直接起動した run は見つからず
"No completed Seyval run found" で落ちる。`run_stage` は実行した mode と揃える。

**BYO Slurm では outputs はジョブ終了後に SSH で回収される。** 実行中に空でも
異常ではない。

**★ 打ち切られた run は SSH で救出できる（2026-08-07 実証）。**
BYO Slurm の成果物回収は**正常終了後にしか走らない**ので、殺された run では
`get_run_outputs` が空を返す。だが**ジョブディレクトリは共有ストレージに残る。**

```bash
scp -r <user>@<login node>:<job dir>/<run_id>/.research/results /tmp/rescue/
```

8時間28分・212系ぶんのチェックポイントを完全な形で回収した実績がある。
**run が死んだら、諦める前にここを見ること。**あわせて、系ごとに結果を書き出す
設計にしておくこと（最後にまとめて書くと、殺された時点で全部消える）。

なお**打ち切られた run では stdout が S3 に上がらない**（`NoSuchKey`）。
`get_run` が返す presigned URL は**発行から最大 1 時間で失効する**ので、URL を
保存せず `run_id` を保存して都度取り直す。

## 計算ノードから見える世界

**グループディレクトリ `/data1/<account>/<user>` は read-only**（`Errno 30`）。
ジョブ用のサブディレクトリだけが書き込み可で、親は read-only でマウントされる。
run をまたぐ永続キャッシュ（例: 数十 GB のデータセットを毎回落とし直さない）を
置きたい場合、現状の bind 設定では不可能。作業ディレクトリとノードローカルの
`/tmp` は書き込み可。

## pip で入らないソフトウェアを持ち込む

conda にしか無いもの（OpenStructure など）は **Dockerfile 内で micromamba を使い、
uv の venv とは別の prefix に入れて subprocess で呼ぶ**。実行時にブートストラップ
する案より優先する。イメージに焼けば実行のたびに入れ直さずに済み、コミット
ハッシュだけで環境が決まる。

```dockerfile
ENV MAMBA_ROOT_PREFIX=/opt/micromamba
RUN set -eux; \
    case "$(uname -m)" in \
      aarch64) MARCH=linux-aarch64 ;; \
      x86_64)  MARCH=linux-64 ;; \
    esac; \
    curl -Ls "https://micro.mamba.pm/api/micromamba/${MARCH}/latest" \
      | tar -xvj -C /usr/local bin/micromamba; \
    micromamba create -y -p /opt/ost -c conda-forge -c bioconda \
      python=3.12 openstructure=2.11.1; \
    micromamba clean --all --yes; \
    /opt/ost/bin/python -c "import ost"   # ビルド時に失敗させる
```

要点。

- **`uname -m` で分岐する。** 組まれるのは対象アーキのイメージなので、
  micromamba の URL を決め打ちしない
- **`bzip2` が要る**（micromamba の tarball が bz2）
- **prefix を分ける。** CLI 契約が uv 側を Python 3.11 に固定している一方、
  bioconda の OpenStructure 2.11.1 は aarch64 だと Python 3.12 必須。同居できない
  ので、スコアリングは `/opt/ost/bin/python` への subprocess で JSON をやり取りする
- **最後に import を走らせる。** 失敗を実行時ではなくビルド時に出せる

## 失敗の切り分け

`failure_origin` は `"user"`（コードの失敗）か `"system"`（Seyval 側）。ただし
**依存解決の非対応が `"system"` として返ることがある**ので、`"system"` を見ても
即座にインフラ障害と決めつけない。

Kaniko のビルドログを参照する API は無い。原因が読めないときは変数を 1 つずつ動かす。

1. **同一構成で再投入**する。同じエラーが再現すれば恒常的、しなければ一時的
2. **疑わしい要素を 1 つ抜いた版**を別ブランチで投入して比較する

**所要時間が毎回ほぼ同じでもタイムアウトとは限らない。** 2 回連続で約 240 秒
ちょうどで失敗したケースの真因は aarch64 wheel の不在だった。

**複数の run が同時に落ちたら、経過時間ではなく終了時刻の分散を見る。** 3 本の
開始が 3 分ばらけていたのに終了が 14 秒以内に集中していたケースがあり、真因は
worker のローリングデプロイだった。run ごとの上限なら終了も開始と同じだけずれる
はずで、**同時終了は外部イベントの署名**である。「経過時間が揃っている」方に
引きずられると誤診する。

打ち切られた run は stdout が残らないので、原因究明は上の抜き差しに頼ることになる。

## 見るものとツールの対応

| 見るもの | ツール |
|---|---|
| 状態・失敗の由来・終了時刻 | `get_run` |
| 実行中のログ | `tail_run_logs`（`since_id` に前回の `last_id` を渡して追尾） |
| 終了後の完全なログ | `get_run` が返す `stdout_url` / `stderr_url` を直接 GET |
| 生成された成果物 | `get_run_outputs` |
| **実際にビルドされた Dockerfile** | `get_run` の `dockerfile` フィールド |

`tail_run_logs` が保持するのは直近 1 万行程度で、高頻度出力は「... N 行省略」に
畳まれて**何度取り直しても出てこない**。完全な記録が要るなら終了後の presigned
URL の方を読む。

最後の行は、持ち込んだ Dockerfile が実際にそのまま使われたかの確認に使う。
リポジトリの実物と一致していなければ、`user_dockerfile_path` が届いていない。
