# 交接文件：目前進度（給三台電腦的 AI）

> 負責人 AI「阿福」在公司電腦，每次有進展就更新這份。其他電腦的 AI 開工前先 `git pull` 再讀這份，
> 然後讀 `tools/TASKS.zh-TW.md`（派給你的任務）。細節：路線圖 `tools/ROADMAP.zh-TW.md`、驗收標準 `tools/ACCEPTANCE.zh-TW.md`。

最後更新：2026-11-27（阿福）

## 專案是什麼
使用者（PoE 老玩家，雷射板金公司負責人，不是程式設計師，稱 AI 為「阿福」）的 Path of Building 分支。
目標：輸入技能＋昇華，自動產生正確又有創意的 build（`tools/generate.py`），用 PoB 本身計算；
之後從大量自我對弈（`tools/selfplay.py`）學權重。驗證三種：保留資料、真人 build、實際遊玩。

## 三台電腦
| 代號 | 電腦 | 角色 |
|---|---|---|
| office | 公司主電腦（阿福在這） | 決定方向、改生成器、驗收。**晚上記憶體被其他工作占用，不跑計算。** |
| pc2 | 公司第 2 台（14 核心） | 晚上跑計算，有執行 AI |
| home | 家裡（最強，00:00～20:00 有空） | 主要計算，有執行 AI |

溝通管道：
1. 程式與文件：公開庫 `xingqiang1120/PathOfBuilding`，分支 `feature/ai-tools`。
2. 私人資料（真人 build 庫、考試結果）：私人庫 `xingqiang1120/pob-lab-data`，用 `python tools/labdata.py pull|push|status`。
3. 即時指揮：各台對話開 Remote Control，阿福用訊息派工作。訊息只限本專案範圍。

## 分工（2026-11-27 使用者定）
- **home：生成器計算優化負責人**（TASKS T3）。自己挑問題、改生成器、跑考試、交回分支。不改考卷和及格標準，不開保留考卷。
- **office（阿福＋使用者）：驗證和把關**。保留考卷（T4，pc2 跑）、實戰驗證（T5，使用者玩）、驗收合併。office 不改 `tools/generate.py`，
  避免跟 home 衝突；實戰找到的問題寫成任務派給 home。
- **pc2**：跑保留考試（獨立的第二份考卷），之後階段二跑自我對弈。

## 目前階段：一（先把計算改準）
- 生成器第 15 版。自我對弈**暫停**：規則還在改，跑了下一版就作廢。
- 算力用來跑驗收考試（`tools/benchmark.py`）和差距報告（`tools/gap.py`），阿福看報告決定下一版改什麼。
- 進入階段二（凍結版本、連跑幾晚自我對弈）的門檻：作者組 ≥ 5/7、底線 10/10、連續兩版沒有退步。
- 版本規則：生成器的修改累積起來一天發一版（升 GENERATOR_VERSION），不在別台跑到一半時改版。

## 考試成績
| 版本 | 作者組 | 底線 | 備註 |
|---|---|---|---|
| 11 | 2/7 | 8/10 | |
| 12 | 2/7 | 9/10 | Smite／Gladiator 11%（沒選輔助寶石）；Glacial Hammer 退步 0.68 |
| 13 | 3/7 | 8/10 | home 跑。Smite／Gladiator 96% 及格；Glacial Hammer 分數回來但混沌抗 -8 不過底線（算問題，第 14 版修）；沒有退步 10/10 |
| 14 | 3/7 | 8/10 | home。輔助池每接一顆重抓、最後互換重複：Storm Call／Hierophant 60%→85%（防禦還差 0.37）；Smite／Gladiator 96%→84%（貪婪路徑雜訊，仍及格）；沒有退步 |
| 15 | 2/7 | 8/10 | home。淨回復、開放 RF／Pact／Blood and Sand：Hierophant 112%、Assassin 84%、Reave 76% DPS；Smite／Gladiator 防禦差 0.01 掉出及格（路徑雜訊，阿福接受）；樣板零退步 |

## 已知的下一批問題（依優先，第 13 版差距報告）
1. 輔助性技能：作者有的 Righteous Fire 類、Vaal 技能（Vaal Arctic Armour 防禦 +1.17）、Pact of Beidat，生成器都沒選。
2. Storm Call／Hierophant 少 Overloaded Intensity（+88%）；Storm Call／Assassin 少 Power Charge On Critical、Less Duration。
3. 混沌抗：Glacial Hammer 為了分數放掉混沌抗（-8）。底線不過就算不及格，不能拿分數抵。
4. KB Necro 防禦不到作者；Cyclone 生命不到 4,000。
5. 珠寶：星團、永恆珠寶都被丟掉（差距報告標 not applicable 的節點）。

## 決定（2026-11-27 阿福）
- Vaal 技能：PoB 當作永遠開著，生成器**不選**，等「實用模式」（有持續時間折算）再開放。考試裡作者 build 的 Vaal 技能也照算，
  所以作者被高估（例如 Smite／Slayer 的 Vaal Smite）。考卷已改成替作者評分時關掉 Vaal 效果（見下）。
- 輔助性技能（RF、Pact of Beidat、Blood and Sand）可以開放，但評分要先算淨回復（扣掉 RF 自燃），home 第 15 版處理。
- 回復權重造成的路徑雜訊（Smite／Gladiator v13 96% → v14 84% → v15 89%）先接受；搜尋穩定性（多起點取最佳）排在混沌抗之後。
- 考卷改動（office，2026-11-27）：替作者評分時關掉作者 Vaal 寶石的 Vaal 效果（Worker 新的 `vaal_off`，等於 PoB 的「Enable Vaal ...」勾選框；
  寶石的另一個技能保留，例如 Vaal Summon Skeletons of Mages 照樣召喚）。第 15 版作者組要用新考卷重算才算數。
- 更正：Storm Call／Hierophant 的作者本來就把 Vaal Arctic Armour 和 Vaal Molten Shell 的 Vaal 效果關掉了（enableGlobal1=false），
  所以它的防禦差距**不是** Vaal 造成的，要從別的地方找（差距報告裡的 +1.17 是把 Vaal 全開的寶石加進生成的 build 量出來的）。

## 各台規格（實測）
- home：16 邏輯核心、31 GB。每組 generate 約 1.1～1.4 GB，用 `--jobs 12`。整套考試約 10 分鐘。

## 使用者定下的規則（每台都要遵守）
- 繁體中文；取捨講清楚，不要只丟術語。
- `library/`、`src/Builds/` 不提交到公開庫（有帳號資料）；真人 build 只放私人庫。
- 不抓 poe.ninja 的 build 頁面；不讀遊戲記憶體或封包。
- 不刪資料庫檔案，要刪先問使用者。不關使用者的程式，先問。
- commit 用 GitHub no-reply 信箱，最後一行 `Co-Authored-By: <你實際的模型名稱> <noreply@anthropic.com>`（照實寫，例如 home 是 Claude Fable 5.1）。
- 遊玩驗證過的設定，使用者確認後才存。
