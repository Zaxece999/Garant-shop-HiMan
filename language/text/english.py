class English:
    def __init__(self):

        self.en_text = {

            0: '',

            'unknown error': '😟 Unknown error.',
            'insufficient funds': '{smile_money} Insufficient funds on the balance\n'
                                  'You can refill your balance with main menu',

            10: 'ℹ️ User ID: <code>{my_user_id}</code>\n\n'
                '{smile_random} <b>Main menu:</b>',

            'join chat': '💬 Join our group chat!',
            'chat': '💬 CHAT',

            'user statistics': '🧽 <b>User:</b> {user_info}\n'
                            '🪪 ID: {user_id}\n\n'
                            '🤝 <b>Successful</b> transactions: {success_count_deals}\n'
                            '⚖ <b>Disputes lost:</b> {lost_disputes}\n\n'
                            '📈 Total <b>purchase</b> amount: <i>{share_amount_buy:.2f}$</i>\n'
                            '📉 Total <b>sale</b> amount: <i>{share_amount_sell:.2f}$</i>\n\n'
                            '🗂️ <b>Rating: {count_reviews} {word_review} | {avg_percent} ⭐</b>',

            'my profile': '🧽 <b>User:</b> {user_info}\n'
                            '🪪 ID: {user_id}\n'
                            '{smile_money} <b>Balance:</b> {balance:.2f}$\n\n'
                            '🤝 <b>Completed</b> deals: {success_count_deals}\n'
                            '⚖ <b>Disputes lost:</b> {lost_disputes}\n\n'
                            '📈 Total <b>purchases:</b> <i>{share_amount_buy:.2f}$</i>\n'
                            '📉 Total <b>sales:</b> <i>{share_amount_sell:.2f}$</i>\n\n'
                            '🗂️ <b>Rating: {count_reviews} {word_review} | {avg_percent} ⭐</b>',

            30: '{smile_money} Current balance: {balance:.2f}$\n\n'
                '<u>Enter</u> the amount of <u>$</u> to replenish your balance\n'
                'Minimum amount: 1$\n'
                'Example: 10, 0.30, 1.5',
            31: '😐 <u>Error</u>\n\n'
                '<u>Enter</u> the amount of <u>$</u> to replenish your balance\n'
                'Minimum amount: 1$\n'
                'Example: 10, 0.30, 1.5',
            32: '⬇️ <u>Select payment method</u>:',
            33: '⬇️ <u>Pay</u> with the button below:',
            34: '😓 Minimum amount to pay with this method: {amount:.2f}$',
            35: '🧾 This invoice has not been paid. Try checking later',
            36: '✅ The balance has been replenished by +{amount:.2f}$',
            37: '🔧 Error creating payment with this method. Try again later',
            38: '{smile_money} Received <u>bonus</u> {amount:.2f}$',

            70: '🔐<b>Rules for joining the chat</b>\n\n'
                '✅ Sellers must keep $40 on their balance at @ESCROWRBOT to make deals and post ads in the chat. This is necessary to place offers and demonstrate seriousness of intentions\n\n'
                '✅ Buyers can freely spend their $40 — it stays on your balance and is used for deals at @ESCROWRBOT\n\n\n'
                '⚠️ Scammers are removed immediately.\n'
                'We have already done a lot of work, and the results are obvious\n\n'
                'Thank you for understanding and supporting a clean, professional space for real deals.\n'
                'Let\'s turn this into something big together. 🚀\n\n'
                '🛑Join the chat after payment at @ESCROWRBOT',
            72: '{smile_random} <b><a href="{link_admin}">Admin</a></b>',
            73: '💠 Your <u>referral</u> link:\n'
                '{ref_link}\n\n'
                '👥 Invited: {my_count_ref}\n'
                '💸 You will <u>receive</u> {percent_ref}% of every deposit made by your referral to your <u>account</u>',
            74: '<b>Instructions:</b>\n\n'
            '<i>1.</i> Go to the <b>main menu</b> of the bot and press the <u>Start Deal</u> button.\n'
            '<i>2.</i> Enter the @username of the user or User ID from the main menu of the bot.\n'
            '<i>3.</i> If the profile is found in the bot, press the <u>Start</u> button.\n'
            '<i>4.</i> Choose who <b>you</b> will be in this deal. After that, enter the amount and fill in the deal terms.\n'
            '<i>5.</i> Wait for the deal to be accepted by the <b>second</b> user.\n'
            '<i>6.</i> Use the buttons in the active deal.',
            76: '🌐 Change Language',
            400: '{smile_money} You don\'t have enough funds to transfer!',
            401: '<i>User ID can be found in the bot\'s main menu</i>\n\n'
                '⬇ Enter the <u>User ID</u> of the person you want to transfer {balance:.2f}$',
            402: '🤨 User with this <u>User ID</u> not found',
            403: '🏦 Transaction <u>successfully completed</u>\n\n'
                '<b>Transfer ID:</b> #{transfer_id}\n'
                '<b>Amount:</b> {amount:.2f}$',
            404: '🏦 You received a transfer of {amount:.2f}$ from <code>{nickname}</code>\n\n'
                '<b>Transfer ID:</b> #{transfer_id}',
            405: '🤧 Transfer to yourself is not possible',
            406: '{smile_money} Your current balance: {balance:.2f}$\n\n'
                'Enter the <u>amount</u> in <u>$</u> to transfer 🏦\n'
                'Example: 10, 0.30, 1.5',
            407: '🤒 You have <u>insufficient funds</u> for the transfer',
            408: '👺 <b>Amount</b> cannot be zero or less!',
            409: '🔥 Minimum transfer amount: {min_transfer:.2f}$',

            'deal enter user': '🪪 @username | UserID',
            500: '⬇️ <u>Enter</u> @username or User ID:',
            501: '{smile_angry} Could not <u>find</u> this user. Try again:',
            502: '😐 The user has too many deals open',
            503: '😐 Start a deal with yourself?',
            504: '⬇️ <b>Who</b> will you <u>be</u> in this deal?',
            505: '{smile_money} Top up your balance to create a deal from the bot menu',
            5051: '💰 To create a sale, you need at least {min_seller_balance:.2f}$ on your balance',
            506: '⬇ Enter the amount in <u>$</u> for <b>creating</b> a purchase deal:',
            507: '⬇ Enter the amount in <u>$</u> for <b>creating</b> a sale deal:',
            508: '👺 The deal <b>amount</b> must be a number!',
            509: '👺 The deal <b>amount</b> cannot be zero or less than <u>{min_amount:.2f}</u>$!',
            510: '⬇️ Enter the <u>terms</u> of this deal:',
            511: '🙁 The deal <u>terms</u> are too short. Enter <b>more</b> information:',

            'purchaser': 'Buyer',
            'seller': 'Seller',
            512: '📫 <b>A request for a deal</b> has been received:\n'
                'Number: #{uniq_id}\n\n'
                'From: {from_user_info}\n'
                '🪪 ID: {from_user_id}\n\n'
                '<b>You:</b> <u>{who_im_in_deal}</u>\n'
                '<b>Him:</b> {who_him_in_deal}\n'
                '<b>Amount:</b> {amount:.2f}$\n\n'
                '<b>Terms:</b> {description}',
            513: '✅ Offer <u>sent</u>\n'
                'Number: #{uniq_id}\n\n'
                '<b>User</b>: {nickname_user_2}\n\n'
                'Wait for the 🤖 <b>bot</b> notification',
            514: '🙁 The user <u>failed</u> to send a message about the new <b>deal</b>',
            515: '',
            516: '{smile_angry} Please wait another {how_much} to create a new deal',
            517: '🥱 This deal can no longer be canceled',
            518: '🤕 You have <u>canceled</u> this deal',
            519: '🤨 {nickname_user_1} canceled this deal {when_end} ago',
            520: '😕 To create this deal, <b>top up your balance</b> by {need_amount:.2f}$',
            521: '{smile_angry} {nickname_user} has <u>rejected</u> deal #{uniq_id}',
            522: '🫤 You do not have this amount on your balance for purchase. You can top up your balance from the main menu',
            523: '🫤 The second user does not have {need_amount:.2f}$ on their balance to start the deal',

            600: '🔥 <b>Deal:</b> #{uniq_id}\n\n'
                'Seller: {who_seller_nickname}\n'
                'Buyer: {who_buyer_nickname}\n\n'
                '<u>Amount:</u> {amount:.2f}$\n'
                'Terms: <i>{description}</i>\n\n'
                '📸 <i>Document important events with videos or photos. They will help you in case of a dispute.</i>',
            601: '🫡 This deal has already been canceled and it is not possible to write in the chat',
            602: '🫡 This deal has already been completed and it is not possible to write in the chat',
            603: '',
            604: '⚖️ A dispute has been opened on this deal and it is not possible to write in the chat',
            605: '🕊️ Enter a <b>message</b> for user {nickname_user}',
            606: '🔴 This deal has already been canceled',
            607: '🗂️ This deal has already been closed',
            608: '⚖️ A dispute has been opened on this deal. No actions are possible until the issue is resolved',
            609: '📬 An offer to <b>close the deal</b> has been sent to user {nickname_user}',
            610: '📫 A request has been received to ✅ <u>complete</u> the deal\n'
                '<b>Number:</b> #{uniq_id}\n\n'
                'Seller: {who_seller_nickname}\n'
                'Buyer: {who_buyer_nickname}\n\n'
                '<u>Amount:</u> {amount:.2f}$\n'
                'Terms: <i>{description}</i>\n\n'
                '⚠️ <i>Make sure the deal was successful. After confirmation, it will not be possible to start a dispute.</i>',
            611: '🙁 Missing <b>text</b> for the user',
            612: '✉️ Message from {nickname_user}\n'
                '<b>Deal:</b> #{uniq_id}\n\n'
                '<i>{message}</i>',
            613: '🫤 Failed to <u>deliver</u> the message to this user. Please try again',
            614: '✅ Message <b>sent</b>',
            615: '✅ Confirmation message for deal #{uniq_id} sent!\n\n'
                '{smile_time} Waiting for confirmation from {nickname_user}',
            616: '⚠️ Are you sure you want to <b>confirm</b> deal #{uniq_id}?\n\n'
                '<i>If the deal terms are not met, starting a dispute will not be possible.</i>',
            617: '✅ You have already confirmed the deal',
            618: '🫤 Failed to <u>deliver</u> the confirmation message to this user. Please try again',
            619: '✅ Deal <u>completed</u>\n'
                '<b>Number:</b> #{uniq_id}\n\n'
                'Seller: {who_seller_nickname}\n'
                'Buyer: {who_buyer_nickname}\n\n'
                '<u>Amount:</u> {amount:.2f}$\n'
                'Terms: <i>{description}</i>\n\n'
                '{smile_time} Deal completed in {how_long_complete}\n\n'
                '⭐ Don\'t forget to leave a review for {nickname_user}',
            620: '{smile_money} Balance for deal #{uniq_id} has been credited with +{final_amount:.2f}$\n\n'
                '<u>Deal amount</u>: {amount:.2f}$\n'
                'Dispute fee: {percent_disput}%\n\n'
                'Total: {amount:.2f}$ - ({percent_amount_service:.2f}$ + {percent_amount_disput:.2f}$) <u>=</u> {final_amount:.2f}$',
            621: '🥲 You have already left a review for {nickname_user}',
            622: '⭐ Rate user {nickname_user}',
            623: '📝 Write your <u>review</u> about {nickname_user}:',
            624: '🙁 Missing <b>text</b> for the review',
            625: '👍 <b>Review</b> for {nickname_user} is ready\n\n'
                '☕ Thank you for your <b>cooperation</b>',
            626: '👌 Good review',
            627: '⚠️ Are you sure you want to <b>cancel</b> deal #{uniq_id}?\n\n'
                '<i>If the deal terms are not met, starting a dispute will not be possible.</i>',
            628: '❌ Deal #{uniq_id} was canceled with the agreement of both parties\n\n'
                'Seller: {who_seller_nickname}\n'
                'Buyer: {who_buyer_nickname}\n\n'
                '⭐ Don\'t forget to leave a review for {nickname_user}',
            629: '📫 A request has been received to 🔴 <u>cancel</u> the deal\n'
                '<b>Number:</b> #{uniq_id}\n\n'
                'Seller: {who_seller_nickname}\n'
                'Buyer: {who_buyer_nickname}\n\n'
                '<u>Amount:</u> {amount:.2f}$\n'
                'Terms: <i>{description}</i>',
            630: '✅ Cancellation message for deal #{uniq_id} sent!\n\n'
                '{smile_time} Waiting for confirmation from {nickname_user}',
            631: '📝 Describe the <u>situation</u> due to which {nickname_user} did not meet the deal terms',
            632: '🗂️ This deal has already been closed. It is not possible to open a dispute',
            633: '⚖️ A dispute on this deal has already been opened by user {nickname_user}',
            634: '⚠️ User {nickname_user} has <u>opened a dispute</u> on deal #{deal_uniq_id}\n\n'
                '🏔️ This deal will be <b>frozen</b> until the dispute is resolved by the administrator.\n\n'
                'Please wait for the <u>notification</u> from the bot with a link to join the chat for resolving this dispute',
            635: '⚠️ You have <u>opened a dispute</u> on deal #{deal_uniq_id}\n\n'
                '🏔️ This deal will be <b>frozen</b> until the dispute is resolved by the administrator.\n\n'
                'Please wait for the <u>notification</u> from the bot with a link to join the chat for resolving this dispute',
            636: '🔴 You have already sent a cancellation request for the deal',

            700: '😟 You have no <b>active</b> deals',
            701: '⬇️ <u>Your deals</u>',
            702: '📃 <b>Page:</b> {page_number}',

            800: '{smile_spanch} Withdrawal is <b>possible</b> only from {need_amount:.2f}$',
            801: '{smile_money} Current balance: {balance:.2f}$\n\n'
                'Enter the <u>amount</u> in <u>$</u> for withdrawal\n'
                'Example: 10, 4.5, 4.50\n\n'
                '🔥 <b>Minimum</b> withdrawal: {min_withdrawal:.2f}$',
            802: '😐 You have entered the withdrawal amount <b>incorrectly</b>',
            803: '🔥 <b>Minimum</b> withdrawal amount — {min_withdrawal:.2f}$',
            804: '😥 You do not have this amount for withdrawal\n'
                '{smile_money} <b>Balance:</b> {balance:.2f}$',
            805: '⚠️ <b>Percent</b> of service: {percent_amount_service:.2f}$\n\n'
                '⬇️ <b>Select</b> the withdrawal method for {amount:.2f}$:',
            806: '😿 You do not have this amount available for withdrawal',
            807: '📫 <b>Withdrawal request</b>: #{uniq_id}\n'
                '<u>Amount:</u> {amount:.2f}$\n\n'
                '{smile_time} Please wait for the <b>notification</b> from 🤖 <u>the bot</u>',
            808: '🔗 Withdrawal <u>link</u>: {link}',

            900: '😟 No reviews',
            901: '📃 <b>Page:</b> {page_number}',
            902: '✍️ From: {nickname_user}\n\n'
                '<i>{message}</i>\n\n'
                '{smile_time} Written {when_write} ago',
            903: 'The user did not leave a comment.',

            1000: '🔗 <a href="{link}">Link</a> to join the chat for <u>resolving</u> the issue on deal #{deal_uniq_id}\n\n'
                '➡️ {link}',
            1001: '⚖️ The dispute on deal #{deal_uniq_id} was closed in favor of {who_win_disput_user}',

            1002: '⬇️ <b>Channel link</b>',

            1003: 'Top-up',
            1004: '⬇️ Click the button below to pay your bill:',
            1005: 'Min amount for the Stars ⭐: {min_amount:.2f}$',
            666: '✅ Deal #{deal_uniq_id} successfully completed\n\nSeller: {seller_info}\nBuyer: {buyer_info}\n\n⭐️ Don\'t forget to leave a review for {nickname_user}',
            667: '⭐ Reviews',
            668: '⭐ [{rating}/5] {from_user_id}',
            669: 'You have already left a review for this deal',
            670: 'Review has been saved successfully',
            671: 'An error occurred while saving the review',
            672: '⭐️ Rate the seller:',
            673: '⭐️ Rate the buyer:',
            674: 'Seller: {seller_info}\nBuyer: {buyer_info}',
            675: '✅ Deal #{deal_uniq_id} successfully completed\n\nSeller: {seller_info}\nBuyer: {buyer_info}\n\n⭐️ Thank you for your review',
            2000: '🔥 Minimum withdrawal amount is — {min_withdrawal:.2f}$',
            2001: '😐 You <b>entered</b> the withdrawal amount <b>incorrectly</b>',
            2002: '😥 You do not have enough funds for withdrawal\n{smile_money} <b>Your balance:</b> {balance:.2f}$',
            2003: '⚠️ <b>Service fee</b> will be: {percent_amount_service:.2f}$\n\n⬇️ <b>Select</b> the withdrawal method for {amount:.2f}$:',
            2004: '😿 You do not have the required amount for withdrawal',
            2005: '📫 <b>Withdrawal request</b>: #{uniq_id}\n<u>Amount:</u> {amount:.2f}$\n\n{smile_time} Please wait for the <b>notification</b> from 🤖 <u>the bot</u>',
            2006: '🔗 Your <u>withdrawal</u> link: {link}',
            2007: '🔥 Minimum withdrawal amount is — {min_withdrawal:.2f}$',
            2008: '😐 You <b>entered</b> the withdrawal amount <b>incorrectly</b>',
            2009: '😥 You do not have enough funds for withdrawal\n{smile_money} <b>Your balance:</b> {balance:.2f}$',
            2010: '⚠️ <b>Service fee</b> will be: {percent_amount_service:.2f}$\n\n⬇️ <b>Select</b> the withdrawal method for {amount:.2f}$:',
            2011: '😿 You do not have the required amount for withdrawal',
            2012: '📫 <b>Withdrawal request</b>: #{uniq_id}\n<u>Amount:</u> {amount:.2f}$\n\n{smile_time} Please wait for the <b>notification</b> from 🤖 <u>the bot</u>',
            2013: '🔗 Your <u>withdrawal</u> link: {link}',
            2014: '💸 Withdrawal request #{withdrawal_id}\n\n',
            2015: '✅ Your withdrawal has been successfully processed!\n\n',
            2016: '🔥 Minimum transfer amount: {min_transfer}$',
            2017: '🌐 Select network for {currency}:',
            2018: '✅ Payment already processed. Your balance is {balance}$ {smile_money}',
            2019: '✅ Payment received! Your balance has been topped up by {amount}$ {smile_money}',
            2020: '💸 Fund Transfer',
            2021: '🔄 Transfer History',
            2022: '✅ Transfer #{transfer_id} successfully sent\n\n'
                  '<b>Recipient:</b> {recipient_info}\n'
                  '<b>Amount:</b> {amount:.2f}$\n'
                  '<b>Date:</b> {date}',
            2023: '📥 Incoming transfer #{transfer_id}\n\n'
                  '<b>Sender:</b> {sender_info}\n'
                  '<b>Amount:</b> {amount:.2f}$\n'
                  '<b>Date:</b> {date}',
            2024: '📤 Outgoing transfer #{transfer_id}\n\n'
                  '<b>Recipient:</b> {recipient_info}\n'
                  '<b>Amount:</b> {amount:.2f}$\n'
                  '<b>Date:</b> {date}',
            2025: '📋 <b>Transfer history:</b>\n\n{transfers_list}',
            2026: '😕 You have no transfer history',
            2027: '⚠️ Error processing transfer. Please try again later.',
            2028: '💳 Enter the user ID or @username of the recipient:',
            2029: '💰 Enter the transfer amount:',
            2030: '✅ Confirm transfer of {amount:.2f}$ to user {recipient_info}',
            2031: '💰 Choose cryptocurrency for top-up:',
            2032: '🔒 <b>Invoice #{invoice_id}</b>\n\n'
                  '<b>Payment address:</b>\n'
                  '<code>{payment_address}</code>\n\n'
                  '<b>Amount:</b> <code>{crypto_amount}</code> {currency}\n'
                  '<b>Network:</b> {network}\n\n'
                  '‼️ <b>After transferring, click the \'Check\' button</b> ‼️\n'
                  'Transfer the exact amount to avoid losing money!\n'
                  'Consider the network fee!',
            2033: '❌ Error: top-up amount not specified. Please start the process again.',
            2034: '❌ Error creating invoice. Please try again later.',
            2035: '❌ Error creating payment. Please try again later.',
            2036: '❌ Error checking payment. Please try again later.',
            2037: '❌ Payment not completed. Please complete the payment and try again.',
            2038: '✅ Payment already processed and credited to your balance!',
            2039: '⚠️ Payment status unknown: {status}. Please contact support.',
            2040: '⚠️ Payment confirmed, but invoice not found in the system. Please contact support.',
            2041: '⚠️ Invalid USDT BEP20 wallet address format. Address should start with \'0x\' and be 42 characters long.',
            2042: '⚠️ An error occurred. Please try again.',
            2043: '✅ Check payment',
            2044: '💼 Please enter your USDT BEP20/ERC20 wallet address for withdrawal:',

        }
