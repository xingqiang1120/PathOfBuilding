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
- 狀態：進行中（v14～v22 已驗收合併；v23 階段二前必修已交回，等阿福驗收；考試對 v22 一字不差 17/17、selfplay 同 seed 可重現，但搜尋本身沒改——進階段二由使用者決定）
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
  ### v14 `home/v14-support-pool`：輔助池會更新、互換做到沒改善（2026-11-27 12:07，home）
  - **題目**：Overloaded Intensity 為什麼沒被選。
  - **原因**：PoB 只有在 Intensify 已經接上之後才把 Overloaded Intensity 列為「可以輔助 Storm Call」；生成器的輔助池是一開始
    （還沒有任何輔助）抓一次就固定，之後選輔助、最後互換都用同一份，所以它從頭到尾沒被試過。另外最後的互換只做一輪、照原順序，
    換了 Awakened Empower 之後（Storm Call／Assassin 從 500 萬跳到 1.2 億）前面的寶石不會重看。
  - **改了什麼**（只動 `tools/generate.py`，不動計分）：`refresh_support_pool()`，每接上一顆輔助就重抓一次池子；`retune_supports()`
    改成最多 3 輪、有換就再來一輪、沒換就停。GENERATOR_VERSION／STILL_VALID_FROM 升到 14。
  - **考試 v13 → v14**：作者組 3/7 → 3/7、底線 8/10 → 8/10、樣板組退步 0 組（Raise Zombie +0.69、Glacial Hammer +0.05，其餘 +0.00）。
    - 目標項：Storm Call／Hierophant 60% → **85%**（8,713 萬 → 1 億 2,360 萬；互換時把 Awakened Spell Echo 換成 Overloaded Intensity）。
      DPS 過了，但防禦 12.07 比作者 12.44 低 0.37，所以還不算及格（作者靠 Vaal Arctic Armour +1.17）。
    - Raise Zombie／Necromancer：70 萬 → 140 萬（多輪互換：Greater Spell Echo → Awakened Empower、→ Greater Spell Echo、→ Awakened Minion Damage）。
    - **退步一組（作者組）：Smite／Gladiator 96% → 84%，分數 28.77 → 28.66（−0.10），仍及格。** 原因是搜尋路徑不同，不是計分改了：
      v13 的樹上剛好有擊中回血來源（每秒 1,013），輔助全拿傷害；v14 的樹沒拿到，互換時把 Volatility 換成 Life Gain on Hit
      （每秒 1,109），分數上回復項 +0.46 > ln(DPS) −0.35。兩版的最後四顆輔助一樣。這是貪婪搜尋的路徑噪音，請阿福判斷算不算退步；
      如果要壓噪音，方向是「每秒回復 %」的 0.2 權重與對數無上限（49% 生命／秒和 20% 差不多值）——這屬計分調整，另開分支談。
    - 其他作者組數字與 v13 完全相同（Storm Call／Assassin 74%、Reave 66%、KB Necro 178%、Smite／Slayer 111%、Skeletons 189%）。
  - **時間／記憶體**（--jobs 12）：全套 14 分 16 秒＋差距報告 43 秒；Python 合計尖峰 14.3 GB、系統 25.3 GB／31 GB（多了每顆輔助一次 candidates 呼叫，
    單組作者 build 從 4.5 分變 3.8～7.9 分）。
  - **下一題準備（還沒改）**：在三組沒及格的生成 build 上單獨加作者的輔助性技能量過：Righteous Fire 對兩組 Storm Call +41～42% DPS、
    RF of Arcane Devotion +26%、Pact of Beidat +16～22%、Blood and Sand 對 Reave +15%、Vaal Smite 對 Reave +30%、Vaal RF +71%。
    但 PoB 把 Vaal 技能和 RF 都當成永遠開著，而且目前評分用的是毛回復（LifeRegenRecovery），RF 的自燃沒被算到。
    PoB 有 NetLifeRegen／TotalDegen，下一個分支打算把淨回復輸出進評分再開放 RF／Pact of Beidat／Blood and Sand；Vaal 技能是否公平要先問阿福。
  - 結果：私人庫 `results/v14/home/`（v14.md、v14.json、v14-gap.md）。

  ### v15 `home/v15-aux-skills`：淨回復進評分，開放 Righteous Fire／Pact of Beidat／Blood and Sand（2026-11-27 12:37，home）
  - **題目**：輔助性技能。前提是先讓評分看得到它們的代價。
  - **改了什麼**（`tools/generate.py`、`tools/PobWorker.lua` 多輸出 4 個數字、`tools/tests/test_generate.py` 加測試）：
    1. 評分的「每秒回復 %」改用 PoB 的淨回復（NetLifeRegen／NetEnergyShieldRegen：回復扣掉自己造成的持續傷害，例如 RF 自燃、
       Blood Rage 每秒 4%、Annihilation's Approach 藥水期間的火傷）。PoB 沒給淨值時維持原本的毛回復，所以沒有自傷的 build 分數不變。
       已確認 PoB 把 RF 算成真的持續傷害：Hierophant 加 RF 後淨回復 1,220 → 768，剛好是 90% × (1 − 85% 火抗)。
    2. 新扣分 `unsustainable`：連吸血、擊中回血全額算進去，淨回復還是負的（站著打也在掉血）→ 扣 1 分（等於 DPS 少 63%）再加
       ln(1 + 每秒掉的 %)。回復加分那邊維持吸血只算一半（要打到才有）。
    3. BUFF_SKILLS 加 Righteous Fire、Righteous Fire of Arcane Devotion、Pact of Beidat、Blood and Sand；主技能不會再被當增益加一次；
       兩種 RF 互斥（EXCLUSIVE_BUFFS）——PoB 會把兩顆疊加（Hierophant 兩顆都帶衝到作者的 159%），遊戲裡同名增益不疊，沒人會兩顆都帶。
       Vaal 技能不開放（阿福 2026-11-27 決定：PoB 當永遠開著，高估）。
  - **公式本身對舊 build 的影響**（把 v14 的 17 個 build 用 v15 公式重算，不重跑搜尋）：16 個變動在 −0.05 以內（帶 Blood Rage 的 Smite／Slayer、
    Glacial Hammer、Cyclone 各 −0.01～−0.03）；只有作者組 Storm Call／Assassin 從 29.72 → 26.78（−2.94）：v14 的那個 build 每秒淨掉 164 血、
    沒有吸血，來源是作者的鞋子 Annihilation's Approach（藥水期間每秒受火傷換 Adrenaline；作者本人靠每秒 839 吸血撐住，生成器的沒有）。
  - **考試 v14 → v15**（--jobs 12，14 分 41 秒＋gap 39 秒；Python 尖峰 14.3 GB、系統 25.4 GB／31 GB）：
    - 底線 8/10 → 8/10；樣板組退步 0（最大 Tornado Shot −0.04、Glacial Hammer −0.03，在 0.05 內）；進步：Fireball +0.23、Fireball block +0.34、
      Essence Drain +0.25、Doryani 樣板 +0.33、Raise Zombie +0.13、Cyclone +0.10。新增益被選的情況：Fireball 兩組、Doryani 樣板、Raise Zombie、
      Essence Drain 選了 RF of Arcane Devotion 和／或 Pact of Beidat；Cyclone 選了 Blood and Sand。
    - 作者組 DPS 四組進步：Storm Call／Hierophant 85% → **112%**（RF of Arcane Devotion＋Pact of Beidat）、Storm Call／Assassin 74% → **84%**、
      Reave 66% → **76%**（Blood and Sand）、Smite／Gladiator 84% → 89%。退步：Smite／Slayer 111% → 94%、KB Necro 178% → 171%（仍遠超作者）。
    - **作者組及格 3/7 → 2/7**（Smite／Slayer、Skeletons 及格）。少的那組是 Smite／Gladiator：DPS 89% 過了，防禦 10.11 比作者 10.22 低 0.11，
      門檻是 0.10，差 0.01。公式本身只讓它 −0.01（Blood Rage 的扣血）；其餘 −0.22 是搜尋走了另一條路（分數 28.65 → 28.49，用生成器自己的尺也更低）。
      這組連續兩版在及格線上翻來翻去（v13 96%、v14 84%、v15 89% 但防禦掉），是貪婪搜尋的噪音，不是這次改動造成的；要治本得讓搜尋更穩
      （例如多起點取最佳），另開題目。
    - Hierophant（112%）、Assassin（84%）DPS 都過了但防禦差 0.26／0.32 不及格；作者兩組都靠 Vaal Arctic Armour（+1.17），阿福說考卷端處理。
  - **有沒有 build 因淨回復為負而換配置**：有，Storm Call／Assassin（作者裝備）：v14 淨 −164／秒；v15 多選 Pact of Beidat＋RF of Arcane Devotion，
    樹多拿回復，最後淨 +353／秒、DPS 1.29 億 → 1.46 億、防禦 11.04 → 10.89。Doryani 樣板也多選了這兩個並拿到每秒 2,588 吸血（混沌抗 70 → 48，仍過底線）。
    帶 Blood Rage 的六個 build 都留著 Blood Rage（自己的回復或吸血撐得住，沒被扣分）。
  - **請阿福判斷**：嚴格照「沒有任何一組退步」，作者組及格數 3 → 2 不過；但那一組差 0.01、主因是路徑噪音，而 DPS 四組進步、樣板組零退步六進步。
    我的建議是收 v15，Smite／Gladiator 的穩定性另開題。
  - 結果：私人庫 `results/v15/home/`（v15.md、v15.json、v15-gap.md）。

  ### v16 `home/v16-deterministic`：同一版跑兩次結果完全相同（2026-11-27 13:52，home）
  - **題目**：搜尋穩定性第一步——決定性（阿福 2026-11-27 調換順序，混沌抗延到 v17）。
  - **問題**：v15 同一份程式連跑兩次作者組，Storm Call／Assassin 84% 與 100%、Smite／Gladiator 96%（及格）與 89%（不及格），其他 5 組相同。
    來源是 Lua 的 pairs() 迭代順序在不同程序間不固定（LuaJIT 字串雜湊種子），而生成器 (a) 分數打平時取清單裡第一個，(b) 樹的步驚每輪
    只試「前 80 個沒試過的」候選——哪 80 個完全由 pairs 順序決定，所以每次跑出不同的樹。
  - **改了什麼**（`tools/PobWorker.lua`、`tools/generate.py`，不動計分、不動考卷）：
    1. Lua：candidates 回傳的 passives、jewelSockets、masteries、removable，以及 ascendancy_candidates 的清單，全部排序（id／effect）後才回傳。
       supports、anoints、spectres、uniques 原本就有排序。
    2. Python：樹的候選排成「最便宜優先、再依 id」（原本哪 80 個被試是隨機的，現在固定且合理：先試便宜的）；昇華候選依 id；
       uniques 依槽位（JSON 物件順序來自 pairs）。`best()` 加平手規則：分數差 < 1e-9 視為平手，取排序在前的（TIE）。
    3. 順手：`recalc()` 與 `checkBuild()` 在 PoB 沒產出 mainOutput 時重算一次、再失敗才報清楚的錯（v15 重跑時偶發的 `attempt to index local 'o'`）。
    版號 16。單元測試 60 全過。
  - **驗收**（阿福定的方法：同一版連跑兩次完整考試，17 組分數要完全相同）：**17/17 完全相同**（score、DPS、defence 到最後一位小數都一樣）。
    前置檢查：Smite／Gladiator 同時跑兩次，每一步都一樣。兩份都在私人庫 `results/v16/home/`：v16.json（第二次）、v16-rerun.json／.md（第一次）。
  - **成績 v15 → v16**（路徑換了，分數不同是預期的；以下與 v15 最後一次的值比）：作者組 3/7 → 3/7（Smite／Slayer 103%、Reave 82%、Skeletons 194% 及格）；
    底線 8/10 → 8/10。作者組：Smite／Slayer 100% → 103%、Storm Call／Assassin 100% → 91%（v15 兩次是 84%／100%，v16 固定在 91%）、Skeletons 189% → 194%，
    其餘四組與 v15 完全相同。樣板組：Fireball +0.01、Fireball block −0.08、Tornado Shot −0.09、Essence Drain −0.03、Raise Zombie −0.09、Raise Spectre −0.02，
    其餘五組 +0.00。考試報告把三組標成 REGRESSION（> 0.05），但 v15 的那些數字本身是隨機路徑的其中一次；從 v16 起「沒有退步」才有意義。
    變化的來源是樹的候選改成「便宜優先」——原本隨機挑 80 個，有時剛好挑到好的。
  - 時間／記憶體（--jobs 12）：兩次各 14 分 33 秒、14 分 44 秒；Python 尖峰 14.3 GB、系統 25.3 GB／31 GB。
  - 結果：私人庫 `results/v16/home/`（v16.md、v16.json、v16-gap.md、v16-rerun.json、v16-rerun.md）。
  - 下一題：v17 混沌抗（半成品在 `home/v17-chaos-floor`，從 v16 接著做；單組驗證 Glacial Hammer 混沌抗 −8 → 38、底線全過，但 DPS 676 萬 → 390 萬）。

  ### v17 `home/v17-chaos-floor`：混沌抗低於目標硬扣分——三種強度對照，由使用者選（2026-11-27 14:43，home）
  - **題目**：Glacial Hammer／Champion 混沌抗 −8 連三版不過底線（底線：混沌抗 ≥ 0 或免疫）。
  - **改了什麼**（`tools/generate.py`、測試；不動考卷）：混沌抗低於 CHAOS_FLOOR 時每點扣 CHAOS_FLOOR_PENALTY=0.05（和火冷電沒滿 75 一樣重），
    疊在原本 60 以下每點 0.005 的軟扣上；選輔助階段一樣延後（resists_later）；Chaos Inoculation 免疫不扣；設定檔的 ignoreResistPenalty 列 ChaosResist 可豁免
    （Doryani 沒加——它只豁免閃電）。CHAOS_FLOOR 預設 0，實驐時可用環境變數 POB_CHAOS_FLOOR 切換（這次用它跑 30、60 兩種對照）。版號 17。單元測試 60 全過。
  - **公式本身對 v16 build 的影響**（v16 的 17 個 build 用目標 0% 的 v17 公式重算、不重跑）：只有 Glacial Hammer／Champion 26.03 → 25.63（−8 × 0.05 = 0.40），其餘 17 組一模一樣。
    之後搜尋把它拉回 25.96（換回混沌抗 38），所以 −0.08 不是退步，是公式要它換的。
  - **為什麼別組也變**：模板裝備和作者裝備一開始混沌抗是 −60（PoB 預設懲罰），硬扣在搜尋一開始就是 3.0 分，讓搜尋更早去補混沌抗（例如先拿 Amethyst 藥水、
    Purity of Elements），之後的路徑就不同——KB Necro（作者裝備混沌 −60）DPS 171% → 220%、Tornado Shot 混沌 61 → 75、Cyclone 70 → 75。
  - **三種強度對照**（完整考試各跑一次；決定性，數字可重現）：

    | 目標 | 作者組 | 底線 | 對 v16 退步 >0.05 | Glacial Hammer 混沌／DPS／分數 | 其他受影響 |
    |---|---|---|---|---|---|
    | v16（無硬扣） | 3/7 | 8/10 | — | −8／676 萬／26.03（不過底線） | — |
    | **0%**（建議） | 3/7 | **9/10** | 2 組（GH −0.08、GH crit −0.05，都是換混沌抗） | 38／390 萬／25.96 | KB Necro 220%、Tornado 75、Cyclone 75（+）、Zombie +0.11 |
    | 30% | 3/7 | 8/10 | 5 組（GH crit −0.37、Cyclone −0.20、Tornado −0.15、ED −0.13、GH −0.12） | 50／361 萬／25.91，但生命+ES 3,989 不到 4,000 | 多組 DPS 下滑 |
    | 60% | 3/7 | 8/10 | 5 組（GH crit −0.54、GH −0.33、Cyclone −0.33、Tornado −0.25、Spectre −0.19） | 63／325 萬／25.70，生命 3,549 不過 | 作者組 KB 220% → 142%、Reave 82% → 73%；Smite／Gladiator 混沌 38 → 65、分數 +0.32 |

    建議採用 **0%**：剛好對應底線「混沌抗 ≥ 0」，只有 Glacial Hammer 兩組付出 DPS，底線多過一組；30%／60% 讓多組為了混沌抗犧牲生命和 DPS，
    反而把 Glacial Hammer 的生命壓到底線下。60 以下的軟扣（0.005／點）維持，讓它仍有動力往 60 走。正式採用哪一種由阿福與使用者定。
  - **給使用者在 PoB 打開的 build**（私人庫 `results/v17/home/builds/`，每種強度一份）：

    | 檔案 | 混沌抗 | DPS | 生命 | 最小最大承傷 | 分數 |
    |---|---|---|---|---|---|
    | Glacial Hammer Champion chaos0.xml | 38 | 3,901,681 | 4,252 | 15,572 | 25.96 |
    | Glacial Hammer Champion chaos30.xml | 50 | 3,613,874 | 3,989 | 15,028 | 25.91 |
    | Glacial Hammer Champion chaos60.xml | 63 | 3,252,426 | 3,549 | 13,371 | 25.70 |
    | Glacial Hammer Champion crit chaos0.xml | 38 | 3,850,824 | 4,374 | 13,022 | 25.84 |
    | Glacial Hammer Champion crit chaos30.xml | 52 | 2,909,053 | 4,199 | 12,012 | 25.53 |
    | Glacial Hammer Champion crit chaos60.xml | 65 | 2,402,162 | 4,085 | 11,828 | 25.35 |
    | Cyclone Slayer chaos0.xml | 75 | 2,786,950 | 3,608 | 10,956 | 25.59 |
    | Cyclone Slayer chaos30.xml | 75 | 2,149,760 | 3,628 | 10,365 | 25.35 |
    | Cyclone Slayer chaos60.xml | 61 | 1,940,753 | 3,650 | 10,397 | 25.22 |
    | Smite Gladiator author chaos0.xml | 38 | 107,498,133 | 2,262 | 6,588 | 28.49 |
    | Smite Gladiator author chaos30.xml | 38 | 107,498,133 | 2,262 | 6,588 | 28.49 |
    | Smite Gladiator author chaos60.xml | 65 | 106,309,267 | 2,381 | 6,733 | 28.81 |

    （作者裝備的 Smite／Gladiator 生命只有 2,262，是作者的裝備走 ES／格擋路線，不是底線對象。）
  - 時間／記憶體：每輪約 15 分鐘（--jobs 12），Python 尖峰 14.3 GB、系統 25.3 GB／31 GB。
  - 結果：私人庫 `results/v17/home/`：v17.json／.md／-gap.md（目標 0%，正式）、v17-floor30.*、v17-floor60.*（對照）、builds/（12 個 XML）。
  - **定稿（2026-11-27 19:58，home）**：使用者選 0%。CHAOS_FLOOR 固定為 0、拿掉 POB_CHAOS_FLOOR 環境變數（commit 42d3e3d，分支重整到 4022de9 之上）。
    單元測試 60 全過；完整考試重跑一次，17 組分數、DPS、防禦和 0% 那輪一字不差（作者 3/7、底線 9/10、退步 8/10 同前）。私人庫 v17.* 已覆蓋為定稿結果（數字相同）。

  ### v18 `home/v18-tree-breadth`：樹換血——先量再做，量出來「廣度」不是問題，問題是貪婪搜尋沒有回頭路（2026-11-27 21:01，home）
  - **先量**（量測腳本只讀不改，Cyclone／Slayer、Glacial Hammer／Champion、Storm Call／Hierophant 作者裝各跑一次 v17）：
    樹的每一輪候選 56～411 個、沒試過的 0～78 個，**「最便宜 80 個」的上限在三組共 107 輪裡一次都沒切到**（沒試過的從來不超過 80）；
    整棵樹長完，看過的 486／395／459 個候選**全部至少試過一次**，沒有任何 keystone 排不到。所以「固定種子抽樣＋最便宜」混合沒有東西可補，不做。
    真正的問題：貪婪搜尋每一步都為「當時」的增益選節點，樹長滿後早期選的節點可能已是最弱的一塊，但沒有機會拆掉重花。
  - **改了什麼**（`tools/generate.py`、`tools/PobWorker.lua`、測試；不動考卷）：
    1. 樹長滿後多一個「換血」階段（retune_tree）：把每個已點的大點／keystone 各拆一次量「每點損失」，取最便宜的 5 個，逐一拆掉、
       把空出的點重花在現況下最好的候選（用長樹時量過的增益排序，每輪只試 16 個已知＋8 個新的，省時間），分數有進步就留下，最多 3 回。
       昇華節點和防禦原型自己的 keystone（例如 es 原型的 Chaos Inoculation）不拆。
    2. PoB 拆一個大點只退它自己那 1 點，通往它的小點會留著變廢點（它們仍連在樹上）。Worker 的 passive_remove 加 `prune`：
       順手把變成死路（只剩 1 個已點鄰居）的小點一起拆掉，整條路的點數退回來；`try` 也學會還原 passive_remove（含天賦精通）。
       `pob_contributions` 等原本用 passive_remove 的地方沒加 prune，行為不變。
    3. 版號 18。單元測試 61 全過（新增：拆點不加 prune 退 1 點、加 prune 退整條路）。
  - **完整考試**（`--jobs 12`，連跑兩次 17/17 分數一模一樣）：**作者 4/7**（v17 3/7）、底線 8/10（v17 9/10）、對 v17 退步 9/10。
    每輪 18～19 分鐘（v17 15 分鐘，+20%）；記憶體沒另外量，每組程序數不變。

    | 組 | 分數 v17 → v18 | DPS | 判定 |
    |---|---|---|---|
    | Smite／Gladiator（作者） | 28.49 → 28.73 | 89% → **107%**，防禦 10.11 → 10.16（作者 10.22） | 不及格 → **及格** |
    | Storm Call／Assassin（作者） | 29.65 → 29.74 | 91% → 100%，防禦 10.76（作者 11.21，差 0.45） | DPS 過、防禦不過 |
    | Storm Call／Hierophant（作者） | 31.07 → 31.08 | 112% → 104%，防禦 12.16 → 12.25（作者 12.42，差 0.26 → 0.17）、生命 3,800 → 4,118 | 防禦還差 0.07 |
    | KB Necro（作者） | 26.87 → 26.91 | 220% → 205%，防禦 11.05 → 11.15（作者 11.76） | 防禦不過 |
    | Smite／Slayer、Reave、Skeletons（作者） | +0.13／+0.25／+0.10 | 117%／85%／194% | 及格（同前） |
    | Glacial Hammer／Champion | 25.96 → 26.04 | 390 萬 → 448 萬 | **生命 4,252 → 3,955，底線不過**（換血拆掉 Art of the Gladiator 那條 18 點的路重花） |
    | Glacial Hammer／Champion（crit） | 25.84 → 25.78 | 385 萬 → 360 萬，生命 4,374 → 4,450 | **退步 −0.06**：換血在樹階段是進步，之後的藥水／珠寶／輔助重選落到另一條路 |
    | Cyclone／Slayer | 25.59 → 25.68 | 279 萬 → 310 萬，生命 3,608 → 3,640 | 底線本來就不過 |
    | Raise Spectre | 24.92 → 25.09 | 防禦 11.12 → 11.38 | |
    | Fireball ×2、ED、Doryani 樣板 | +0.04～+0.09 | | |
    | Tornado Shot、Zombie | +0.00 | 換血沒找到更好的 | |

  - **怎麼看**：七組作者裝全部進步（+0.01～+0.25），兩組新過及格線（Assassin DPS 過但防禦差 0.45）。底線少一組是 Glacial Hammer 為了分數把生命換掉：
    分數裡沒有「生命 4,000 底線」這一項，和 Cyclone 3,608 是同一件事（第 3 題），換血只是把它放大。建議 v18 和 v19（生命底線）一起看再決定合併。
  - 結果：私人庫 `results/v18/home/`：v18.json／.md／-gap.md（第二次）、v18-rerun.json／.md（第一次，相同）。
  - 下一題：v19 生命底線（第 3 題）——penalty 加「生命+ES 低於 4,000 每點扣分」，和混沌抗底線同一種做法；從 v18 分支接著做。

  ### v19 `home/v19-life-floor`：生命底線（第 3 題）＋ prune 縮小範圍（阿福 v18 審查意見）（2026-11-27 22:07，home；建在 v18 分支上，兩版一起驗收）
  - **題目**：Cyclone／Slayer 生命 3,608 連幾版不過底線 4,000；v18 的換血又把 Glacial Hammer 從 4,252 換到 3,955。分數裡沒有「生命底線」。
  - **改了什麼**（`tools/generate.py`、`tools/PobWorker.lua`、測試；不動考卷）：
    1. **生命底線**：生命+ES 低於 LIFE_FLOOR=4,000 時每點扣 LIFE_FLOOR_PENALTY=0.002（和混沌抗底線同一種做法）。
       **係數怎麼選**：100 生命 = 0.2 分，約是 100 生命透過 ln(EHP) 自然值的 16 倍、一顆 +10% DPS 大點（0.095）的 2 倍——
       要的是「底線」不是「權重」：差多少就要補到，但補到就停、不再多拿。試過 0.001：GH 補過頭（4,713）DPS 反而掉更多，差別是路徑雜訊不是更溫和，所以不用。
    2. **樹長完之後才算**（life_floor_later，像 resists_later）：第一版從頭就算，樹一開始就往生命走——GH 生命衝到 4,948 但 DPS 448 萬 → 150 萬，
       Smite／Gladiator 作者裝 DPS 砍半還補不到。改成樹先照 v18 長完，進換血階段才開始扣，由換血「用最少代價補到底線」：
       生命不夠時換血會一直做（最多 8 回，平常 3 回），且候選重新量（長樹時量的增益沒算生命）。之後的藥水、珠寶、暗金也都看得到底線。
    3. **作者裝不套底線**（life_floor=0）：作者的裝備決定生命預算，考卷也只對樣板組查底線。測過「底線取 4,000 和作者自己的生命+ES 取小」：
       Smite／Gladiator 作者自己 3,378、生成 2,626，補到 3,452 要付 40% DPS（107% → 63%）變不及格，所以不這樣做。
    4. **prune 只剪這次拆除造成的死路**（阿福意見）：先記下拆除前就是葉子的小點、從被拆節點的鄰居往外剪；單元測試加「原本就有的死路小點不會被剪」。
       結果：七組作者和八組樣板的 build 和 v18 一字不差，只有 GH、Cyclone 兩組（生命底線起作用的）不同——所以 v18 考試裡 prune 範圍太寬沒有影響到結果。
    5. penalty() 對 benchmark.scorer（跳過 __init__ 的 Generator）容錯：新旗標用 getattr 預設，不會再像 v13 那樣讓作者組全部跳掉。
    6. 版號 19。單元測試 61 全過。
  - **完整考試**（`--jobs 12`，連跑兩次 17/17 相同；每輪 18.5 分鐘）：作者 **4/7**（和 v18 相同）、**底線 10/10**（第一次全過）、對 v18 退步 9/10。

    | 組 | 分數 v18 → v19 | DPS | 生命+ES | 判定 |
    |---|---|---|---|---|
    | Glacial Hammer／Champion | 26.04 → 26.01 | 448 萬 → 390 萬 | 3,955 → **4,625** | 底線過（v18 不過）；−0.03 不算退步 |
    | Cyclone／Slayer | 25.68 → 25.54 | 310 萬 → 259 萬 | 3,640 → **4,017** | **底線過（v11 以來第一次）**；**退步 −0.14**：補 +377 生命付了 16% DPS，換血拆 Hatchet Master 那條 7 點路改拿 Blood Drinker、Life Mastery 等 |
    | 其他 8 組樣板、7 組作者 | +0.00 | 相同 | 相同 | 和 v18 一字不差 |

  - **怎麼看**：Cyclone 的 −0.14 是分數制度的必然——底線補到後罰分為 0，剩下的就是「為了生命少掉的 DPS」。這不是搜尋退步，是使用者定的底線在要求它。
    如果要 Cyclone 不掉 DPS，得靠別的來源補生命（珠寶、藥水、暗金），這是之後的題目。
  - 結果：私人庫 `results/v19/home/`：v19.json／.md／-gap.md（第二次）、v19-rerun.*（第一次，相同）。
  - 下一題（給阿福排）：第 2 題 KB Necro／Storm Call 防禦差距（Hierophant 線索：護甲 32.7k vs 14.2k、生命；Assassin 防禦差 0.45）。

  ### v20 `home/v20-defence-gap`：防禦差距（第 2 題）——差在格擋，原因是順序：樹和光環都在「其他東西還沒定」時就決定了（2026-11-27 23:40，home）
  - **先量**（三組作者裝：KB Necro、Storm Call／Assassin、Storm Call／Hierophant，v19 的生成 build 對作者 build）：
    1. **防禦分數拆開**：差距全在 ln(EHP)，最小最大承傷和回復生成的都不輸作者（Assassin 最小承傷 14.9k vs 作者 13.1k）。
    2. **EHP 差在格擋**：PoB 的 TotalEHP = 能吃幾下 × 每下傷害，格擋是乘法。有效格擋／法術格擋：KB 作者 72／72 vs 生成 36／25；Assassin 作者 90／88 vs 42／52；
       Hierophant 作者 78／73 vs 75／44。Doryani 兩組的護甲（作者 20k／33k vs 生成 5k／15k）是第二項，但只影響閃電承傷，而閃電不是生成 build 最小的那項。
    3. **每個零件單加到生成 build 上**（v19-gap 的移植法再加格擋欄）：Tempest Shield 一顆 Hierophant 法術格擋 44 → 71、防禦 +0.195；Assassin 52 → 82、+0.168；
       零點數、零 DPS。Assassin 的 Faith and Steel 2 點 +0.125、Cruel Preparation 2 點 +0.108。格擋零件合起來比單加總和大（Assassin 四個合加 +0.64 vs 單加總和 +0.57）。
    4. **為什麼生成器沒拿**：(a) Tempest Shield 要保留魔力，光環在空 build 上選時 DPS 光環先佔滿（Assassin 加上去保留 −265，Hierophant −167）；
       (b) 樹換血在藥水、珠寶、輔助互換**之前**就結束，之後 Assassin DPS 從 1.13 億跳到 1.75 億，防禦節點相對變值錢，但沒有步驟回頭看樹：
       在最終 build 上算，拆最便宜的 2 點只損 0.034、加 Faith and Steel 賺 +0.085——換血會做，只是沒機會。
    5. **評分有沒有算漏**（阿福問的）：沒有。護甲對閃電的折算、格擋、閃避、壓制都在 PoB 的 EHP 裡，defence 分數用的就是它。差距是**搜尋順序**，不是公式。
       KB Necro 例外：作者是 CI＋Bone Offering（Mistress of Sacrifice 讓祭品作用在自己）的格擋路線，是整個原型的選擇，局部換血到不了；
       生成的 DPS 是作者的 203%，分數比作者高（26.9 vs 26.5），但考卷要防禦 ≥ 作者 −0.1——分數和考卷在這組意見不同，要不要讓生成器知道「DPS 夠了就換防禦」是另一題。
  - **改了什麼**（`tools/generate.py`、`tools/PobWorker.lua`、測試；不動考卷）：
    1. **光環互換**（retune_buffs）：所有東西定了之後，每個已選光環／增益對所有沒選的逐一互換，分數進步就換，最多 2 回。Worker 新增 `group_replace`（可還原）。
    2. **結尾再做一次樹換血**（retune_tree(fresh=True)）：在光環互換之後，候選全部重新量（長樹時量的增益已失效），每輪 40 個新候選。
    3. 版號 20。單元測試 62 全過（新增 group_replace 換光環並還原、skill_groups 追蹤互換）。
  - **完整考試**（`--jobs 12`，連跑兩次 17/17 相同；每輪 30 分鐘，v19 是 18.5 分）：作者 **5/7**（Hierophant 新過；v19 4/7）、底線 **10/10**、對 v19 **無退步 10/10**（10 組樣板 7 組進步、3 組持平）。

    | 組 | 分數 v19 → v20 | DPS（作者%） | 防禦（作者） | v20 多做了什麼 | 判定 |
    |---|---|---|---|---|---|
    | Storm Call／Hierophant | 31.08 → 31.28 | 1.50 億 → 1.45 億（104% → 100%） | 12.25 → **12.49**（12.42） | Wrath → Tempest Shield、RF of Arcane Devotion → Righteous Fire；拆 Annihilation、Divine Fervour | **過（v19 不過）** |
    | Storm Call／Assassin | 29.74 → 29.80 | 1.75 億 → 1.67 億（100% → 96%） | 10.76 → 10.86（11.21，差 0.35） | Zealotry → Wrath；拆 Coldhearted Calculation、Enduring Bond 拿防禦珠寶、Mana Mastery、Resourcefulness | 不過 |
    | KB Necro | 26.91 → 26.94 | 7.1M → 7.0M（203%） | 11.15 → 11.19（11.76，差 0.57） | 光環沒換；結尾拆 Will of Blades | 不過（原型問題，見上） |
    | Smite／Slayer | 30.08 → 30.22 | 1.50 億 → 1.28 億（117% → 100%） | 11.27 → 11.56 | Wrath → Arctic Armour、Blood Rage → Tempest Shield、Enduring Cry → Blood Rage | 過 |
    | Smite／Gladiator | 28.73 → 29.30 | 1.29 億 → 1.46 億（107% → 122%） | 10.16 → 10.61 | Purity of Elements → Wrath、Precision → Vitality、Blood Rage → War Banner、Herald of Thunder → Precision | 過 |
    | Reave／Gladiator | 30.80 → 30.86 | 1.49 億 → 1.59 億（85% → 91%） | 12.01 → 12.00 | 光環沒換；結尾拆 Bladedancer、Beef、Bloodless | 過 |
    | Skeleton Mages | 26.26 → 26.28 | 2.77M → 2.78M（195%） | 11.43 → 11.44 | 結尾拆 Mind Over Matter、Melding | 過 |
    | GH／Champion（crit） | 25.78 → 26.05（+0.27） | 3.60M → 4.49M | 10.80 → 10.84 | Vitality → Precision、Anger → Hatred、Herald of Ash → Tempest Shield | 底線過 |
    | Essence Drain | 22.63 → 22.81（+0.18） | 137k → 185k | 10.88 → 10.76 | 結尾拆 Steeped in the Profane、Melding | 底線過 |
    | Fireball（兩組） | +0.12／+0.14 | 8.0M → 8.8M／7.4M → 8.1M | +0.02／+0.05 | Vitality → Tempest Shield、Anger → Zealotry | 底線過 |
    | Cyclone／Slayer | 25.54 → 25.66（+0.12） | 2.59M → 2.97M | 10.77 → 10.76 | Haste → Flesh and Stone、Blood and Sand → Pride；生命 4,017 → 4,044 | 底線過；v19 的 −0.14 補回大半 |
    | Raise Zombie／Spectre | +0.03／+0.02 | 1.56M → 1.53M／相同 | +0.05／+0.02 | Vitality → Tempest Shield／結尾拆 Might、Mind Over Matter | 底線過 |
    | GH／Champion、Tornado Shot | +0.00 | 相同 | 相同 | 一字不差 | 底線過 |
    | Doryani 樣板 | 28.47 → 28.46（−0.00） | 76.0M → 74.4M | 10.38 → 10.40 | 結尾拆 Breath of Lightning 拿 Physique、Fervour | 底線過 |

  - **怎麼看**：
    1. Tempest Shield 在 6 組靠互換拿到（Hierophant、Smite／Slayer、GH crit、Fireball×2、Zombie；KB、Reave、Spectre 原本就有），印證「量」的結論：格擋便宜、原本是順序讓它排不進去。
    2. 互換也會往 DPS 走（Smite／Gladiator Purity → Wrath +17%、Assassin Zealotry → Wrath），它只認分數，不是偏防禦。
    3. Assassin 還差 0.35：作者格擋 90／88 是好幾個格擋零件合起來的（Faith and Steel、Sanctuary、Arcane Guarding 等，四個合加 +0.64 而單加各只 +0.1 左右），換血一次拆 2～3 點只拿得到一個，單個不夠划算；和 KB 一樣偏「路線」問題，但沒 KB 那麼遠。
    4. **一個觀察**：Doryani 樣板組結尾換血搜尋中量到 28.469 → 28.473（+0.004），考卷重算存檔的 build 卻是 28.464——搜尋中的量測和存檔重算差 0.009（DPS 相同，差在防禦）。
       不影響任何判定，但表示「存檔重放」和「try 量測」有一點不一致（可能是精通或 prune 重放），值得之後查一下。
    5. 時間：每組多 2～8 分鐘（光環互換每回 ≈ 已選光環數 × 未選光環數次 try；結尾換血每輪 40 個新候選 × 5 次試拆），整輪 18.5 → 30 分。
  - 結果：私人庫 `results/v20/home/`：v20.json／.md／-gap.md（第二次）、v20-rerun.*（第一次，相同）。
  - 第二階段條件：作者 ≥ 5/7 這版達到；「連續兩版無退步」v19 是 9/10（Cyclone）、v20 10/10，再一版無退步就齊。
  - 下一題（給阿福排）：(a) Assassin／KB 剩下的格擋差距是路線問題——要不要讓生成器在 DPS 遠超作者時主動往防禦走（分數和考卷目前意見不同）；
    (b) 搜尋量測 vs 存檔重算的 0.009 差；(c) 時間 30 分，若要縮短可把光環互換限制在「有保留魔力的光環」。

  ### v21 `home/v21-replay-gap`：搜尋量到的分數＝存檔重放的分數（阿福排的 (b)）——差在等長路徑的平手判法（2026-11-28 01:30，home）
  - **找到的原因**（Doryani 樣板組 v20：搜尋量到 28.473、存檔重算 28.464，差 0.009）：
    1. 兩邊只差一個數：**閃避 3,091 vs 2,788**（EHP 跟著差 500），DPS、生命、最大承傷全同。v20 的 17 組裡有 simdata 紀錄可對的 14 組，最終量測不一致的只有這一組。
    2. 不是還原沒還乾淨：最終狀態重放和 export 一致；最終狀態上 105 種候選、換血當下狀態上 425 種候選，每個「試完接空候選」都和基準一字不差。
    3. 是**同一批候選互相影響**：換血當下那一批 40 個候選裡，Harrier 排第 14 個，批次裡量到配 4 點拿不到 Dex（閃避 2,788），單獨量是走 3 個 Dex 小點（2,879）。
       要前面 4 個候選（Lord of the Dead → Harsh Lessons → Deep Wisdom → Life Raker）都試過才會翻，任何 3 個子集都不翻。
    4. **機制**：PoB 算每個節點的路徑用多源 BFS，根節點來自 `pairs(spec.allocNodes)`，兩條**等長**路徑誰先到誰贏；這張表的 `pairs` 順序取決於它的配置歷史（配過、拆過哪些點）。
       同一次 try 裡前面試過的候選改了這個歷史，後面的候選就可能改走另一條等長路徑（同樣的點數、不同的小點）。搜尋收下那個數字，存檔重放時歷史不同、走回另一條：
       Fervour 那一步在搜尋裡走到 3 個 Dex 小點（+303 閃避），存檔沒有。
  - **改了什麼**（`tools/PobWorker.lua`、`tools/generate.py`、測試；不動考卷）：
    1. **canonicalPaths**：`passive_add`、`mastery_add`、`candidates` 讀 `node.path` 之前，把 allocNodes 依 id 排序重建成新表再 `BuildAllDependsAndPaths()`。
       路徑從此只跟「配了哪些點」有關，和歷史無關；try、重放、export 三邊一致。
    2. passive_add／mastery_add 的還原順手補兩件事：還原 `masterySelections`（否則同一批裡同一效果的下一個候選會被判「已被拿」）、還原後重算路徑。
    3. retune_buffs 的區域變數 `pool` 改名 `choices`（阿福意見）。
    4. 單元測試 63 全過。新增「每個候選批次量到＝單獨量到＝收進狀態重放」：測試 build 上長 12 個天賦的樹，162 個候選全部相同，且 `candidates` 列的費用＝實際付的點
       （修之前 162 個有 16 個不同）。prune 的舊測試改挑「路徑沒借用舊死路」的天賦（正規化後路徑固定，挑到的永遠同一個）；prune 本身沒改。
    5. 版號 21。
  - **驗證**：Doryani 樣板組單跑：搜尋最後量到、整個狀態重新 try、export 三邊 **28.5520 一字不差**，沒有任何指標不同。
  - **(c) 光環互換只換有保留的光環**：這版沒做——平手改判後考試本來就不可能和 v20 一字不差，照阿福的前提要另開一版；而且光環互換的量不大
    （每回 ≈ 已選光環數 × 未選數 ≈ 150 次 try、兩回 300；結尾換血 5 次試拆 × 每輪 56 個候選 × 幾輪 ≈ 800+），時間主要在結尾換血。
  - **完整考試**（`--jobs 12`，連跑兩次 17/17 相同；每輪 30／28 分）：作者 **4/7**（v20 5/7）、底線 10/10、對 v20 退步 **9/10**（Tornado Shot −0.07）。
    **這版有退步，第二階段「連續兩版無退步」沒達成。**

    | 組 | 分數 v20 → v21 | DPS（作者%） | 防禦 | 怎麼回事 | 判定 |
    |---|---|---|---|---|---|
    | Smite／Gladiator | 29.30 → 29.15 | 1.46 億 → 0.80 億（122% → **66%**） | 10.61 → 11.10 | 樹從早期就走到另一個盆地（格擋側：Blade Barrier、Wall of Steel、Versatile Combatant，v20 是 Acuity、Ballistics 那側）；結尾輔助互換 Volatility → Life Gain on Hit，DPS 1.14 億 → 0.80 億但分數 28.99 → 29.14 | **不過（v20 過）** |
    | Storm Call／Hierophant | 31.08 → 31.40 | 1.45 億 → 1.88 億（100% → 129%） | 12.49 → 12.35（12.42） | 拿 Eldritch Battery、Arcane Guarding、Breath of Lightning | 過（防禦差 0.07 在 −0.1 內） |
    | Storm Call／Assassin | 29.80 → 29.85 | 1.67 億 → 1.86 億（107%） | 10.86 → 10.81（11.21） | 路不同 | 不過（差 0.40） |
    | Smite／Slayer | 30.22 → 30.21 | 1.28 億 → 1.23 億（95%） | 11.56 → 11.60 | 路不同 | 過 |
    | Skeleton Mages | 26.28 → 26.26 | 2.78M → 2.53M（177%） | 11.44 → 11.52 | 路不同 | 過 |
    | KB Necro、Reave | 相同 | 相同 | 相同 | 一字不差 | 不過／過 |
    | Tornado Shot | 22.84 → 22.77（**−0.07**） | 235k → 239k | 10.48 → 10.39；生命 5,518 → 4,900、混沌抗 75 → 61 | v20 的 Heart of Oak、Herbalism、Fangs of the Viper 等 7 個天賦換成 Atrophy、Golem Commander 兩個，精通少 3 個 | **退步** |
    | GH／Champion | 26.01 → 26.09（+0.07） | 3.90M → 4.42M | 生命 4,625 → 4,308 | 路不同 | 底線過 |
    | Doryani 樣板 | 28.46 → 28.55（+0.09） | 74.4M → 87.6M | 10.40 → 10.32 | 路不同 | 底線過 |
    | Essence Drain | 22.81 → 22.78（−0.03） | 185k → 165k | 10.76 → 10.90 | 路不同 | 不算退步 |
    | 其他 6 組樣板 | +0.00 | 相同 | 相同 | 一字不差 | 底線過 |

  - **怎麼看**：
    1. 修法本身成立（三邊一致），且「量測一致」是第二階段自我對弈的前提，這部分達成。
    2. 考試變動不是修法加分或扣分，是**平手路徑改判 → 貪婪搜尋走到另一個盆地**：17 組 9 組一字不差、8 組不同，分數有升（+0.32、+0.09、+0.07、+0.05）有降（−0.15、−0.07、−0.03），加總 +0.28。
       這說明 v20 的 5/7 和 v21 的 4/7 都有運氣成分——同一套規則、平手往左或往右，就差一組作者。考卷要「連續兩版無退步」，而搜尋對路徑這麼敏感，門檻會一直被路徑雜訊左右。
    3. Smite／Gladiator 的 Life Gain on Hit 和 v20 的 KB Necro 一樣：分數說值得（+0.15），考卷說 DPS 掉太多。分數和考卷意見不同的例子已經兩個。
  - 結果：私人庫 `results/v21/home/`：v21.json／.md／-gap.md（第二次）、v21-rerun.*（第一次，相同）。
  - **給阿福決定**：(a) v21 的退步算不算「路徑雜訊」而非退步（若算，它和 v20 的規則差異只有平手判法）；(b) 要不要處理搜尋對路徑的敏感
    （例如換血結束前比較「兩種平手判法」各跑一次取高分，或多起點）；(c) 分數和考卷意見不同（Life Gain on Hit、KB Necro）要改哪一邊。這三個都先不動，等指示。

  ### v22 `home/v22-tie-noise`：樹的階段雙起點（兩種平手規則各長一次樹，取高分）——先量雜訊，再縮雜訊（2026-11-28 04:10，home）
  - **先量**（同一份 v21 程式，只把平手規則反過來，完整考試跑一次，27 分；`library/benchmark/v21-tie-reverse.*`）：
    1. 對 v21 正常平手：17 組 **8 組一字不差、9 組不同**。分數差：KB +0.02、Smite／Slayer −0.03、Assassin −0.03、Hierophant −0.05、Skeletons −0.07、GH crit −0.02、
       Cyclone 0.00、**GH −0.07、Spectre −0.17**（超過 0.05 門檻）、**Smite／Gladiator −0.55**（第三個盆地：v20 29.30、v21 29.15、反向 28.60）。平均 |差| 0.059。
    2. 及格翻轉：作者這一對沒翻（兩邊 4/7），但 v20→v21 翻過 Smite／Gladiator；底線 10/10 兩邊都過；退步判定以 v21 為基準 8/10。
       **考卷本身的雜訊：典型 ±0.05，10 組樣板有 2 組會超過 0.05，作者偶爾翻一組。**
    3. **分岔點**（simdata 逐步比對）：Smite／Gladiator 在 state size 27、Spectre 45、GH 69／70——全部在**長樹階段**（grow_tree），之後各走各的盆地。
       所以修法只在樹的階段多起點，不全程雙跑。
  - **改了什麼**（`tools/PobWorker.lua`、`tools/generate.py`、測試；不動考卷）：
    1. 平手規則變成請求參數 `tie`（asc／desc／alt／altdesc；alt 用 id 的末三位先排），worker 的 canonicalPaths 照它排序。
    2. **tree_phase**：長樹＋第一次換血用 TIE_RULES（asc、desc）各跑一次，從同樣的寶石、藥水出發，取分數高的樹，之後**沿用那條規則**（重放才一致）。
       結果 json 多 `tie` 欄、報告步驟表多一行「tie rule kept」、build 備註寫明規則（重放生成器的變更需要同一規則）。
    3. `POB_TIE_RULES=alt,altdesc` 讓整個搜尋改用另一對規則——量「雙起點之後還剩多少雜訊」用的。
    4. 單元測試 64 全過。新增 `test_tie_rules_cost_the_same_and_replay_alike`：另一規則下每個候選**費用相同**（才叫平手）、部分改走別的小點（20 個天賦的樹，179 個候選 5 個會翻）、
       批次＝單獨＝重放在新規則下仍成立。v21 的 `test_a_candidate_measures_the_same_in_a_batch_as_alone` 照舊通過。
    5. 版號 22。
  - **完整考試**（`--jobs 12`，同一份程式三次：預設對 asc／desc → alt／altdesc → 預設再一次）：
    1. **決定性**：預設兩次 17 組一字不差。判定（預設、alt 兩對都一樣）：**作者 4/7、底線 10/10、對 v21 無退步 10/10**。及格名單和 v21 相同，兩對規則沒翻任何一組。
    2. **對 v21**：15 組一字不差（asc 贏的組就是 v21 的路）。KB +0.02（desc 贏）、Hierophant −0.05（desc 贏；樹階段 desc 分高，走到最後卻比 v21 的 asc 低 0.05——樹階段的高分不保證最後最高）。
       Smite／Gladiator asc 贏，留在 29.15，沒掉進反向規則的 28.60。保留的規則：預設對 15 組 asc、2 組 desc；alt 對 11 組 alt、6 組 altdesc。
    3. **雙起點之後的雜訊**（預設 vs alt，同一份 v22 程式）：**9 組一字不差、8 組不同**。Assassin −0.10、Skeletons −0.08、GH +0.0497、Tornado +0.04、Hierophant +0.04、
       KB −0.02、GH crit +0.01、Smite／Gladiator +0.01。平均 |差| **0.059 → 0.021**，最大 **0.55 → 0.10**；10 組樣板超過 0.05 的 **2 → 0**（GH 剛好在門檻下），作者超過 0.05 的 2 → 2（換了人：Assassin、Skeletons）。
       量法不對稱（v21 是一條規則對它的反向，v22 是一對取高分對另一對取高分），但極端值（−0.55、−0.17）消失了，樣板全部落在門檻內。
    4. 剩下的雜訊在作者組：Assassin 0.10、Skeletons 0.08。這兩組都還差 0.05 以上才會翻及格（Assassin 防禦差 0.40、Skeletons 過關有餘），這次沒翻。
  - **時間**（home，`--jobs 12`）：每組 ×1.27～×1.61，合計 **244.5 → 350.5 組·分（×1.43）**；整場 v21 30／28 分 → v22 **40／38／39 分**。阿福的上限是每組 ≤ ×2、整場 ≤ 60 分，都在內。
    樹的階段跑兩次，但長樹之後的階段只跑一次，所以不到 ×2。
  - 結果：私人庫 `results/v22/home/`：v22.*／v22-gap.md（預設，第二次）、v22-rerun.*（預設，第一次，相同）、v22-tie-alt.*、v21-tie-reverse.*。
  - **給阿福決定**：(a) 雜訊有縮（極端消失、樣板全在門檻內、平均 1/3），但沒歸零——要不要就這樣接受，門檻怎麼訂（例如樣板 0.05 保留、作者看及格翻轉而不看分差）；
    (b) 第二階段「連續兩版無退步」從哪一版起算（v22 對 v21 10/10）；(c) 時間縮短（光環互換只換有保留的）要不要排 v23。(c) 之前說好 v22 之後才做，分數和考卷意見不同的兩組仍沒動。

  ### v23 `home/v23-selfplay-prep`：階段二前必修——紀錄補平手規則、換規則前重設亂數、光環互換限保留技能（開關）（2026-11-28 07:00，home）
  - **先量**（simdata 裡 v22 的 51 次考試 run，390,867 筆 try）：
    1. 換血階段（buff swap）**9,870 筆，佔 2.5%**；其中換出或換入「不保留魔力／生命」技能的 5,580 筆（換血的 57%，**全部 try 的 1.4%**）。
       長樹 60%、輔助互換 17%、輔助 8%——時間在樹，不在光環。
    2. v22 考試有 **3 組保留了無保留技能的互換**：Smite／Slayer「Blood Rage → Tempest Shield」「Enduring Cry → Blood Rage」、Hierophant「Righteous Fire of Arcane Devotion → Righteous Fire」。
       所以「只試有保留的」若直接當預設，考試不可能和 v22 一字不差——和完成標準衝突。做成開關，另跑一場量影響。
    3. 哪些技能「有保留」照 PoB 自己的判法（CalcPerform 算保留用的 SkillType.HasReservation、排除 ReservationBecomesCost）：光環、先驅、Precision、Vitality、
       Flesh and Stone、Blood and Sand、Tempest Shield、Arctic Armour 有（40 個）；**旗幟三種、Pact of Beidat 在 PoB 資料裡沒有保留**（遊戲改版過），Enduring Cry、Blood Rage、正義之火兩種也沒有。
  - **改了什麼**（`tools/simlog.py`、`tools/generate.py`、`tools/PobWorker.lua`、測試；不動考卷）：
    1. **simdata 多 `tie` 欄**：`samples.tie`（每筆 try 跑在哪條平手規則下）、`runs.tie`（最後留下的規則）。舊資料 NULL ＝ asc（v23 之前只有這一條）。
       同一個狀態在另一條規則下是另一個狀態（走的小點不同、數字不同），所以 `state_hash` 把非 asc 的規則算進去；asc 和舊資料的 hash 不變。
       舊資料庫第一次 connect 自動 ALTER 加欄（兩張表）——`library/simdata.db` 已加好，v22 的 51 個 run tie 為 NULL，v23 的 51 個 run 45 asc／6 desc。
    2. **tree_phase 的亂數**：進每條規則前把 `self.rng` 還原到同一個狀態，選完樹後從「贏的那條規則」的亂數狀態接著走——結果不再和規則先後順序有關。
       亂數只在有 guide 時用到（narrow、換血未試過的候選抽樣），考試沒 guide，所以不影響考試。
    3. **`POB_BUFF_SWAP=reserving`**（開關，預設 all＝和 v22 一樣）：結尾光環互換只在「有保留」的技能之間換（換出、換入都限）。worker 新方法 `reserving` 從 PoB 資料列出。
    4. `TIE = 1e-9` 的註解放回原行。
    5. 版號 23；`STILL_VALID_FROM` 維持 22（搜尋本身沒變，v22 的 selfplay 結果仍有效）。
    6. 單元測試 **68 全過**。新增：simlog 記 tie（asc 與無規則同 hash、desc 另一個狀態、runs.tie）、舊資料庫自動加欄、
       worker 的 reserving 名單（Grace／Hatred／Tempest Shield 有，Enduring Cry／Blood Rage／正義之火／旗幟／Pact of Beidat 沒有）、
       tree_phase 兩條規則抽到同一批亂數且與順序無關（換序跑一次，最後亂數狀態相同）。
  - **完整考試**（`--jobs 12`，預設兩次＋`POB_BUFF_SWAP=reserving` 一次）：
    1. **對 v22 一字不差 17/17**（分數、DPS 全同），預設兩次也 17/17 相同（決定性）。判定：作者 4/7、底線 10/10、對 v22 無退步 10/10（全部 +0.00）。保留的規則和 v22 相同：15 組 asc、2 組 desc。
    2. **開關開著**（限保留技能）：15 組一字不差，**2 組變、都變差**：Smite／Slayer 30.21 → 30.11（防禦 11.60 → 11.50，少了 Blood Rage → Tempest Shield 那一換）、
       Hierophant 31.35 → 31.23（DPS 181.5M → 156.1M，作者比 125% → 108%，少了正義之火兩版互換）。兩組仍及格，判定不變。
       時間 351.3 → **331.5 組·分（−5.6%）**，但整場 38:24 → 38:26 **沒縮**：整場看最長的 KB／Necro（30～31 分），它不在光環那一段。
  - **selfplay**（`POB_LIBRARY` 指到兩個暫存目錄，`--hours 0.1 --jobs 3 --runs 3 --seed 1`，同三組跑兩次：Detonate Dead of Scavenging／Saboteur、Blade Trap of Greatswords／Deadeye、Double Strike of Momentum／Assassin，每組 10～14 分）：
    1. 紀錄裡有 tie：`samples.tie` asc 13,738／desc 8,025（共 21,763 筆）、`runs.tie` asc 2／desc 1。
    2. 同 seed 兩次：三組 final 一字不差，**21,763 筆 try 逐筆相同**（含 tie、state_hash）。
  - **時間**（home，`--jobs 12`）：預設 352.4／351.3 組·分對 v22 350.5（同一份搜尋，差在雜訊內）；整場 40:03／38:24 對 v22 40／38／39 分。
    **預設沒縮**——這版沒改搜尋本身，照完成標準「時間要縮短」只有開關開著才成立，且只縮組·分不縮整場。
  - 結果：私人庫 `results/v23/home/`：v23.*（預設，第二次）、v23-rerun.*（預設，第一次，相同）、v23-buffswap.*（開關開著）。
  - **給阿福決定**：(a) 光環互換限保留技能要不要改成預設——省 5.6% 組·分、整場不省，Smite／Slayer −0.10、Hierophant −0.12（都還及格）；
    (b) 要真正縮時間得從長樹（60%）和輔助互換（17%）下手，例如第二條規則的長樹沿用第一條量過的候選排序、或兩條規則共用「沒變的候選」的量測；
    (c) 這版只是階段二的地基（紀錄齊、亂數可重現），考試一字不差＝「沒退步」第二版，但搜尋沒進步——進不進階段二由使用者決定。

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

## T6 home：抓市場裝備池（2026-11-28 使用者指派）
- 給：home（使用者在家幫忙登入）
- 狀態：基本裝完成（2026-11-28，私人庫 `-r2`、`-r3`、`-rB`，搜尋方法改成 MARKET 的「定案」）；剩腰帶混沌抗組、畢業裝
- 內容：照 `tools/MARKET.zh-TW.md` 的搜尋條件，用 home 的內建瀏覽器在官方交易網站（國際服、當季聯盟）搜尋：
  - 基本裝每件 ≤ 10 混沌石，每個部位 10～20 件；畢業裝每件 ≥ 10 神聖石，每個部位 5～10 件；武器先不做。
  - Cloudflare 驗證和登入**由使用者自己點、自己登入**，AI 不代點驗證、不輸入密碼。
  - 每個部位最多搜 2～3 次，每次間隔至少 10 秒；只讀，不交易、不私訊賣家。
  - 存：裝備英文原文、價格（含幣別）、日期、聯盟、搜尋條件；**不存賣家帳號和角色名**。
    放私人庫 `inputs/gear/market/<聯盟>/<日期>/<部位>.json`，用 labdata 的 git 流程推上去（commit 簽 Claude Fable 5.1）。
- 交回：各部位抓到幾件、價格範圍、生命／抗性／命中值等數值的分佈（中位數、前 25%），給阿福定門檻；
  遇到被擋（查詢次數限制）就停，回報，不要重試硬衝。
- 完成標準：七個部位（不含武器）基本裝都有資料，畢業裝至少有參考；數值分佈報告。

## T7 home：第 24 版——樣板裝換成市場真實裝備（2026-11-28 使用者同意）
- 給：home，分支 `home/v24-market-gear`
- 狀態：待做
- 資料：私人庫 `inputs/gear/market/intl-Covens/2026-11-28-r2`、`-r3`、`-rB`（每部位每底材 10 件，已排序）。
- 內容：
  1. 每個部位、每種底材取**第 5 名**（中等偏好的 10c 貨）的原文，轉成 PoB 物品文字（隱性／詞綴標記照 PoB 格式），
     存成公開庫 `tools/data/gear_templates.json`（只有物品詞綴、聯盟、日期，沒有賣家）。
  2. `armour_set` 改讀這份：防具依流派的底材（護甲／閃避／能盾）；頭盔、手套用「加命中」組；戒指用「加命中」組；
     項鍊：暴擊路線用「暴擊加成」組，其他用「生命＋元抗」組；腰帶用「生命＋元抗」組。武器、盾牌先不變。
  3. **不再額外加屬性**（使用者：屬性只配到夠用）。屬性不夠時由天賦樹補；確認生成器有把「屬性需求沒達到」算進去，
     沒有的話要加。混沌抗沿用目前規則（市場 10c 的混沌抗很少，影片也說撐到 0 左右即可）。
  4. 能盾原型的「生命行換成能盾」改寫法要跟著改（直接用能盾底材的市場裝備）。
  5. 法術流派戴「加命中」頭盔手套會浪費詞綴，這版先接受，記在報告裡，下一版補洞配裝再處理。
- 驗收：`GENERATOR_VERSION = 24`，跑考試，跟 v23 逐組比（生命、抗性、混沌抗、屬性、DPS、分數）。
  這版換了裝備基準，分數變動是預期的，「沒退步」從 v24 重新算；報告要說明哪些組變了、原因是哪個部位。
  給使用者看的 build 放 `src\Builds\AI 試算 v24\`，同一份推私人庫。測試要過（python -m unittest discover tools/tests）。
- 之後（不在這版）：補洞配裝（從每部位 10 件挑最能補缺口的）、腰帶混沌抗組、畢業裝。

## （暫停）家裡電腦跑自我對弈（第 2～5 份）
- 階段二才開始，指令見 HOME_PC B 段。
