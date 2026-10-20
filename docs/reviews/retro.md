# Retro 五項改善：#2 前置完成紀錄

範圍起點：`823e091`。依使用者確認，在 #2 開始前完成本次五項環境改善；未開始離線核心、產品 CLI／GUI，也未修改 oracle fixtures、原有 `2026-10-20` snapshot 或版本狀態。

| 改善 | 交付 |
|---|---|
| 統一檢查與 guardrail | `scripts/dev.py check`、Windows/Linux GitHub Actions；明確 EULA 的整合入口 |
| 證據封存及唯讀驗證 | `scripts/evidence.py`，缺檔／多檔／雜湊／預期實際值／來源 commit 檢查，拒絕覆寫；suite receipt 綁定所有被封存 run artifacts |
| 更新 agent 導覽 | 精簡 AGENTS.md，以 README／開發指南為命令與維護流程入口，加入文件失效 review 要求 |
| doctor 預檢 | Python、Git、GitHub CLI PATH、Docker daemon/Linux；無主機 Java 依賴，環境錯誤獨立退出碼 |
| 降低探索輸出 | javap 完整檔依 image ID 快取，指定方法、原始行號與顯示上限 |

## Validation

- `python scripts/dev.py check`：9 項工具測試，包含成功封存、覆寫拒絕、來源／provenance 變更拒絕、缺失／損毀／多餘 artifact、歷史／當前來源區別、EULA gate、doctor。
- `python scripts/dev.py check --integration --accept-eula`：固定映像 Java 編譯檢查與原版完整 2 個 test methods（5 個新世界）通過。補強 receipt 後最新 suite 為 127.503 秒；固定案例 19 列，加 2 次重複查詢。
- 真實結果封存及唯讀重驗使用全新 `validation/reference/evidence/2026-10-20-retro-final/`；其 summary 釘選受測來源 commit。歷史 snapshot 對 `823e091` Git blobs 另行重驗。
- Bytecode 工具實測 `getDispensingItems`，只顯示 12 行（方法共 65 行），完整 class 保存快取。
- doctor 實測：Python 3.13.14、Git 可用、Docker Linux daemon 可用；gh 不在 PATH，正確列為可選缺項。指定 `--github` 時視為環境缺項。
- 沙箱內 Windows tempfile 與 Docker pipe 權限失敗；相同檢查在獲准的沙箱外通過。這是 agent 執行限制，不算原版測試失敗。

## Standards review

獨立唯讀 reviewer 對 `git diff --cached 823e091` 初審有 2 項具體發現：缺少本完成紀錄、whitespace 只檢查 unstaged diff。已新增本檔，並檢查 tracked text 的行尾空白、staged 與 unstaged diff，讓乾淨 CI checkout 也能檢查。

另有 case 名稱重複的判斷性建議；目前維持固定三組 reference contract，避免擴大重構。run artifacts 的路徑與雜湊收集由共用函式統一處理。

最終 staged 差異複查：兩項具體發現已解決，無剩餘 blocker；固定 case 名稱重複維持非阻擋建議。

## Spec review

獨立唯讀 reviewer 初審有 1 項 P2：receipt 未涵蓋 run request／provenance／log／properties／normalizer。已補齊，新增測試後改動 provenance 必須拒絕發布的回歸測試，再重跑原版 suite。

最終 staged 差異複查：P2 已解決，無剩餘 blocker。reviewer 查閱程式與回歸測試，原版 suite 由主 agent 執行並記錄。

## 限制與順序

GitHub Actions 已設定，尚未 push，故未聲稱遠端 CI 執行成功。本機平台仍為 Windows 10 x64，未做 Windows 11 產品發布驗收；未測量 token 節省量或峰值記憶體。26.2 仍 `unverified`，核心比對仍為 0。

本次只完成 #2 前的 retro 改善；#2 留待下一個明確實作任務。無發布 issue／comment、push 或 PR。
