# 開發與證據維護

Retro 五項改善是 #2 前置工作，完成紀錄見 [retro review](reviews/retro.md)。此工作不實作離線核心，也不改變版本驗證門檻。

## 檢查與環境

命令入口見 [README](../README.md)。先執行 `python -m pip install -r requirements-dev.txt` 安裝 pytest；Python 測試使用 pytest，不使用 unittest。快速檢查不啟動 Minecraft；CI 在 Windows、Linux 執行相同命令。CI 不代表 Windows 11 產品發布驗收，也不要求主機 Java。

整合檢查先檢查環境，再使用既有 prepare wrapper 編譯 Java（`-Xlint:all,-classfile -Werror`），執行完整原版測試並保存 `.cache/full-suite.log`。只有成功且來源未變時產生 `.cache/reference-tests/suite-receipt.json`。環境預檢失敗回傳 2，測試／命令失敗回傳非零並保留 log。

doctor 的 GitHub CLI 檢查只確認 PATH，不代表登入或 repository 權限；Docker info 確認 daemon 可達且為 Linux，實際 build/run 權限仍由整合檢查驗證。遇到 Docker pipe/log 權限錯誤，檢查 Docker Desktop 啟動狀態及目前帳號權限。

整合測試需要執行者明確閱讀並同意 Minecraft EULA。`--accept-eula` 只適用該次執行；既有開發者的同意不代表 clone 使用者或 CI 操作者同意。CI 預設只跑快速檢查；有授權的操作者可手動執行整合命令。直接執行 pytest 會略過未授權的 Minecraft 測試，不應把 skipped 當成整合通過。

## 證據封存與驗證

歷史 `2026-10-20` snapshot 保持原樣，以 `823e091` Git blobs 驗證來源。快速檢查中的歷史驗證只證明 snapshot 完整，不代表目前原始碼測試通過或 26.2 verified。

```powershell
python scripts/evidence.py verify validation/reference/evidence/2026-10-20 --source-ref 823e091
python scripts/dev.py check --integration --accept-eula
# 先建立 .cache/metadata.json，填寫本次實際 date、timezone、host、runtime。
python scripts/evidence.py archive validation/reference/evidence/NEW-SNAPSHOT --suite-log .cache/full-suite.log --metadata .cache/metadata.json --source-ref SOURCE-COMMIT
python scripts/evidence.py verify validation/reference/evidence/NEW-SNAPSHOT
```

新 snapshot 必須直接位於 `validation/reference/evidence/` 下。metadata 範例結構（值須填本次測量，勿複製歷史主機資訊）：

```json
{"date":"YYYY-MM-DD","timezone":"Asia/Taipei","host":{"os":"actual OS","cpu":"actual CPU","physical_ram_bytes":0},"runtime":{"java":"actual container Java","docker_engine":"actual engine","peak_memory":"not_measured"}}
```

封存會檢查 suite 收據、所有 run artifacts、固定三組案例、重複結果及 normalizer，再於暫存完成後發布到全新目錄；固定 oracle fixtures 與舊 snapshot 均不覆寫。先提交受測來源，再用 `--source-ref <來源 SHA>` 封存，工具會確認該 commit 的來源雜湊。省略此參數則記錄 `source_ref: worktree`，只能作為未釘選的暫存證據；後續可使用 `verify --source-ref <來源 SHA>` 重驗。歷史驗證需要完整 Git 歷史，CI 因此使用 full checkout。

## Bytecode 探索

```powershell
python scripts/bytecode.py net.minecraft.world.level.block.entity.trialspawner.TrialSpawnerStateData --method getDispensingItems --max-lines 80
```

完整 javap 存於 `.cache/javap/<image-id>/<class>.txt`，依映像 ID 重用；輸出只有指定方法與原始行號，超過上限時顯示完整檔案位置。用 `--refresh` 重建快取。先搜尋檔案內的方法與行號，再讀必要區段。原有 `.cache/minecraft-26.2/*.javap` 可供先前探索查閱。此改善尚無 token 節省量測。
