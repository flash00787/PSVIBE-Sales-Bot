-- ============================================
-- Phase 1: Silent Branch Architecture Migration
-- Date: 2026-06-22
-- Impact: ZERO downtime, backward compatible
-- ============================================

-- 1. Rename existing branch to Sanchaung
UPDATE branches SET name = 'Sanchaung Branch', code = 'SANCHAUNG' WHERE id = 1;

-- ============================================
-- 2. Add branch_id to PER-BRANCH tables
-- (Shared tables like members, member_wallets, games_library are NOT included)
-- ============================================

-- Console / Session
ALTER TABLE console_booking ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE console_status ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE console_status_audit ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE console_games ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE console_games_backup ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- Sales / Revenue
ALTER TABLE sales_daily ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE sales_daily_backup_20260617 ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE food_cart ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE topup_log ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE receipts ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- Inventory
ALTER TABLE inventory ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE stock_in ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE stock_out ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE stock_hold ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- Finance
ALTER TABLE finance_opex_log ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE finance_assets ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE finance_prepaid ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE finance_payables ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE finance_receivables ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE finance_advances ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE accounts ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE cash_movements ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE cash_transfers ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE capital_movements ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE opex ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE prepaid_amortization ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE asset_disposals ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- Staff / HR
ALTER TABLE dashboard_users ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE staff_records ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE staff_records_bak ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE attendance_log ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE salary_advance ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE salary_payroll ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- Marketing / Promotions
ALTER TABLE promotions ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE promotions_log ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE member_coupons ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- Customer
ALTER TABLE customer_feedback ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- Settings
ALTER TABLE settings ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE settings_config ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- Profit / Distribution
ALTER TABLE profit_distributions ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE profit_distribution_details ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE dividends ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;
ALTER TABLE shareholders ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- Legacy
ALTER TABLE card_wallet ADD COLUMN branch_id INT DEFAULT 1 NOT NULL AFTER id;

-- ============================================
-- 3. Add indexes for branch_id on key tables
-- ============================================
ALTER TABLE console_booking ADD INDEX idx_branch_id (branch_id);
ALTER TABLE console_status ADD INDEX idx_branch_id (branch_id);
ALTER TABLE sales_daily ADD INDEX idx_branch_id (branch_id);
ALTER TABLE topup_log ADD INDEX idx_branch_id (branch_id);
ALTER TABLE finance_opex_log ADD INDEX idx_branch_id (branch_id);
ALTER TABLE finance_assets ADD INDEX idx_branch_id (branch_id);
ALTER TABLE dashboard_users ADD INDEX idx_branch_id (branch_id);
ALTER TABLE attendance_log ADD INDEX idx_branch_id (branch_id);
ALTER TABLE inventory ADD INDEX idx_branch_id (branch_id);

-- ============================================
-- Done!
-- ============================================
