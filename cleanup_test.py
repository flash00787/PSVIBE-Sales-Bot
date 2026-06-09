import os, sys
sys.path.insert(0, '/root/psvibe_api_server')
from mysql_db import execute as _me, query as _mq

# Clean up test data
_me("DELETE FROM console_booking WHERE console_id='C-TEST'")
_me("UPDATE console_status SET status='Free', current_member=NULL, current_game=NULL, start_time=NULL WHERE console_id='C-02'")
_me("DELETE FROM console_booking WHERE id=257")
print('Cleaned up')

cs = _mq("SELECT status FROM console_status WHERE console_id='C-02'")
print('C-02 status:', cs[0]['status'])
