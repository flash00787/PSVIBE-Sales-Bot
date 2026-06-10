import logging
logging.basicConfig(level=logging.DEBUG)
# fix_unicode.py - Fix broken \u escapes in booking_handlers.py
import re

with open('/root/psvibe-sales-bot/customer_bot/booking_handlers.py', 'r') as f:
    content = f.read()

# The problematic line has \u102\ with non-ASCII after it
# Find lines with \u (single backslash u) that have fewer than 4 hex digits

def fix_broken_unicode(m):
    match = m.group(0)
    # \u followed by hex digits - check length
    prefix = match[:2]  # \u or \U
    hex_part = match[2:]
    if len(hex_part) < 4:
        # Pad with zeros on the left
        return prefix + hex_part.zfill(4)
    if len(hex_part) > 4 and prefix == '\\u':
        # Truncate to 4 chars
        return prefix + hex_part[:4]
    return match

# Find \u followed by 1-3 hex digits then a non-hex char
content = re.sub(r'\\\\u([0-9a-fA-F]{{1,3}})(?![0-9a-fA-F])', r'\\\\u\1', content)
# Actually the file uses single backslash \u, let me check
# The file can't be parsed so \u is literal in the Python source

# Find the problematic pattern - \u102 followed by non-hex
# The issue is \u102း where း is U+1038
# We need to replace this with the correct sequence
# "ရွေးပါ" in Unicode = \u101b\u103d\u1031\u1038\u1015\u102b
# "ကြာချိန်" in Unicode = \u1000\u103c\u102c\u1001\u103b\u102d\u102f\u1004\u103a

# Replace broken "\u101b\u103d\u1031\u102း\u1015\u102b" with proper Unicode
old = b'\\u101b\\u103d\\u1031\\u102'
# The problem is the character AFTER \u102, which is း (U+1038 encoded as E1 80 B8)
# We need to find and replace this exact byte pattern in the source file
old_byte = '\\u101b\\u103d\\u1031\\u102'.encode() + '\u0e38\u1038\u1015\u102b'.encode()

logging.info("Script loaded")
logging.info(f"Old bytes: {old}")
