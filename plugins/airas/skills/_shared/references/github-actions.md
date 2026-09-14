# AIRAS × GitHub Actions 実行リファレンス

実験リポジトリの `run_experiment.yml` で回すための手順。`run-experiments` の
step 1 で GitHub Actions を選んだときに読む。

前提が 2 つ。runner は **`runner_label` で選ぶ**（既定 `["ubuntu-latest"]` は
CPU のみ。GPU は self-hosted runner を登録して `["self-hosted", "gpu"]` のように
指定する）、そして結果は **workflow の artifact に上がるだけ**で、
`import_run_outputs` を挟むまでリポジトリには入らない。

## フロー

```
dispatch_experiment       → backend="github_actions"。workflow_run_id を execution_id として返す
get_experiment_run_status → backend="github_actions"、github_owner / repository_name も渡す
import_run_outputs        → backend="github_actions"、execution_id、branch_name に staging ref(verify)
fetch_experiment_results  → リポジトリを読む
```

## 1. 起動する

```python
dispatch_experiment(
    github_owner=..., repository_name=..., branch_name=..., run_id=..., run_stage="sanity",
    backend="github_actions",
    runner_label=["ubuntu-latest"],
)
```

workflow は `src.main && make evaluate && src.evaluate` を 1 つのジョブで通し、
`.research/results/<run_id>/` を `<mode>-<run id>-<run_id>` という名前の artifact に
上げる。実行に必要な API キーは `set_github_actions_secrets` で repository secret に
入れておく（workflow が `-e` で渡す名前は `run_experiment.yml` を見る）。

`ubuntu-latest` の上限はジョブ 6 時間、ディスク約 14 GB。sanity と pilot 向けで、
full は GPU runner か Seyval を使う。

## 2. 追跡して回収する

`get_experiment_run_status(execution_id, backend="github_actions",
github_owner=..., repository_name=...)` で `status` / `conclusion` を見る。ログ末尾は
返らないので、失敗の原因は `execution_url` の run ページか
`download_workflow_artifacts` の `stdout.txt` / `stderr.txt` を読む。

`conclusion` が `success` になったら `import_run_outputs(backend="github_actions",
execution_id=..., branch_name="verify")` で artifact をリポジトリに取り込む。
`branch_name` は staging ref（`verify`）で、`main` ではない。取り込み後は

```
git pull --ff-only origin verify
```

## artifact の保持期限

artifact は既定 90 日で消える（private リポジトリは設定で 400 日まで延ばせる）。
`import_run_outputs` は取り込み時に各ファイルの sha256 を `.provenance.json` に
書くので、artifact が消えた後の record gate はそのハッシュと git 履歴で結果の
不変性を確かめる。期限内なら artifact のバイトと直接比較する。
