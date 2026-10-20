# ominous-trial-predictor

依 [SPEC.md](SPEC.md) 開發的離線不祥試煉預測工具。目前完成範圍僅為 [#1](https://github.com/Whitecatuwu/ominous-trial-predictor/issues/1)：26.2 原版參考查詢。尚無離線計算核心、產品 CLI 或 GUI JAR；26.2 仍為 `unverified`。

## 開發用原版參考查詢

需要 Python 3.11+ 與可執行 Linux 容器的 Docker。Java 25 JDK 由固定 digest 的開發映像提供，無須依賴主機 PATH 中的 Java。Windows PowerShell 與其他平台均從 repository 根目錄執行：

```powershell
python scripts/reference.py prepare
# 閱讀 Minecraft EULA 後，僅在同意時使用 --accept-eula。
python scripts/reference.py query --seed 1 --position 0 0 0 --accept-eula
python scripts/reference.py query --seed 1 --position -30 -30 -30 --position -31 -31 -31 --accept-eula
python scripts/reference.py query --seed 1 --position -1 -1 -1 --accept-eula
python scripts/dev.py check --integration --accept-eula
git diff --check
```

`prepare` 是開發建置 wrapper：下載雜湊鎖定的官方服務端、驗證 SHA-1／SHA-256，並建置 Java 查詢 adapter。初次準備需要網路；來源 JAR 與基底映像快取後可重建。每次修改 Java adapter／測試都要重新 `prepare`。編譯使用 `javac -Xlint:all,-classfile -Werror`；只排除上游 JAR 缺少 compile-only annotation 所產生的 classfile 警告，未導入額外 formatter／linter。

`query` 使用 `--network none`，不發布連接埠，每次建立全新原版預設世界；結束後容器與世界刪除。JSON 寫 stdout，執行位置寫 stderr。每次輸入、完整服務端 log、來源紀錄、實際 server.properties 與結果保存在 `.cache/minecraft-26.2/runs/<id>/`。查詢失敗、逾時或未產生結果時回傳非零；這是開發工具，並非 SPEC §8 的產品 CLI。

整合測試會啟動多次原版服務端；每位執行者先閱讀 [Minecraft EULA](https://aka.ms/MinecraftEULA)，同意後使用下列明確授權入口。

## 統一檢查與環境預檢

```powershell
python scripts/dev.py doctor
python scripts/dev.py doctor --integration --github
python scripts/dev.py check
# 閱讀並同意 EULA 後：重新編譯 Java + 完整原版整合測試
python scripts/dev.py check --integration --accept-eula
```

`check` 執行 Python 語法檢查、whitespace、工具測試及歷史證據完整性驗證，無須 Docker／主機 Java，也不啟動 Minecraft。GitHub Actions 對 push／PR 在 Windows、Linux 自動執行相同快速檢查；整合檢查由已同意 EULA 的操作者明確啟動。doctor 對缺少的可選工具顯示診斷，指定 `--integration`／`--github` 時才要求 Docker Linux daemon／GitHub CLI。

整合 log 與測試收據寫入 `.cache/`。證據封存、唯讀驗證、錯誤退出碼及限量 bytecode 探索見 [開發指南](docs/development.md)。Retro 五項改善排在 #2 前；#2 尚未開始。

## 現有路徑

| 路徑 | 用途 |
|---|---|
| `scripts/reference.py` | 下載、建置及開發用 Docker 查詢 wrapper |
| `scripts/dev.py`、`scripts/tests/` | 統一檢查、doctor 與工具測試 |
| `scripts/evidence.py` | 證據封存與唯讀驗證 |
| `scripts/bytecode.py` | 保存完整 javap、依方法限量輸出 |
| `validation/reference/src/reference/` | 原版方法觀察 adapter 與結果正規化，獨立於未來計算核心 |
| `validation/reference/tests/` | 公開查詢命令整合測試、原版 registry 正規化測試 |
| `validation/reference/fixtures/` | 固定輸入與一次性擷取的原版預期值，測試不重寫預期值 |
| `validation/reference/evidence/` | 本次實測結果、log、配置與通過紀錄 |
| `version-data/26.2.json` | 官方來源、產物雜湊、Java 映像及驗證狀態 |
| `docs/validation-progress.md` | 全部目標版本進度及驗收邊界 |

查詢步驟、世界狀態、輸出語意及未查證項目見 [原版參考指南](docs/reference-26.2.md)。後續純計算核心、產品 CLI、GUI、翻譯將各自分離；本票未建立這些模組。
