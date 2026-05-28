"""
PS VIBE Gaming Lounge — Report Generator
==========================================
Generates sales reports, weekly trends, and member insights
from Google Sheets data (Sales_Daily, TopUp_Log, Card_Wallet).

Usage (from bot handlers):
    from bot.report_generator import ReportGenerator
    gen = ReportGenerator()
    daily  = gen.daily_report()
    weekly = gen.weekly_report()
    member = gen.member_insights()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── MMT timezone ──
MMT = timezone(timedelta(hours=6, minutes=30))


def now_mmt() -> datetime:
    return datetime.now(MMT)


def today_str() -> str:
    """Return today's date in M/D/YYYY format (matching sheet format)."""
    d = now_mmt()
    return f"{d.month}/{d.day}/{d.year}"


def date_obj(s: str) -> Optional[datetime]:
    """Parse a date string in M/D/YYYY or M/D/YY format to a datetime.date object."""
    if not s or not s.strip():
        return None
    s = s.strip()
    formats = ["%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%-m/%-d/%Y", "%-m/%-d/%y"]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=MMT)
        except ValueError:
            continue
    return None


def int_safe(val) -> int:
    if val is None:
        return 0
    try:
        s = str(val).replace(",", "").replace(" ", "").strip()
        if not s:
            return 0
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def float_safe(val) -> float:
    if val is None:
        return 0.0
    try:
        s = str(val).replace(",", "").replace(" ", "").strip()
        if not s:
            return 0.0
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def escape_md(text: str) -> str:
    """Escape MarkdownV2 special characters for Telegram."""
    special_chars = r"_*[]()~`>#+-=|{}.!"
    for ch in special_chars:
        text = text.replace(ch, f"\\{ch}")
    return text


@dataclass
class SaleRecord:
    """Parsed row from Sales_Daily sheet."""
    date: str = ""
    voucher_no: str = ""
    member_id: str = ""
    console_id: str = ""
    play_mins: int = 0
    game_amt: int = 0       # revenue from gaming
    food_total: int = 0     # revenue from food
    discount: int = 0
    net_total: int = 0
    kpay: int = 0
    cash: int = 0
    wallet_deduct: int = 0  # col N
    staff: str = ""

    @property
    def total_revenue(self) -> int:
        return self.game_amt + self.food_total


@dataclass
class TopUpRecord:
    """Parsed row from TopUp_Log sheet."""
    date: str = ""
    member_id: str = ""
    topup_type: str = ""    # New Member, Top Up, Referral Bonus
    amount: int = 0
    kpay: int = 0
    cash: int = 0
    added_mins: int = 0
    staff: str = ""


@dataclass
class MemberRecord:
    """Parsed row from Card_Wallet sheet."""
    member_id: str = ""
    member_name: str = ""
    phone: str = ""
    net_spend: int = 0      # total spend (col F, 0-indexed 5)
    tier: str = "Warrior"
    wallet_mins: int = 0    # balance (col I, 0-indexed 8)
    effective_rate: float = 1.0
    reg_staff: str = ""


@dataclass
class DailyReport:
    """Structured daily report data."""
    date: str = ""
    sales: List[SaleRecord] = field(default_factory=list)
    topups: List[TopUpRecord] = field(default_factory=list)

    @property
    def total_gross(self) -> int:
        return sum(s.game_amt + s.food_total for s in self.sales)

    @property
    def total_discount(self) -> int:
        return sum(s.discount for s in self.sales)

    @property
    def total_net(self) -> int:
        return sum(s.net_total for s in self.sales)

    @property
    def total_food(self) -> int:
        return sum(s.food_total for s in self.sales)

    @property
    def total_gaming(self) -> int:
        return sum(s.game_amt for s in self.sales)

    @property
    def total_kpay(self) -> int:
        return sum(s.kpay for s in self.sales)

    @property
    def total_cash(self) -> int:
        return sum(s.cash for s in self.sales)

    @property
    def new_members(self) -> int:
        return len([t for t in self.topups if "New Member" in t.topup_type])

    @property
    def topup_total(self) -> int:
        return sum(t.amount for t in self.topups)

    @property
    def total_wallet_deduct(self) -> int:
        return sum(s.wallet_deduct for s in self.sales)

    @property
    def unique_members(self) -> int:
        ids = set()
        for s in self.sales:
            mid = s.member_id.strip()
            if mid and mid != "0 (Guest)":
                ids.add(mid)
        return len(ids)


@dataclass
class WeeklyReport:
    start_date: str = ""
    end_date: str = ""
    daily_data: List[DailyReport] = field(default_factory=list)
    best_day: str = ""
    best_day_revenue: int = 0
    worst_day: str = ""
    worst_day_revenue: int = 0

    @property
    def week_total(self) -> int:
        return sum(d.total_net for d in self.daily_data)

    @property
    def week_average(self) -> float:
        n = len(self.daily_data)
        return self.week_total / n if n > 0 else 0

    @property
    def week_topups(self) -> int:
        return sum(d.topup_total for d in self.daily_data)

    @property
    def week_new_members(self) -> int:
        return sum(d.new_members for d in self.daily_data)


@dataclass
class MemberInsights:
    total_members: int = 0
    tier_distribution: Dict[str, int] = field(default_factory=dict)
    top_spenders: List[Tuple[str, str, int, str]] = field(default_factory=list)  # (id, name, spend, tier)
    inactive_members: List[Tuple[str, str, str, int]] = field(default_factory=list)  # (id, name, phone, balance)
    total_wallet_minutes: int = 0
    average_wallet_mins: float = 0.0
    high_value_members: int = 0  # members with > 1000 mins


# ═══════════════════════════════════════════════════════════════════
#  ReportGenerator
# ═══════════════════════════════════════════════════════════════════

class ReportGenerator:
    """Generates reports from Google Sheets data.

    The generator accesses the same sheet objects used by the bot
    (sales_sh, topup_sh, member_sh, setting_sh) and reads data
    directly.
    """

    def __init__(self):
        """Initialise the generator — lazily imports sheet objects."""
        self._sales_sh = None
        self._topup_sh = None
        self._member_sh = None
        self._setting_sh = None

    @property
    def sales_sh(self):
        if self._sales_sh is None:
            from bot import sales_sh
            self._sales_sh = sales_sh
        return self._sales_sh

    @property
    def topup_sh(self):
        if self._topup_sh is None:
            from bot import topup_sh
            self._topup_sh = topup_sh
        return self._topup_sh

    @property
    def member_sh(self):
        if self._member_sh is None:
            from bot import member_sh
            self._member_sh = member_sh
        return self._member_sh

    @property
    def setting_sh(self):
        if self._setting_sh is None:
            from bot import setting_sh
            self._setting_sh = setting_sh
        return self._setting_sh

    # ── Data Fetching ──────────────────────────────────────────────

    def _fetch_sales_rows(self, since_date: Optional[str] = None) -> List[SaleRecord]:
        """Fetch sales rows from Sales_Daily, optionally filtered by date.

        Args:
            since_date: If provided, only return rows from this date (M/D/YYYY) onward.

        Returns:
            List of SaleRecord objects.
        """
        try:
            raw = self.sales_sh.get_all_values()
        except Exception as e:
            logger.error("Failed to read Sales_Daily: %s", e)
            return []

        records = []
        for row in raw[1:]:  # skip header
            if not row or len(row) < 6:
                continue
            d = row[0].strip() if len(row) > 0 else ""
            v = row[1].strip() if len(row) > 1 else ""
            if not d or not v:
                continue

            # Apply date filter
            if since_date:
                d_obj = date_obj(d)
                s_obj = date_obj(since_date)
                if d_obj and s_obj and d_obj < s_obj:
                    continue

            rec = SaleRecord(
                date=d,
                voucher_no=v,
                member_id=row[2].strip() if len(row) > 2 else "",
                console_id=row[3].strip() if len(row) > 3 else "",
                play_mins=int_safe(row[4]) if len(row) > 4 else 0,
                game_amt=int_safe(row[5]) if len(row) > 5 else 0,
                food_total=int_safe(row[6]) if len(row) > 6 else 0,
                discount=int_safe(row[7]) if len(row) > 7 else 0,
                net_total=int_safe(row[8]) if len(row) > 8 else 0,
                kpay=int_safe(row[9]) if len(row) > 9 else 0,
                cash=int_safe(row[10]) if len(row) > 10 else 0,
                wallet_deduct=int_safe(row[13]) if len(row) > 13 else 0,  # col N
                staff=row[14].strip() if len(row) > 14 else "",  # col O
            )
            records.append(rec)

        return records

    def _fetch_topup_rows(self, since_date: Optional[str] = None) -> List[TopUpRecord]:
        """Fetch top-up rows from TopUp_Log, optionally filtered by date."""
        try:
            raw = self.topup_sh.get_all_values()
        except Exception as e:
            logger.error("Failed to read TopUp_Log: %s", e)
            return []

        records = []
        for row in raw[1:]:
            if not row or len(row) < 7:
                continue
            d = row[0].strip() if len(row) > 0 else ""
            m = row[1].strip() if len(row) > 1 else ""
            if not d or not m:
                continue

            if since_date:
                d_obj = date_obj(d)
                s_obj = date_obj(since_date)
                if d_obj and s_obj and d_obj < s_obj:
                    continue

            rec = TopUpRecord(
                date=d,
                member_id=m,
                topup_type=row[2].strip() if len(row) > 2 else "",
                amount=int_safe(row[4]) if len(row) > 4 else 0,
                kpay=int_safe(row[5]) if len(row) > 5 else 0,
                cash=int_safe(row[6]) if len(row) > 6 else 0,
                added_mins=int_safe(row[7]) if len(row) > 7 else 0,
                staff=row[9].strip() if len(row) > 9 else "",  # col J
            )
            records.append(rec)

        return records

    def _fetch_member_rows(self) -> List[MemberRecord]:
        """Fetch all member rows from Card_Wallet."""
        try:
            raw = self.member_sh.get_all_values()
        except Exception as e:
            logger.error("Failed to read Card_Wallet: %s", e)
            return []

        records = []
        for row in raw[1:]:
            if not row or len(row) < 2:
                continue
            mid = row[1].strip() if len(row) > 1 else ""
            if not mid:
                continue
            rec = MemberRecord(
                member_id=mid,
                member_name=row[2].strip() if len(row) > 2 else "",
                phone=row[3].strip() if len(row) > 3 else "",
                net_spend=int_safe(row[5]) if len(row) > 5 else 0,  # col F
                tier=row[6].strip() if len(row) > 6 and row[6].strip() else "Warrior",
                wallet_mins=int_safe(row[7]) if len(row) > 7 else 0,  # col I (0-indexed)
                effective_rate=float_safe(row[11]) if len(row) > 11 else 1.0,
                reg_staff=row[10].strip() if len(row) > 10 else "",  # col K
            )
            records.append(rec)

        return records

    # ── Report Generation ──────────────────────────────────────────

    def daily_report(self, date_str: Optional[str] = None) -> DailyReport:
        """Generate a daily report for a specific date or today.

        Args:
            date_str: Date in M/D/YYYY format. Defaults to today in MMT.

        Returns:
            DailyReport object.
        """
        if date_str is None:
            date_str = today_str()

        # Fetch all sales for this date
        all_sales = self._fetch_sales_rows(since_date=date_str)
        day_sales = [s for s in all_sales if s.date.strip() == date_str.strip()]

        # Fetch all topups for this date
        all_topups = self._fetch_topup_rows(since_date=date_str)
        day_topups = [t for t in all_topups if t.date.strip() == date_str.strip()]

        logger.info(
            "Daily report for %s: %d sales, %d topups",
            date_str, len(day_sales), len(day_topups),
        )

        return DailyReport(date=date_str, sales=day_sales, topups=day_topups)

    def weekly_report(self) -> WeeklyReport:
        """Generate a 7-day rolling report ending today.

        Returns:
            WeeklyReport object.
        """
        today = now_mmt()
        # Go back 6 days for start
        start = today - timedelta(days=6)
        start_str = f"{start.month}/{start.day}/{start.year}"
        end_str = today_str()

        # Get all data from start date
        all_sales = self._fetch_sales_rows(since_date=start_str)
        all_topups = self._fetch_topup_rows(since_date=start_str)

        # Group by date
        sales_by_date: Dict[str, List[SaleRecord]] = defaultdict(list)
        topups_by_date: Dict[str, List[TopUpRecord]] = defaultdict(list)

        for s in all_sales:
            sales_by_date[s.date].append(s)
        for t in all_topups:
            topups_by_date[t.date].append(t)

        # Build daily reports for each day
        daily_reports: List[DailyReport] = []
        best_rev = -1
        worst_rev = float('inf')
        best_day = ""
        worst_day = ""

        for offset in range(6, -1, -1):
            d = today - timedelta(days=offset)
            d_str = f"{d.month}/{d.day}/{d.year}"
            dr = DailyReport(
                date=d_str,
                sales=sales_by_date.get(d_str, []),
                topups=topups_by_date.get(d_str, []),
            )
            daily_reports.append(dr)
            if dr.total_net > best_rev:
                best_rev = dr.total_net
                best_day = d_str
            if dr.total_net < worst_rev:
                worst_rev = dr.total_net
                worst_day = d_str

        wr = WeeklyReport(
            start_date=start_str,
            end_date=end_str,
            daily_data=daily_reports,
            best_day=best_day,
            best_day_revenue=best_rev,
            worst_day=worst_day,
            worst_day_revenue=worst_rev,
        )

        logger.info("Weekly report: %s to %s, total=%d", start_str, end_str, wr.week_total)
        return wr

    def member_insights(self) -> MemberInsights:
        """Generate member insights from Card_Wallet data.

        Returns:
            MemberInsights object.
        """
        members = self._fetch_member_rows()

        # Tier distribution
        tier_dist: Dict[str, int] = defaultdict(int)
        for m in members:
            tier = m.tier if m.tier else "Warrior"
            tier_dist[tier] += 1

        # Top spenders (top 10)
        sorted_by_spend = sorted(members, key=lambda m: m.net_spend, reverse=True)
        top_spenders = [
            (m.member_id, m.member_name, m.net_spend, m.tier)
            for m in sorted_by_spend[:10]
        ]

        # Inactive members (balance < 60 mins, non-guest)
        inactive = [
            m for m in members
            if m.wallet_mins < 60 and m.member_id.strip() not in ("", "0 (Guest)")
        ]
        inactive_sorted = sorted(inactive, key=lambda m: m.wallet_mins)[:10]
        inactive_members = [
            (m.member_id, m.member_name, m.phone, m.wallet_mins)
            for m in inactive_sorted
        ]

        # Aggregate stats
        total_wallet = sum(m.wallet_mins for m in members)
        n = len(members)
        avg_wallet = total_wallet / n if n > 0 else 0
        high_value = len([m for m in members if m.wallet_mins > 1000])

        return MemberInsights(
            total_members=n,
            tier_distribution=dict(tier_dist),
            top_spenders=top_spenders,
            inactive_members=inactive_members,
            total_wallet_minutes=total_wallet,
            average_wallet_mins=avg_wallet,
            high_value_members=high_value,
        )

    # ── Telegram Formatting ────────────────────────────────────────

    def format_daily_report(self, report: DailyReport) -> str:
        """Format a daily report as a Telegram Markdown message."""
        if not report.sales and not report.topups:
            return (
                f"📊 *Daily Sales Report*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📅 Date: *{escape_md(report.date)}*\n\n"
                f"ℹ️ No sales recorded today yet\\."
            )

        # Stats for console usage
        console_counts: Dict[str, int] = defaultdict(int)
        for s in report.sales:
            c = s.console_id if s.console_id else "N/A"
            console_counts[c] += 1

        lines = [
            f"📊 *Daily Sales Report*",
            f"━━━━━━━━━━━━━━━━━━",
            f"📅 Date: *{escape_md(report.date)}*",
            "",
            f"💵 *Revenue Summary*",
        ]

        if report.total_gaming > 0:
            lines.append(f"   🎮 Gaming: *{report.total_gaming:,} Ks*")
        if report.total_food > 0:
            lines.append(f"   🍔 Food: *{report.total_food:,} Ks*")
        lines.extend([
            f"   💰 Gross Total: *{report.total_gross:,} Ks*",
        ])
        if report.total_discount > 0:
            lines.append(f"   🎁 Discounts: *-{report.total_discount:,} Ks*")
        lines.append(f"   ✅ Net Revenue: *{report.total_net:,} Ks*")

        lines.extend([
            "",
            f"📈 *Session Stats*",
            f"   🎯 Total Sessions: *{len(report.sales)}*",
            f"   👤 Unique Members: *{report.unique_members}*",
            f"   🕹️ Wallet Minutes Used: *{report.total_wallet_deduct}*",
        ])

        # Payment breakdown
        if report.total_kpay > 0 or report.total_cash > 0:
            lines.append("")
            lines.append(f"💳 *Payment Breakdown*")
            if report.total_kpay > 0:
                lines.append(f"   📱 Kpay: *{report.total_kpay:,} Ks*")
            if report.total_cash > 0:
                lines.append(f"   💵 Cash: *{report.total_cash:,} Ks*")

        # Console usage
        if console_counts:
            lines.append("")
            lines.append(f"🕹️ *Console Usage*")
            for cid, count in sorted(console_counts.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"   • {escape_md(cid)}: *{count}* sessions")

        # Top-up section
        if report.topups:
            lines.append("")
            lines.append(f"🔄 *Top-Ups*")
            lines.append(f"   📈 Total Top-Ups: *{len(report.topups)}*")
            lines.append(f"   💰 Total Amount: *{report.topup_total:,} Ks*")
            if report.new_members > 0:
                lines.append(f"   🆕 New Members: *{report.new_members}*")

        lines.extend([
            "",
            f"━━━━━━━━━━━━━━━━━━",
            f"🏢 *PS VIBE Gaming Lounge*",
            f"   Auto-generated at {now_mmt().strftime('%I:%M %p')} MMT",
        ])

        return "\n".join(lines)

    def format_weekly_report(self, report: WeeklyReport) -> str:
        """Format a weekly report as a Telegram Markdown message."""
        lines = [
            f"📊 *Weekly Sales Report*",
            f"━━━━━━━━━━━━━━━━━━",
            f"📅 *{escape_md(report.start_date)}* → *{escape_md(report.end_date)}*",
            "",
            f"📈 *Daily Breakdown*",
        ]

        # Build a simple ASCII/emoji bar chart
        max_rev = max((d.total_net for d in report.daily_data), default=1)
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        for i, dr in enumerate(report.daily_data):
            # Determine day of week
            d_obj = date_obj(dr.date)
            if d_obj:
                dow = d_obj.strftime("%a")
            else:
                dow = day_names[i] if i < 7 else "???"

            bar_len = int((dr.total_net / max_rev * 15)) if max_rev > 0 else 0
            bar = "█" * bar_len + "▁" * (15 - bar_len) if max_rev > 0 else "▁" * 15
            marker = " 🔥" if dr.date == report.best_day else ""

            lines.append(
                f"   {escape_md(dow)} {bar} *{dr.total_net:,}* Ks"
                f"  ({len(dr.sales)} sessions){marker}"
            )

        lines.extend([
            "",
            f"💰 *Week Totals*",
            f"   ✅ Total Revenue: *{report.week_total:,} Ks*",
            f"   📊 Daily Average: *{report.week_average:,.0f} Ks*",
            f"   🔄 Top-Up Total: *{report.week_topups:,} Ks*",
            f"   🆕 New Members: *{report.week_new_members}*",
            "",
            f"🏆 *Highlights*",
            f"   🔥 Best Day: *{escape_md(report.best_day)}* — *{report.best_day_revenue:,} Ks*",
        ])
        if report.worst_day_revenue > 0:
            lines.append(
                f"   😴 Slowest: *{escape_md(report.worst_day)}* — *{report.worst_day_revenue:,} Ks*"
            )

        lines.extend([
            "",
            f"━━━━━━━━━━━━━━━━━━",
            f"🏢 *PS VIBE Gaming Lounge*",
            f"   Auto-generated at {now_mmt().strftime('%I:%M %p')} MMT",
        ])

        return "\n".join(lines)

    def format_member_insights(self, insights: MemberInsights) -> str:
        """Format member insights as a Telegram Markdown message."""
        lines = [
            f"👥 *Member Insights Report*",
            f"━━━━━━━━━━━━━━━━━━",
            "",
            f"📊 *Overview*",
            f"   👥 Total Members: *{insights.total_members}*",
            f"   ⏱️ Total Wallet Mins: *{insights.total_wallet_minutes:,}*",
            f"   📊 Avg Balance: *{insights.average_wallet_mins:,.0f} mins*",
            f"   💎 High-Value (>1K mins): *{insights.high_value_members}*",
            "",
        ]

        # Tier distribution
        if insights.tier_distribution:
            tier_order = ["Immortal", "Master", "Warrior"]
            lines.append("🏅 *Tier Distribution*")
            for tier in tier_order:
                count = insights.tier_distribution.get(tier, 0)
                if count > 0:
                    emoji_map = {"Immortal": "👑", "Master": "⭐", "Warrior": "⚔️"}
                    em = emoji_map.get(tier, "🎮")
                    lines.append(f"   {em} {tier}: *{count}*")
            # Any other tiers
            for tier, count in sorted(insights.tier_distribution.items()):
                if tier not in tier_order:
                    lines.append(f"   🎮 {escape_md(tier)}: *{count}*")

        # Top spenders
        if insights.top_spenders:
            lines.append("")
            lines.append(f"🏆 *Top Spenders*")
            for i, (mid, name, spend, tier) in enumerate(insights.top_spenders[:5], 1):
                display_name = name if name else mid
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                lines.append(
                    f"   {emoji} *{escape_md(display_name)}* "
                    f"— {spend:,} Ks [{escape_md(tier)}]"
                )

        # Low-balance members (inactive/at-risk)
        if insights.inactive_members:
            lines.append("")
            lines.append(f"⚠️ *Low Balance Members* (<60 mins)")
            for mid, name, phone, bal in insights.inactive_members[:5]:
                display_name = name if name else mid
                lines.append(
                    f"   • *{escape_md(display_name)}* — "
                    f"{bal} mins"
                )

        lines.extend([
            "",
            f"━━━━━━━━━━━━━━━━━━",
            f"🏢 *PS VIBE Gaming Lounge*",
            f"   Auto-generated at {now_mmt().strftime('%I:%M %p')} MMT",
        ])

        return "\n".join(lines)

    def format_daily_report_brief(self, report: DailyReport) -> str:
        """Short summary format suitable for scheduled auto-send."""
        if not report.sales:
            return (
                f"📊 PS VIBE Daily — {escape_md(report.date)}\n"
                f"ℹ️ No sales recorded today yet\\."
            )

        return (
            f"📊 *PS VIBE Daily — {escape_md(report.date)}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎮 Sessions: *{len(report.sales)}*  |  👤 Members: *{report.unique_members}*\n"
            f"💰 Revenue: *{report.total_net:,} Ks*"
            f"{' (🎁 -' + str(report.total_discount) + 'K disc)' if report.total_discount > 0 else ''}\n"
            f"🔄 Top-Ups: *{report.topup_total:,} Ks* ({len(report.topups)} txn{('' if len(report.topups)==1 else 's')})\n"
            f"{'🆕 New Members: *' + str(report.new_members) + '* | ' if report.new_members > 0 else ''}"
            f"📱 Kpay: *{report.total_kpay:,}*  |  💵 Cash: *{report.total_cash:,}*\n"
            f"━━━━━━━━━━━━━━━━━━"
        )


# ── Global singleton ──
_report_generator: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """Return the singleton report generator instance."""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator
