# AIRAS × Lean 実行リファレンス

`verifier.kind = lean` の claim を、実験と同じ `dispatch_experiment` →
`get_experiment_run_status` → `import_run_outputs` → `update_record` で通すための手順。
`run-experiments` の step 3 と `write-experiment-code` から参照される。

前提が 3 つ。**証明は `lean/` 配下の Lake プロジェクトに書く**（toolchain と mathlib は
リポジトリが pin している）、**`lean.json` は自分で書かない**（`make run` が
`lake exe airas-report` で書く。airas-eval が `metrics.json` を書くのと同じ分離）、
**statement は preregister で凍結される**（証明は後から書く。型が変わればその run は
inconclusive）。

## 手順（実験の流れのどこで何をするか）

実験とまったく同じ流れで、Lean が動くのは実装フェーズから。preregister の前に
Lean を実行することはない。

| 段階 | 実験 | Lean |
| --- | --- | --- |
| hypothesize-and-design | run_id と metric 名を決める | module・decl・定理の型（statement）を決める |
| preregister-paper | claim を凍結 | claim を凍結。statement は仕様として Lean の構文で手で書く（§1） |
| write-experiment-code | `src/` を書く。手元の sanity は反復のため | `lean/Airas/<Module>.lean` に statement と証明を書く（§2）。手元の `lake build` は反復のためで証拠にならない |
| run-experiments | backend で走らせ、`import_run_outputs` | 同じ（§3、§4） |
| publish-paper | `update_record` → 論文 | 同じ |

証拠になるのは backend（GitHub Actions か Seyval）の run が `make run` で書き、
`import_run_outputs` が provenance 付きで取り込んだ `lean.json` だけ。ローカルで
作った `lean.json` は commit しない（manifest も store も無いので gate で落ちる）。
push 後に statement を変えると凍結との不一致で inconclusive になり、証明を変えるなら
freeze commit の子孫で走り直す。手元で確かめてから push し、push 後は隔離された
環境の結果だけを使う、が原則。

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
- `statement` は定理の型を Lean が受理する式で書く。report ツールがこの文字列を
  モジュールと同じ環境で elaborate して項にし、ビルドされた宣言の型と束縛変数名を
  除いて一致するか（`statement_matches`）を判定するので、記法の違い（`Nat` と `ℕ`、
  `∑ i ∈ s, f i` と `Finset.sum s fun i => f i`、`∀ n,` と `(n : ℕ) →`）は問わない。
  定義上等しいだけの別の型（`n = n` に対する `n + 0 = n`）は一致しない。名前は
  完全修飾（`Finset.range`）で書くか、`config/run/<run_id>.yaml` の `open` に名前空間を
  列挙する（scoped な記法と短い名前がそこで有効になる。mathlib の `∑` と `ℕ` には不要）。
  不一致なら run は失敗し、record では inconclusive。
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
# open: BigOperators,Finset   # 宣言の statement が scoped 記法や短い名前を使うとき
```

`lean/lakefile.toml`、`lean/lake-manifest.json`、`lean/lean-toolchain`、
`lean/AirasReport.lean` は managed（Makefile と同じ）。依存を足したり版を上げたりするのは
record の verifier を変えることなので、勝手にやらない。`module` と `decl` は
英数字・`_`・`.`・`'` のみ。

### 未証明の部分を残して論文にするとき

`sorry` は許可できない（`sorryAx` は `allowed_axioms` に何を書いても error）。`sorry` は
匿名で、何を仮定したのかが record に残らないからである。部分的な形式化を出すなら、
穴を**名前付きの公理**として書き、claim の `allowed_axioms` に列挙する。

```lean
axiom sum_lemma_L (n : ℕ) : ∑ i ∈ Finset.range n, i = n * (n - 1) / 2   -- 未証明の補題
theorem main_thm (n : ℕ) : ... := by ... sum_lemma_L n ...
```

```
"allowed_axioms": ["propext", "Classical.choice", "Quot.sound", "sum_lemma_L"]
```

- `collectAxioms` が `sum_lemma_L` を返し、`allowed_axioms` にあるので supported。record と
  claims.tex に「この公理を仮定した上での結果」として残る。仮説の `assumptions` にも
  同じ補題を書く。
- 予定外の公理に頼れば inconclusive。`allowed_axioms` は preregister で凍結される。
- 後で証明できたら、公理を定理に置き換え、claim を同じ id で append して
  `allowed_axioms` から外す。前の entry も読める。

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

`LeanResult.id` には manifest の実行 id（GitHub Actions の run id）が写され、claims.tex の
Lean claim には realize 後に `Evidence: run <run_id>, execution <id>, commit <sha>; axioms: ...`
が描かれる。論文の claim 一覧から実行まで辿れるのはこのため。main.tex の Data Availability
には `\airasrecordlink{record.json}` を置く（`update_record` が record の commit 固定 URL で
定義する。prereg 段階は `\providecommand{\airasrecordlink}[1]{#1}` で素の文字）。

gate（`verify_record.yml`）は今のところ `lean.json` と record の一致と、artifact との
バイト比較まで。gate 自身が再ビルドして report を導き直すのは airas-org/airas#1020。

sanity stage は必須ではない。実装フェーズで、証明を書く前に statement だけを backend で
型検査したいときに使う（`sorry` のまま `run_stage="sanity"`）。結果は record に入らない。
