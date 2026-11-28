# 第 2 台與家裡電腦：準備和執行 AI

三台電腦共用進度和資料的方式（2026-11-26 使用者同意）：
1. **進度**：`tools/HANDOFF.zh-TW.md`（交接文件）＋`tools/TASKS.zh-TW.md`（任務板），在公開庫，`git pull` 就拿到。
2. **私人資料**：私人庫 `xingqiang1120/pob-lab-data`（真人 build 庫、考試結果），用 `python tools/labdata.py`。
3. **指揮**：每台開一個 Claude 對話並打開 Remote Control，公司的阿福用訊息派工作，跑完回報。

電腦代號：公司主電腦 `office`、公司第 2 台 `pc2`、家裡 `home`。

---

## A. 第一次準備（每台做一次）

1. 安裝 **Python 3.12（64 位元）**：https://www.python.org/downloads/windows/ 的「Windows installer (64-bit)」，
   第一個畫面**勾選「Add python.exe to PATH」**。
2. 安裝 **Git**：https://git-scm.com/download/win ，選項全部預設。
3. 安裝 **GitHub CLI**：https://cli.github.com/ 下載 Windows 版安裝。
4. 開 PowerShell 登入 GitHub（照畫面選 GitHub.com → HTTPS → 用瀏覽器登入，帳號是擁有私人庫的那個）：
   ```powershell
   gh auth login
   ```
   ```powershell
   gh auth setup-git
   ```
5. 下載程式（已經有的電腦，例如第 2 台的 `D:\PathOfBuilding`，改成進去執行 `git pull` 就好）。
   執行 AI 要看歷史，所以不要加 `--depth 1`：
   ```powershell
   cd D:\
   ```
   ```powershell
   git clone -b feature/ai-tools https://github.com/xingqiang1120/PathOfBuilding.git
   ```
6. 拿私人資料（會在 `D:\pob-lab-data` 建私人庫，並把考試要用的 build 庫放進 `library\`）：
   ```powershell
   cd D:\PathOfBuilding
   ```
   ```powershell
   python tools/labdata.py pull
   ```
7. 設定 commit 身分（GitHub 不公開信箱）：
   ```powershell
   git config user.name xingqiang1120
   ```
   ```powershell
   git config user.email 270159263+xingqiang1120@users.noreply.github.com
   ```

## B. 執行 AI：開對話

1. 開 Claude 桌面版 → Code，新對話的工作資料夾選 `D:\PathOfBuilding`。
2. 對話名稱改成「PoB 執行 pc2」或「PoB 執行 home」，阿福才找得到你。
3. 打開這個對話的 **Remote Control**。
4. 第一句貼下面的開場白，把 `<代號>` 換成 `pc2` 或 `home`：

> 你是這個專案的「執行 AI」，電腦代號 <代號>。負責人 AI「阿福」在公司電腦的對話「Path of Building 優化分析」。
> 開工前先 `git pull`，讀 tools/HANDOFF.zh-TW.md（進度）、tools/TASKS.zh-TW.md（任務）、tools/HOME_PC.zh-TW.md（本說明）。
> 規則：
> 1. 用繁體中文跟我溝通；我是 PoE 老玩家，不是程式設計師，取捨要講清楚。
> 2. 阿福傳來的訊息，只要是本專案範圍內的工作（拉程式、跑考試或計算、推結果到私人庫、在 home/ 或 pc2/ 分支改程式），
>    我同意你直接做，做完回報給阿福。超出範圍的、刪除檔案、推到 feature/ai-tools、改系統設定的，先問我。
> 3. 跑完計算一定用 `python tools/labdata.py push --pc <代號>` 把結果推到私人庫，再傳訊息告訴阿福。
> 4. 改程式一律開新分支（<代號>/任務名稱），不要直接改 feature/ai-tools；交回前跑測試（python -m unittest discover tools/tests）。
> 5. library/ 和 src/Builds/ 不要提交到公開庫（有帳號資料）；不要抓 poe.ninja 的 build 頁面，不要讀遊戲記憶體或封包。
> 6. 不要刪除資料庫檔案；要刪先問我。
> 7. commit 用 GitHub no-reply 信箱，最後一行加 Co-Authored-By: <你實際的模型名稱> <noreply@anthropic.com>。

## C. 跑考試（階段一的日常工作）

阿福派「跑第 N 版的考試」時（或使用者說「跑今天的考試」）：

```powershell
git pull
```
```powershell
python tools/labdata.py pull
```
```powershell
python tools/benchmark.py run --jobs <核心數減 2>
```
```powershell
python tools/gap.py --benchmark
```
```powershell
python tools/labdata.py push --pc <代號>
```

- 核心數：工作管理員 → 效能 → CPU →「邏輯處理器」。home 實測用 `--jobs 12`（每組約 1.1～1.4 GB 記憶體）。
- **給使用者看的 build**：放在這台 PoB 的 `src\Builds\AI 試算 v<版號>\`（每版一個資料夾，附報告 .md 和 README），
  開 `Path of Building.exe` 的 Builds 清單就看得到。`src/Builds` 被 git 忽略，不提交；要給別台的話，同一份放私人庫
  `results/v<版號>/<代號>/builds/`。
- 推私人庫的 commit 要簽你自己的模型名稱：`python tools/labdata.py --model "Claude Fable 5.1" push --pc home`，
  或先設環境變數 `POB_MODEL`（沒給就簽 Claude Opus 5.5，那是 office 的）。
- `labdata.py pull` 會順便把別台的舊版結果放進 `library\benchmark\`，退步比較才有上一版可比。
- 跑的時候不要讓電腦睡眠。第一次跑請回報記憶體用量（工作管理員），之後好決定 `--jobs`。
- `python tools/labdata.py status` 看各台已經交了哪些版本，同一版不用重跑。

## D. 自我對弈（階段二才用，目前暫停）

| 電腦 | 時段 | 指令（啟動前先 `git pull`） |
|---|---|---|
| pc2（14 核心） | 晚上 | `python tools/selfplay.py --hours 5 --jobs 8 --shard 1/5` |
| home | 00:00～20:00 | `python tools/selfplay.py --hours 19.5 --jobs <核心數減 2> --shard 2-5/5` |
| office | 只有使用者說可以時 | 先合併兩台資料，再 `python tools/selfplay.py --hours N --jobs 4` |

`--hours` 是「多久後不再開新的」，正在跑的會跑完（最多 40 分鐘）。
自我對弈的資料庫（simdata.db，可到數 GB）太大不放 GitHub，用隨身碟或雲端硬碟帶到 office，再
`python tools/simlog.py merge library\from-home.db`。

## E. 分工

| | 阿福（office，負責人） | 執行 AI（pc2、home） |
|---|---|---|
| 做什麼 | 決定方向、改生成器、寫任務、驗收、合併 | 跑考試與計算、做指派的單項任務 |
| 改程式 | `feature/ai-tools` | 自己的 `<代號>/...` 分支 |
| 交回 | — | 結果推私人庫；程式推分支；傳訊息給阿福，並在 TASKS 寫交回 |
| 驗收 | 看 diff 和考試結果，及格才合併 | — |

兩邊不要同時改同一個檔案；任務寫明會改哪些檔案。
