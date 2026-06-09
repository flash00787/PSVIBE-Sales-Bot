"""
PS Vibe Game Library — static game data, title aliases, and style knowledge.
"""
from .faq import FAQ_DATA

# ── Static Game Library (fallback when API unavailable) ───────────────────────
GAME_LIBRARY = """
🏆 PS VIBE OFFICIAL GAME LIST:

⚽ Sports: FC 26 (New!), FIFA 23, NBA 2K25, WWE 2K24, UFC 5
⚔️ Action/Adventure: Black Myth: Wukong, God of War Ragnarök, Marvel's Spider-Man 2, Elden Ring, Ghost of Tsushima
🥊 Fighting: Tekken 8, Mortal Kombat 1, Street Fighter 6
🏎️ Racing: Gran Turismo 7, Need for Speed Unbound
🤝 Co-op: It Takes Two
"""

# ── Hardware / non-game keywords to filter from game lists ────────────────────
HARDWARE_KEYWORDS = {
    "sandisk", "samsung", "ssd", "transfer", "record", "from (", "hard disk",
    "harddisk", "usb", "storage", "hdd", "backup", "data",
}

def _is_real_game(title: str) -> bool:
    """Return False for hardware/storage/metadata rows that sneak into the sheet."""
    t = title.lower()
    return not any(kw in t for kw in HARDWARE_KEYWORDS)


# Sheet title typos → canonical lookup key
TITLE_ALIASES: dict[str, str] = {
    "assassian creeds shadow": "assassin's creed shadows",
    "blackmyth wukong": "black myth: wukong",
    "elder ring": "elden ring",
    "expedition 33": "clair obscur: expedition 33",
    "fifa 2026": "fc 26",
    "horizontal forbidden west": "horizon forbidden west",
    "last of us part 2 remastered": "the last of us part ii remastered",
    "sprit fiction": "split fiction",
    "sillent hill": "silent hill 2",
    "spiderman": "marvel's spider-man 2",
    "basketball 2026": "nba 2k25",
    "hitman": "hitman world of assassination",
    "mortal kombat": "mortal kombat 1",
    "naruto x boruto ultimate": "naruto x boruto: ultimate ninja storm connections",
    "rise of ronnin": "rise of the ronin",
    "wwe 2025": "wwe 2k25",
    "witcher 3": "the witcher 3: wild hunt",
    "god of war ragnarok": "god of war ragnarök",
    "dragon ball sparking zero": "dragon ball sparking! zero",
    "gta 5": "gta 5",
}


# ── Play style knowledge: canonical key → genre, player mode, style description ─
GAME_STYLES: dict[str, dict] = {
    "assassin's creed shadows": {
        "genre": "Action/Stealth RPG", "players": "Solo",
        "style": "Open world feudal Japan, 2 protagonists (stealth ninja or samurai), gorgeous visuals"},
    "astro bot": {
        "genre": "Platformer", "players": "Solo",
        "style": "Best DualSense showcase, family-friendly and creative, charming PS mascot levels"},
    "batman arkham knight": {
        "genre": "Action/Adventure", "players": "Solo",
        "style": "Stealth + brawler combat, Batmobile sections, dark story finale of Arkham trilogy"},
    "black myth: wukong": {
        "genre": "Action RPG", "players": "Solo",
        "style": "Boss-heavy Chinese mythology, Unreal Engine 5 visuals, DualSense haptics on every hit"},
    "devil may cry 5": {
        "genre": "Hack-and-Slash", "players": "Solo",
        "style": "Stylish combo system, 3 playable characters, high skill ceiling, flashy and fast"},
    "dragon ball sparking! zero": {
        "genre": "Anime Arena Fighter", "players": "1-2",
        "style": "180+ characters, destructible arenas, true to anime, easy to jump in for fans"},
    "elden ring": {
        "genre": "Souls-like Open World RPG", "players": "Solo (co-op optional)",
        "style": "Very hard, massive open world, incredibly rewarding after each boss kill, FromSoftware masterpiece"},
    "clair obscur: expedition 33": {
        "genre": "Turn-based RPG", "players": "Solo",
        "style": "Cinematic French RPG, emotional story, unique action-timing parry system, critically acclaimed"},
    "fc 26": {
        "genre": "Football", "players": "1-4",
        "style": "Rush mode (4-player co-op), career mode, Ultimate Team, newest football title at the shop"},
    "fifa 23": {
        "genre": "Football", "players": "1-2",
        "style": "Classic football sim, last FIFA-branded title before EA Sports FC"},
    "ghost of tsushima": {
        "genre": "Action/Adventure", "players": "Solo + online co-op",
        "style": "Samurai open world, stunning visuals, stealth or sword combat, cinematic feel, VIP-worthy"},
    "ghost of yotei": {
        "genre": "Action/Adventure", "players": "Solo",
        "style": "Spiritual sequel set in Hokkaido, new heroine, same cinematic Ghost of Tsushima feel"},
    "god of war ragnarök": {
        "genre": "Action/Adventure", "players": "Solo",
        "style": "Cinematic masterpiece, brutal yet emotional, Norse mythology, father-son story, DualSense heavy"},
    "gran turismo 7": {
        "genre": "Racing Sim", "players": "1-2",
        "style": "400+ real cars, ultra-realistic driving, DualSense trigger resistance simulates brakes"},
    "gta 5": {
        "genre": "Open World Crime", "players": "Solo + online",
        "style": "Massive open world, 3 protagonists, heists, free roam chaos, online multiplayer"},
    "hades": {
        "genre": "Roguelike Action", "players": "Solo",
        "style": "Fast-paced dungeon crawler, every run different, god power builds, great story between runs"},
    "hitman world of assassination": {
        "genre": "Stealth Puzzle", "players": "Solo",
        "style": "Creative assassination sandbox, disguise and plan kills, very replayable levels"},
    "horizon forbidden west": {
        "genre": "Action RPG", "players": "Solo",
        "style": "Sci-fi open world, robot dinosaurs, bow + weapon combat, breathtaking environments"},
    "injustice 2": {
        "genre": "Fighting", "players": "1-2",
        "style": "DC superhero fighter, gear upgrade system, solid story mode, accessible for newcomers"},
    "it takes two": {
        "genre": "Co-op Adventure", "players": "2 REQUIRED",
        "style": "Must play with a friend, gameplay changes every chapter, emotional story, best co-op game made"},
    "the last of us part ii remastered": {
        "genre": "Action/Stealth", "players": "Solo",
        "style": "Deeply emotional story, stealth + brutal combat, PS5 remaster with improved visuals"},
    "little nightmares 3": {
        "genre": "Horror Platformer", "players": "1-2 co-op",
        "style": "Creepy atmospheric puzzle platformer, dark visual storytelling, co-op available"},
    "minecraft": {
        "genre": "Sandbox/Survival", "players": "1-4+",
        "style": "Build anything, survival or creative mode, endless exploration, great for groups of friends"},
    "mortal kombat 1": {
        "genre": "Fighting", "players": "1-2",
        "style": "Brutal fatalities, iconic 2D fighter, Kameo assist system, story mode reboot"},
    "naruto x boruto: ultimate ninja storm connections": {
        "genre": "Anime Arena Fighter", "players": "1-2",
        "style": "Full Naruto universe roster, accessible arena fighter, great for anime fans"},
    "nba 2k25": {
        "genre": "Basketball", "players": "1-4",
        "style": "Most realistic basketball sim, MyCareer story mode, The City online, best basketball game"},
    "red dead redemption 2": {
        "genre": "Open World Western", "players": "Solo",
        "style": "Cinematic outlaw epic, immersive slow-paced world, stunning detail, emotional ending"},
    "resident evil 9": {
        "genre": "Survival Horror", "players": "Solo",
        "style": "Over-the-shoulder horror action, resource management, intense atmospheric horror"},
    "rise of the ronin": {
        "genre": "Action RPG", "players": "Solo (co-op optional)",
        "style": "Open world feudal Japan, fast sword combat, story branching choices"},
    "silent hill 2": {
        "genre": "Psychological Horror", "players": "Solo",
        "style": "Atmospheric horror remake, iconic monster design, emotional story, not action-heavy"},
    "marvel's spider-man 2": {
        "genre": "Action/Adventure", "players": "Solo",
        "style": "Web-swinging open world NYC, Peter + Miles playable, fast fluid combat, Venom story"},
    "split fiction": {
        "genre": "Co-op Adventure", "players": "2 REQUIRED",
        "style": "By Hazelight (same studio as It Takes Two), genre-mixing sci-fi/fantasy co-op, wildly creative"},
    "tekken 8": {
        "genre": "3D Fighting", "players": "1-2",
        "style": "Competitive 3D fighter, Heat system, great story mode, newcomer-friendly while deep for pros"},
    "ufc 5": {
        "genre": "MMA Sports", "players": "1-2",
        "style": "Realistic MMA simulation, doctor stoppages, career mode, best sports combat feel"},
    "the witcher 3: wild hunt": {
        "genre": "Open World RPG", "players": "Solo",
        "style": "Massive story RPG, moral choices matter, best side quests in gaming, 100+ hours of content"},
    "wwe 2k25": {
        "genre": "Wrestling Sports", "players": "1-4",
        "style": "WWE universe mode, create-a-wrestler, chaotic multiplayer fun with friends"},
}


# ── Live game library text builder (used by AI system prompt) ──────────────────
def _build_live_game_library_text(fetch_games_fn) -> str:
    """Build enriched game library for AI: title + genre + player mode + play style.
    Args:
        fetch_games_fn: callable that returns list of game dicts from API.
    """
    try:
        games = fetch_games_fn()
        if not games:
            return GAME_LIBRARY
        lines = [
            "=== OFFICIAL PS VIBE GAME LIBRARY ===",
            "ONLY recommend or discuss games from this list. Each entry: Title [Genre, Players] — Style",
            "Sheet titles may have typos — use context to match (e.g. 'Sprit Fiction'=Split Fiction, "
            "'Elder Ring'=Elden Ring, 'Sillent Hill'=Silent Hill 2, 'Horizontal'=Horizon Forbidden West).",
        ]
        for g in sorted(games, key=lambda x: (x.get("title") or "").lower()):
            title  = (g.get("title") or "").strip()
            status = (g.get("status") or "").strip()
            if not title or not _is_real_game(title):
                continue
            status_lc = status.lower()
            is_installed   = "c -" in status_lc or "c-" in status_lc
            is_not_inst    = status_lc == "not installed"
            is_ref_error   = status == "#REF!"
            if not (is_installed or is_not_inst or is_ref_error):
                continue
            canonical = TITLE_ALIASES.get(title.lower(), title.lower())
            info = GAME_STYLES.get(canonical, {})
            genre   = info.get("genre", "")
            players = info.get("players", "")
            style   = info.get("style", "")
            line = f"  • {title}"
            if genre or players:
                line += f" [{', '.join(x for x in (genre, players) if x)}]"
            if style:
                line += f" — {style}"
            lines.append(line)
        return "\n".join(lines)
    except Exception:
        return GAME_LIBRARY

