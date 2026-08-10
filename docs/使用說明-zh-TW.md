# Spec Reference Kit 使用說明

## 1. 這個 repo 是做什麼的

`spec-reference-kit` 是一個把受控 specification 轉成「可追溯、可 review、可明確 promotion」參考資料的模板。

它不是：

- raw PDF/Word/Excel 的儲存庫；
- 直接把整份 spec 丟進 RAG 的系統；
- firmware runtime 行為資料庫；
- certification、customer acceptance 或 silicon correctness 的證明系統。

public repo 只放 synthetic demo data。真實 datasheet、產品資料、客戶資料與內部規格應放在 private internal repository，以及 Git 外部的 read-only Source Vault。

## 2. 核心資料流程

```text
Source Vault
    -> source registry + SHA-256
    -> extraction receipt
    -> AI/工程師 proposal
    -> schema / provenance validation
    -> 真人 domain review receipt
    -> explicit promotion
    -> canonical YAML
    -> generated Markdown / manifest
```

每一層的責任不同：

| 層級 | 放什麼 | 誰可以做 | 代表什麼 |
|---|---|---|---|
| Source Vault | 原始 PDF、Word、Excel 等 | 內部受控流程 | 原始來源，不進 public Git |
| `sources/` | source ID、revision、locator、SHA-256 | 工程流程 | 指向哪一份來源 |
| `evidence/extraction_receipts/` | section/page/table 與 extract hash | AI/工程師可產生 | 實際讀了來源哪一段 |
| `proposals/` | 結構化但尚未核准的 claim | AI/工程師 | 候選資料，不是 canonical truth |
| `evidence/review_packets/` | 真人 reviewer 的判定與 fingerprint | 有權限的 domain owner | 人工 review 證據 |
| `tables/` | approved canonical YAML | promotion 流程 | 唯一 canonical source |
| `exports/`、generated Markdown | canonical YAML 的投影 | generator | 查詢與閱讀用 view，不是 source of truth |

## 3. 如何開始使用

### 3.1 準備環境

需要 Python 3.9+ 與 requirements.txt 中的套件。安裝後，基本驗證不需要網路：

```bash
python -m pip install -r requirements.txt
python scripts/validate_repository.py --repo . --check-generated
python -m unittest discover -s tests -v
```

### 3.2 建立私有 pilot workspace

不要把真實來源直接放進這個 public template。建議建立 private reference repository，或在外部建立不會被 Git 追蹤的 pilot workspace，並保留：

- `sources/source_registry.yaml`
- `evidence/extraction_receipts/`
- `proposals/`
- `evidence/review_packets/`
- `contract/authority_levels.yaml`
- 對應的測試結果與 review index

原始文件則留在 read-only Source Vault。registry 只記錄來源的 identity、revision、locator 與 SHA-256。

### 3.3 登錄來源並建立 fingerprint

每一份來源要有穩定的 `source_id`，並記錄：

- 文件類型與產品範圍；
- revision / effective date；
- Source Vault 中的 artifact locator；
- 原始 artifact 的 SHA-256；
- authority level 與 review owner。

確認 registry 指向的原始檔案沒有被替換：

```bash
python scripts/probe_fingerprint.py \
  --registry sources/source_registry.yaml \
  --vault-root <read-only-source-vault>
```

### 3.4 建立 extraction receipt

每個 proposal 必須能回到一張 extraction receipt。receipt 至少要固定：

- source ID 與 artifact SHA-256；
- section、page、table 或其他可重現 locator；
- bounded extracted surface 的 hash；
- 使用的 extraction method 與時間。

不要只寫「來源在第 9 頁」而沒有 section/table；頁碼或版次變動時，reviewer 會無法重現。

### 3.5 產生 proposal

AI 或工程師只能先寫入 `proposals/`。一筆 proposal 應該是一個 bounded claim，並明確寫出：

- entry type；
- claim；
- product / revision scope；
- authority level；
- source locator 與 extraction receipt ID；
- verification scope 與 exclusions；
- `review.status: proposed`。

以目前 v0.1 為例，`register_bit` proposal 只應描述 register bit 的名稱、位置與 encoding，不應順便宣稱板級功能、firmware 支援或 runtime 行為。

### 3.6 執行 validation

`validate_proposal.py` 需要 proposal 所屬 workspace 同時具備 source registry、extraction receipt 與 `contract/authority_levels.yaml`：

```bash
python scripts/validate_proposal.py \
  --repo <private-pilot-repo> \
  --proposal <private-pilot-repo>/proposals/<entry>.yaml
```

完成一批 proposal 後，再執行：

```bash
python scripts/validate_repository.py --repo <private-pilot-repo> --check-generated
```

validation 會檢查 schema、authority、source binding、locator、receipt 與 proposal 的一致性；它不會替代 domain review。

### 3.7 真人 review 與 promotion

具備 source scope 權限的 domain owner 必須檢查：

1. proposal 是否忠實反映來源；
2. locator 與 extraction surface 是否能重現；
3. claim scope 與 exclusions 是否合理；
4. product/revision/authority 邊界是否正確。

reviewer 產生 review receipt 後，才可使用 promotion CLI：

```bash
python scripts/promote_entry.py \
  --repo <private-pilot-repo> \
  --proposal <private-pilot-repo>/proposals/<entry>.yaml \
  --review-receipt <private-pilot-repo>/evidence/review_packets/<receipt>.yaml \
  --table <private-pilot-repo>/tables/<canonical-table>.yaml
```

promotion 會重新比對 proposal、source、extraction receipt 與 review receipt 的 fingerprint。任何一項不一致都應 fail closed。

promotion 後才會更新 canonical YAML，再由 generator 產生 manifest 與 Markdown。generated Markdown 不能被當成另一份手工維護的 source of truth。

## 4. 這個 repo 的驗證層級

請分開看三種結果：

| 結果 | 能證明什麼 | 不能證明什麼 |
|---|---|---|
| Disconnected package smoke | bundle、submodule、offline dependency 與啟動流程可重現 | 真實 Source Vault 或產品資料存在 |
| Synthetic scale smoke | proposal、review、promotion、generation 流程可用 | 真實 extraction accuracy 或 domain approval |
| Real internal pilot | 真實 bounded source 經過 review 後可形成 approved reference | firmware runtime、certification、customer acceptance |

本次 PI4IOE5V6408 pilot 屬於 real-source 的 software-only pilot：24 筆 proposal、source/receipt/hash/locator validation 已完成，但沒有硬體操作，也沒有 human review receipt 或 promotion。

## 5. 所有 spec 都能用同一套 flow 嗎？

**可以共用治理骨架，但不能把所有 spec 都塞進同一個 entry type。**

可共用的部分是：

```text
受控來源 -> fingerprint -> bounded extraction -> proposal
-> validation -> 真人 review -> promotion -> canonical view
```

不能直接共用的部分是 claim schema、locator 規則、驗證方式與 evidence 類型。

| Spec 內容 | 是否適合目前 `register_bit` | 建議處理方式 |
|---|---|---|
| register map 的單一 bit | 適合 | 直接使用 `register_bit` |
| register field、多 bit encoding、enum | 不完全適合 | 新增 `register_field` 或 enum entry type |
| timing diagram、protocol sequence | 不適合 | 需要 timing/sequence schema 與邊界條件 fixture |
| state machine、transition rule | 不適合 | 需要 state/transition entry type，不能只存文字摘要 |
| 電氣規格、min/typ/max、absolute maximum | 不適合 | 需要 numeric limit、unit、condition、temperature/supply scope |
| pin mux、board schematic mapping | 不適合 | 需要 `pin_mapping`，並綁定 board revision 與裝配 scope |
| firmware API、command、error code | 不適合 | 需要 API/command contract 與 firmware version scope |
| 多份文件交叉推論 | 不直接適合 | 需要多來源 evidence、precedence 與 inference boundary |
| customer-specific requirement | 不應直接併入 base repo | 使用獨立 private overlay repository |
| certification、customer acceptance、runtime result | 不能由 static spec claim 代替 | 使用獨立的測試/認證 evidence contract |

因此，正確策略不是先做一個包辦所有格式的 schema，而是：

1. 先選一種低歧義、可 bounded 的 claim；
2. 用一種 entry type 完成真實 pilot；
3. 只有當 pilot 明確暴露 schema gap 時，才新增下一種 entry type；
4. 每新增一種 type，都要補 positive/negative fixtures、validator 與 promotion tests。

## 6. 使用時的判斷規則

- 一筆 proposal 只處理一個可 review 的 bounded claim。
- 原始來源留在 Source Vault，不把整份 spec 複製進 Git。
- AI/工程師可以提出 proposal，但不能自行把 proposal 變成 canonical。
- `approved` 只表示 claim 在宣告的來源與 scope 內通過 review。
- 不可從 static datasheet claim 推導 firmware correctness、硬體 runtime 或 certification。
- base product reference 與 customer overlay 分開管理。
- 先量測 false extraction rate、review time、reject/fingerprint mismatch 與 revision friction，再擴大 schema。

## 7. 目前這個 repo 的適用範圍

目前 v0.1 已實作並測試：

- source registry 與 fingerprint probe；
- extraction receipt；
- `register_bit` proposal / canonical schema；
- fail-closed promotion checks；
- deterministic Markdown 與 governed-surface manifest；
- positive/negative pipeline tests；
- pinned AI Governance Framework。

目前尚未實作：

- arbitrary PDF/table extraction；
- timing diagram、state machine、cross-document inference；
- customer overlay；
- cryptographically authenticated reviewer identity；
- 硬體 runtime 或 firmware integration test。

所以答案是：**所有 spec 可以沿用同一條受治理的生命週期，但只有符合目前 schema 與 evidence 邊界的 spec，才能直接使用目前這個 v0.1 implementation。**
