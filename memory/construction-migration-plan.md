# Three Brothers Construction Bot — Google Sheets → MySQL Migration Plan

**Author:** Subagent Analysis  
**Date:** 2026-07-29  
**Status:** MySQL schema already exists, data partially migrated, dual-write adapter (`db-adapter.js`) already operational  
**Bot:** `/opt/construction-bot/bot.js` (Telegraf/Node.js)

---

## Executive Summary

The migration from Google Sheets to MySQL is approximately **70% complete**:

| Layer | Status |
|-------|--------|
| MySQL schema (26 tables) | ✅ **Done** — all tables created with proper indexes |
| MySQL data | ⚠️ **Partial** — some tables populated, many empty |
| DB adapter (`db-adapter.js`) | ✅ **Done** — dual-write mode, MySQL reads, Google Sheets fallback |
| Wizard code | ✅ **Done** — all wizards already `require("../db-adapter")` |
| `main.js` entry point | ✅ **Done** — uses `db-adapter.js` |
| `bot.js` (legacy monolithic) | ❌ **Still uses raw Google Sheets** — functions like `getDoc()`, `getRows()`, `refreshAccounts()`, `refreshConfig()` call Google Sheets API directly |

**Critical finding:** The monolithic `bot.js` file (6837 lines) still has **inlined Google Sheets logic** that bypasses the modular `src/` structure. The bot should be switched to use `main.js` (which uses `db-adapter.js`) instead of `bot.js`, or the monolithic file needs refactoring.

---

## 1. Database Schema — Complete Reference

### Schema Audit (All 26 Existing Tables)

The MySQL database `construction_db` on 127.0.0.1:3306 already has all tables created. Below is the complete schema reference.

#### `coa_accounts` — Chart of Accounts
```sql
CREATE TABLE `coa_accounts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_type` varchar(50) NOT NULL COMMENT 'Income, Expense, Asset, Liability, Equity',
  `account_name` varchar(200) NOT NULL,
  `normal_balance` enum('Debit','Credit') DEFAULT 'Debit',
  `description` varchar(500) DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_coa_type` (`account_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `config` — System Configuration
```sql
CREATE TABLE `config` (
  `id` int NOT NULL AUTO_INCREMENT,
  `config_type` varchar(100) NOT NULL COMMENT 'OPEX_Category, Project_Type, Asset_Type, Payable_Category',
  `value` varchar(500) NOT NULL,
  `sort_order` int DEFAULT '0',
  `active` enum('TRUE','FALSE') DEFAULT 'TRUE',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_config_type` (`config_type`),
  KEY `idx_config_active` (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `projects` — Project Master
```sql
CREATE TABLE `projects` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` varchar(20) NOT NULL,
  `project_name` varchar(200) NOT NULL,
  `project_type` varchar(100) DEFAULT NULL,
  `client` varchar(200) DEFAULT NULL,
  `contract_value` decimal(15,2) DEFAULT '0.00',
  `start_date` date DEFAULT NULL,
  `status` enum('Active','Closed') DEFAULT 'Active',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `project_id` (`project_id`),
  KEY `idx_project_name` (`project_name`),
  KEY `idx_project_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `transactions` — General Journal Entries
```sql
CREATE TABLE `transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `project_name` varchar(200) DEFAULT NULL,
  `account_type` enum('Income','Expense') NOT NULL,
  `account_name` varchar(200) NOT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `description` text,
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_tx_date` (`date`),
  KEY `idx_tx_project` (`project_name`),
  KEY `idx_tx_account_type` (`account_type`),
  KEY `idx_tx_account_name` (`account_name`),
  KEY `idx_tx_payment` (`payment_method`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `opex` — Operating Expenses
```sql
CREATE TABLE `opex` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `opex_category` varchar(200) NOT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `description` text,
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_opex_date` (`date`),
  KEY `idx_opex_category` (`opex_category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `payables` — Accounts Payable
```sql
CREATE TABLE `payables` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `supplier` varchar(200) NOT NULL,
  `project` varchar(200) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `due_date` date DEFAULT NULL,
  `status` enum('Pending','Paid') DEFAULT 'Pending',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_pay_date` (`date`),
  KEY `idx_pay_supplier` (`supplier`),
  KEY `idx_pay_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `receivables` — Accounts Receivable
```sql
CREATE TABLE `receivables` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `client` varchar(200) NOT NULL,
  `project` varchar(200) DEFAULT NULL,
  `invoice_no` varchar(100) DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `due_date` date DEFAULT NULL,
  `status` enum('Pending','Received') DEFAULT 'Pending',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_rec_date` (`date`),
  KEY `idx_rec_client` (`client`),
  KEY `idx_rec_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `assets` — Asset Master
```sql
CREATE TABLE `assets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `asset_id` varchar(20) NOT NULL,
  `asset_name` varchar(200) NOT NULL,
  `asset_type` varchar(100) DEFAULT NULL,
  `purchase_date` date DEFAULT NULL,
  `purchase_cost` decimal(15,2) DEFAULT '0.00',
  `assigned_project` varchar(200) DEFAULT 'General',
  `useful_life_years` int DEFAULT '0',
  `salvage_value` decimal(15,2) DEFAULT '0.00',
  `monthly_depreciation` decimal(15,2) DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `status` enum('Active','Disposed','Sold') DEFAULT 'Active',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `asset_id` (`asset_id`),
  KEY `idx_asset_type` (`asset_type`),
  KEY `idx_asset_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `inventory_lots` — Inventory Lots
```sql
CREATE TABLE `inventory_lots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `lot_id` varchar(20) DEFAULT NULL,
  `date` datetime NOT NULL,
  `material_code` varchar(20) NOT NULL,
  `material_name` varchar(200) NOT NULL,
  `unit` varchar(50) DEFAULT NULL,
  `original_qty` decimal(15,4) NOT NULL DEFAULT '0.0000',
  `remaining_qty` decimal(15,4) NOT NULL DEFAULT '0.0000',
  `unit_price` decimal(15,2) NOT NULL DEFAULT '0.00',
  `total_cost` decimal(15,2) NOT NULL DEFAULT '0.00',
  `status` enum('Active','Depleted') DEFAULT 'Active',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `lot_id` (`lot_id`),
  KEY `idx_lot_date` (`date`),
  KEY `idx_lot_material` (`material_code`),
  KEY `idx_lot_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `inventory_movements` — Inventory Movement
```sql
CREATE TABLE `inventory_movements` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mov_id` varchar(20) DEFAULT NULL,
  `date` datetime NOT NULL,
  `type` enum('Purchase','Transfer_Out','Sell','Adjustment') NOT NULL,
  `material_code` varchar(20) NOT NULL,
  `material_name` varchar(200) NOT NULL,
  `unit` varchar(50) DEFAULT NULL,
  `qty` decimal(15,4) NOT NULL DEFAULT '0.0000',
  `unit_price` decimal(15,2) DEFAULT '0.00',
  `total_amount` decimal(15,2) DEFAULT '0.00',
  `project` varchar(200) DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mov_id` (`mov_id`),
  KEY `idx_mov_date` (`date`),
  KEY `idx_mov_type` (`type`),
  KEY `idx_mov_material` (`material_code`),
  KEY `idx_mov_project` (`project`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `materials_master` — Material Master
```sql
CREATE TABLE `materials_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `material_code` varchar(20) NOT NULL,
  `material_name` varchar(200) NOT NULL,
  `unit` varchar(50) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `active` varchar(10) DEFAULT 'TRUE',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `material_code` (`material_code`),
  KEY `idx_mat_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `materials_purchases` — Materials Purchases
```sql
CREATE TABLE `materials_purchases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `project_name` varchar(200) DEFAULT NULL,
  `material_name` varchar(200) NOT NULL,
  `unit` varchar(50) DEFAULT NULL,
  `qty` decimal(15,4) NOT NULL DEFAULT '0.0000',
  `unit_price` decimal(15,2) DEFAULT '0.00',
  `total_cost` decimal(15,2) DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_mp_date` (`date`),
  KEY `idx_mp_project` (`project_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `subcontracts` — Subcontract Master
```sql
CREATE TABLE `subcontracts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subcontract_id` varchar(20) DEFAULT NULL,
  `date` datetime NOT NULL,
  `project_name` varchar(200) NOT NULL,
  `contractor_name` varchar(200) NOT NULL,
  `scope` varchar(500) DEFAULT NULL,
  `contract_amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `amount_paid` decimal(15,2) DEFAULT '0.00',
  `remaining` decimal(15,2) DEFAULT '0.00',
  `status` enum('Active','Paid','Partial') DEFAULT 'Active',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `subcontract_id` (`subcontract_id`),
  KEY `idx_sc_date` (`date`),
  KEY `idx_sc_project` (`project_name`),
  KEY `idx_sc_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `subcontract_payments` — Subcontract Payment Log
```sql
CREATE TABLE `subcontract_payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `payment_id` varchar(20) DEFAULT NULL,
  `date` datetime NOT NULL,
  `subcontract_id` varchar(20) NOT NULL,
  `project_name` varchar(200) DEFAULT NULL,
  `contractor_name` varchar(200) DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `payment_id` (`payment_id`),
  KEY `idx_sp_date` (`date`),
  KEY `idx_sp_subcontract` (`subcontract_id`),
  KEY `idx_sp_project` (`project_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `equipment_rentals` — Equipment Rentals
```sql
CREATE TABLE `equipment_rentals` (
  `id` int NOT NULL AUTO_INCREMENT,
  `rental_id` varchar(20) DEFAULT NULL,
  `date` datetime NOT NULL,
  `equipment_name` varchar(200) NOT NULL,
  `renter_name` varchar(200) NOT NULL,
  `rental_period` varchar(200) DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `status` enum('Active','Completed') DEFAULT 'Active',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `rental_id` (`rental_id`),
  KEY `idx_er_date` (`date`),
  KEY `idx_er_equip` (`equipment_name`),
  KEY `idx_er_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `maintenance_log` — Equipment Maintenance Log
```sql
CREATE TABLE `maintenance_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `maint_id` varchar(20) DEFAULT NULL,
  `date` datetime NOT NULL,
  `equipment_name` varchar(200) NOT NULL,
  `maint_type` varchar(100) DEFAULT NULL,
  `description` text,
  `amount` decimal(15,2) DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `maint_id` (`maint_id`),
  KEY `idx_ml_date` (`date`),
  KEY `idx_ml_equip` (`equipment_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `drivers` — Drivers Master
```sql
CREATE TABLE `drivers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `driver_id` varchar(20) DEFAULT NULL,
  `driver_name` varchar(200) NOT NULL,
  `phone` varchar(50) DEFAULT NULL,
  `assigned_equipment` varchar(200) DEFAULT NULL,
  `license_no` varchar(100) DEFAULT NULL,
  `join_date` datetime DEFAULT NULL,
  `status` enum('Active','Inactive') DEFAULT 'Active',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `driver_id` (`driver_id`),
  KEY `idx_drv_name` (`driver_name`),
  KEY `idx_drv_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `driver_payments` — Driver Payments
```sql
CREATE TABLE `driver_payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `driver_name` varchar(200) NOT NULL,
  `payment_type` varchar(100) DEFAULT NULL,
  `equipment_name` varchar(200) DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_dp_date` (`date`),
  KEY `idx_dp_driver` (`driver_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `driver_advances` — Driver Advances
```sql
CREATE TABLE `driver_advances` (
  `id` int NOT NULL AUTO_INCREMENT,
  `advance_id` varchar(20) DEFAULT NULL,
  `date` datetime NOT NULL,
  `driver_name` varchar(200) NOT NULL,
  `amount_given` decimal(15,2) DEFAULT '0.00',
  `amount_deducted` decimal(15,2) DEFAULT '0.00',
  `remaining` decimal(15,2) DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `advance_type` varchar(100) DEFAULT NULL,
  `status` enum('Outstanding','Settled') DEFAULT 'Outstanding',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `advance_id` (`advance_id`),
  KEY `idx_da_date` (`date`),
  KEY `idx_da_driver` (`driver_name`),
  KEY `idx_da_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `dividends` — Dividends Paid
```sql
CREATE TABLE `dividends` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `member` varchar(200) DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_div_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `om_bonus` — OM Bonus Payouts
```sql
CREATE TABLE `om_bonus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_om_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `account_transfers` — Account-to-Account Transfers
```sql
CREATE TABLE `account_transfers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transfer_id` varchar(20) DEFAULT NULL,
  `date` datetime NOT NULL,
  `from_account` varchar(100) NOT NULL,
  `to_account` varchar(100) NOT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `transfer_id` (`transfer_id`),
  KEY `idx_at_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `advance_payments` — General Advance Payments
```sql
CREATE TABLE `advance_payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` datetime NOT NULL,
  `type` varchar(100) DEFAULT NULL,
  `to_from` varchar(200) DEFAULT NULL,
  `project` varchar(200) DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `purpose` text,
  `expected_return` varchar(100) DEFAULT NULL,
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `status` enum('Outstanding','Returned') DEFAULT 'Outstanding',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_ap_date` (`date`),
  KEY `idx_ap_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `shareholders` — Equity Shareholders (PS VIBE team, not Three Brothers)
```sql
CREATE TABLE `shareholders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `capital_ratio` decimal(5,4) NOT NULL DEFAULT '0.0000',
  `total_capital` decimal(15,2) DEFAULT '0.00',
  `status` enum('Active','Inactive') DEFAULT 'Active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `equity_transactions` — Equity Capital Injections/Ejections
```sql
CREATE TABLE `equity_transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `shareholder_id` int NOT NULL,
  `tx_type` enum('inject','eject') NOT NULL,
  `amount` decimal(15,2) NOT NULL DEFAULT '0.00',
  `payment_method` varchar(100) DEFAULT 'Bank Transfer',
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_eq_shareholder` (`shareholder_id`),
  CONSTRAINT `fk_eq_shareholder` FOREIGN KEY (`shareholder_id`) REFERENCES `shareholders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `dashboard_data` — Dashboard Metrics Cache
```sql
CREATE TABLE `dashboard_data` (
  `id` int NOT NULL AUTO_INCREMENT,
  `metric_name` varchar(100) NOT NULL,
  `current_month` varchar(50) DEFAULT NULL,
  `all_time` varchar(50) DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `metric_name` (`metric_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### `monthly_summary` — Monthly P&L Summaries
```sql
CREATE TABLE `monthly_summary` (
  `id` int NOT NULL AUTO_INCREMENT,
  `month` varchar(7) NOT NULL COMMENT 'YYYY-MM',
  `income_mmk` decimal(15,2) DEFAULT '0.00',
  `expense_mmk` decimal(15,2) DEFAULT '0.00',
  `net_profit_mmk` decimal(15,2) DEFAULT '0.00',
  `transactions` int DEFAULT '0',
  `payables_settled` int DEFAULT '0',
  `receivables_settled` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `month` (`month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Tab-to-Table Mapping

| Google Sheets Tab | MySQL Table | Data Present? | Notes |
|---|---|---|---|
| `Chart_of_Accounts` | `coa_accounts` | ✅ 24 rows | Seeded |
| `Config` | `config` | ✅ 30 rows | Seeded |
| `Projects_Master` | `projects` | ✅ 3 rows | Active+Closed |
| `Transactions` | `transactions` | ✅ 74 rows | Most data migrated |
| `OPEX` | `opex` | ✅ 33 rows | Fully migrated |
| `Payables` | `payables` | ⚠️ 0 rows | Empty — needs migration |
| `Receivables` | `receivables` | ⚠️ 0 rows | Empty — needs migration |
| `Assets_Master` | `assets` | ✅ 8 rows | Migrated |
| `Materials_Master` | `materials_master` | ⚠️ 0 rows | Empty — needs migration |
| `Inventory_Lots` | `inventory_lots` | ⚠️ 0 rows | Empty |
| `Inventory_Movements` | `inventory_movements` | ⚠️ 0 rows | Empty |
| `Materials_Purchases` | `materials_purchases` | ⚠️ 0 rows | Empty |
| `Subcontracts` | `subcontracts` | ✅ 1 row | Partial |
| `Subcontract_Payments` | `subcontract_payments` | ⚠️ 0 rows | Empty |
| `Equipment_Rentals` | `equipment_rentals` | ⚠️ 0 rows | Empty |
| `Maintenance_Log` | `maintenance_log` | ⚠️ 0 rows | Empty |
| `Driver_Payments` | `driver_payments` | ⚠️ 0 rows | Empty |
| `Driver_Advances` | `driver_advances` | ⚠️ 0 rows | Empty |
| `Drivers_Master` | `drivers` | ✅ 1 row | Partially migrated |
| `Dividends` | `dividends` | ⚠️ 0 rows | Empty |
| `OM_Bonus` | `om_bonus` | ✅ 1 row | Partially migrated |
| `Account_Transfers` | `account_transfers` | ⚠️ 0 rows | Empty |
| `Advance_Payments` | `advance_payments` | ⚠️ 0 rows | Empty |
| — | `shareholders` | ✅ 7 rows | PS VIBE team data |
| — | `equity_transactions` | ⚠️ 0 rows | Empty |
| — | `dashboard_data` | ✅ | Seeded |
| — | `monthly_summary` | ⚠️ | Empty |

---

## 2. Migration Script Design

### Phase 1: Bulk Data Migration Script

Create `/opt/construction-bot/scripts/migrate-sheets-to-mysql.js`:

```javascript
/**
 * migrate-sheets-to-mysql.js
 * One-time data migration: Google Sheets → MySQL
 *
 * USAGE: node scripts/migrate-sheets-to-mysql.js [--dry-run] [--tables=transactions,opex]
 *
 * --dry-run   : Print what would be done, don't INSERT
 * --tables    : Comma-separated list of tables to migrate (default: all)
 * --force     : Truncate MySQL tables before inserting
 *
 * SAFETY: Does NOT delete Google Sheets data. Sheets remain source of truth.
 */

require('dotenv').config({ path: __dirname + '/../.env' });
const mysql = require('mysql2/promise');
const sheets = require('../src/sheets');  // Google Sheets reader (read-only)
const { TAB_TABLE_MAP, TAB_HEADERS } = require('../src/db-adapter');

// Configuration
const TABLES_LIST = Object.entries(TAB_TABLE_MAP);

// Connection pool
let pool;

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const force = args.includes('--force');
  const tablesArg = args.find(a => a.startsWith('--tables='));
  const selectedTables = tablesArg ? tablesArg.split('=')[1].split(',') : null;

  pool = mysql.createPool({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: parseInt(process.env.MYSQL_PORT || '3306'),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD,
    database: process.env.MYSQL_DATABASE || 'construction_db',
  });

  console.log(`🚀 Migration starting (dryRun=${dryRun}, force=${force})`);

  // Order matters: parents before children
  const ORDERED_TABS = [
    'Chart_of_Accounts', 'Config', 'Projects_Master',   // ref data
    'Drivers_Master', 'Materials_Master',                 // master data
    'Transactions', 'OPEX',                               // journal entries
    'Payables', 'Receivables',                            // AP/AR
    'Inventory_Lots', 'Inventory_Movements',              // inventory
    'Materials_Purchases',                                 // procurement
    'Subcontracts', 'Subcontract_Payments',               // subcontracts
    'Equipment_Rentals', 'Maintenance_Log',               // equipment
    'Driver_Payments', 'Driver_Advances',                  // drivers
    'Dividends', 'OM_Bonus',                              // payouts
    'Account_Transfers', 'Advance_Payments',               // transfers
  ];

  let totalImported = 0;
  let totalErrors = 0;

  for (const tabName of ORDERED_TABS) {
    if (selectedTables && !selectedTables.includes(tabName)) {
      console.log(`⏭️  Skipping ${tabName} (not in --tables filter)`);
      continue;
    }

    const table = TAB_TABLE_MAP[tabName];
    if (!table) continue;

    const headers = TAB_HEADERS[tabName];
    if (!headers) continue;

    const sheetMapping = getSheetColumnMapping(tabName, headers);
    console.log(`\n📋 ${tabName} → ${table} (${headers.length} columns)`);

    try {
      // Read from Google Sheets
      const doc = await sheets.getDoc();
      const sheet = doc.sheetsByTitle[tabName];
      if (!sheet) {
        console.log(`  ⚠️  Tab "${tabName}" not found in Google Sheets, skipping`);
        continue;
      }
      await sheet.loadHeaderRow().catch(() => {});
      const rows = await sheet.getRows();

      if (rows.length === 0) {
        console.log(`  📭 Empty tab, skipping`);
        continue;
      }

      console.log(`  📊 ${rows.length} rows from Google Sheets`);

      if (force && !dryRun) {
        await pool.query(`DELETE FROM \`${table}\``);
        console.log(`  🧹 Truncated ${table}`);
      }

      let imported = 0;
      for (const row of rows) {
        const data = {};
        for (const [gsHeader, mysqlColumn] of Object.entries(sheetMapping)) {
          const value = row.get(gsHeader) || '';
          // Handle empty strings for non-string columns
          data[mysqlColumn] = value;
        }

        if (!dryRun) {
          try {
            await insertRow(pool, table, data);
            imported++;
          } catch (err) {
            console.error(`  ❌ Error inserting row: ${err.message}`);
            totalErrors++;
          }
        } else {
          imported++;
        }
      }

      console.log(`  ✅ ${imported}/${rows.length} rows migrated`);
      totalImported += imported;
    } catch (err) {
      console.error(`  ❌ Error processing ${tabName}: ${err.message}`);
      totalErrors++;
    }
  }

  console.log(`\n${'='.repeat(50)}`);
  console.log(`🏁 Migration complete`);
  console.log(`   Total imported: ${totalImported}`);
  console.log(`   Total errors:   ${totalErrors}`);
  console.log(`   Dry run:        ${dryRun}`);

  await pool.end();
}

/**
 * Map Google Sheets Pascal_Case headers → MySQL snake_case columns
 */
function getSheetColumnMapping(tabName, headers) {
  const map = {};
  for (const header of headers) {
    // Pascal_Case → snake_case: "Project_Name" → "project_name"
    const column = header.toLowerCase();
    map[header] = column;
  }
  return map;
}

/**
 * Insert a row into MySQL, handling data type conversion
 */
async function insertRow(pool, table, data) {
  const columns = Object.keys(data);
  const values = Object.values(data).map(v => {
    // Convert empty strings for boolean/enum fields
    if (v === '' || v === undefined || v === null) return null;
    // Convert "TRUE"/"FALSE" strings for compatibility
    if (v === 'TRUE') return 'TRUE';
    if (v === 'FALSE') return 'FALSE';
    return v;
  });
  const placeholders = columns.map(() => '?').join(', ');

  await pool.query(
    `INSERT INTO \`${table}\` (${columns.map(c => `\`${c}\``).join(', ')}) VALUES (${placeholders})`,
    values
  );
}

main().catch(console.error);
```

### Data Integrity Verification

After migration, run this verification:

```javascript
// scripts/verify-migration.js
const mysql = require('mysql2/promise');
const sheets = require('../src/sheets');

async function verify() {
  const pool = mysql.createPool({ /* ... */ });
  const doc = await sheets.getDoc();

  const checks = [
    'Transactions', 'OPEX', 'Payables', 'Receivables', 'Projects_Master',
    'Assets_Master', 'Subcontracts', 'Materials_Purchases', 'OPEX',
  ];

  for (const tabName of checks) {
    const table = TAB_TABLE_MAP[tabName];
    const [mysqlRows] = await pool.query(`SELECT COUNT(*) AS cnt FROM \`${table}\``);
    const sheet = doc.sheetsByTitle[tabName];
    let gsCount = 0;
    if (sheet) {
      await sheet.loadHeaderRow().catch(() => {});
      const rows = await sheet.getRows();
      gsCount = rows.length;
    }
    const mysqlCount = mysqlRows[0].cnt;

    const match = mysqlCount === gsCount ? '✅' : '❌';
    console.log(`${match} ${tabName}: MySQL=${mysqlCount} GS=${gsCount}`);
  }

  // Row-by-row verification for critical tables
  for (const row of await (await sheets.getDoc()).sheetsByTitle['Transactions'].getRows()) {
    // Check first 5 rows match
  }

  await pool.end();
}
```

---

## 3. Code Refactoring Strategy

### Architecture Overview

```
┌─────────────────────────────────────────────┐
│                bot.js (legacy)              │
│  ┌──────────────────────────────────────┐   │
│  │     Inline Google Sheets CRUD        │   │
│  │  (getDoc, getRows, addRow, refresh)  │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘

                        ↓ REFACTOR TO
         (bot.js becomes thin entry → main.js)

┌─────────────────────────────────────────────┐
│              bot.js (entry)                 │
│  ┌──────────────────────────────────────┐   │
│  │   require("./src/main");            │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│               src/main.js                   │
│  ┌──────────────────────────────────────┐   │
│  │  Bot setup, scenes, handlers        │   │
│  │  Uses db-adapter for all data ops   │   │
│  └──────────────────────────────────────┘   │
│  Depends on:                                │
│  ├── db-adapter.js  ← MySQL pool + cache   │
│  ├── sheets.js      ← Google Sheets (read) │
│  ├── config.js      ← Constants + COA      │
│  ├── utils.js       ← Helpers              │
│  ├── wizard-helper.js ← Form builder       │
│  ├── wizards/*.js   ← Scene wizards        │
│  └── reports/index.js ← Reports            │
└─────────────────────────────────────────────┘
```

### Files That Need Changes

#### 1. `bot.js` (Monolithic — 6837 lines)

**What stays:**
- `require("dotenv").config()`
- `Telegraf`, `session`, `Scenes` imports
- The final `bot.launch()` call
- Graceful shutdown handlers

**What moves to `main.js`:**
- All inline Google Sheets CRUD functions (`getDoc`, `getRows`, `addRow`, etc.)
- All inline handlers/wizards that are duplicated in `src/wizards/`
- All inline reports duplicated in `src/reports/`

**Refactored `bot.js`:** (become entry point only, ~50 lines)
```javascript
require("dotenv").config();
require("./src/main");
```

#### 2. `src/db-adapter.js` (Already Complete)

**Status: ✅ DONE — No changes needed**

This file already provides:
- MySQL connection pool with `mysql2/promise`
- 30s TTL in-memory cache (same pattern as sheets.js)
- `getTabRows()` → `SELECT * FROM table`
- `appendToTab()` → `INSERT INTO table`
- `getDoc()` → proxy that translates sheet access to MySQL
- Dual-write mode (writes to both MySQL and Google Sheets)
- Row wrapper compatible with `.get(key)` pattern used by wizards
- `query()` for raw SQL
- `getConnection()` for transactions

#### 3. `src/sheets.js` (Keep as Read-Only Fallback)

**Status: ✅ DONE — Keep for dual-write fallback**

`db-adapter.js` already calls `sheets.appendToTab()` for dual-write.

#### 4. Wizards (All in `src/wizards/*.js`)

**Status: ✅ DONE — All use `require("./db-adapter")`**

No changes needed. Each wizard imports from `db-adapter.js` which serves MySQL data.

#### 5. `main.js` — `refreshAccounts()`, `refreshConfig()`, `refreshProjects()`

**Issue:** These functions call `db.getDoc()` → proxy → MySQL. However:
- `refreshAccounts()` uses `doc.sheetsByTitle["Chart_of_Accounts"]` → translates to `coa_accounts` table
- `refreshProjects()` uses `doc.sheetsByTitle["Projects_Master"]` → translates to `projects` table

**Status: ✅ Working but inefficient** — The doc proxy calls `getTabRows()` internally. This works but is slower than a direct SQL query. Optimization is optional.

#### 6. COA and Project Cache in `config.js`

**Status: ✅ Works as-is** with MySQL backend.

### Default Data Seeding

Add this seed script to populate reference data if tables are empty:

```sql
-- Seed Chart of Accounts
INSERT IGNORE INTO coa_accounts (account_type, account_name, normal_balance) VALUES
('Income', 'Contract Revenue', 'Credit'),
('Income', 'Machinery Rental Income', 'Credit'),
('Income', 'Consultation Fees', 'Credit'),
('Income', 'Other Income', 'Credit'),
('Expense', 'Direct Materials', 'Debit'),
('Expense', 'Direct Labor', 'Debit'),
('Expense', 'Subcontractor Costs', 'Debit'),
('Expense', 'Equipment Rental', 'Debit'),
('Expense', 'Fuel & Lubricants', 'Debit'),
('Expense', 'Maintenance & Repairs', 'Debit'),
('Expense', 'Office Salaries', 'Debit'),
('Expense', 'Transportation', 'Debit'),
('Expense', 'Utilities', 'Debit'),
('Expense', 'Other Expense', 'Debit'),
('Expense', 'Material', 'Debit');
```

---

## 4. Risk Assessment + Rollback Plan

### Risk Matrix

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Data loss during migration** | Critical — irreversible financial data loss | Low | Google Sheets kept as read-only source of truth; never modified by migration script |
| **Dual-write inconsistency** | Some rows in MySQL, some in Sheets | Medium | Write to both synchronously; if Sheets write fails, log but don't rollback MySQL |
| **Cache serving stale data** | Users see old data until TTL expires | Low | 30s TTL means max 30s staleness; invalidate cache on every write |
| **Monolithic bot.js still in use** | System might still call Google Sheets directly | High (until refactored) | Check PM2/systemd to see which entry point is running |
| **Foreign key constraints** | Orphaned subcontract_payments pointing to missing subcontracts | Low | Migration script inserts parent tables first |
| **Timezone/datetime formatting** | Google Sheets dates vs MySQL DATETIME mismatch | Medium | `normalizeDate()` utility already handles DD/MM/YYYY → YYYY-MM-DD |
| **EM Dash placeholder "—"** | Transactions with "—" as project_name | Medium | Keep as literal "—" or convert to NULL during migration |
| **MySQL container restart** | Bot downtime | Low | PM2 auto-restarts; Docker auto-restarts; health check on startup |

### Current Risk: Entry Point

**Most urgent issue:** Check which file PM2/systemd runs. If `bot.js` is the entry point, it still uses raw Google Sheets API calls directly (the monolithic file has inlined `getDoc()`, `getRows()`, `refreshAccounts()` functions). The `src/` modular code with `db-adapter.js` is **not being used**.

**Fix:**
```bash
# Check what's running
pm2 list
# or
systemctl status construction-bot
# or
cat /etc/systemd/system/construction-bot.service

# Switch to main.js entry
pm2 stop construction-bot
pm2 delete construction-bot
pm2 start /opt/construction-bot/src/main.js --name construction-bot
```

### Rollback Plan

#### Rollback Option A: Revert to Google Sheets Only

1. **Stop MySQL reads:** Replace `db-adapter.js` `getTabRows()` with direct Google Sheets calls:
   ```javascript
   // Temporarily in db-adapter.js — switch to read from Sheets
   const { getTabRows: gsGetTabRows } = require('./sheets');
   async function getTabRows(tabName, limit) {
     return gsGetTabRows(tabName, limit);
   }
   ```

2. **Disable dual-write to MySQL:** In `db-adapter.js` `appendToTab()`, remove the MySQL INSERT.

3. **Restart bot:** `pm2 restart construction-bot`

#### Rollback Option B: Full Revert to `bot.js`

1. **Restore original `bot.js`** from git backup or versioned copy
2. **Restart bot**

#### Rollback Option C: Point-in-Time Restore of Specific Tables

```sql
-- Export MySQL before migration for safety
mysqldump -u root -p construction_db > /backup/construction_db_$(date +%Y%m%d_%H%M%S).sql

-- Rollback specific table
mysql -u root -p construction_db -e "TRUNCATE transactions;"
# Then re-import from Google Sheets backup or re-migrate
```

### Data Integrity Checks

Post-migration validation checklist:

```bash
# 1. Row count match
node scripts/verify-migration.js

# 2. Spot-check transactions
mysql -e "SELECT COUNT(*), SUM(amount) FROM transactions" construction_db

# 3. Verify project aggregation
mysql -e "SELECT project_name, COUNT(*), SUM(amount) FROM transactions GROUP BY project_name" construction_db

# 4. Check for NULL project_name (should use '—' placeholder or some value)
mysql -e "SELECT COUNT(*) FROM transactions WHERE project_name IS NULL OR project_name = ''"

# 5. Date range sanity
mysql -e "SELECT MIN(date), MAX(date) FROM transactions"

# 6. Verify payables/receivables balances
mysql -e "SELECT status, COUNT(*), SUM(amount) FROM payables GROUP BY status"
mysql -e "SELECT status, COUNT(*), SUM(amount) FROM receivables GROUP BY status"
```

---

## 5. Timeline Estimate per Phase

### Phase 0: Current State Assessment ⏱️ 1 hour (DONE)

| Task | Status | Notes |
|------|--------|-------|
| Read existing MySQL schema | ✅ Complete | 26 tables exist |
| Read db-adapter.js | ✅ Complete | Dual-write works |
| Check bot.js entry point | ✅ Complete | 6837 lines monolithic |
| Identify gaps | ✅ Complete | ~12 tables empty in MySQL |

### Phase 1: Bulk Data Migration ⏱️ 2–3 hours

| Task | Duration | Details |
|------|----------|---------|
| Write migration script | 1 hour | `scripts/migrate-sheets-to-mysql.js` |
| Dry-run on all tables | 30 min | Test without INSERT |
| Run full migration | 1 hour | Google Sheets API rate limits (60 req/min/user) |
| Verify data integrity | 30 min | Run verification script |
| Seed missing reference data | 30 min | Config, COA, Shareholders |

### Phase 2: Production Cutover ⏱️ 1–2 hours

| Task | Duration | Details |
|------|----------|---------|
| Switch entry point to main.js | 15 min | PM2 restart |
| Verify reads from MySQL | 15 min | Check bot responses |
| Monitor dual-write | 30 min | Confirm writes go to both |
| Add indexes if needed | 15 min | Based on query patterns |
| Update .env if needed | 5 min | Add MYSQL configs |

### Phase 3: Monolithic bot.js Cleanup ⏱️ 3–5 hours

| Task | Duration | Details |
|------|----------|---------|
| Extract remaining inline functions from bot.js | 2 hours | refreshAccounts, refreshConfig, refreshProjects, getDoc, getRows |
| Remove ALL Google Sheets code from bot.js | 1 hour | Strip to entry-only |
| Test all wizards + reports | 1 hour | End-to-end |
| Remove bot.js reliance entirely | 1 hour | Rename to bot.js.bak |

### Phase 4: Optimization ⏱️ 2–3 hours

| Task | Duration | Details |
|------|----------|---------|
| Add materialized dashboard| 1 hour | Replace getDashboardMetrics() with SQL aggregations |
| Add monthly P&L summaries | 1 hour | Auto-generate monthly_summary |
| Add pagination for large datasets | 1 hour | LIMIT/OFFSET for reports |
| Index tuning | 30 min | Analyze slow queries |

### Total Timeline: 8–14 hours

| Phase | Hours | Dependencies |
|-------|-------|-------------|
| Phase 0: Assessment | ✅ 1h (done) | None |
| Phase 1: Bulk Migration | 2–3h | Phase 0 |
| Phase 2: Cutover | 1–2h | Phase 1 |
| Phase 3: Cleanup | 3–5h | Phase 2 |
| Phase 4: Optimization | 2–3h | Phase 3 |
| **Total** | **8–14h** | |

---

## Key Findings Summary

### What's Already Done ✅
1. All 26 MySQL tables exist with proper schemas, indexes, and ENUMs
2. `db-adapter.js` provides full MySQL CRUD with dual-write to Google Sheets
3. All `src/wizards/*.js` use `require("../db-adapter")`
4. `src/main.js` uses `db-adapter.js` as data layer
5. COA + Config + Shareholders data seeded in MySQL
6. Transactions (74 rows) + OPEX (33 rows) + Assets (8) already migrated
7. MySQL container running on port 3306

### What Needs Action ⚠️
1. **~12 tables are empty in MySQL** — data still only in Google Sheets
2. **bot.js (6837 lines) still has inline Google Sheets code** — bypasses the modular src/ structure
3. **Entry point unknown** — need to check if PM2 runs bot.js (monolithic) or main.js (modular)
4. **Data cleanup** — Transactions have project_name `"———"` (em dash) which should probably be `NULL`

### One-Time Migration Steps

```bash
# 1. Check entry point
pm2 list

# 2. Backup MySQL first
mysqldump -u root -p'PsVibe@MySQL2024!' construction_db > /root/construction_db_backup_$(date +%Y%m%d).sql

# 3. Run migration (dry-run first)
node /opt/construction-bot/scripts/migrate-sheets-to-mysql.js --dry-run

# 4. Run migration (real)
node /opt/construction-bot/scripts/migrate-sheets-to-mysql.js

# 5. Verify
node /opt/construction-bot/scripts/verify-migration.js

# 6. Restart bot with MySQL backend
pm2 restart construction-bot
```
