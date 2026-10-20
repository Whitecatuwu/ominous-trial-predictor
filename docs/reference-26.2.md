# 26.2 原版參考查詢

對應 [issue #1](https://github.com/Whitecatuwu/ominous-trial-predictor/issues/1)，依 SPEC §2、§3、§4、§10、§12。這是原版對照來源，尚未進行離線核心比對。

## 原版來源與觀察方式

官方 [版本清單](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json) 中 `26.2` 為 `release`。固定 [版本 JSON](https://piston-meta.mojang.com/v1/packages/91ef51b7d36ca092c5c02aba42f0f40c7cc1db84/26.2.json) 及 [官方 server.jar](https://piston-data.mojang.com/v1/objects/823e2250d24b3ddac457a60c92a6a941943fcd6a/server.jar)，雜湊完整保存於 `version-data/26.2.json`。

Dockerfile 驗證外層 SHA-256 及 bundler 內 `server-26.2.jar` SHA-256，使用官方隨附 libraries，沒有 Fabric、Forge、Paper、外部資料包或另寫的戰利品演算法。Java 25 開發基底映像以 digest 鎖定；Minecraft JAR、library 與映像不提交 Git。

Java agent 使用 Java 25 正式 Class-File API，僅在 `MinecraftServer.tickServer(BooleanSupplier)` 開頭插入一次觀察 callback，等原版世界與 registry 完成初始化後執行。原版 JAR 檔案不變；執行中 tick 方法有這一處 instrumentation，因此此環境是**原版邏輯加觀察掛鉤**。不轉換 `TrialSpawnerStateData`、`LootTable`、RNG、物品或效果類別。

查詢直接呼叫原版 `new TrialSpawnerStateData().getDispensingItems(level, config, position)`。混合種子亦透過反射呼叫原版私有 `lowResolutionPosition` 取得，未在 adapter 複製種子混合或亂數演算法。之後由原版 codec 序列化完整有效元件，由原版 PotionContents 取得全部效果。

可在已建置映像中自行檢查方法：

```powershell
docker run --rm --network none --entrypoint javap ominous-trial-reference:26.2 -p -c -classpath /opt/reference/META-INF/versions/26.2/server-26.2.jar net.minecraft.world.level.block.entity.trialspawner.TrialSpawnerStateData
```

`getDispensingItems` 讀取配置指定的原版戰利品表，使用 `lowResolutionPosition` 回傳值呼叫 `LootTable.getRandomItems`，再把每個物品原始數量轉為權重，候選 ItemStack 的 count 設為 1。adapter 只讀取其回傳值。

## 每次查詢的步驟與世界狀態

1. 讀取明確的十進位有號 64-bit 種子與一或多個完整有號 32-bit XYZ。
2. 記錄固定來源資料、實際 Docker image ID、Docker 版本與 request.json；執行時使用該 image ID，避免 tag 在 inspect 後改指向其他映像。
3. 在無網路、無公開 port 的新容器啟動官方 Main。只設定 `level-seed`，其他 server.properties 與遊戲規則維持原版預設。容器限制 2 CPU、3 GiB；Java heap 上限 2 GiB。
4. 原版預設生成 Overworld／Nether／End；以 Overworld 作為查詢上下文。確認服務端版本、實際世界種子及選用資料包，遇到非 vanilla 資料包即失敗。
5. 選用原版 `minecraft:trial_chamber/melee/zombie/ominous` 配置，輸出其實際 `itemsToDropWhenOminous`，即 `minecraft:spawners/trial_chamber/items_to_drop_when_ominous`。不要求該 XYZ 在世界上已存在生怪磚，不因世界高度或邊界拒絕 XYZ。
6. 每個位置使用全新的 TrialSpawnerStateData，表示其 dispensing cache 尚未建立。保留輸入順序與重複座標。混合種子非零時取得完整候選清單；為零時依 SPEC 回傳 `requires_world_state`，`result: null`，不消耗世界 random sequence 或猜測結果。
7. 保存 result.json 與原版實際 server.properties，正常關閉服務端，再刪除容器與世界。相同非零輸入可在下一個全新容器重現。錯誤會保留 log 並使 wrapper 失敗。

`world_state` 保存維度、全新世界／全新 cache 前提、實際配置與戰利品表、實際選用資料包。非零混合種子的這個候選查詢不需實體清單、目標 UUID、遊戲時間或世界 global RNG 的當前狀態。零混合種子不在本工具提供只憑種子和座標的完整答案。

## 結果語意

`status` 是列狀態；`version_status` 永遠保持 `unverified`。世界種子與 mixed_seed 都保存為十進位字串。

`result.dispensing_items` 是原版預先產生的**可投放候選與權重**，不是未來每次投射物事件的時序清單。第一個來自滯留藥水 pool，第二個來自另一投射物 pool。實際何時、向哪個實體投放哪個候選仍使用世界狀態，不在本票預測。

每個候選保留 `item_id`、`potion_id`（不適用時 null）、原版序列化的完整有效 `components`、`effects` 陣列、count 與 weight。效果保留 effect_id、原始 amplifier、display_level、raw_duration_ticks、base_duration_ticks／seconds、instant、infinite。

基礎時間取自物品／藥水效果資料，沒有套用 `minecraft:potion_duration_scale` 或命中後剩餘時間。瞬間效果的原始 duration sentinel 仍可在 raw_duration_ticks 查閱，兩個 base_duration 欄位為 null，不虛構持續時間。無藥水的投射物為 `potion_id: null`、`effects: []`。

## 已測得與尚待驗證

固定案例由原版方法一次性擷取，位於 `validation/reference/fixtures/`，後續測試只讀取，不自動更新。

- 種子 1 的固定案例：全部 7 個藥水選項，以及普通箭、帶 poison 的原版 arrow、帶 strong_slowness 的原版 arrow、fire_charge、wind_charge；保留原版物品識別碼，不自行把帶藥水的 arrow 改名為 tipped_arrow。fire_charge／wind_charge 權重 1、2、3 均有案例。
- 負座標在 -30／-31 的分組邊界、XYZ 的 signed int 極值、零座標與重複座標。
- signed long 種子極值，以字串完整保存。
- 種子 1、(-1,-1,-1)：原版混合種子為零，回報 requires_world_state；此列不是已測得的完整投放答案。
- 正規化測試額外建立原版 Turtle Master（複合效果）與 Healing（瞬間效果）物品。這兩者用來測試序列化，不宣稱它們出現在不祥戰利品表中。

尚未驗證：離線核心（尚未實作）、10,000 組原版／核心比對、零混合種子下各種既有世界 random sequence 狀態、已有 dispensing cache 的生怪磚、實際投放時序與實體命中效果，以及其他版本。完整發布驗收仍依 SPEC；原版參考查詢成功不等於版本 verified。
