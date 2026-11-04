# 保存成果物の順序反転リプレイ計画

2026-11-04。参照mainは `541a4bed`（実行manifestに完全SHAを保存）。#293の保存済み成果物と独立oracleを使うP0の再現性確認。新しいmodel実行やWorker/Verifierの反復ではない。

仮説: 同一oracle・同一成果物の採点は、順序T0→T1とT1→T0の2 blockで同じ結果を返す。変われば再現性FAIL。初期コードの負の対照は6/18、保存最終成果物は両方18/18を期待する（既知結果の再現であり、新しいheld-out評価ではない）。

固定するもの: task、oracle、初期・T0・T1成果物は親directoryの保存版。実行前にhashをmanifestへ保存し、終了後に再照合。各blockに負の対照を先行させ、各採点は新しいPython subprocess、timeout 30秒、同一Python・権限・環境で行う。新しいモデル起動、依存導入、外部通信はない。2 blockを上限とし、結果を見て反復数を増やさない。

b01: control→T0→T1。b02: control→T1→T0。各出力をopaque labelで保存し、arm対応表を別ファイルへ置く。採点器にはarm名を入力しない。ただし元コード/hashは公開され共有FSなので厳密な盲検・隔離を保証しない。これはlabel分離のリハーサルである。

欠測・異常を除外しない。subprocess exit、stderr、timeout、JSON取得不能と開始終了monotonic時刻を保存。失敗があっても残りの固定6採点を記録し、最終exitは非0にする。既存出力directoryへの上書きは拒否。計測はPython採点の経過時間で、agent latencyではない。model/effort/token/USD/human attentionはnull、理由を記録する。OS/cache負荷やkernel cacheは統制しない。

完了条件: 全6採点の記録、期待結果との照合、前後hash一致、上書き拒否と欠落source時の失敗記録を確認する。oracleは変更しない。実モデル比較、native dispatch、隔離、選択効果、費用・注意力は未検証のまま。
