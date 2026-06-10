"""PS VIBE Bot — Game Library Handler (paginated + search)."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
import logging, re, json
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta
from bot import (
    BTN_BACK, BTN_BACK_MAIN, BTN_CANCEL,

    BTN_VIEW_GAMES, GAME_ADD_GENRE,
    GAME_ADD_PLATFORM, GAME_ADD_STATUS, GAME_ADD_TITLE, GAME_DEL_SELECT, GAME_DETAIL_PICK,
    GAME_EDIT_FIELD, GAME_EDIT_SELECT, GAME_EDIT_VALUE, GAME_MENU,

    fetch_console_games, fetch_console_games_async, fetch_games, fetch_games_async,  show_game_menu,
    show_main_menu, show_console_menu, SSD_NAMES,
)



# ── Pagination constants ──
GAMES_PER_PAGE = 8

# Navigation button labels
BTN_PREV = "⬅️ Prev"
BTN_NEXT = "Next ➡️"
BTN_SEARCH = "🔍 ရှာမည်"
BTN_SHOW_ALL = "📋 အားလုံး"


def _build_game_kb(games: list, page: int, total_pages: int, show_nav: bool = True) -> list:
    """Build ReplyKeyboardMarkup rows for a page of games."""
    start = page * GAMES_PER_PAGE
    end = start + GAMES_PER_PAGE
    page_games = games[start:end]

    kb = []
    for i, g in enumerate(page_games, start=start + 1):
        name = g.get("title", "").strip()
        if not name:
            continue
        genre = g.get("genre", "").strip()
        sm = g.get("solo_multi", "").strip()
        sm_icon = "🧑" if sm == "Solo" else ("👥" if sm == "Multiplayer" else ("🧑👥" if sm else ""))
        label = f"{i}. {name}"
        if genre:
            label += f" · {genre}"
        kb.append([label])

    if show_nav and total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(BTN_PREV)
        nav_row.append(f"Page {page + 1}/{total_pages}")
        if page < total_pages - 1:
            nav_row.append(BTN_NEXT)
        kb.append(nav_row)

    kb.append([BTN_SEARCH, BTN_BACK])
    return kb


def _build_game_list_text(games: list, page: int, total_pages: int, query: str = "") -> str:
    """Build the text display for a page of games."""
    start = page * GAMES_PER_PAGE
    end = start + GAMES_PER_PAGE
    page_games = games[start:end]

    header = "🎮 <b>Game Library</b>"
    if query:
        header += f' — "<i>{query}</i>"'

    lines = [f"{header} ({len(games)} ဂိမ်း)"]
    if total_pages > 1:
        lines.append(f"📄 Page {page + 1}/{total_pages}")
    lines.append("━━━━━━━━━━━━━━━━━━")

    for i, g in enumerate(page_games, start=start + 1):
        name = g.get("title", "").strip()
        if not name:
            continue
        sm = g.get("solo_multi", "").strip()
        genre = g.get("genre", "").strip()
        discs = g.get("discs", "").strip()

        sm_icon = "🧑" if sm == "Solo" else ("👥" if sm == "Multiplayer" else ("🧑👥" if sm else ""))
        tags = ""
        if sm_icon and sm:
            tags += f" {sm_icon}{sm}"
        if genre:
            tags += f" · {genre}"
        if discs and discs not in ("", "0"):
            tags += f" · 💿{discs}"

        lines.append(f"{i}. <b>{name}</b>{tags}")

    lines.append("")
    lines.append("🔍 ဂိမ်းနာမည်ရိုက်၍ ရှာနိုင်သည်")
    return "\n".join(lines)


async def _show_game_detail(update, game: dict) -> None:
    """Show detailed info for a single game (console/SSD installs)."""
    game_name = game.get("title", "").strip()
    solo_multi = game.get("solo_multi", "").strip()
    genre = game.get("genre", "").strip()
    discs = game.get("discs", "").strip()

    cgames = fetch_console_games()
    cons_list = []
    ssd_list = []
    session_list = []
    for r in cgames:
        if r.get("game_title", "").strip().lower() == game_name.lower():
            cid = r.get("console_id", "").strip()
            status = r.get("status", "").strip()
            if cid:
                # Show consoles where the game is installed (status = "Installed")
                # Show SSD entries with status = "SSD Copy"
                # Show Session-loaded games (status = "Session")
                if status == "Installed":
                    # SSD (external) drives have IDs starting with SSD-
                    if cid.upper().startswith("SSD"):
                        it = (r.get("install_type","") or "").strip()
                        ssd_list.append(f"{SSD_NAMES.get(cid, cid)} ({it})" if it else SSD_NAMES.get(cid, cid))
                    else:
                        cons_list.append(cid)
                elif status in ("SSD Copy", "Moved"):
                    ssd_list.append(f"{SSD_NAMES.get(cid, cid)} ({status})")
                elif status == "Session":
                    session_list.append(f"{cid}")
                # Skip entries with status "Not Installed"

    sm_icon = "🧑" if solo_multi == "Solo" else ("👥" if solo_multi == "Multiplayer" else ("🧑👥" if solo_multi else ""))
    discs_str = f" 💿 {discs}pc" if discs and discs not in ("", "0") else ""

    info_lines = [
        f"🎮 <b>{game_name}</b>{discs_str}",
        "━━━━━━━━━━━━━━━━━━",
    ]
    if sm_icon and solo_multi:
        info_lines.append(f"{sm_icon} <b>Mode:</b> {solo_multi}")
    if genre:
        info_lines.append(f"🎯 <b>Genre:</b> {genre}")

    info_lines.append("")
    if cons_list:
        unique_cons = sorted(set(cons_list))
        info_lines.append(f"📀 <b>Console တွင်ရှိသည်:</b> {', '.join(unique_cons)}")
    else:
        info_lines.append("📀 <b>Console:</b> <i>Not installed</i>")

    if ssd_list:
        unique_ssd = sorted(set(ssd_list))
        info_lines.append(f"💾 <b>SSD တွင်ရှိသည်:</b> {', '.join(unique_ssd)}")
    else:
        info_lines.append("💾 <b>SSD:</b> <i>မရှိပါ</i>")

    if session_list:
        unique_sessions = sorted(set(session_list))
        info_lines.append(f"⏱️ <b>Session ကစားဖူးသည်:</b> {', '.join(unique_sessions)}")

    await update.message.reply_text(
        "\n".join(info_lines),
        parse_mode="HTML",
    )


async def show_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show game library directly with paginated view and edit/delete options."""
    games = await fetch_games_async()
    count = len(games)
    # Clear any lingering game view state
    context.user_data.pop("game_list", None)
    context.user_data.pop("game_page", None)
    context.user_data.pop("game_query", None)
    context.user_data.pop("game_searching", None)

    if not games:
        await update.message.reply_text(
            "ℹ️ Game Library ဗလာ ဖြစ်နေသည်\nဂိမ်းထည့်ပါ",
            reply_markup=ReplyKeyboardMarkup([[BTN_BACK_MAIN]], resize_keyboard=True),
        )
        return GAME_MENU

    context.user_data["game_list"] = games
    context.user_data["game_page"] = 0
    context.user_data["game_query"] = ""
    total_pages = max(1, (len(games) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
    text = _build_game_list_text(games, 0, total_pages)
    kb = _build_game_kb(games, 0, total_pages)
    # Add edit option at bottom
    kb.append([BTN_BACK_MAIN])

    await update.message.reply_text(text, parse_mode="HTML",
                                     reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return GAME_MENU


async def step_game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    game_list = context.user_data.get("game_list", [])
    game_page = context.user_data.get("game_page", 0)
    game_query = context.user_data.get("game_query", "")

    # ── Back ──
    if choice in (BTN_BACK, BTN_BACK_MAIN):
        context.user_data.pop("game_list", None)
        context.user_data.pop("game_page", None)
        context.user_data.pop("game_query", None)
        return await show_console_menu(update, context)

    # ── Page navigation (only when viewing games) ──
    if choice == BTN_PREV and game_list:
        game_page = max(0, game_page - 1)
        context.user_data["game_page"] = game_page
        total_pages = max(1, (len(game_list) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        text = _build_game_list_text(game_list, game_page, total_pages, game_query)
        kb = _build_game_kb(game_list, game_page, total_pages)
        await update.message.reply_text(text, parse_mode="HTML",
                                         reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return GAME_MENU

    if choice == BTN_NEXT and game_list:
        total_pages = max(1, (len(game_list) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        game_page = min(total_pages - 1, game_page + 1)
        context.user_data["game_page"] = game_page
        text = _build_game_list_text(game_list, game_page, total_pages, game_query)
        kb = _build_game_kb(game_list, game_page, total_pages)
        await update.message.reply_text(text, parse_mode="HTML",
                                         reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return GAME_MENU

    # ── Search button ──
    if choice == BTN_SEARCH and game_list:
        await update.message.reply_text(
            "🔍 <b>ဂိမ်းရှာမည်</b>\n━━━━━━━━━━━━━━━━━━\n"
            "ဂိမ်းနာမည် (သို့) genre ရိုက်ပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup([[BTN_SHOW_ALL, BTN_BACK]], resize_keyboard=True),
        )
        context.user_data["game_searching"] = True
        return GAME_MENU

    # ── Show all (from search) ──
    if choice == BTN_SHOW_ALL:
        context.user_data.pop("game_searching", None)
        all_games = await fetch_games_async()
        context.user_data["game_list"] = all_games
        context.user_data["game_page"] = 0
        context.user_data["game_query"] = ""
        total_pages = max(1, (len(all_games) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        text = _build_game_list_text(all_games, 0, total_pages)
        kb = _build_game_kb(all_games, 0, total_pages)
        await update.message.reply_text(text, parse_mode="HTML",
                                         reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return GAME_MENU

    # ── Search execution (user typed search query) ──
    if context.user_data.get("game_searching"):
        context.user_data.pop("game_searching", None)
        query = choice.lower()
        all_games = await fetch_games_async()
        filtered = [
            g for g in all_games
            if query in g.get("title", "").lower()
            or query in g.get("genre", "").lower()
            or query in g.get("solo_multi", "").lower()
        ]
        if not filtered:
            await update.message.reply_text(
                f"🔍 '<b>{choice}</b>' နှင့် ကိုက်ညီသော ဂိမ်းမရှိပါ",
                parse_mode="HTML",
            )
            # Go back to full list
            all_games = await fetch_games_async()
            context.user_data["game_list"] = all_games
            context.user_data["game_page"] = 0
            context.user_data["game_query"] = ""
            total_pages = max(1, (len(all_games) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
            text = _build_game_list_text(all_games, 0, total_pages)
            kb = _build_game_kb(all_games, 0, total_pages)
            await update.message.reply_text(text, parse_mode="HTML",
                                             reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
            return GAME_MENU

        context.user_data["game_list"] = filtered
        context.user_data["game_page"] = 0
        context.user_data["game_query"] = choice
        total_pages = max(1, (len(filtered) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        text = _build_game_list_text(filtered, 0, total_pages, choice)
        kb = _build_game_kb(filtered, 0, total_pages)
        await update.message.reply_text(text, parse_mode="HTML",
                                         reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return GAME_MENU

    # ── Game selection from keyboard (e.g., "1. GameName · Genre") ──
    if game_list:
        for i, g in enumerate(game_list, 1):
            prefix = f"{i}. "
            if choice.startswith(prefix):
                await _show_game_detail(update, g)
                # Re-show the same page
                total_pages = max(1, (len(game_list) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
                text = _build_game_list_text(game_list, game_page, total_pages, game_query)
                kb = _build_game_kb(game_list, game_page, total_pages)
                await update.message.reply_text(
                    "အခြားဂိမ်းရွေးပါ (သို့) Back နှိပ်ပါ:",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                )
                return GAME_DETAIL_PICK

    # ── View Games ──
    if choice == BTN_VIEW_GAMES:
        games = await fetch_games_async()
        if not games:
            await update.message.reply_text("ℹ️ Game Library ဗလာ ဖြစ်နေသည်\nဂိမ်းထည့်ပါ")
            return await show_game_menu(update, context)
        context.user_data["game_list"] = games
        context.user_data["game_page"] = 0
        context.user_data["game_query"] = ""
        total_pages = max(1, (len(games) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        text = _build_game_list_text(games, 0, total_pages)
        kb = _build_game_kb(games, 0, total_pages)
        await update.message.reply_text(text, parse_mode="HTML",
                                         reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return GAME_MENU











    return await show_game_menu(update, context)


async def step_game_detail_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game detail pick — user selects a game from paginated view or navigates."""
    text = update.message.text.strip()

    game_list = context.user_data.get("game_list", [])
    game_page = context.user_data.get("game_page", 0)
    game_query = context.user_data.get("game_query", "")

    # ── Back ──
    if text == BTN_BACK:
        return await show_game_menu(update, context)

    # ── Page navigation ──
    if text == BTN_PREV and game_list:
        game_page = max(0, game_page - 1)
        context.user_data["game_page"] = game_page
        total_pages = max(1, (len(game_list) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        kb = _build_game_kb(game_list, game_page, total_pages)
        await update.message.reply_text(
            "အခြားဂိမ်းရွေးပါ (သို့) Back နှိပ်ပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return GAME_DETAIL_PICK

    if text == BTN_NEXT and game_list:
        total_pages = max(1, (len(game_list) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        game_page = min(total_pages - 1, game_page + 1)
        context.user_data["game_page"] = game_page
        kb = _build_game_kb(game_list, game_page, total_pages)
        await update.message.reply_text(
            "အခြားဂိမ်းရွေးပါ (သို့) Back နှိပ်ပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return GAME_DETAIL_PICK

    # ── Search ──
    if text == BTN_SEARCH and game_list:
        await update.message.reply_text(
            "🔍 <b>ဂိမ်းရှာမည်</b>\nဂိမ်းနာမည် (သို့) genre ရိုက်ပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup([[BTN_SHOW_ALL, BTN_BACK]], resize_keyboard=True),
        )
        context.user_data["detail_searching"] = True
        return GAME_DETAIL_PICK

    if text == BTN_SHOW_ALL:
        context.user_data.pop("detail_searching", None)
        all_games = await fetch_games_async()
        context.user_data["game_list"] = all_games
        context.user_data["game_page"] = 0
        context.user_data["game_query"] = ""
        total_pages = max(1, (len(all_games) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        kb = _build_game_kb(all_games, 0, total_pages)
        await update.message.reply_text(
            "အသေးစိတ်ကြည့်လိုသော ဂိမ်းကို ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return GAME_DETAIL_PICK

    # ── Detail search execution ──
    if context.user_data.get("detail_searching"):
        context.user_data.pop("detail_searching", None)
        query = text.lower()
        all_games = await fetch_games_async()
        filtered = [
            g for g in all_games
            if query in g.get("title", "").lower()
            or query in g.get("genre", "").lower()
            or query in g.get("solo_multi", "").lower()
        ]
        if not filtered:
            await update.message.reply_text(
                f"🔍 '<b>{text}</b>' နှင့် ကိုက်ညီသော ဂိမ်းမရှိပါ",
                parse_mode="HTML",
            )
            all_games = await fetch_games_async()
            context.user_data["game_list"] = all_games
            context.user_data["game_page"] = 0
            context.user_data["game_query"] = ""
            total_pages = max(1, (len(all_games) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
            kb = _build_game_kb(all_games, 0, total_pages)
            await update.message.reply_text(
                "အသေးစိတ်ကြည့်လိုသော ဂိမ်းကို ရွေးပါ:",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            )
            return GAME_DETAIL_PICK

        context.user_data["game_list"] = filtered
        context.user_data["game_page"] = 0
        context.user_data["game_query"] = text
        total_pages = max(1, (len(filtered) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        kb = _build_game_kb(filtered, 0, total_pages)
        await update.message.reply_text(
            f"🔍 '<b>{text}</b>' ရှာတွေ့သည် ({len(filtered)} ဂိမ်း)\nအသေးစိတ်ကြည့်လိုသော ဂိမ်းကို ရွေးပါ:",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return GAME_DETAIL_PICK

    # ── Game selection ──
    if game_list:
        for i, g in enumerate(game_list, 1):
            prefix = f"{i}. "
            if text.startswith(prefix):
                target = g
                game_name = target.get("title", "").strip()
                solo_multi = target.get("solo_multi", "").strip()
                genre = target.get("genre", "").strip()
                discs = target.get("discs", "").strip()

                cgames = fetch_console_games()
                cons_list = []
                ssd_list = []
                for r in cgames:
                    if r.get("game_title", "").strip().lower() == game_name.lower():
                        cid = r.get("console_id", "").strip()
                        status = r.get("status", "").strip()
                        if cid:
                            # Show consoles where the game is installed (status = "Installed")
                            # Show SSD entries with status = "SSD Copy"
                            # Show Session-loaded games (status = "Session")
                            if status == "Installed":
                                # SSD (external) drives have IDs starting with SSD-
                                if cid.upper().startswith("SSD"):
                                    it = (r.get("install_type","") or "").strip()
                                    ssd_list.append(f"{SSD_NAMES.get(cid, cid)} ({it})" if it else SSD_NAMES.get(cid, cid))
                                else:
                                    cons_list.append(cid)
                            elif status in ("SSD Copy", "Moved"):
                                ssd_list.append(f"{SSD_NAMES.get(cid, cid)} ({status})")
                            elif status == "Session":
                                ssd_list.append(f"{SSD_NAMES.get(cid, cid)} (Session)")
                            # Skip entries with status "Not Installed"

                sm_icon = "🧑" if solo_multi == "Solo" else ("👥" if solo_multi == "Multiplayer" else ("🧑👥" if solo_multi else ""))
                discs_str = f" 💿 {discs}pc" if discs and discs not in ("", "0") else ""

                info_lines = [
                    f"🎮 <b>{game_name}</b>{discs_str}",
                    "━━━━━━━━━━━━━━━━━━",
                ]
                if sm_icon and solo_multi:
                    info_lines.append(f"{sm_icon} <b>Mode:</b> {solo_multi}")
                if genre:
                    info_lines.append(f"🎯 <b>Genre:</b> {genre}")

                info_lines.append("")
                if cons_list:
                    unique_cons = sorted(set(cons_list))
                    info_lines.append(f"📀 <b>Console တွင်ရှိသည်:</b> {', '.join(unique_cons)}")
                else:
                    info_lines.append("📀 <b>Console:</b> <i>Not installed</i>")

                if ssd_list:
                    unique_ssd = sorted(set(ssd_list))
                    info_lines.append(f"💾 <b>SSD တွင်ရှိသည်:</b> {', '.join(unique_ssd)}")
                else:
                    info_lines.append("💾 <b>SSD:</b> <i>မရှိပါ</i>")

                await update.message.reply_text("\n".join(info_lines), parse_mode="HTML")

                total_pages = max(1, (len(game_list) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
                kb = _build_game_kb(game_list, game_page, total_pages)
                await update.message.reply_text(
                    "အခြားဂိမ်းရွေးပါ (သို့) Back နှိပ်ပါ:",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                )
                return GAME_DETAIL_PICK

    # ── No match — show hint ──
    if game_list:
        total_pages = max(1, (len(game_list) + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
        kb = _build_game_kb(game_list, game_page, total_pages)
        await update.message.reply_text(
            "⚠️ Keyboard မှ ရွေးပေးပါ (သို့) 🔍 ရှာမည် နှိပ်ပါ",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return GAME_DETAIL_PICK

    return await show_game_menu(update, context)


# ── Game Add Flow (unchanged) ──
async def step_game_add_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_game_menu(update, context)
    context.user_data["new_game"]["title"] = text
    await update.message.reply_text(
        f"🎮 <b>{text}</b>\n\n"
        "👥 Solo / Multiplayer ရွေးပါ:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [["Solo", "Multiplayer"], ["Solo & Multi"], [BTN_CANCEL]],
            resize_keyboard=True,
        ),
    )
    return GAME_ADD_PLATFORM


async def step_game_add_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Repurposed as Solo/Multiplayer selection step."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_game_menu(update, context)
    valid = ("Solo", "Multiplayer", "Solo & Multi")
    if text not in valid:
        await update.message.reply_text(
            "⚠️ Solo / Multiplayer / Solo & Multi မှ ရွေးပါ",
            reply_markup=ReplyKeyboardMarkup(
                [["Solo", "Multiplayer"], ["Solo & Multi"], [BTN_CANCEL]],
                resize_keyboard=True,
            ),
        )
        return GAME_ADD_PLATFORM
    context.user_data["new_game"]["solo_multi"] = text
    await update.message.reply_text(
        "🎯 Genre ရွေးပါ (သို့) ရိုက်ထည့်ပါ:",
        reply_markup=ReplyKeyboardMarkup(
            [["Action", "Sports"], ["Racing", "Fighting"],
             ["Adventure", "RPG"], ["Horror", "Simulation"],
             ["Puzzle", "Other"], [BTN_CANCEL]],
            resize_keyboard=True,
        ),
    )
    return GAME_ADD_GENRE


async def step_game_add_genre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genre selection step — then ask for copies count."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_game_menu(update, context)
    if not text:
        await update.message.reply_text("⚠️ Genre ရိုက်ပါ:")
        return GAME_ADD_GENRE
    context.user_data["new_game"]["genre"] = text
    await update.message.reply_text(
        f"🎯 Genre: <b>{text}</b>\n\n"
        "💿 Disc/Copy ဘယ်နှစ်ခု ရှိသလဲ?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [["1", "2", "3"], [BTN_CANCEL]],
            resize_keyboard=True,
        ),
    )
    return GAME_ADD_STATUS


async def step_game_add_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Copies count step — then save to sheet."""
    text = update.message.text.strip()
    if text == BTN_CANCEL:
        return await show_game_menu(update, context)
    try:
        copies = int(text)
        if copies < 1 or copies > 20:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ ဂဏန်း (1-20) ရိုက်ပါ:",
            reply_markup=ReplyKeyboardMarkup([["1", "2", "3"], [BTN_CANCEL]], resize_keyboard=True),
        )
        return GAME_ADD_STATUS
    g = context.user_data.get("new_game", {})
    g["copies"] = copies
    title = g.get("title", "")
    solo_multi = g.get("solo_multi", "")
    genre = g.get("genre", "")
    meta = f"{solo_multi}|{genre}"
    try:
        payload = {"title": title, "solo_multi": solo_multi, "genre": genre, "copies": copies}
        result = _psvibe_post("add_game", payload)
        if result is None or not result.get("success"):
            raise Exception(result.get("error", "API call failed") if result else "API unavailable")
        import bot as _bot_mod
        _bot_mod._GAME_ROWS = []
        _bot_mod._GAME_TS = 0
        sm_icon = "🧑" if solo_multi == "Solo" else ("👥" if solo_multi == "Multiplayer" else "🧑👥")
        await update.message.reply_text(
            f"✅ <b>ဂိမ်းထည့်ပြီ!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎮 Game     : <b>{title}</b>\n"
            f"{sm_icon} Mode     : <b>{solo_multi}</b>\n"
            f"🎯 Genre    : <b>{genre}</b>\n"
            f"💿 Copies   : <b>{copies}</b>\n"
            f"📊 Status   : <b>Not Installed</b>\n\n"
            f"ℹ️ Console Install မှ console ထဲ ထည့်နိုင်သည်",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Save မအောင်မြင်ပါ: {e}")
    return await show_game_menu(update, context)


# ── Game Edit Flow (unchanged) ──
async def step_game_edit_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked a game to edit — ask which field to edit."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    games = context.user_data.get("edit_games", [])
    target = None
    for i, g in enumerate(games, 1):
        if text.startswith(f"{i}."):
            target = g
            break
    if not target:
        await update.message.reply_text("⚠️ Keyboard မှ ရွေးပေးပါ")
    context.user_data["edit_target"] = target
    sm = target.get("solo_multi", "") or "မသတ်မှတ်ရသေး"
    gen = target.get("genre", "") or "မသတ်မှတ်ရသေး"
    await update.message.reply_text(
        f"✏️ <b>{target['title']}</b>\n━━━━━━━━━━━━━━━━━━\n👥 Solo/Multi : <b>{sm}</b>\n🎯 Genre      : <b>{gen}</b>\n"
        f"ဘာပြင်မလဲ?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            [["👥 Solo/Multi", "🎯 Genre"], [BTN_BACK]],
            resize_keyboard=True,
        ),
    )
    return GAME_EDIT_FIELD


async def step_game_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User picked which field to edit — ask for new value."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    if text == "👥 Solo/Multi":
        context.user_data["edit_field"] = "solo_multi"
        await update.message.reply_text(
            "👥 Solo/Multi ရွေးပါ:",
            reply_markup=ReplyKeyboardMarkup(
                [["Solo", "Multiplayer"], ["Solo & Multi"], [BTN_BACK]],
                resize_keyboard=True,
            ),
        )
    elif text == "🎯 Genre":
        context.user_data["edit_field"] = "genre"
        await update.message.reply_text(
            "🎯 Genre ရွေးပါ (သို့) ရိုက်ထည့်ပါ:",
            reply_markup=ReplyKeyboardMarkup(
                [["Action", "Sports"], ["Racing", "Fighting"],
                 ["Adventure", "RPG"], ["Horror", "Simulation"],
                 ["Puzzle", "Other"], [BTN_BACK]],
                resize_keyboard=True,
            ),
        )
    else:
        await update.message.reply_text("⚠️ Solo/Multi သို့မဟုတ် Genre ရွေးပါ")
        return GAME_EDIT_FIELD
    return GAME_EDIT_VALUE


async def step_game_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User entered new value — save to col U of Game_Library sheet."""
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    field = context.user_data.get("edit_field", "")
    target = context.user_data.get("edit_target", {})
    if not field or not target:
        return await show_game_menu(update, context)
    if field == "solo_multi" and text not in ("Solo", "Multiplayer", "Solo & Multi"):
        await update.message.reply_text(
            "⚠️ Solo / Multiplayer / Solo & Multi မှ ရွေးပါ",
            reply_markup=ReplyKeyboardMarkup(
                [["Solo", "Multiplayer"], ["Solo & Multi"], [BTN_BACK]],
                resize_keyboard=True,
            ),
        )
        return GAME_EDIT_VALUE
    cur_sm = target.get("solo_multi", "")
    cur_gen = target.get("genre", "")
    if field == "solo_multi":
        new_sm = text
        new_gen = cur_gen
    else:
        new_sm = cur_sm
        new_gen = text
    meta = f"{new_sm}|{new_gen}"
    row_num = target.get("row", 0)
    title = target.get("title", "?")
    try:
        sh = get_game_lib_sh()
        payload = {"title": title, "field": field, "value": text}
        result = _psvibe_put("edit_game", payload)
        if result is None or not result.get("success"):
            raise Exception(result.get("error", "API call failed") if result else "API unavailable")
        import bot as _bot_mod
        _bot_mod._GAME_ROWS = []
        _bot_mod._GAME_TS = 0
        field_label = "Solo/Multi" if field == "solo_multi" else "Genre"
        await update.message.reply_text(
            f"✅ <b>{title}</b>\n━━━━━━━━━━━━━━━━━━\n✏️ {field_label}: <b>{text}</b> မှတ်သားပြီ",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Save မအောင်မြင်ပါ: {e}")
    return await show_game_menu(update, context)


# ── Game Delete Flow (unchanged) ──
async def step_game_del_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == BTN_BACK:
        return await show_game_menu(update, context)
    games = context.user_data.get("del_games", [])
    target = None
    for i, g in enumerate(games, 1):
        if text.startswith(f"{i}."):
            target = g
            break
    if not target:
        await update.message.reply_text("⚠️ Keyboard မှ ရွေးပေးပါ")
        return GAME_DEL_SELECT
    game_name = target.get("title", "")
    try:
        result = _psvibe_delete(f"delete_game/{game_name}")
        if result is None or not result.get("success"):
            raise Exception(result.get("error", "API call failed") if result else "API unavailable")
        await update.message.reply_text(
            f"🗑️ <b>\"{game_name}\"</b> ဂိမ်း ဖျက်ပြီ",
            parse_mode="HTML",
        )
    except Exception as e:
        err_str = str(e)
        await update.message.reply_text(f"❌ ဖျက်မရပါ: {e}")

    return await show_game_menu(update, context)
