# Provenance監査の運用評価（#57）

2026-10-15 JST、main `45a50fef75531299682a6332e4d0b696b52ff678` のチェックポイント。#188のread-only audit実装を、既存の受理検査・手動レビューと比較します。非規範的な運用提案であり、旧Runのacceptance・DECISION・Schemaを変更しません。

## 検出範囲の比較

Python 3.12.14で既存の合成fixture9件を再監査しました。canonical validatorの比較結果は[設計時の実測](PROVENANCE_AUDIT_DESIGN.md#12-負側fixtureによる再現)を参照します。手動レビューは既存PR templateのCross-artifact consistency reviewを基準に、確認できる範囲を記載しています。手動検出率・所要時間は未実測です。

| 対象 | 独立audit実測 | canonical検査の既存実測 | 手動レビューで必要な材料 |
|---|---|---|---|
| baseline-consistent | PASS | exit 0 | 一致値の照合 |
| ctl-trace-model-mismatch | FAIL | exit 1 | runtime/model原文 |
| session / fresh / timestamp / token mismatch（4ケース） | 各FAIL | 各exit 0 | 各Artifactの同じ関係を原文照合 |
| token / wallclock欠測、session unknown（3ケース） | 各UNKNOWN | 各exit 0 | 欠測を明示、原本の追加確認 |
| 受理済み18 Run | 18 PASS / 0 FAIL / 0 UNKNOWN | completenessは期待18件PASS | 既存受理の制約・原本・環境Gateを保持 |
| 原本偽造、記録外の副作用、Permission違反 | 観測範囲外 | この比較の対象外 | 独立原本・実行環境・Enforcer証跡が別途必要 |

機械の一致は同じCapture sequenceから生成された値の内部整合です。観測範囲外を「違反0」と推定しません。UNKNOWNのprocess exitは0でも、PASSや受理とは数えません。FAILはexit1で、実際の不一致か入力/解釈の問題かをReviewerが調査します。

## 機械実行コストの実測

Codex cloudのLinux x86_64、kernel 6.18.44、Python 3.12.14、上記SHAで、18 Runに対するCLIを新しいsubprocessとして5回実行しました。各回exit0、`SUMMARY PASSED=18 FAILED=0 UNKNOWN=0` を確認しました。

- elapsed ms: `141.512, 151.660, 150.533, 142.586, 144.278`
- median: `144.278 ms`、min–max: `141.512–151.660 ms`
- 計測範囲: `time.perf_counter()`でsubprocess開始から終了まで。Python起動、YAML読込、照合、capture_outputを含む。Git fetch、依存導入、CI待ち、手動レビューを含まない。
- 同じfilesystem cacheを共有する逐次5回であり、cold-cache benchmarkや他端末/CIの速度保証ではない。18 Run以外へのスケール特性は未測定。

再現コマンド:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/audit_provenance.py \
  --runs-root experiments/EXP-001-t0-vs-t1/runs/pilot-codex
PYTHONDONTWRITEBYTECODE=1 python scripts/test_audit_provenance.py
```

所要時間の再測定ではPython版、main SHA、環境、反復数、計測境界を記録します。手動レビューとの速度比や工数削減量は、手動側の独立計測なしには算出しません。

同じ計測境界での再測定例:

```bash
PYTHONDONTWRITEBYTECODE=1 python - <<'PY'
import statistics, subprocess, sys, time
elapsed = []
for _ in range(5):
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, 'scripts/audit_provenance.py', '--runs-root',
         'experiments/EXP-001-t0-vs-t1/runs/pilot-codex'],
        capture_output=True, text=True)
    elapsed.append((time.perf_counter() - start) * 1000)
    assert result.returncode == 0, result.stderr
    assert 'SUMMARY PASSED=18 FAILED=0 UNKNOWN=0' in result.stdout
print(elapsed, 'median_ms=', statistics.median(elapsed))
PY
```

## 運用上の提案と撤回条件

案Bのread-only報告と既存の負側testsを維持することを提案します。合成の不一致と欠測を区別でき、現時点の機械コストは上記環境で小さく、受理ゲートを変えずに手動レビューの照合材料を補えます。既存CIはtestsを実行し、運用CLIの報告そのものを新しいRun acceptance gateへ置換しません。手動レビューと原本確認は継続します。

誤検出、意味の異なるfieldの比較、観測欠落のPASS化、保守コストが確認された場合はIssueに事例を残し、audit/test/CI stepの撤回または修正を独立レビューします。過去のRunデータと受理判定は書き換えません。

現18件の一致だけではSchemaの必須化を正当化できません。次Experimentで必要field、欠測の扱い、Runtimeごとの差を宣言し、受理意味論とversioningを別PRでレビューします。原本独立性、実運用の手動工数、監査の常用/撤回の最終判断は未解決で、#57をこの報告だけで完了扱いにはしません。
