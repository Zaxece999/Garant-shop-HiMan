class KEnglish:

    def __init__(self) -> None:

        self.kb = {

            0: '⬅ Back',
            1: '❌ Cancel',
            2: '❌ Hide',
            'menu': '🧑‍💻 Menu',

            'admin': '👑 Admin',
            'start deal': '🆕 New a deal',
            'all deals': '🗂 All deals',
            'refill balance': '💳 Top Up',
            'information': 'ℹ️ Info',
            'my profile': '👤 Profile',
            'withdrawal': '💰 Withdrawal',
            'shop': '🛒 Shop',
            'chat': '💬 CHAT',

            30: '➡️ Pay',
            31: '✅ Check payment',
            32: '👤 Transfer the balance',

            70: '👤 Admin/Support',
            71: '👥 Ref. system',
            73: '💠 Share this link',
            74: '🔐 Rules',
            75: '📖 Instructions',
            76: '🌐 Change Language',

            100: '⚡ Start',
            101: '💫 Reviews {count_reviews} | {avg_percent} ⭐',
            102: '🛍️ Buyer',
            103: '👨‍💼 Seller',
            104: '✅ Start',
            105: '👎 Reject',
            106: '❌ Cancel',
            107: '❌ Deal canceled',

            200: '🕊️ Send message',
            201: '✅ Complete',
            202: '🔴 Cancel',
            203: '⚖️ Open dispute',
            204: '📨 Reply',
            205: '✅ You have confirmed',
            206: 'Are you sure?',

            300: '⭐ Leave a review',

            400: '⬅️ Back',
            401: '➡️ Next',
            402: '{icon_deal} #{deal_uniq_id}, {price:.2f}$',

            500: '🧾 CryptoBot receipt',
            501: '🧾 xRocket receipt',

            599: '',

            700: '🔗 Link',

            600: '⭐️ Reviews',
            601: '⭐ [{rating}/5] {from_user_id}',
            602: 'You have already left a review for this deal',
            603: 'Review has been saved successfully',
            604: 'An error occurred while saving the review',
            606: '⭐️ Rate the seller:',
            607: '⭐️ Rate the buyer:',
            608: 'Seller: {seller_info}\nBuyer: {buyer_info}',

            800: '🏪 Categories',
            801: '📦 Products',
            802: '🛒 My Orders',
            803: '🏷️ View Category',
            804: '🛍️ Buy Now',
            805: '📦 Add to Inventory',
            806: '✏️ Edit',
            807: '🗑️ Delete',
            808: '➕ Add New',
            809: '📊 Statistics',
            810: '📋 Product Details',
            811: '🔑 Keys / Accounts',
            812: '💲 Price: ${price}',
            813: '🔄 Processing',
            814: '✅ Completed',
            815: '❌ Canceled',
            816: '💳 Pay ${price}',
            817: '⬆️ Top Up Balance',
            818: '📝 Admin Panel',
            819: '🔍 Search',
            820: '📊 Dashboard',
            821: '📦 Available: {quantity}',
            822: '🛒 Order #{order_id}',
            823: '⏱️ Status: {status}',
            824: '📅 Date: {date}',
            825: '💎 Digital Product',
            826: '🔑 Show Key/Account',
            827: 'Item has been added to inventory',
            828: 'Item has been updated',
            829: 'Item has been deleted',
            830: 'Purchase successful! Here is your product:',
            831: 'Insufficient balance. Please top up your balance.',
        }

    def get_text(self, number):
        return self.kb[number]
