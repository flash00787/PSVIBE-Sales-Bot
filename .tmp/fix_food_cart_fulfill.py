with open('/root/psvibe_api_server/patch_routes.py', 'r') as f:
    c = f.read()

old = '@app.delete("/api/food-cart/{booking_id}", tags=["Food Cart"])\nasync def food_cart_clear(booking_id: str):'

new = '@app.api_route("/api/food-cart/{booking_id}", methods=["DELETE", "POST"], tags=["Food Cart"])\nasync def food_cart_clear(booking_id: str):'

c = c.replace(old, new)

with open('/root/psvibe_api_server/patch_routes.py', 'w') as f:
    f.write(c)

import ast
ast.parse(c)
print('SYNTAX OK')
