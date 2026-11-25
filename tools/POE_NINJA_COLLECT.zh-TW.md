# 從 poe.ninja 手動收集 build（批次匯入）

程式**不會**自動去 poe.ninja 抓資料（它的角色資料不開放給第三方程式）。
做法是你用瀏覽器挑角色、複製 PoB 分享碼，貼進一個文字檔，再一次匯入。
角色的帳號名稱只存在你的電腦（library/ 不會上傳到 GitHub）。

## 1. 收集

1. 在 poe.ninja 的 builds 頁面，用**物品（傳奇裝備）篩選**，例如 Doryani's Prototype。
2. 點進一個角色，按 **Path of Building** 的按鈕，複製它的分享碼（一長串英數字）。
   - 如果拿到的是網址（例如 pobb.in），打開網址，在頁面上複製分享碼本身。
3. 每件傳奇挑 3～5 個角色就夠了（不同昇華、不同技能更好）。

## 2. 貼進文字檔

用記事本建一個檔案，例如 `library\codes\2026-11-25.txt`，格式：

```
# 這行是註解，會被略過
[Doryani's Prototype]
Arc Inquisitor eNrtfWtz2zi...（分享碼）
eNrtvXtz2zia...（只貼分享碼也可以）

[Cospri's Malice]
eNrt...
```

- `[方括號]` 一行代表一組，底下的分享碼都會標上這個標籤（通常寫傳奇裝備名稱）。
- 分享碼前面可以寫名稱（空格隔開），不寫也可以。
- 空行、`#` 開頭的行會略過；網址、太短或複製不完整的分享碼會列出行號，不影響其他行。

## 3. 匯入

在 PathOfBuilding 資料夾執行：

```powershell
python tools/library.py batch library\codes\2026-11-25.txt
```

匯入後每個 build 會用 PoB 計算並建立索引，之後可以查：

```powershell
python tools/library.py search --tag "doryani's prototype"
```

## 建議先收集的傳奇（玩法型，可自行增減）

Doryani's Prototype、Cospri's Malice、Cospri's Will、Shavronne's Wrappings、Indigon、Original Sin、
Ryslatha's Coil、Melding of the Flesh、Aul's Uprising、The Saviour、Hand of Wisdom and Action、
Bino's Kitchen Knife、Death's Oath、Kaom's Heart、The Brass Dome、Progenesis、The Squire、
Ashes of the Stars、Mageblood

你知道、玩過、覺得「一定要圍繞它來玩」的傳奇，請優先加進來。
