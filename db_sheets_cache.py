"""
PS VIBE V2 — Sheets Cache Module
Reads from Google Sheets via gspread with SQLite cache layer.
"""

import json
import logging
import time
from datetime import datetime, timezone, timedelta

from .core import (
    get_sheet, get_sheet_safe,
    cache_get, cache_set, cache_config_get, cache_config_set,
    _get_wb, _SHEET_ID,
)

logger = logging.getLogger("psvibe.db.sheets")

# Myanmar Time (GMT+6:30)
MMT = timezone(timedelta(hours=6, minutes=30))

def now_mmt():
    return datetime.now(MMT)

def today_str():
    return now_mmt().strftime("%-m/%-d/%Y")

# ── Cached Google Sheets wrapper ─────────────────────────────────────────────

_CACHE_TTL = {
    "promotions": 120,      # 2 min
    "config": 300,          # 5 min
    "inventory": 180,       # 3 min
    "consoles": 60,         # 1 min
    "pnl": 300,             # 5 min
    "report_data": 120,     # 2 min
    "staff_breakdown": 300, # 5 min
}


def _sheets_read_cache(key: str, ttl: int = None) -> dict | None:
    """Read from sheets_cache via config_cache table."""
    ttl = ttl or _CACHE_TTL.get(key, 300)
    val = cache_config_get(f"sheets:{key}")
    if val:
        try:
            data = json.loads(val)
            ts = data.get("_ts", 0)
            if time.time() - ts < ttl:
                return data
        except json.JSONDecodeError:
            pass
    return None


def _sheets_write_cache(key: str, data: dict):
    """Write sheets data to config_cache with timestamp."""
    data["_ts"] = time.time()
    cache_config_set(f"sheets:{key}", json.dumps(data, ensure_ascii=False))


# ── PROMOTIONS ───────────────────────────────────────────────────────────────

def database_sheets_get_promotions() -> list[dict]:
    """Return active promotions from Promotions sheet."""
    # Try cache first
    cached = _sheets_read_cache("promotions")
    if cached:
        return cached.get("promotions", [])

    try:
        sh = get_sheet_safe("Promotions", rows=200, cols=10,
                            headers=["PromoID", "Title", "Type", "Value", "Description",
                                     "Active", "StartDate", "EndDate", "MinSpend", "BundleItems"])
        rows = sh.get_all_records()
        promos = []
        for r in rows:
            active = str(r.get("Active", "")).strip().lower()
            if active in ("true", "yes", "1", "active"):
                promos.append({
                    "id": str(r.get("PromoID", "")).strip(),
                    "title": str(r.get("Title", "")).strip(),
                    "type": str(r.get("Type", "")).strip(),
                    "value": str(r.get("Value", "")).strip(),
                    "description": str(r.get("Description", "")).strip(),
                    "active": True,
                    "start_date": str(r.get("StartDate", "")).strip(),
                    "end_date": str(r.get("EndDate", "")).strip(),
                    "min_spend": str(r.get("MinSpend", "")).strip(),
                    "bundle_items": str(r.get("BundleItems", "")).strip(),
                })
        data = {"promotions": promos}
        _sheets_write_cache("promotions", data)
        return promos
    except Exception as e:
        logger.warning("Failed to fetch promotions: %s", e)
        return []


# ── CONFIG ───────────────────────────────────────────────────────────────────

def database_sheets_get_config() -> dict:
    """Return Setting sheet as config dict."""
    cached = _sheets_read_cache("config")
    if cached:
        # Remove _ts before returning
        return {k: v for k, v in cached.items() if k != "_ts"}

    try:
        sh = get_sheet("Setting")
        all_vals = sh.get_all_values()

        config = {
            "sheet_id": _SHEET_ID,
        }

        # Named cell mappings from Setting sheet:
        # B2  = base_rate
        # B20 = new_member_card_price
        # B21 = new_member_base_mins
        # B30 = allowed_staff_ids
        # H:J = consoles (handled by consoles endpoint)
        # O2:R5 = bonus_table
        # S:T = staff/salaries

        def cell(row, col):
            try:
                return all_vals[row - 1][col - 1].strip() if row <= len(all_vals) and col <= len(all_vals[row - 1]) else ""
            except (IndexError, AttributeError):
                return ""

        # Read named cells
        try:
            config["base_rate"] = int(cell(2, 2)) if cell(2, 2).isdigit() else 0
        except: config["base_rate"] = 0

        try:
            config["new_member_card_price"] = int(cell(20, 2)) if cell(20, 2).isdigit() else 0
        except: config["new_member_card_price"] = 0

        try:
            config["new_member_base_mins"] = int(cell(21, 2)) if cell(21, 2).isdigit() else 0
        except: config["new_member_base_mins"] = 0

        config["allowed_staff_ids"] = cell(30, 2)

        # Console multipliers: H(8):J(10)
        names = []
        types = []
        mults = []
        for row in all_vals[1:]:  # skip header
            if len(row) > 7 and row[7].strip():
                names.append(row[7].strip())
                types.append(row[8].strip() if len(row) > 8 else "")
                try:
                    mults.append(float(str(row[9]).replace(",", "").strip()) if len(row) > 9 else 1.0)
                except (ValueError, IndexError):
                    mults.append(1.0)

        console_multipliers = {}
        consoles_list = []
        for i, name in enumerate(names):
            console_multipliers[name] = mults[i] if i < len(mults) else 1.0
            consoles_list.append({
                "id": name,
                "type": types[i] if i < len(types) else "",
                "mult": mults[i] if i < len(mults) else 1.0,
            })

        config["console_multipliers"] = console_multipliers
        config["consoles"] = consoles_list

        # Bonus table O2:R5
        bonus_table = []
        for r in range(2, 6):
            row_data = [cell(r, 15), cell(r, 16), cell(r, 17), cell(r, 18)]
            if any(row_data):
                bonus_table.append({"rank": row_data[0], "min_spend": row_data[1],
                                    "bonus_mins": row_data[2], "description": row_data[3]})
        config["bonus_table"] = bonus_table

        # Staff & Salaries: S(19):T(20)
        staff_list = []
        for row in all_vals[1:]:
            if len(row) > 18 and row[18].strip():
                sname = row[18].strip()
                try:
                    salary = float(str(row[19]).replace(",", "").strip()) if len(row) > 19 else 0.0
                except (ValueError, IndexError):
                    salary = 0.0
                staff_list.append({"name": sname, "base_salary": salary})
        config["staff"] = staff_list

        # Food prices from Setting
        try:
            config["food_prices"] = {}
            config["food_costs"] = {}
        except: pass

        _sheets_write_cache("config", config)
        return config

    except Exception as e:
        logger.warning("Failed to fetch config: %s", e)
        return {}


# ── INVENTORY ────────────────────────────────────────────────────────────────

def database_sheets_get_inventory(nocache: bool = False) -> list[dict]:
    """Return inventory items from Inventory sheet."""
    if not nocache:
        cached = _sheets_read_cache("inventory")
        if cached:
            return cached.get("items", [])

    try:
        sh = get_sheet_safe("Inventory", rows=500, cols=7,
                            headers=["Item", "Qty", "Unit", "UnitCost", "TotalCost", "LastUpdated", "Notes"])
        rows = sh.get_all_records()
        items = []
        for r in rows:
            name = str(r.get("Item", "")).strip()
            if not name:
                continue
            qty = int(r.get("Qty", 0)) if str(r.get("Qty", "")).strip() else 0
            unit_cost = float(str(r.get("UnitCost", 0)).replace(",", "")) if str(r.get("UnitCost", "")).strip() else 0.0
            total_cost = float(str(r.get("TotalCost", 0)).replace(",", "")) if str(r.get("TotalCost", "")).strip() else 0.0

            # Determine stock status
            if qty <= 0:
                status = "Out of Stock"
                emoji = "🔴"
            elif qty <= 3:
                status = "Low Stock"
                emoji = "🟡"
            else:
                status = "In Stock"
                emoji = "🟢"

            items.append({
                "name": name,
                "current_stock": qty,
                "unit": str(r.get("Unit", "")).strip(),
                "unit_cost": unit_cost,
                "total_cost": total_cost,
                "inv_value": qty * unit_cost,
                "status": status,
                "emoji": emoji,
                "last_updated": str(r.get("LastUpdated", "")).strip(),
                "notes": str(r.get("Notes", "")).strip(),
            })

        data = {"items": items}
        _sheets_write_cache("inventory", data)
        return items
    except Exception as e:
        logger.warning("Failed to fetch inventory: %s", e)
        return []


# ── CONSOLES ─────────────────────────────────────────────────────────────────

def database_sheets_get_consoles() -> list[dict]:
    """Return console list with live status from Console_Booking."""
    cached = _sheets_read_cache("consoles")
    if cached:
        return cached.get("consoles", [])

    try:
        # Read from Setting!H:J for console definitions
        setting_sh = get_sheet("Setting")
        names = setting_sh.col_values(8)[1:]  # H
        types = setting_sh.col_values(9)[1:]  # I
        mults = setting_sh.col_values(10)[1:]  # J

        # Read active bookings for status overlay
        consoles = []
        today = today_str()

        # Get active bookings
        active_consoles = set()
        try:
            bk_sh = get_sheet_safe("Console_Booking", rows=1000, cols=9,
                                   headers=["BookingID", "Date", "ConsoleID", "MemberID",
                                            "StartTime", "EndTime", "Status", "Staff", "Notes"])
            bk_rows = bk_sh.get_all_values()
            for row in bk_rows[1:]:
                if len(row) >= 7 and row[6].strip() == "Active":
                    active_consoles.add(row[2].strip() if len(row) > 2 else "")
        except Exception:
            pass

        for i, name in enumerate(names):
            name = name.strip()
            if not name:
                continue
            try:
                mult = float(str(mults[i] if i < len(mults) else "1").replace(",", "").strip()) or 1.0
            except (ValueError, IndexError):
                mult = 1.0
            ctype = (types[i] if i < len(types) else "").strip()
            status = "Active" if name in active_consoles else "Free"
            consoles.append({
                "id": name,
                "type": ctype,
                "mult": mult,
                "status": status,
                "liveStatus": status,
            })

        data = {"consoles": consoles}
        _sheets_write_cache("consoles", data)
        return consoles
    except Exception as e:
        logger.warning("Failed to fetch consoles: %s", e)
        return []


# ── P&L ──────────────────────────────────────────────────────────────────────

def database_sheets_get_pnl(month: str = "") -> dict:
    """Return P&L data for given month from Sales_Daily and OPEX_Log sheets."""
    cached = _sheets_read_cache(f"pnl:{month}")
    if cached:
        return {k: v for k, v in cached.items() if k != "_ts"}

    try:
        if not month:
            month = now_mmt().strftime("%m/%Y")

        # Month prefix for matching
        month_prefix = month  # e.g. "05/2026"
        # Also try alternate formats
        alt_prefix = month.lstrip("0")  # e.g. "5/2026"

        # Read Sales_Daily for revenue
        sales_sh = get_sheet_safe("Sales_Daily", rows=5000, cols=13)
        sales_rows = sales_sh.get_all_values()

        total_revenue = 0.0
        total_discount = 0.0
        total_kpay = 0.0
        total_cash = 0.0
        total_mins = 0
        tx_count = 0

        for row in sales_rows[1:]:
            if len(row) < 2:
                continue
            date_val = row[1].strip() if len(row) > 1 else ""
            # Match month from date like "5/27/2026" or "05/27/2026"
            if month_prefix not in date_val and alt_prefix not in date_val:
                continue
            tx_count += 1
            try:
                total_revenue += float(str(row[9]).replace(",", "")) if len(row) > 9 and str(row[9]).strip() else 0
            except: pass
            try:
                total_discount += float(str(row[8]).replace(",", "")) if len(row) > 8 and str(row[8]).strip() else 0
            except: pass
            try:
                total_kpay += float(str(row[10]).replace(",", "")) if len(row) > 10 and str(row[10]).strip() else 0
            except: pass
            try:
                total_cash += float(str(row[11]).replace(",", "")) if len(row) > 11 and str(row[11]).strip() else 0
            except: pass
            try:
                total_mins += int(float(str(row[4]).replace(",", ""))) if len(row) > 4 and str(row[4]).strip() else 0
            except: pass

        # Read OPEX for expenses
        total_opex = 0.0
        opex_items = []
        try:
            opex_sh = get_sheet_safe("OPEX_Log", rows=1000, cols=6,
                                     headers=["Date", "Category", "Description", "Amount", "Account", "Payment"])
            opex_rows = opex_sh.get_all_values()
            for row in opex_rows[1:]:
                if len(row) < 1:
                    continue
                date_val = row[0].strip() if row else ""
                if month_prefix not in date_val and (alt_prefix not in date_val if alt_prefix else True):
                    continue
                try:
                    amt = float(str(row[3]).replace(",", "")) if len(row) > 3 and str(row[3]).strip() else 0
                except: amt = 0
                total_opex += amt
                opex_items.append({
                    "date": date_val,
                    "category": row[1].strip() if len(row) > 1 else "",
                    "description": row[2].strip() if len(row) > 2 else "",
                    "amount": amt,
                    "account": row[4].strip() if len(row) > 4 else "",
                })
        except Exception:
            pass

        gross_profit = total_revenue - total_discount
        net_income = gross_profit - total_opex

        pnl = {
            "month": month,
            "revenue": round(total_revenue, 2),
            "discount": round(total_discount, 2),
            "gross_profit": round(gross_profit, 2),
            "opex": round(total_opex, 2),
            "net_income": round(net_income, 2),
            "total_kpay": round(total_kpay, 2),
            "total_cash": round(total_cash, 2),
            "total_mins": total_mins,
            "tx_count": tx_count,
            "opex_items": opex_items,
            "depreciation": 0,  # computed by finance module
        }

        _sheets_write_cache(f"pnl:{month}", pnl)
        return pnl
    except Exception as e:
        logger.warning("Failed to fetch P&L: %s", e)
        return {"month": month, "revenue": 0, "discount": 0, "gross_profit": 0,
                "opex": 0, "net_income": 0, "total_kpay": 0, "total_cash": 0,
                "total_mins": 0, "tx_count": 0, "opex_items": [], "depreciation": 0}


# ── REPORT DATA ──────────────────────────────────────────────────────────────

def database_sheets_get_report_data() -> dict:
    """Return today/period report summary data."""
    cached = _sheets_read_cache("report_data")
    if cached:
        return {k: v for k, v in cached.items() if k != "_ts"}

    try:
        today = today_str()
        sales_sh = get_sheet_safe("Sales_Daily", rows=5000, cols=13)
        sales_rows = sales_sh.get_all_values()

        today_revenue = 0.0
        today_tx_count = 0
        today_mins = 0
        today_kpay = 0.0
        today_cash = 0.0

        for row in sales_rows[1:]:
            if len(row) < 2:
                continue
            date_val = row[1].strip() if len(row) > 1 else ""
            if date_val != today:
                continue
            today_tx_count += 1
            try:
                today_revenue += float(str(row[9]).replace(",", "")) if len(row) > 9 and str(row[9]).strip() else 0
            except: pass
            try:
                today_kpay += float(str(row[10]).replace(",", "")) if len(row) > 10 and str(row[10]).strip() else 0
            except: pass
            try:
                today_cash += float(str(row[11]).replace(",", "")) if len(row) > 11 and str(row[11]).strip() else 0
            except: pass
            try:
                today_mins += int(float(str(row[4]).replace(",", ""))) if len(row) > 4 and str(row[4]).strip() else 0
            except: pass

        # Active sessions count
        active_sessions = 0
        try:
            bk_sh = get_sheet_safe("Console_Booking", rows=1000, cols=9)
            bk_rows = bk_sh.get_all_values()
            for row in bk_rows[1:]:
                if len(row) >= 7 and row[6].strip() == "Active":
                    active_sessions += 1
        except: pass

        data = {
            "date": today,
            "today": {
                "revenue": round(today_revenue, 2),
                "tx_count": today_tx_count,
                "mins": today_mins,
                "kpay": round(today_kpay, 2),
                "cash": round(today_cash, 2),
            },
            "active_sessions": active_sessions,
            "summary": {
                "total_revenue": round(today_revenue, 2),
                "total_tx": today_tx_count,
                "total_mins": today_mins,
                "active_sessions": active_sessions,
            },
        }

        _sheets_write_cache("report_data", data)
        return data
    except Exception as e:
        logger.warning("Failed to fetch report data: %s", e)
        return {"date": today_str(), "today": {"revenue": 0, "tx_count": 0, "mins": 0, "kpay": 0, "cash": 0}, "active_sessions": 0, "summary": {}}


# ── STAFF BREAKDOWN ──────────────────────────────────────────────────────────

def database_sheets_get_staff_breakdown() -> list[dict]:
    """Return staff sales breakdown from Sales_Daily."""
    cached = _sheets_read_cache("staff_breakdown")
    if cached:
        return cached.get("staff", [])

    try:
        month = now_mmt().strftime("%m/%Y")
        alt_prefix = month.lstrip("0")

        sales_sh = get_sheet_safe("Sales_Daily", rows=5000, cols=13)
        sales_rows = sales_sh.get_all_values()

        staff_data = {}  # staff_name -> {revenue, tx_count, mins}

        for row in sales_rows[1:]:
            if len(row) < 2:
                continue
            date_val = row[1].strip() if len(row) > 1 else ""
            if month not in date_val and alt_prefix not in date_val:
                continue
            staff = row[12].strip() if len(row) > 12 else "Unknown"
            if not staff:
                staff = "Unknown"

            if staff not in staff_data:
                staff_data[staff] = {"name": staff, "revenue": 0.0, "tx_count": 0, "mins": 0}

            staff_data[staff]["tx_count"] += 1
            try:
                staff_data[staff]["revenue"] += float(str(row[9]).replace(",", "")) if len(row) > 9 and str(row[9]).strip() else 0
            except: pass
            try:
                staff_data[staff]["mins"] += int(float(str(row[4]).replace(",", ""))) if len(row) > 4 and str(row[4]).strip() else 0
            except: pass

        staff_list = sorted(staff_data.values(), key=lambda x: x["revenue"], reverse=True)
        for s in staff_list:
            s["revenue"] = round(s["revenue"], 2)

        data = {"staff": staff_list, "month": month}
        _sheets_write_cache("staff_breakdown", data)
        return staff_list
    except Exception as e:
        logger.warning("Failed to fetch staff breakdown: %s", e)
        return []


# ── PROMOTIONS LOG ───────────────────────────────────────────────────────────

def database_sheets_post_promotions_log(data: dict) -> dict:
    """Create promotion usage record in Promotions_Log sheet."""
    try:
        sh = get_sheet_safe("Promotions_Log", rows=500, cols=8,
                            headers=["Date", "PromoID", "PromoTitle", "MemberID", "Discount", "NetAmount", "Staff", "Notes"])

        now = now_mmt()
        sh.append_row([
            now.strftime("%-m/%-d/%Y %H:%M"),
            str(data.get("promo_id", "")),
            str(data.get("promo_title", "")),
            str(data.get("member_id", "")),
            str(data.get("discount", 0)),
            str(data.get("net_amount", 0)),
            str(data.get("staff", "")),
            str(data.get("notes", "")),
        ], value_input_option="USER_ENTERED")

        return {"status": "ok", "message": "Promotion log recorded"}
    except Exception as e:
        logger.warning("Failed to log promotion: %s", e)
        return {"status": "error", "message": str(e)}
