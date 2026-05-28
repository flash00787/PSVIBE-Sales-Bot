import os
import sys
import json
import re
from datetime import datetime

# --- Constants ---
MEMORY_DIR = os.path.dirname(__file__)
SESSION_MEMORY_FILE = os.path.join(MEMORY_DIR, 'session-memory.md')
MEMORY_FILE = os.path.join(os.path.dirname(MEMORY_DIR), 'MEMORY.md')
TODAY_DATE = datetime.now().strftime('%Y-%m-%d')

# --- Categorization Keywords ---
CATEGORIES = {
    "✅ Completed": ["✅", "created", "installed", "fixed", "deployed"],
    "❌ Pending": ["❌", "pending", "incomplete", "partial", "failed", "todo"],
    "💡 Key Decisions": ["decision", "rule", "protocol", "convention", "decided", "boss"],
    "📝 Notes": [],  # Default category
}

# --- Helper Functions ---
def get_daily_log_path(date_str):
    return os.path.join(MEMORY_DIR, f"{date_str}.md")

def read_file_lines(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return f.readlines()

def write_to_file(path, content, mode='a'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode, encoding='utf-8') as f:
        f.write(content)

def categorize_line(line):
    line_lower = line.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in line_lower for keyword in keywords):
            return category
    return "📝 Notes"

def generate_summary(lines, date_str):
    if not lines:
        return "No significant activity found in the session log."

    categorized_lines = {key: [] for key in CATEGORIES}
    for line in lines:
        stripped_line = line.strip()
        if stripped_line:
            category = categorize_line(stripped_line)
            categorized_lines[category].append(f"- {stripped_line.lstrip('- ')}")

    summary = f"## Session Summary ({date_str})\n\n"
    for category, items in categorized_lines.items():
        if items:
            summary += f"### {category}\n"
            summary += "\n".join(items) + "\n\n"
    
    return summary.strip()

# --- Main Logic ---
def main():
    args = sys.argv[1:]
    
    dry_run = '--dry-run' in args or not args
    generate = '--generate' in args
    update_memory = '--update-memory' in args
    
    session_date_str = TODAY_DATE
    if '--session' in args:
        try:
            session_date_index = args.index('--session') + 1
            session_date_str = args[session_date_index]
            datetime.strptime(session_date_str, '%Y-%m-%d') # Validate format
        except (ValueError, IndexError):
            print("Error: Invalid or missing date for --session. Use YYYY-MM-DD format.", file=sys.stderr)
            sys.exit(1)

    session_log_path = get_daily_log_path(session_date_str) if '--session' in args else SESSION_MEMORY_FILE

    # --- Read Session Log ---
    session_lines = read_file_lines(session_log_path)
    if session_lines is None:
        print(f"Error: Session log file not found at {session_log_path}", file=sys.stderr)
        sys.exit(1)

    # --- Generate Summary ---
    summary = generate_summary(session_lines, session_date_str)
    
    if dry_run:
        print("--- DRY RUN ---")
        print(summary)
        if update_memory:
            categorized_lines = {key: [] for key in CATEGORIES}
            for line in session_lines:
                stripped_line = line.strip()
                if stripped_line:
                    category = categorize_line(stripped_line)
                    categorized_lines[category].append(f"- {stripped_line.lstrip('- ')}")
            
            if categorized_lines["💡 Key Decisions"]:
                 print("\n--- Would update MEMORY.md with: ---")
                 key_decisions_content = "\n".join(categorized_lines["💡 Key Decisions"])
                 memory_update_content = f"## Memory ({session_date_str})\n{key_decisions_content}\n"
                 print(memory_update_content)
        return

    # --- File Writing ---
    if generate or update_memory:
        daily_log_path = get_daily_log_path(session_date_str)
        print(f"Appending summary to {daily_log_path}...")
        write_to_file(daily_log_path, f"\n\n{summary}\n")

    if update_memory:
        categorized_lines = {key: [] for key in CATEGORIES}
        for line in session_lines:
            stripped_line = line.strip()
            if stripped_line:
                category = categorize_line(stripped_line)
                categorized_lines[category].append(f"- {stripped_line.lstrip('- ')}")
        
        if categorized_lines["💡 Key Decisions"]:
            print(f"Updating {MEMORY_FILE} with key decisions...")
            key_decisions_content = "\n".join(categorized_lines["💡 Key Decisions"])
            memory_update_content = f"\n## Memory ({session_date_str})\n{key_decisions_content}\n"
            write_to_file(MEMORY_FILE, memory_update_content)
        else:
            print("No key decisions found to update in MEMORY.md.")

    print("Done.")


if __name__ == "__main__":
    main()