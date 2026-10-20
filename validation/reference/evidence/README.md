# #1 原版參考查詢實測證據

`2026-10-20/` 保存本次完整測試的實際結果，不是離線核心驗證或 Windows 11 發布驗收。

- `summary.json`：主機／容器環境、測試結論、每組耗時、預期值／實際值雜湊與受測程式來源雜湊。
- `full-suite.log`：完整 unittest 執行紀錄。
- `seed-*/`：三組固定輸入各自的 request、原版服務端 log、來源／映像 ID、實際 server.properties、完整實際結果與正規化測試結果。
- `repeat-1/`、`repeat-2/` 與 `repeat-first.json`／`repeat-second.json`：相同輸入在兩個全新世界的重跑證據。
- `manifest.json`：封存檔案 SHA-256；log 換行統一為 LF。固定預期值另存於 `../fixtures/`，測試不自動覆寫。

重跑：先在 repository 根目錄執行 `python scripts/reference.py prepare`，同意 Minecraft EULA 後執行 `python -m unittest discover -s validation/reference/tests -v`。每次新執行的實際結果與比對紀錄保存在 `.cache/reference-tests/`，服務端原始執行資料保存在 `.cache/minecraft-26.2/runs/`；不會修改本次封存。

TDD 紀錄：正規化測試先因缺少實作失敗，之後改為在原版完成 registry 初始化的公開邊界執行並通過；公開命令測試先因缺少 wrapper 失敗，加入 wrapper 後全新世界重跑一致；固定案例測試先因缺少 fixture 失敗，一次性擷取原版答案後獨立重跑通過。最終完整套件結果以封存 log 與 summary 為準。

所有目標版本均維持 `unverified`，核心比對通過組數為 0；19 列固定參考含 1 列 `requires_world_state`，該列不算作完整計算結果。
