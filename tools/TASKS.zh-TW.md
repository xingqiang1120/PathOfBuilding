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
- 狀態：進行中（v14～v17 已驗收合併；v18 樹換血已交回，等阿福驗收；接著 v19 生命底線）
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
    Purity of Elements），之後的路徵就不同——KB Necro（作者裝備混沌 −60）DPS 171% → 220%、Tornado Shot 混沌 61 → 75、Cyclone 70 → 75。
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
