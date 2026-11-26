# 多台電腦一起跑自我對弈

> **目前排程（2026-11-26）見 `tools/HOME_PC.zh-TW.md` B 段**：第 2 台晚上 `--shard 1/5`、家裡 `--shard 2-5/5`、公司這台預設不跑。
> 下面是原本兩台的說明（準備步驟和合併方式不變）。

每台電腦跑不同的技能（「分份」），各自存在自己的資料庫，隔天再合併到主電腦。
電腦之間不需要連線，只要能複製檔案（隨身碟、網路芳鄰）。

- **主電腦**：E:\ai\path of exile\PathOfBuilding（資料最後都合併到這裡）
- **第 2 台**：跑第 2 份（`--shard 2/2`）；主電腦跑第 1 份（`--shard 1/2`）

技能用固定的方式分成兩份（同一個技能的所有昇華都在同一台），兩台不會重複。

---

## A. 第 2 台的第一次準備（只做一次）

1. **安裝 Python 3.12（64 位元）**：從 https://www.python.org/downloads/windows/ 下載
   「Windows installer (64-bit)」。安裝第一個畫面**勾選「Add python.exe to PATH」**再按 Install。
2. **安裝 Git**：從 https://git-scm.com/download/win 下載安裝，選項全部用預設。
3. 開 **PowerShell**，選一個磁碟（例如 D:），下載程式：

   ```powershell
   cd D:\
   git clone -b feature/ai-tools --depth 1 https://github.com/xingqiang1120/PathOfBuilding.git
   ```

4. **在主電腦**產生「已完成清單」（約 1 MB，只有清單沒有細節），讓第 2 台跳過主電腦做過的組合：

   ```powershell
   python tools/simlog.py seed library\seed-for-pc2.db
   ```

5. 把 `seed-for-pc2.db` 複製到第 2 台，放到 `D:\PathOfBuilding\library\`，**改名為 `simdata.db`**
   （library 資料夾不存在就自己建一個）。

## B. 每天晚上

**主電腦**（如果已經有一個沒分份的在跑，先 `python tools/selfplay.py --stop`，等幾分鐘
`--status` 顯示 FINISHED 再啟動）：

```powershell
cd "E:\ai\path of exile\PathOfBuilding"
python tools/selfplay.py --hours 14 --jobs 4 --shard 1/2
```

**第 2 台**（先更新程式，再啟動；`--jobs` 用「CPU 核心數減 2」，例如 8 核心用 6）：

```powershell
cd D:\PathOfBuilding
git pull
python tools/selfplay.py --hours 14 --jobs 6 --shard 2/2
```

看到「started in the background」就可以關視窗。1～2 分鐘後用 `python tools/selfplay.py --status`
確認是 RUNNING。

## C. 隔天合併資料到主電腦

1. 第 2 台跑完後（`--status` 顯示 FINISHED，或先 `--stop`），把 `D:\PathOfBuilding\library\simdata.db`
   複製到主電腦，例如放成 `E:\ai\path of exile\PathOfBuilding\library\from-pc2.db`。
2. 主電腦執行：

   ```powershell
   python tools/simlog.py merge library\from-pc2.db
   ```

   - 只會複製「跑完的」組合；已經有的會自動跳過，所以同一個檔案合併兩次也沒關係。
   - 第 2 台的 simdata.db **不要刪**，繼續用；下次合併只會加入新的部分。
3. 合併完 `from-pc2.db` 可以刪掉。

## 常見問題

- **第 3 台電腦？** 改成 `--shard 1/3`、`2/3`、`3/3`，每台各一份。改份數後已跑完的不受影響。
  家裡電腦的準備和指令見 `tools/HOME_PC.zh-TW.md`。
- **第 2 台程式要更新嗎？** 每晚啟動前 `git pull` 一次，兩台的計算規則才會一致。
- **資料會上傳到哪裡嗎？** 不會。只在你自己的電腦之間複製檔案。
