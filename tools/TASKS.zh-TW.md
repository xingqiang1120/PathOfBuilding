# 任務板（公司負責人 AI ⇄ 家裡執行 AI）

說明見 `tools/HOME_PC.zh-TW.md`。每個任務寫：給誰、要改哪些檔案、完成標準；做完的人在「交回」寫結果。
狀態：待做 → 進行中 → 已交回 → 已驗收（或退回，附原因）。

---

## 目前階段：一（先把計算改準，2026-11-26 使用者同意）
規則還在改，自我對弈先不跑（跑了下一版就作廢）。算力拿來跑驗收考試和差距報告，阿福看報告決定下一版改什麼。
進入階段二（凍結版本、連跑幾晚自我對弈學權重）的門檻：作者組至少 5/7、底線 10/10、連續兩版沒有退步。

## T1 家裡電腦第一次準備＋跑第 13 版考試（2026-11-26 晚上）
- 給：home
- 狀態：已驗收（2026-11-27 阿福：結果與私人庫檔案相符，benchmark.py 修正已合併；Glacial Hammer 混沌抗不過底線算不及格，第 14 版處理）
- 內容：
  1. 照 HOME_PC A 段準備（已經有 Claude；缺 Python、Git、GitHub CLI 的話先裝，`gh auth login` 登入擁有私人庫的帳號）。
  2. 照 B 段把這個對話命名為「PoB 執行 home」、打開 Remote Control。
  3. 照 C 段跑第 13 版考試和差距報告，最後 `python tools/labdata.py push --pc home --version 13`。
  4. 回報使用者：考試結果摘要（作者組幾組及格、底線幾組過）、跑了多久、記憶體用量。
- 改檔案：無（只跑計算）
- 完成標準：私人庫有 results/v13/home/ 的三個檔案（v13.md、v13.json、v13-gap.md）。
- 交回（home，2026-11-27 00:40）：
  - **結果：作者組 3/7（v12 是 2/7）、底線 8/10（v12 是 9/10）、對 v12 沒有退步 10/10。** 私人庫 `results/v13/home/` 三個檔案已推上。
  - 作者組：及格 Smite／Slayer 111%、Smite／Gladiator 96%（v12 只有 11%，v13 的修正生效）、Summon Skeletons 189%。
    沒及格：Storm Call／Assassin 74%、Storm Call／Hierophant 60%、Reave 66%（DPS 不到 80%）；KB Necro DPS 178% 但防禦 11.18 低於作者 11.76 超過 0.1。
    v13 和 v12 的 7 組裡有 6 組數字完全一樣（考試是決定性的），只有 Smite／Gladiator 改變。
  - 底線：Glacial Hammer／Champion 分數 25.33→26.01（+0.68，回來了）但混沌抗 -8 不過底線（v12 過）；Cyclone／Slayer 生命+ES 3,760 不到 4,000（v12 也沒過）。其他 8 組都過、分數都 +0.00。
    → 底線 9/10 變 8/10 是 Glacial Hammer 的抗性被換成分數造成的，請阿福判斷算不算退步。
  - 差距報告（v13-gap.md）最大的單項：Storm Call／Hierophant 少了 Overloaded Intensity 輔助（+88%）、Righteous Fire（+42%）；
    Storm Call／Assassin 少了 Power Charge On Critical（+28%）、Righteous Fire of Arcane Devotion（+26%）、Increased Critical Damage（+24%）、Less Duration（+21%）；
    Reave 少了 Vaal Smite（+30%）、Blood and Sand（+15%）。共通點：作者有的「輔助性技能」（RF 類、Pact of Beidat、Vaal 技能）生成器都沒選。
    許多作者的珠寶／星團節點（Divine Flesh、Dance with Death、Summon Spectral Tiger…）報告標「not applicable」，就是珠寶被丟掉的部分。
  - 時間：樣板組 10 組 7 分 18 秒、作者組 7 組 7 分 35 秒、差距報告 43 秒（--jobs 14，home 16 邏輯核心）。整套不分段大約 10 分鐘。
  - 記憶體：每組 generate 約 1.1～1.4 GB。10 組同時跑時 Python 合計尖峰 12.7 GB、系統用量 24.0 GB／31 GB（開跑前系統已用 11.9 GB）。
    推算 14 組同時跑約 29～30 GB，很接近上限；建議 home 用 `--jobs 12`，或跑前關掉其他程式。
  - **考試程式 bug（已修，分支 `home/t1-v13`，請阿福合併回 feature/ai-tools）：** v13 在 Generator.__init__ 新增 `resists_later`，
    但 benchmark.py 的 `scorer()` 用 `__new__` 建物件沒設它，替作者 build 評分時 AttributeError，7 組作者全被 skip。
    修正是補一行 `g.resists_later = False`（與 __init__ 預設相同），只動 benchmark.py，不影響生成器與成績可比性。gap.py 也用同一個 scorer，一起受惠。
    因此這次是先跑樣板組、修完再 `--only authors` 補跑合併；單元測試 60 個全過。
  - 另外：home 本機沒有 v12 結果，退步比較會顯示 version None；我把私人庫的 v11/v12.json 複製到 `library/benchmark/` 才算得出來。
    建議 `labdata.py pull` 順便把其他台的最新 benchmark json 放進 library/benchmark/（或在 HOME_PC C 段加一步）。

## T2 第 2 台設定（2026-11-27）
- 給：pc2
- 狀態：待做（使用者明天裝好 Claude 後）
- 內容：照 HOME_PC A、B 段準備，對話命名「PoB 執行 pc2」。第 13 版考試由 home 跑，pc2 等阿福派下一版。
- 改檔案：無
- 完成標準：`python tools/labdata.py status` 列得出版本；阿福能傳訊息給「PoB 執行 pc2」。
- 交回：

## T3 home：生成器計算優化負責人（2026-11-27 起，持續）
- 給：home
- 狀態：待做
- 內容：home 自己負責「改生成器→跑考試→交回」的循環，不用等阿福逐項派工。
  1. 從最新的差距報告（`library\benchmark\v<版本>-gap.md`）和 HANDOFF「已知的下一批問題」挑一個問題。
  2. 開分支 `home/v<下一版>-<主題>`，改 `tools/generate.py`（和它需要的 PobWorker.lua、tools/data/ 的樣板資料），
     升 `GENERATOR_VERSION` 和 `STILL_VALID_FROM`，跑單元測試和完整考試（`--jobs 12`）。
  3. 及格條件（全部要有）：沒有任何一組退步（分數掉超過 0.05）；底線沒有變少；作者組或底線至少一項變好，或差距報告裡目標那一項變小。
  4. 推分支、`labdata.py push --pc home`，在這個任務下面寫交回（改了什麼、為什麼、考試前後），再傳訊息給阿福。
  5. 阿福看 diff，在 pc2 跑保留考試，都過了才合併到 feature/ai-tools。合併前 home 可以先開下一個分支，但要從上一個分支接著做，版號依序。
- 規則：
  - **不能改考卷和及格標準**：`tools/benchmark.py` 的判定、`tools/data/benchmark.json`、`tools/ACCEPTANCE.zh-TW.md` 不動。
    考試程式有 bug 可以修，但另開一個 commit 說明，不要跟生成器的修改混在一起。
  - **不開保留考卷**：私人庫的 `holdout/` 和任何 `*-holdout*` 結果不看、不針對它調整。
  - 一個分支只解一個問題，方便看出是哪個改動造成的效果。
  - 改到計分方式（score、penalty、defence 的權重）要在交回裡講清楚對每組的影響，因為它會改變所有 build 的取捨。
- 第一批題目：輔助性技能（Righteous Fire 類、Vaal 技能、Pact of Beidat）、Overloaded Intensity 為什麼沒被選、Glacial Hammer 混沌抗底線。
- 交回：

## T4 office：保留考卷
- 給：使用者＋阿福（office）、pc2 跑
- 狀態：待做（等使用者收集 build）
- 內容：使用者手動收集 5～10 個新的真人 build（最好是主考卷沒有的技能和昇華），阿福匯入 build 庫，寫進私人庫
  `holdout/holdout.json`。home 每交一版，pc2 跑 `python tools/benchmark.py run --holdout` 和 `python tools/gap.py --benchmark --holdout`。
- 完成標準：保留考卷有至少 5 組，pc2 能跑出結果。

## T5 office：實戰驗證
- 給：使用者＋阿福（office）
- 狀態：待做
- 內容：照 `tools/PLAYTEST.zh-TW.md`，一次測一個生成器的 build，阿福把結果整理成修正規則派給 home。

## （暫停）家裡電腦跑自我對弈（第 2～5 份）
- 階段二才開始，指令見 HOME_PC B 段。
