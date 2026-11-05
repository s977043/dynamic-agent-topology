# T0 が解けなかった Task での T1 の比較の事前登録（第 2 版）補遺 1: スクリーニング前の除外

状態: **下書き（補遺は未成立）**。本補遺は、独立レビュー・Operator の確定・merge 後の main で計算した blob hash の #244 への記録を経るまで成立しません（§6）。成立するまで、どの候補もスクリーニング前の除外として扱いません。本補遺は、スクリーニング Run を含む model 起動・予算消費の許可ではありません。予算の承認と課金が発生する model 起動は Human（Operator）専権で、Agent は代行しません（[AGENT_HARNESS.md](AGENT_HARNESS.md) の自律境界）。

- 起案日: 2026-11-05 / 基準: origin/main `b85b5ac`（PR #304 の merge commit `b85b5ac13fe077386c0dba9b22900eeeef12c999`）
- 対象 Issue: [#244](https://github.com/s977043/dynamic-agent-topology/issues/244)
- 補う文書: [HARD_TASK_T0_FAIL_T1_PREREGISTRATION.md](HARD_TASK_T0_FAIL_T1_PREREGISTRATION.md)（以下「本文」。blob `57007effd1fd502c86ea7e63029352df902670d0`、[#244 の確定 blob 記録](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6428095927)で成立済み）。本文は成立後に書き換えないと定めているため（本文の成立条件）、本文は変えず、別ファイルの補遺とする
- 経緯: PR #304 で、本文 §3 のスクリーニングで T0 に渡す症状説明を order 6〜44 のうち 32 件に置いた。残る 7 件（order 10・11・16・26・28・32・38）には説明を置かなかった。その除外の規則は本文 §3 にないため、補遺として固定すると [#244 のコメント（2026-11-05）](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6652857499)と PR #304 の本文で予告した
- 一次ソース: 本文、[hard-task/CANDIDATES.yaml](hard-task/CANDIDATES.yaml)（以下「候補表」。blob `aad6f23629efaefdd266f0e21ca59248e4693c7b`）、[hard-task/task-descriptions/](hard-task/task-descriptions/)、[hard-task/CALIBRATION_RUNBOOK.md](hard-task/CALIBRATION_RUNBOOK.md) §6、PR #304 の独立レビュー 2 回（Codex gpt-6.1-sol / high、read-only。1 回目は head `d83852b` で CHANGES_REQUIRED、2 回目は head `2f01697` で MERGE_OK）
- 形式の先例: [HARD_TASK_T0_T1_PREREGISTRATION.md](HARD_TASK_T0_T1_PREREGISTRATION.md)、[MODEL_ROLE_SPLIT_PREREGISTRATION.md](MODEL_ROLE_SPLIT_PREREGISTRATION.md)

## 0. Source claim・Evidence・解釈・Judgment の区別

| 区分 | 内容 |
|---|---|
| Source claim | 各候補の上流 fixCommit のテスト（AC）が、修正で新設する名前や具体値を直接参照している、という点は上流 repo の公開 commit の内容で、DAT の観測ではない |
| 観測済み DAT Evidence | 候補表の各候補の repo・revision・fixCommit・failingBeforeFix。PR #304 の独立レビュー 1 回目が order 06〜44 の説明 36 件を OK 25・要修正 8・除外推奨 3（26・32・38）と判定し、未作成の 11・16・28 を除外推奨と記録した。2 回目が要修正 7 件の解消と、order 10・26・32・38 の削除の妥当性を確認した（order 10 は、修正前の revision で 9 通りの符号化と復号がすべて成功し、正解バイト列との不一致以外の不具合を公開動作で裏付けられなかった）。order 6 以降のスクリーニング Run は 0 件 |
| DAT 側の解釈 | 7 件は、症状だけの説明を渡す条件では、T0 / T1 が症状を正しく直しても現行 AC を満たせない場合が残る。スクリーニングに入れると、Topology の効果ではなく説明と AC の不整合を測ることになる |
| Judgment（設計判断） | §1 の判定基準と §3 の扱いを推奨する（Agent の起案。独立レビューと Operator の確定を経て成立）。実験結果についての Judgment はなし |

## 1. 判定基準

**基準 E1（説明と AC の不整合）**: 次のどちらかに当たる候補を、スクリーニングの前に除外する。

1. 現行 AC（候補表の `acceptanceCriteria`。fixCommit で追加・変更されたテスト）が、修正で新設する公開 API・引数・例外型、または私有の実装（属性・helper の名前）を直接参照し、症状・再現手順・期待結果・実際の結果だけの説明（CALIBRATION_RUNBOOK §6 の書き方）からはその名前や仕様を導けない。
2. 症状を示すには AC の正解の具体値（期待するバイト列など）を説明に書くしかなく、具体値を除くと、修正前の revision で観測できる公開動作の不具合が説明に残らない。

- 説明にそれらの名前・具体値を書き足して候補を残すことはしない（解答を渡すことになるため。CALIBRATION_RUNBOOK §6 の決定と同じ）。
- 判定は説明・候補表・上流の fixCommit と AC の静的な確認、および修正前の revision での再現コードの実行だけで行い、model の Run 結果を使わない。
- **適用範囲**: 基準は候補表の初回 44 件のうち、未スクリーニングの order 06〜44 の 39 件すべてに同じに適用した。order 01〜05 は本文 §3.1 によりスクリーニング済みとして扱い、本補遺の対象外とする（5 件とも説明があり、#253 で固定済み）。
- **適用結果**: order 06〜44 の 39 件のうち、E1 に当たったのは 7 件、当たらなかったのは 32 件。32 件は PR #304 の独立レビューで OK（1 回目の OK 25 件と、2 回目で解消を確認した 7 件）となり、説明が置かれている（SHA-256 は [#244 の記録](https://github.com/s977043/dynamic-agent-topology/issues/244#issuecomment-6652857499)）。

## 2. 除外する 7 件

判定時点はいずれも PR #304 の merge（2026-11-05T07:58:49Z）より前。判定者は作成に関与していない独立レビュー（Codex gpt-6.1-sol / high）で、1 回目は head `d83852b`、2 回目は head `2f01697`。repo@revision・fixCommit・AC は候補表から転記した。

| order | repo@revision | fixCommit | 該当する AC（failingBeforeFix） | 基準 | 除外理由 | 判定 |
|---|---|---|---|---|---|---|
| 10 | `https://github.com/pyasn1/pyasn1@7b3f79cac2ce765537baa406762d59eae47de04c` | `62efcb94b15ca7fbd5261ca999bf5eca5680de5f` | `tests.codec.cer/der.test_encoder` の `testEncodeOpenTypeChoiceOne`・`testEncodeOpenTypeChoiceTwo`（計 8 件） | E1-2 | 説明の期待結果が AC の具体的な符号化期待値（バイト列）そのものだった。具体値を除くと、修正前の revision で 9 通り（タグなし・implicit・explicit × BER・CER・DER）の符号化と復号がすべて成功し、公開動作の不具合を裏付けられなかった。別の入力を含めて不具合が存在しないことの証明ではない | 1 回目: 要修正（裏付けられなければ除外が妥当）→ 2 回目: 削除を支持 |
| 11 | `https://github.com/python/typing_extensions@700eadd2bad0bb118a884dd85adbcd073a2c0046` | `ca41832bbce2f2d800edbca0a2a48fb66ae406be` | `ConcatenateTests.test_is_param_expr`・`ParamSpecTests.test_is_param_expr` | E1-1 | AC が修正で新設する私有 helper `typing_extensions._is_param_expr` を直接呼ぶ。公開 API の症状を説明しても、この helper 名の採用は導けない。公開症状が全く存在しないとまでは、静的確認からは断定しない | 1 回目: 除外推奨（未作成を支持） |
| 16 | `https://github.com/pyparsing/pyparsing@b6dccc8f796f4879b8bdc62aac8fe94d73d90f60` | `51560caba558d87349f4f497b82acef1de9ec8f8` | `testOneOrMoreMax`・`testOneOrMoreMaxNegative`・`testZeroOrMoreMax`・`testZeroOrMoreMaxNegative`（Test09 / Test10、計 6 件） | E1-1 | 大きな上限の反復という既存 API の症状は説明できる。ただし AC は新設する `OneOrMore(..., max=...)`・`ZeroOrMore(..., max=...)` と値の検証も要求し、症状の修正だけでは新しい引数仕様を要求する AC を満たせない | 1 回目: 除外推奨（未作成を支持） |
| 26 | `https://github.com/pyasn1/pyasn1@ca9ec2e4182a020764eb29f1b80af73678a20e54` | `24b16971d3455b4f51a6fbd2bad6462c9302000e` | `SequenceWithoutSchema.testExplicitEmptyComponentTypeOverridePreserved`、`Choice` / `SequenceWithoutSchema` の `testLateBoundComponentTypeOnExistingInstance` | E1-1 | AC が修正で新設する私有属性 `_componentTypeExplicit` を `del s.__dict__['_componentTypeExplicit']` で直接削除する。別の実装で症状を直しても `KeyError` になり得る。原理的に絶対不可能とまでは断定しないが、未提示の実装選択を採点条件にしている | 1 回目: 除外推奨 → 2 回目: 削除を確認 |
| 28 | `https://github.com/cpburnz/python-pathspec@811bde1c624e85accee683b9cbf07c01538afacb` | `3ceb237ff97ffad067b35c98a512cf975232f0b1` | `test_09_single_backslash_fail`、`test_09_single_exclamation_mark_fail`（basic / spec、計 3 件） | E1-1 | 単独のバックスラッシュ等の既存動作は症状として説明できる。ただし AC は新設する `errors='literal'/'null'/'raise'` の仕様を直接検査し、これを伏せた説明と AC が整合しない | 1 回目: 除外推奨（未作成を支持） |
| 32 | `https://github.com/rthalley/dnspython@1f1888d35b820f67f3bb9262427e8b64f44d62f8` | `78362aa6b9bce8f0942577c72773cb36c5050b92` | `RRsetTestCase` の `testFullMatch1`・`testFullMatch2`・`testMatchCompatibilityWithRdatasetMatch`・`testNoFullMatch1〜3` | E1-1 | 修正で導入する API `full_match` を AC の複数テストが直接呼ぶ。名前を消すと、既存 `match` の互換性を直しても AC を満たせない場合が残る | 1 回目: 除外推奨 → 2 回目: 削除を確認 |
| 38 | `https://github.com/rthalley/dnspython@380846b2d6b550963d3e117f15abf8da26d18505` | `51a96a2e2c80aaf81229ce01e3f74a15d67f7ef9` | `RdataTestCase.test_relative_vs_absolute_compare`・`test_relative_vs_relative_compare`、`ZoneDigestTestCase.test_relative_zone_sorting` | E1-1 | 修正で新設する例外型 `NoRelativeRdataOrdering` を AC が直接参照する。名前を伏せると、意味上は妥当な別の例外型で失敗し、名前を書くと解答を渡すことになる | 1 回目: 除外推奨 → 2 回目: 削除を確認 |

## 3. 扱い

- 除外した候補も候補表の元の order のまま残し、order を詰めず番号を振り直さない。候補表は変更しない。
- 除外した候補は、失敗・0/3・budget-excluded のどれにも数えず、評価集合の 12 件にも入れない。スクリーニング Run を行わない。
- 残りの候補（order 06〜44 のうち 32 件）を元の order の昇順で処理し、本文 §3 と §3.1 の規則（order 1〜5 の n1〜n3 の再利用を含む）のとおり、0/3 が 12 件そろった時点で止める。
- 初回 44 件の範囲で 12 件に届かなければ、本文 §3 のとおり feasibility-only とし、予備の候補で補わない。除外した 7 件の分を予備から足すこともしない。
- 報告では、評価集合が「E1 で除外した後の候補集合」に条件付くことを、本文 §2.2 の「結論の射程」に加えて明記する。除外件数と order を併記する。

## 4. model の結果を見ていないこと

- order 6 以降のスクリーニング Run は 0 件で、7 件の判定はすべて model の結果より前に行った。
- order 1〜5 には較正 25 Run（#244、2026-10-26 の結果コメント）があるが、7 件に含まれず、E1 の判定にも使っていない。
- 判定に使ったのは、候補表・上流の fixCommit と AC・説明の静的な確認と、修正前の revision での再現コードの実行（order 10 の 9 通りを含む）だけである。

## 5. 制限

- **後から追加した選定規則**: E1 は候補表の作成と固定（blob `aad6f236…`）および本文の成立の後に、説明を作る過程で必要になって追加した規則である。model の結果は見ていないが、説明の作成とレビューの結果（どの候補が説明できなかったか）を見た後に基準を言語化したため、基準が 7 件から独立に決まったことはこの記録では検証できない。報告ではこの事実を制限として残す。
- **判定の確度**: 判定は静的な確認と限られた再現の実行による。order 10・11・26 については「公開動作の不具合が存在しない」「AC を満たすことが不可能」とまでは断定していない（§2）。
- **採らない代替案**: 7 件の AC を症状に対応する外部動作の検証に改め、候補として残す方法は採らない。理由: (1) AC の固定条件（候補表の `acceptanceCriteria` と negativeOracle の「AC のテストファイルが修正 commit の blob と一致すること」）が変わり、本文と候補表のまま実行する扱いにできない。(2) 新しい AC の妥当性に別の独立レビューが要り、候補ごとに AC を作る判断が新しい恣意性になる。(3) 除外しても残り 32 件で本文の手順は実行でき、不足すれば本文どおり feasibility-only になる。
- **偏り**: 新設 API・引数・例外型を伴う修正を持つ候補が評価集合から外れるため、評価集合は「既存の公開動作の範囲で直せる不具合」に偏る。

## 6. 成立の手順

本文 §7 と同じ流れで成立させる。

1. **補遺の起案**（本書、Agent）。
2. **独立レビュー**: 作成とは別のセッションの Reviewer が、本書・本文・候補表・説明・PR #304 の 2 回のレビューを材料に確認し、MERGE_OK まで修正する。
3. **Operator の確定**: Operator が §1 の基準と §2 の 7 件、§3 の扱いを #244 で確定する（**未確定**）。
4. **merge と hash の記録**: merge 後の main で本書の blob hash を計算し #244 に記録する（Agent。HOTL の範囲の記録操作）。この時点で補遺が成立する。成立後に結果を見て本書を書き換えない。
5. 成立は model 起動の許可ではない。スクリーニングの起動には、本文 §5.1b の停止条件の解消と、キットのスクリーニングモード（除外した order を処理しないことを含む）の準備、Operator の判断が別に要る。

## 7. 未確認（UNKNOWN / NOT_TESTED）

- 7 件で、症状だけの説明から T0 / T1 が現行 AC を満たせる可能性が実際にどの程度あるか（**NOT_TESTED**。model を起動していない）。
- E1 による除外が、残る候補での 0/3 の割合 q0 にどう影響するか（**UNKNOWN**）。
