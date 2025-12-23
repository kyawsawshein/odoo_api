Here’s a detailed list of **Inventory Configuration settings** you’ll find in **Odoo 19** under the *Inventory* (Warehouse Management) module — covering **Warehouse, Location, Product Category, Costing, Valuation, Lots/Serials, Expiry, UoM, and Accounting**.

---

### 🏢 **1. Warehouse Configuration**

**Path:** *Inventory → Configuration → Warehouses*

* **Warehouse Name:** e.g., Main Warehouse
* **Short Name / Code:** Used in stock moves (e.g., WH)
* **Company:** Select company
* **Address:** Warehouse address
* **Routes:** Automatic routes such as Buy, Manufacture, Replenish on Order (MTO)
* **Outgoing/Incoming Shipment:** One-step, two-step, or three-step routes
* **Storage Locations:** Enable if multiple internal locations are used
* **Resupply from other Warehouse:** Used for multi-warehouse replenishment

---

### 📦 **2. Location Configuration**

**Path:** *Inventory → Configuration → Locations*

* **Location Name:** e.g., Stock, Shelf 01
* **Parent Location:** e.g., WH/Stock
* **Location Type:**

  * *Vendor Location (Supplier)*
  * *Customer Location*
  * *Internal Location*
  * *Inventory Loss*
  * *Production*
* **Is a Scrap Location:** Yes/No
* **Is a Return Location:** Yes/No
* **Removal Strategy:** FIFO / LIFO / FEFO (useful for lots & expiry)

---

### 🏷️ **3. Product Category Configuration**

**Path:** *Inventory → Configuration → Product Categories*

* **Category Name:** e.g., Raw Materials, Finished Goods
* **Parent Category:** Hierarchy setup
* **Costing Method:**

  * *Standard Price (Manual)*
  * *Average Cost (AVCO)*
  * *First In First Out (FIFO)*
* **Inventory Valuation:**

  * *Manual* (non-integrated)
  * *Automated* (linked with accounting journal)
* **Stock Input/Output Accounts:** For automated valuation
* **Price Difference Account:** Optional

---

### 💰 **4. Costing Method & Valuation**

Usually configured per **Product Category** or **Product Template**.

* **Costing Method Options:**

  * **Standard Price** → Fixed cost manually defined
  * **Average Cost (AVCO)** → Weighted average based on purchases
  * **FIFO** → First In First Out valuation

* **Inventory Valuation:**

  * **Manual:** No automatic journal entries
  * **Automated:** Creates accounting entries on stock moves (requires Accounting app)

---

### 🔢 **5. Product Lot & Expiry Tracking**

**Path:** *Inventory → Configuration → Settings*

* Enable the following:

  * ✅ *Lots & Serial Numbers*
  * ✅ *Expiration Dates*

**Then in each Product:**

* **Tracking:**

  * *No Tracking*
  * *By Lots*
  * *By Unique Serial Number*
* **Expiration Settings:**

  * *Expiration Time (days)*
  * *Best Before Time*
  * *Removal Time (FEFO)*
  * *Alert Time*

---

### 📏 **6. Unit of Measure (UoM) Configuration**

**Path:** *Inventory → Configuration → Units of Measure*

**UoM Categories Examples:**

* *Unit* → Used for discrete items
* *Length / Distance* → Used for meters, centimeters, etc.
* *Weight* → Used for kilograms, grams
* *Volume* → Used for liters, cubic meters

**Example Units for Meter and Unit:**

| UoM Name   | Category | Type      | Ratio | Rounding Precision |
| ---------- | -------- | --------- | ----- | ------------------ |
| Unit       | Unit     | Reference | 1     | 1                  |
| Meter      | Length   | Reference | 1     | 0.01               |
| Centimeter | Length   | Smaller   | 0.01  | 0.01               |
| Kilometer  | Length   | Bigger    | 1000  | 0.01               |

---

### 📚 **7. Accounting Configuration (Linked to Inventory)**

**Path:** *Accounting → Configuration → Chart of Accounts / Journals*

When **Automated Valuation** is enabled:

* **Stock Valuation Account:** Asset account (e.g., Inventory)
* **Stock Input Account:** Used when receiving goods (credit)
* **Stock Output Account:** Used when delivering goods (debit)
* **Price Difference Account:** Captures PO price vs actual cost difference
* **Stock Journal:** Journal used for inventory valuation entries

---

### ✅ **Example Flow**

**Product → Product Category → Warehouse → Accounting**

| Level      | Config Item             | Example                    |
| ---------- | ----------------------- | -------------------------- |
| Warehouse  | WH/Stock                | Main Warehouse             |
| Location   | WH/Stock/Shelf01        | Internal                   |
| Category   | Finished Goods          | FIFO + Automated Valuation |
| Product    | Router                  | Track by Serial            |
| UoM        | Unit                    | Each                       |
| Accounting | Stock Valuation Account | 110000 Inventory Assets    |

---

Would you like me to generate a **visual flowchart** of how these configurations link together (Warehouse → Location → Product Category → Costing → Accounting)?
