# 家裡電腦加入（第 3 台＋家裡的 AI）

家裡電腦有兩個用途：
1. **跑計算**：家裡時間最多（半夜到隔天晚上 8 點），拿最大份的自我對弈，也跑驗收考試（benchmark）。
2. **家裡的 AI**（第二階段）：在家裡開 Claude，接「單項優化任務」，做完交回來給公司這邊的負責人（阿福）驗收。

兩個 AI **不會自動共享記憶**，所以靠 repo 裡的文件溝通：
- `tools/ROADMAP.zh-TW.md`：方向和做過什麼。
- `tools/ACCEPTANCE.zh-TW.md`：驗收標準（考卷）。
- `tools/TASKS.zh-TW.md`：派給家裡 AI 的任務、狀態和交回的結果。
- git 歷史：誰改了什麼。

---

## A. 第一次準備（只做一次）

1. 照 `tools/MULTI_PC.zh-TW.md` 的 A 段第 1～3 步：安裝 Python 3.12（64 位元，勾選 Add to PATH）、安裝 Git，然後 `git clone`。
   - 家裡要「改程式」的話，clone 時**不要**加 `--depth 1`，才有完整歷史。
2. **（要跑驗收考試才需要）** 把真人 build 庫從公司電腦複製過去。它不在 git 裡，因為裡面有帳號和角色名稱：
   - 公司：`E:\ai\path of exile\PathOfBuilding\library\builds.db`、`library\raw\`、`library\summary\`
   - 家裡：放到同樣的 `library\` 位置。
3. 模擬資料不用複製：第 11 版全部重跑，家裡從空的開始就好。

## B. 跑計算（依每台的時間分份）

> **目前是階段一（見 TASKS）：自我對弈暫停，家裡和第 2 台只跑驗收考試和差距報告。** 下面的排程是階段二用的。

2026-11-26 起的排程（使用者定）：公司這台晚上常常在做別的事，**預設不跑**；第 2 台只有晚上；
家裡電腦從半夜 12 點跑到隔天晚上 8 點，時間最多，所以拿大份。技能分成 5 份：

| 電腦 | 時段 | 指令（啟動前先 `git pull`） |
|---|---|---|
| 第 2 台（14 核心） | 晚上 | `python tools/selfplay.py --hours 5 --jobs 8 --shard 1/5` |
| 家裡 | 00:00～20:00 | `python tools/selfplay.py --hours 19.5 --jobs <核心數減 2> --shard 2-5/5` |
| 公司這台 | 只有使用者說可以時 | 不分份：先合併兩台的資料，再 `python tools/selfplay.py --hours N --jobs 4`（會自動跳過已跑完的） |

`--hours` 是「多久後不再開新的」，正在跑的會跑完（最多 40 分鐘），所以家裡設 19.5 小時，8 點前就會停。

隔天合併：把家裡的 `library\simdata.db` 帶到公司（隨身碟或雲端硬碟），放成 `library\from-home.db`，再執行
`python tools/simlog.py merge library\from-home.db`。

## C. 家裡的 AI：開場白

在家裡用 Claude 開新對話，工作資料夾選 clone 下來的 PathOfBuilding，第一句貼這段：

> 你是這個專案的「執行 AI」，負責人 AI（阿福）在公司電腦。開工前先讀 tools/ROADMAP.zh-TW.md、
> tools/ACCEPTANCE.zh-TW.md、tools/TASKS.zh-TW.md，然後只做 TASKS 裡指派給「家裡」的任務。規則：
> 1. 用繁體中文跟我溝通；我是 PoE 老玩家，不是程式設計師，取捨要講清楚。
> 2. 改程式一律開新分支（home/任務名稱），不要直接改 feature/ai-tools；做完推上 GitHub，在 TASKS 寫交回說明。
> 3. 交回前跑測試（python -m unittest discover tools/tests）；改到生成器的話也跑驗收考試
>    （python tools/benchmark.py run --jobs N），把結果寫進交回說明。
> 4. library/ 和 src/Builds/ 不要提交（有帳號資料）；不要抓 poe.ninja 的 build 頁面，不要讀遊戲記憶體或封包。
> 5. 白天以外才跑大量計算；不要刪除資料庫檔案，要刪先問我。
> 6. commit 用 GitHub no-reply 信箱，最後一行加 Co-Authored-By: Claude。

## D. 分工規則

| | 公司（阿福，負責人） | 家裡（執行 AI） |
|---|---|---|
| 做什麼 | 決定方向、寫任務、驗收、合併 | 跑計算、做指派的單項任務 |
| 改程式 | `feature/ai-tools` 主分支 | 自己的 `home/...` 分支 |
| 交回 | — | 推分支，加上 TASKS 裡的交回說明（含考試結果） |
| 驗收 | 看 diff 和考試結果，及格才合併 | — |

兩邊不要同時改同一個檔案；任務寫明「會改哪些檔案」，阿福派任務時避開自己正在改的檔案。

## E. 階段
1. **第一階段**：家裡只跑計算（B 段）。
2. **第二階段**：穩定後，阿福在 TASKS 派第一個單項任務給家裡。
