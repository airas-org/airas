# AIRAS × Lean 実行リファレンス

`verifier.kind = lean` の claim を、実験と同じ `dispatch_experiment` →
`get_experiment_run_status` → `import_run_outputs` → `update_record` で通すための手順。
`run-experiments` の step 3 と `write-experiment-code` から参照される。

前提が 3 つ。**証明は `lean/` 配下の Lake プロジェクトに書く**（toolchain と mathlib は
リポジトリが pin している）、**`lean.json` は自分で書かない**（`make run` が
`lake exe airas-report` で書く。airas-eval が `metrics.json` を書くのと同じ分離）、
**statement は preregister で凍結される**（証明は後から書く。型が変わればその run は
inconclusive）。

## 1. record に宣言する

```
"verifier": {"kind": "lean", "toolchain": "leanprover/lean4:v4.33.1",
             "mathlib_rev": "<lean/lake-manifest.json の mathlib の rev>",
             "allowed_axioms": ["propext", "Classical.choice", "Quot.sound"]},
"designs": [{"id": "d1", "runs": [{"run_id": "thm1",
    "params": {"module": "Airas.Thm1", "decl": "thm1",
               "statement": "∀ (n : ℕ), n + 0 = n"}}]}]
```

- `toolchain` は `lean/lean-toolchain`、`mathlib_rev` は `lean/lake-manifest.json` の
  `mathlib` の `rev` をそのまま写す。report と一致しなければ error になる。
- `statement` は `#check @thm1` が出す型。空白の違いは無視されるが、記法の違い
  （`Nat` と `ℕ`）は違う型として扱われる。mathlib を import するなら `ℕ` で書く。
- `allowed_axioms` の既定は標準 3 公理。`sorryAx` は常に error。

## 2. 証明を書く

| Path | 役割 |
| --- | --- |
| `lean/Airas/<Module>.lean` | 定理と証明。1 run = 1 宣言 |
| `lean/Airas.lean` | ルート。書いたモジュールを import に足す |
| `config/run/<run_id>.yaml` | `kind: lean`、`module`、`decl` の 3 行 |

```yaml
kind: lean
module: Airas.Thm1
decl: thm1
```

`lean/lakefile.toml`、`lean/lake-manifest.json`、`lean/lean-toolchain`、
`lean/AirasReport.lean` は managed（Makefile と同じ）。依存を足したり版を上げたりするのは
record の verifier を変えることなので、勝手にやらない。`module` と `decl` は
英数字・`_`・`.`・`'` のみ。

## 3. 走らせる

実験と同じく `dispatch_experiment(run_id=..., run_stage=...)` で起動する。backend は
GitHub Actions を本線にする（GPU も長時間も不要。`ubuntu-latest` で mathlib の
キャッシュ取得が数分）。Seyval でも `make run` がそのまま通る。

| stage | 意味 | 通る条件 |
| --- | --- | --- |
| `sanity` | statement が型検査を通る | ビルド成功（`sorry` 許容） |
| `full` | 完全証明 | ビルド成功かつ `sorry` 無し |
| `pilot` | 無い | 拒否される |

`make run` の中身は `lake exe cache get` → `lake build <module>` →
`lake exe airas-report`。report は判定しない（statement の一致と公理の可否は
`update_record` が決める）が、ビルド失敗と full での `sorry` は run 自体を失敗にする。

## 4. 回収して record に載せる

`import_run_outputs` が `.research/results/<run_id>/` の `lean.json` と `build.txt` を
provenance 付きで commit し、`update_record` が `lean.json` を `LeanResult` として
追記して verdict を導く。

```
{"commit", "toolchain", "mathlib_rev", "module", "decl", "mode",
 "statement", "axioms", "errors", "warnings"}
```

verdict は `supported`（errors が空）か `inconclusive`（ビルド失敗、`sorry`、
statement 不一致、module / decl / toolchain / mathlib_rev の不一致、許可外公理）の
どちらか。Lean は反証しない。

gate（`verify_record.yml`）は今のところ `lean.json` と record の一致と、artifact との
バイト比較まで。gate 自身が再ビルドして report を導き直すのは airas-org/airas#1020。
