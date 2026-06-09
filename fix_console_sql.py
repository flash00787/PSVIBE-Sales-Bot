import base64, json, sys

with open('/root/psvibe_api_server/dashboard_routes.py', 'r') as f:
    content = f.read()

old_sql = """        rows = _mysql_query(\"\"\"
            SELECT c.console_id as id, c.console_id as name, c.status,
                   cb.id as booking_id, cb.member_id as customer_name,
                   cb.start_time, cb.end_time, cb.status as booking_status
            FROM console_status c
            LEFT JOIN console_booking cb ON c.console_id = cb.console_id
                AND DATE(cb.booking_date) = %s
                AND cb.status IN ('Active', 'Confirmed')
                AND c.status = 'Active'
            ORDER BY c.console_id
        \"\"\", (today,))"""

new_sql = """        rows = _mysql_query(\"\"\"
            SELECT c.console_id as id, c.console_id as name, c.status,
                   cb.id as booking_id, cb.member_id as customer_name,
                   cb.start_time, cb.end_time, cb.status as booking_status
            FROM console_status c
            LEFT JOIN (
                SELECT cb1.*
                FROM console_booking cb1
                INNER JOIN (
                    SELECT console_id, MAX(id) as max_id
                    FROM console_booking
                    WHERE DATE(booking_date) = %s
                    AND status IN ('Active', 'Confirmed')
                    GROUP BY console_id
                ) cb2 ON cb1.id = cb2.max_id
            ) cb ON c.console_id = cb.console_id
                AND c.status = 'Active'
            ORDER BY c.console_id
        \"\"\", (today,))"""

content = content.replace(old_sql, new_sql)

with open('/root/psvibe_api_server/dashboard_routes.py', 'w') as f:
    f.write(content)

print("SQL query updated - now uses subquery to get only latest booking per console")
