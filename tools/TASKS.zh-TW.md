# 任務板（公司負責人 AI ⇄ 家裡執行 AI）

說明見 `tools/HOME_PC.zh-TW.md`。每個任務寫：給誰、要改哪些檔案、完成標準；做完的人在「交回」寫結果。
狀態：待做 → 進行中 → 已交回 → 已驗收（或退回，附原因）。

---

## T1 家裡電腦跑第 3 份自我對弈
- 給：家裡
- 狀態：待做
- 內容：照 HOME_PC B 段，晚上跑 `--shard 3/3`。跑完把 `library\simdata.db` 帶到公司合併。
- 改檔案：無（只跑計算）
- 完成標準：`python tools/selfplay.py --status` 顯示 FINISHED，資料庫交給使用者帶到公司。
- 交回：
