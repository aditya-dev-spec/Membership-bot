import os
import logging
import qrcode
import config
from io import BytesIO
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment variables (for deployment) or config.py
BOT_TOKEN = os.environ.get('BOT_TOKEN', config.BOT_TOKEN)
UPI_ID = os.environ.get('UPI_ID', config.UPI_ID)
ADMIN_ID = int(os.environ.get('ADMIN_ID', config.ADMIN_ID))
PORT = int(os.environ.get('PORT', 8443))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

# Define states for conversation
SELECT_PLAN, PAYMENT_CONFIRMATION, UPLOAD_SCREENSHOT = range(3)

# Membership plans with duration in days
PLANS = {
    "1_month": {
        "name": "1 Month Premium",
        "price": 99,
        "duration": 30,
        "description": "Access to all premium groups for 1 month"
    },
    "3_months": {
        "name": "3 Months Premium",
        "price": 249,
        "duration": 90,
        "description": "Access to all premium groups for 3 months (Save ₹48)"
    },
    "6_months": {
        "name": "6 Months Premium",
        "price": 499,
        "duration": 180,
        "description": "Access to all premium groups for 6 months (Save ₹95)"
    }
}

# Store temporary user data (in production, use a database)
user_sessions = {}

async def delete_previous_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete previous bot message to keep chat clean"""
    if 'last_message_id' in context.user_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['last_message_id']
            )
        except:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send welcome message with plan selection"""
    await delete_previous_message(update, context)
    
    keyboard = [
        [InlineKeyboardButton("1 Month - ₹99", callback_data="plan_1_month")],  # Fixed price
        [InlineKeyboardButton("3 Months - ₹249", callback_data="plan_3_months")],  # Fixed price
        [InlineKeyboardButton("6 Months - ₹499", callback_data="plan_6_months")],  # Fixed price
        [InlineKeyboardButton("ℹ️ How It Works", callback_data="how_it_works")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = await update.message.reply_text(
        "🎟️ *Premium Membership Subscription*\n\n"
        "Select your plan to proceed:\n\n"
        "✅ Access to exclusive content\n"
        "✅ Priority support\n"
        "✅ All premium groups\n"
        "✅ Regular updates\n\n"
        "_Choose a plan below:_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    context.user_data['last_message_id'] = message.message_id
    return SELECT_PLAN

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle plan selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "how_it_works":
        await how_it_works(update, context)
        return SELECT_PLAN
    
    plan_key = query.data.replace("plan_", "")
    plan = PLANS[plan_key]
    
    # Store user selection
    user_sessions[query.from_user.id] = {
        'plan': plan_key,
        'selected_at': datetime.now().isoformat(),
        'user_id': query.from_user.id,
        'username': query.from_user.username
    }
    
    await delete_previous_message(update, context)
    
    # Generate UPI payment QR code
    upi_url = f"upi://pay?pa={UPI_ID}&pn=Premium%20Membership&am={plan['price']}&cu=INR&tn={plan['name']}%20Subscription"
    
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    
    # Send QR code with payment instructions
    keyboard = [
        [InlineKeyboardButton("✅ I Have Paid", callback_data="payment_done")],
        [InlineKeyboardButton("🔙 Change Plan", callback_data="change_plan")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = await context.bot.send_photo(
        chat_id=query.from_user.id,
        photo=bio,
        caption=f"*{plan['name']} - ₹{plan['price']}*\n\n"
                f"📋 *Plan Details:*\n"
                f"{plan['description']}\n\n"
                f"💳 *Payment Instructions:*\n"
                f"1. Scan QR code with any UPI app\n"
                f"2. Pay ₹{plan['price']} to:\n"
                f"   `{UPI_ID}`\n"
                f"3. Click 'I Have Paid' below\n"
                f"4. Upload payment screenshot with UTR\n\n"
                f"⚠️ *Important:* Keep payment screenshot with UTR number ready!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    context.user_data['last_message_id'] = message.message_id
    return PAYMENT_CONFIRMATION

async def how_it_works(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show how it works"""
    query = update.callback_query
    await query.answer()
    
    await delete_previous_message(update, context)
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Plans", callback_data="back_to_plans")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = await query.edit_message_text(
        "📋 *How It Works:*\n\n"
        "1️⃣ *Select Plan* - Choose your membership duration\n"
        "2️⃣ *Make Payment* - Scan QR code with any UPI app\n"
        "3️⃣ *Upload Proof* - Send payment screenshot with UTR number\n"
        "4️⃣ *Verification* - We verify your payment (20 minutes)\n"
        "5️⃣ *Get Access* - Automatically added to premium groups\n\n"
        "⏰ *Verification Time:* 20 minutes maximum\n"
        "✅ *Instant Access:* After verification\n"
        "🔄 *Refund:* Only if verification fails\n\n"
        "_Click below to continue:_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    context.user_data['last_message_id'] = message.message_id

async def payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment confirmation"""
    query = update.callback_query
    await query.answer()
    
    await delete_previous_message(update, context)
    
    message = await context.bot.send_message(
        chat_id=query.from_user.id,
        text="📤 *Upload Payment Proof*\n\n"
             "Please upload/forward the payment screenshot *with UTR number visible*.\n\n"
             "⚠️ *Requirements:*\n"
             "• Screenshot must show UPI transaction\n"
             "• UTR number must be visible\n"
             "• Amount should match selected plan\n"
             "• Timestamp should be recent\n\n"
             "_Send the screenshot now:_",
        parse_mode='Markdown'
    )
    
    context.user_data['last_message_id'] = message.message_id
    return UPLOAD_SCREENSHOT

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle uploaded screenshot"""
    if not update.message or not update.message.photo:
        await update.message.reply_text("Please send a screenshot image.")
        return UPLOAD_SCREENSHOT
    
    await delete_previous_message(update, context)
    
    # Get user data
    user_id = update.message.from_user.id
    user_data = user_sessions.get(user_id, {})
    
    # Notify admin
    admin_text = (
        f"🔄 *New Payment Verification*\n\n"
        f"👤 User: @{update.message.from_user.username or 'N/A'}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📋 Plan: {PLANS[user_data['plan']]['name']}\n"
        f"💰 Amount: ₹{PLANS[user_data['plan']]['price']}\n"
        f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    try:
        # Forward screenshot to admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode='Markdown'
        )
        
        # Forward the photo
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id
        )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
    
    # Send confirmation to user
    message = await update.message.reply_text(
        "✅ *Payment Received!*\n\n"
        "📋 *Your Membership is Under Verification*\n"
        "⏰ *Time:* Up to 20 minutes\n\n"
        "🔍 *What happens next:*\n"
        "1. We verify your payment\n"
        "2. Check UTR number\n"
        "3. Confirm amount\n"
        "4. Add you to premium groups\n\n"
        "✅ *As verification completes, you will automatically be joined to the group.*\n\n"
        "📬 You will receive a confirmation message here.\n"
        "🔄 No further action required from your side.",
        parse_mode='Markdown'
    )
    
    context.user_data['last_message_id'] = message.message_id
    
    # Clear conversation
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation"""
    await delete_previous_message(update, context)
    
    message = await update.message.reply_text(
        "❌ Process cancelled. Type /start to begin again."
    )
    
    context.user_data['last_message_id'] = message.message_id
    return ConversationHandler.END

async def change_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to plan selection"""
    query = update.callback_query
    await query.answer()
    
    # Clear current session
    user_id = query.from_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    # Send plan selection again
    await start_from_callback(update, context)
    return SELECT_PLAN

async def start_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command for callback queries"""
    query = update.callback_query
    await query.answer()
    
    await delete_previous_message(update, context)
    
    keyboard = [
        [InlineKeyboardButton("1 Month - ₹99", callback_data="plan_1_month")],  # Fixed price
        [InlineKeyboardButton("3 Months - ₹249", callback_data="plan_3_months")],  # Fixed price
        [InlineKeyboardButton("6 Months - ₹499", callback_data="plan_6_months")],  # Fixed price
        [InlineKeyboardButton("ℹ️ How It Works", callback_data="how_it_works")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = await context.bot.send_message(
        chat_id=query.from_user.id,
        text="🎟️ *Premium Membership Subscription*\n\nSelect your plan:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    context.user_data['last_message_id'] = message.message_id

async def back_to_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to plans from how it works"""
    query = update.callback_query
    await query.answer()
    await start_from_callback(update, context)

def main() -> None:
    """Start the bot in webhook mode."""
    
    # Check if BOT_TOKEN is set
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("BOT_TOKEN is not set! Please set it in environment variables or config.py")
        return
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_PLAN: [
                CallbackQueryHandler(select_plan, pattern="^plan_"),
                CallbackQueryHandler(how_it_works, pattern="^how_it_works$"),
                CallbackQueryHandler(back_to_plans, pattern="^back_to_plans$"),
            ],
            PAYMENT_CONFIRMATION: [
                CallbackQueryHandler(payment_done, pattern="^payment_done$"),
                CallbackQueryHandler(change_plan, pattern="^change_plan$"),
                CallbackQueryHandler(start_from_callback, pattern="^back_to_plans$"),
            ],
            UPLOAD_SCREENSHOT: [
                MessageHandler(filters.PHOTO, handle_screenshot),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="membership_conversation",
        persistent=False
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    
    # Webhook mode for deployment
    if WEBHOOK_URL:
        logger.info(f"Starting bot in webhook mode on port {PORT}")
        logger.info(f"Webhook URL: {WEBHOOK_URL}")
        
        # Set webhook
        async def set_webhook_on_startup(app):
            await app.bot.set_webhook(
                url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
                drop_pending_updates=True
            )
            logger.info("Webhook set successfully")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            url_path=BOT_TOKEN,
            secret_token='WEBHOOK_SECRET',  # Optional security
            drop_pending_updates=True
        )
    else:
        # Polling mode for local development
        logger.info("Starting bot in polling mode (local development)")
        application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
