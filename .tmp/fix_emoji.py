with open('/root/psvibe-sales-bot/bot/__init__.py', 'r') as f:
    c = f.read()
# Fix the broken emoji
c = c.replace('"0001F354 FOOD SALE"', '"\U0001f354 Food Sale"')
with open('/root/psvibe-sales-bot/bot/__init__.py', 'w') as f:
    f.write(c)
print('FIXED')
