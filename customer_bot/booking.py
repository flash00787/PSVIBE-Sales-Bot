# /root/psvibe-sales-bot/customer_bot/booking.py
# Stub module — commands will be implemented in next phase
import logging
logger = logging.getLogger(__name__)

async def cmd_mybookings(update, context):
    await update.message.reply_text("Your bookings feature coming soon!")

async def cmd_refer(update, context):
    await update.message.reply_text("Referral feature coming soon!")

async def cmd_waitlist(update, context):
    await update.message.reply_text("Waitlist feature coming soon!")
