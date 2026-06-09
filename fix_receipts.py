import re

with open("/root/Aung Chan Myint/Sales-Tele-Bot/api_server/api_server.js", "r") as f:
    js = f.read()

# Old static payment row pattern
old = '<tr class="payment-row"><td>KPay</td><td class="right">${fmt(d.kpay)} Ks</td></tr><tr class="payment-row"><td>Cash</td><td class="right">${fmt(d.cash)} Ks</td></tr>'

# New dynamic payment rows
new = (
    '<tr class="payment-row"><td>KPay</td><td class="right">${fmt(d.kpay)} Ks</td></tr>'
    '<tr class="payment-row"><td>Cash</td><td class="right">${fmt(d.cash)} Ks</td></tr>'
    '${d.wave?`<tr class="payment-row"><td>Wave Money</td><td class="right">${fmt(d.wave)} Ks</td></tr>`:""}'
    '${d.cb?`<tr class="payment-row"><td>CB Pay</td><td class="right">${fmt(d.cb)} Ks</td></tr>`:""}'
    '${d.aya?`<tr class="payment-row"><td>AYA Pay</td><td class="right">${fmt(d.aya)} Ks</td></tr>`:""}'
)

count = js.count(old)
js = js.replace(old, new)
print(f"Replaced {count} occurrences")

with open("/root/Aung Chan Myint/Sales-Tele-Bot/api_server/api_server.js", "w") as f:
    f.write(js)

print("API_DONE")
