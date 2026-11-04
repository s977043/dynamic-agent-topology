# DAT手動dispatch canary（2026-11-03）

## 対象と完了条件

公開可能な小さいPython修正をT0とWorker→Verifierで各1回試す。構成選択の理由、実際のhandoff、独立した固定oracleによる結果、計測できた時間と欠測を残す。DATの自動dispatch実装や有効性の採用判断は行わない。

参照main: `95a4c8dad9564c1235108c0bee77161c0c1225ef`。開始時worktreeはclean、専用branch `research/dat-runtime-canary-20261103`。#291・#292はmerged、#288はdraftのまま。#287の人間計時、#248のfolding、#220のモデル役割分担と重複させない。これらの承認・完了条件は本canaryで満たさない。

## 構成選択

[dat-select](../../skills/dat-select/SKILL.md)をローカルファイルとして読み、[R0](../../policies/routing/R0_dynamic.yaml)の先頭分岐 `complexity: low, ambiguity: low` によりT0を選択した。辞書の選択規則が明示された1関数修正で、外部副作用がない。P0は固定テスト実行には十分だが未知の修正を作る役割は担わない。T1は比較候補としてのみ実行し、標準構成へ昇格しない。独立した助言ReviewerとVerifierを同一視しない。

## 実行方式の境界

- Plugin manifest/skillsの静的検証: `python scripts/validate_plugin.py` 成功。今回のhostへのPlugin登録・自動ロードは未検証。
- Skill利用: DATリポジトリの手順を明示的に読み適用した。Plugin経由の呼出しとは主張しない。
- orchestration: hostの通常collaborationツールを親が手動で呼び、別セッションに依頼する方式。DATコードによる選択結果からの自動dispatchではない。
- native: Codex CLI 0.159.2のhelpにagentsコマンドがあることを確認。ただしCLI model起動・custom role設定・native agents登録を試していない。CLIはPATH alias作成にread-only警告を出した。CLI版はhostのmodel/runtime版の証拠ではない。
- DATのREADME、Skill、Codex adapter、plugin manifestは自動applyしない契約で一致する。自動dispatchに進むには別のruntime mapping設計が必要。既存Skillに暗黙の起動機能を追加する変更は今回しない。

## 事前固定

[PLAN.md](PLAN.md)、[task.md](task.md)、[initial.py](initial.py)をworkers開始前にcommit。oracleは別セッションで作り、両workerへ結果を見せる前にhash固定する。原本planは英語のまま保存する。全fixtureは本検証のために作成した公開可能な合成データ。非公開プロジェクト資料・会話・認証・raw traceは含めない。

結果は後段に記録する。RunObservationやcanonical RunEvaluationではなく、このcanary固有の資料である。

## 実測と解釈

blockId=`cloud-dispatch-20261103-b01`、scenario=`latest-valid-record`。T0先行、T1後行、各1回。両workerは同じ[依頼テンプレート](WORKER_PROMPT.md)と初期コードから開始し、T1のみ別セッションVerifierがworker成果物を確認した。VerifierはPASS、修正要求なし。初回と最終のT1コードは同一。fork_turns=noneで親会話を渡さず起動したが、モデル・effortの実効値やアクセス隔離の証明ではない。

| 観測 | T0 | T1候補 |
|---|---:|---:|
| worker起動数 | 1 | 1 |
| verifier起動数 | 0 | 1 |
| 親の開始〜完了観測時間 | 32.325秒 | 68.605秒 |
| うちworker区間 | 32.325秒 | 34.217秒 |
| うちverifier区間 | 該当なし | 34.388秒 |
| verifier指摘による修正 | 該当なし | 0 |
| 実効model / effort | null | null |
| tokens / USD / 人間注意時間 | null | null |

時刻原本・計測式の入力は[measurement.json](measurement.json)。monotonic clockでspawn直前と親が完了を観測した直後を記録した。host待ち・tool処理・親の観測遅れを含み、モデル推論時間ではない。oracle準備・採点・PR作業は除外したため総開発コストでもない。計測取得不能値を0にしない。

固定した18ケースの採点は[evaluate.py](evaluate.py)で独立evaluatorが実行する。T0とT1の追加自己テストはそれぞれ異なるため、その件数を品質差の比較には使わない。実行task名はmeasurementに残すが、platform session IDや異なるモデルの証明ではない。

### 限界と次の最小実験

この1組は**実モデルを使った手動連携のfeasibility**であり、offline/mockをliveに数えたものではない。一方、統制されたpaired efficacy実験ではない。model/effort不明、共有filesystem、順序固定、cache/host負荷未統制、worker自己テストの差、親の観測遅れ、容易な単一課題による天井効果がある。T1の追加呼出しと経過時間は観測できても、速度・品質・費用の優劣に一般化できない。selector精度や「すべての課題で最も単純で十分」を証明しない。

現状の選択はT0維持。T1への複雑化を支持する独立した品質改善の証拠が必要である。自動dispatch/native登録・実効権限・人間時間は未検証。

次は新runtimeを実装する前に、実効model/effortとusage、等価なworkspace/権限を取得できる既存runtimeを確認し、同じtaskの順序反転1組を別blockとして事前固定する。条件が取得できなければ有効性比較を開始しない。有料model起動や予算承認は既存Operator境界に従う。#244の難課題実験、#248、#287にこのcanaryを代入しない。

## 再現

Python 3.12、標準ライブラリのみ。保存成果物の採点を再実行できる（モデルの再実行・同一出力は保証しない）。

```sh
PYTHONDONTWRITEBYTECODE=1 python docs/runtime-canary/evaluate.py docs/runtime-canary/initial.py
# 負の対照。exit 1を期待。
PYTHONDONTWRITEBYTECODE=1 python docs/runtime-canary/evaluate.py docs/runtime-canary/t0-final.py
PYTHONDONTWRITEBYTECODE=1 python docs/runtime-canary/evaluate.py docs/runtime-canary/t1-final.py
```

oracleは信頼済みのこの小さな保存fixture専用。Python importを実行するので、未信頼コードのsandboxや一般的なベンチ実行器ではない。

## 独立採点結果

`/root/oracle`（修正担当とは別セッション）が固定oracleを使って採点し、plan・task・初期コード・oracleが事前固定commit `6136a92` とbyte単位で一致することを確認した。

| 対象 | PASS | FAIL | 記録 |
|---|---:|---:|---|
| 初期コード（負の対照） | 6/18 | 12/18 | [initial.json](initial.json) |
| T0最終コード | 18/18 | 0/18 | [t0.json](t0.json) |
| T1最終コード | 18/18 | 0/18 | [t1.json](t1.json) |

oracle SHA256: `fc5a50aca33f897c54c2f0afc6500f878a8fd37f5d2ab04764551e11d1b97fd6`。両armの成功数差は0。負の対照が12件失敗したため全件無条件PASSの判定器ではないが、18例で全入力の正しさを証明するものではない。非破壊性の検査は終了時点の値と要素identityを調べ、一時的に変更して復元する実装は検出しない。custom subclass、性能・並行性・悪意あるruntimeは対象外。ソースの目視確認も別に行った。

この結果は、当該小課題をT0でも解けたことと、T1のhandoffを実行できたことを示す。T1を標準採用する根拠にはしない。
