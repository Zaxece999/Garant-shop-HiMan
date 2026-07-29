import configparser
from typing import TYPE_CHECKING

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.types.keyboard_button import KeyboardButton

from language.keyboard.russian import KRussian
from language.keyboard.english import KEnglish


class UserKeyboard(KRussian, KEnglish):
    def __init__(self, config: configparser.ConfigParser):

        self.config = config
        self.KRussian = KRussian()
        self.KEnglish = KEnglish()

    def get_text(self, key, user = None):

        if user is None:
            buttons = []
            for keyboard in [self.KRussian, self.KEnglish]:
                buttons.append(keyboard.get_text(number=key))
            return buttons

        elif user.lang == 'ru':
            return self.KRussian.get_text(key)
        elif user.lang == 'en':
            return self.KEnglish.get_text(key)

    def paginate(self, list_model, page_size):
        return [list_model[i:i + page_size] for i in range(0, len(list_model), page_size)]

    def btn_hide(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(2, user), callback_data='hide'))
        return kb.as_markup()

    def btn_cancel(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(1, user), callback_data='cancel'))
        return kb.as_markup()

    def btn_menu(self, user):
        kb = ReplyKeyboardBuilder()
        kb.row(KeyboardButton(text=self.get_text('chat', user)))
        kb.row(KeyboardButton(text=self.get_text('menu', user)))
        return kb.as_markup(resize_keyboard=True)

    def btn_menu_inline(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text('menu', user), callback_data='go_to_menu'))
        return kb.as_markup()

    def btn_back(self, user, callback):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data=callback))
        return kb.as_markup()

    def main_menu(self, user):
        kb = ReplyKeyboardBuilder()

        if user.admin > 0:
            kb.row(KeyboardButton(text=self.get_text('admin', user)))

        kb.row(KeyboardButton(text=self.get_text('start deal', user)))
        kb.row(
            KeyboardButton(text=self.get_text('all deals', user)),
            KeyboardButton(text=self.get_text('refill balance', user)))
        kb.row(
            KeyboardButton(text=self.get_text('information', user)),
            KeyboardButton(text=self.get_text('my profile', user)))
        kb.row(
            KeyboardButton(text=self.get_text('withdrawal', user)),
            KeyboardButton(text=self.get_text('shop', user)))
        kb.row(KeyboardButton(text=self.get_text('chat', user)))

        return kb.as_markup(resize_keyboard=True)

    def info_menu(self, user):
        kb = ReplyKeyboardBuilder()

        kb.row(
            KeyboardButton(text=self.get_text(75, user)),
            KeyboardButton(text=self.get_text(74, user)))

        kb.row(
            KeyboardButton(text=self.get_text(76, user)),
            KeyboardButton(text=self.get_text(70, user)))

        kb.row(KeyboardButton(text=self.get_text('menu', user)))
        return kb.as_markup(resize_keyboard=True)

    def info_inline_admin(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="Admin", url=self.config['LINKS']['admin']))
        return kb.as_markup()

    def my_ref(self, user, ref_link):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(73, user), url=f'https://t.me/share/url?url={ref_link}'))
        return kb.as_markup()

    def get_top_up_balance(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(22, user), callback_data='getTopUpBalance'))
        kb.row(InlineKeyboardButton(text=self.get_text(2, user), callback_data='hide'))
        return kb.as_markup()

    def choice_merchant_top_up(self, user, amount):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(text='💸 Crypto Payment', callback_data=f'topUpHeleket'))
        kb.row(InlineKeyboardButton(text=self.get_text(1, user), callback_data='cancel'))

        return kb.as_markup()

    def choose_heleket_currency(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text='💰 USDT', callback_data='heleket_currency_USDT'))
        kb.row(InlineKeyboardButton(text='₿ BTC', callback_data='heleket_currency_BTC'))
        kb.row(InlineKeyboardButton(text='Ξ ETH', callback_data='heleket_currency_ETH'))
        kb.row(InlineKeyboardButton(text='Ł LTC', callback_data='heleket_currency_LTC'))
        kb.row(InlineKeyboardButton(text=self.get_text(1, user), callback_data='cancel'))
        return kb.as_markup()

    def choose_heleket_network(self, user, currency):
        kb = InlineKeyboardBuilder()

        if currency == 'USDT':
            kb.row(InlineKeyboardButton(text='🔄 TRC20', callback_data='heleket_network_TRON'))
            kb.row(InlineKeyboardButton(text='🔄 ERC20', callback_data='heleket_network_ERC20'))
            kb.row(InlineKeyboardButton(text='🔄 BEP20 (BSC)', callback_data='heleket_network_BEP20'))
        elif currency == 'BTC':
            kb.row(InlineKeyboardButton(text='🔄 Bitcoin', callback_data='heleket_network_BTC'))
            kb.row(InlineKeyboardButton(text='🔄 Lightning Network', callback_data='heleket_network_LIGHTNING'))
        elif currency == 'ETH':
            kb.row(InlineKeyboardButton(text='🔄 Ethereum', callback_data='heleket_network_ETH'))
        elif currency == 'LTC':
            kb.row(InlineKeyboardButton(text='🔄 Litecoin', callback_data='heleket_network_LTC'))

        kb.row(InlineKeyboardButton(text=self.get_text(1, user), callback_data='cancel'))
        return kb.as_markup()

    def heleket_check_payment(self, user, invoice_id):
        kb = InlineKeyboardBuilder()
        from init import convert
        kb.row(InlineKeyboardButton(text=convert.cv(2043, user), callback_data=f'heleket_check_{invoice_id}'))
        kb.row(InlineKeyboardButton(text=self.get_text(1, user), callback_data='cancel'))
        return kb.as_markup()

    def link_pay(self, user, link, check=False):
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text=self.get_text(30, user), url=link))

        if check is not False:
            kb.row(InlineKeyboardButton(text=self.get_text(31, user), callback_data=f'checkPayment_{check}'))

        return kb.as_markup()

    def refill_balance(self, user):
        kb = ReplyKeyboardBuilder()
        kb.row(KeyboardButton(text=self.get_text('menu', user)))
        return kb.as_markup(resize_keyboard=True)

    def start_deal(self, user, user_id_2, count_reviews, rating):
        kb = InlineKeyboardBuilder()

        if user.user_id != user_id_2:
            kb.add(InlineKeyboardButton(text=self.get_text(100, user), callback_data=f'startDeal_{user_id_2}'))

        kb.add(
            InlineKeyboardButton(text=self.get_text(101, user).format(
                count_reviews=count_reviews,
                avg_percent=rating
            ),
            callback_data=f'checkReviews_{user_id_2}'))
        return kb.as_markup()

    def select_whoim_in_deal(self, user, user_id_2):
        kb = InlineKeyboardBuilder()
        kb.add(
            InlineKeyboardButton(text=self.get_text(102, user), callback_data=f'selectTypeDeal_purchase_{user_id_2}'),
            InlineKeyboardButton(text=self.get_text(103, user), callback_data=f'selectTypeDeal_sell_{user_id_2}'))
        kb.row(InlineKeyboardButton(text=self.get_text(2, user), callback_data='hide'))
        return kb.as_markup()

    def cancel_deal(self, user, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text=self.get_text(106, user), callback_data=f'declineDeal_{deal_uniq_id}'))
        return kb.as_markup()

    def accept_or_decline_deal(self, user, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        kb.add(
            InlineKeyboardButton(text=self.get_text(104, user), callback_data=f'acceptDeal_{deal_uniq_id}'),
            InlineKeyboardButton(text=self.get_text(105, user), callback_data=f'declineDeal_{deal_uniq_id}'))
        return kb.as_markup()

    def panel_deal(self, user, deal, confirm=False):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(text=self.get_text(200, user), callback_data=f'sendMessageDeal_{deal}'))

        if confirm is False:
            kb.row(InlineKeyboardButton(text=self.get_text(201, user), callback_data=f'getConfirmDeal_{deal}'))
        else:
            kb.row(InlineKeyboardButton(text=self.get_text(205, user), callback_data='randomSmile'))

        kb.row(InlineKeyboardButton(text=self.get_text(202, user), callback_data=f'getCancelDeal_{deal}'))
        kb.row(InlineKeyboardButton(text=self.get_text(203, user), callback_data=f'openDisputDeal_{deal}'))
        return kb.as_markup()

    def confirmation_about_confirm_deal(self, user, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(206, user), callback_data='randomSmile'))
        kb.row(InlineKeyboardButton(text=self.get_text(201, user), callback_data=f'confirmDeal_{deal_uniq_id}'))
        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data=f'backToDeal_{deal_uniq_id}'))
        return kb.as_markup()

    def btn_answer_message(self, user, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(204, user), callback_data=f'sendMessageDeal_{deal_uniq_id}'))
        return kb.as_markup()

    def btn_deal_canceled(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(107, user), callback_data='randomSmile'))
        return kb.as_markup()

    def leave_feedback(self, user, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(300, user), callback_data=f'leaveFeedback_{deal_uniq_id}'))
        return kb.as_markup()

    def set_stars_review(self, user, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        for i in range(0, 5):
            kb.add(InlineKeyboardButton(text='⭐', callback_data=f'setStarsReview_{i + 1}_{deal_uniq_id}'))
        kb.row(InlineKeyboardButton(text=self.get_text(1, user), callback_data='cancel'))
        return kb.as_markup()

    def confirmation_cancel_deal(self, user, deal_uniq_id):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(206, user), callback_data='randomSmile'))
        kb.row(InlineKeyboardButton(text=self.get_text(202, user), callback_data=f'cancelDeal_{deal_uniq_id}'))
        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data=f'backToDeal_{deal_uniq_id}'))
        return kb.as_markup()

    def my_deals(self, user, deals, page_number, page_size=6):
        kb = InlineKeyboardBuilder()

        paginated_deals = self.paginate(deals, page_size)
        current_page_deals = paginated_deals[page_number]

        from tables.deals import StatusDeal
        for deal in current_page_deals:
            if deal.status == StatusDeal.active:
                icon_deal = '🟢'
            elif deal.status == StatusDeal.canceled:
                icon_deal = '🔴'
            elif deal.status == StatusDeal.closed:
                icon_deal = '✅'
            elif deal.status == StatusDeal.wait_confirm:
                icon_deal = '⏳'

            kb.row(
                InlineKeyboardButton(
                    text=self.get_text(402, user).format(
                        icon_deal=icon_deal,
                        deal_uniq_id=deal.uniq_id,
                        price=float(deal.price)
                    ),
                    callback_data=f"backToDeal_{deal.uniq_id}"
                )
            )
        kb.row()

        if page_number > 0:
            kb.row(InlineKeyboardButton(text=self.get_text(400, user), callback_data=f"getPageDeals_{page_number - 1}"))
        else:
            kb.row(InlineKeyboardButton(text='.', callback_data='randomSmile'))
        if page_number < len(paginated_deals) - 1:
            kb.add(InlineKeyboardButton(text=self.get_text(401, user), callback_data=f"getPageDeals_{page_number + 1}"))
        else:
            kb.add(InlineKeyboardButton(text='.', callback_data='randomSmile'))

        return kb.as_markup()

    def select_method_withdrawal(self, user, amount):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text='USDT BEP20', callback_data=f'withdrawalMethod_usdt_bep20_{amount}'))
        kb.row(InlineKeyboardButton(text='USDT ERC20', callback_data=f'withdrawalMethod_usdt_erc20_{amount}'))
        return kb.as_markup()

    def reviews_check(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(600, user), callback_data=f'checkReviews_{user.user_id}'))
        return kb.as_markup()

    def reviews_user(self, user, reviews, page_number, page_size=6):
        kb = InlineKeyboardBuilder()

        paginated_reviews = self.paginate(reviews, page_size)
        current_page_review = paginated_reviews[page_number]

        for review in current_page_review:
            kb.row(
                InlineKeyboardButton(
                    text=self.get_text(601, user).format(rating=review.rating, from_user_id=review.from_user_id),
                    callback_data=f"checkReview_{review.id}_{page_number}"
                )
            )

        if page_number > 0:
            kb.row(InlineKeyboardButton(text=self.get_text(400, user), callback_data=f"nextPageReviews_{review.to_user_id}_{page_number - 1}"))
        else:
            kb.row(InlineKeyboardButton(text='.', callback_data='randomSmile'))
        if page_number < len(paginated_reviews) - 1:
            kb.add(InlineKeyboardButton(text=self.get_text(401, user), callback_data=f"nextPageReviews_{review.to_user_id}_{page_number + 1}"))
        else:
            kb.add(InlineKeyboardButton(text='.', callback_data='randomSmile'))

        kb.row(InlineKeyboardButton(text=self.get_text(2, user), callback_data='hide'))
        return kb.as_markup()

    def link_inline(self, user, link, link_name):
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text=link_name, url=link))
        return kb.as_markup()

    def shop_main_menu(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text=self.get_text(800, user), callback_data='shop_categories'))
        kb.row(InlineKeyboardButton(text=self.get_text(802, user), callback_data='shop_my_orders'))
        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data='go_to_menu'))
        return kb.as_markup()

    def shop_categories(self, user, categories, page=0, page_size=10):
        kb = InlineKeyboardBuilder()

        paginated_categories = self.paginate(categories, page_size)

        if paginated_categories:
            current_page_categories = paginated_categories[page]

            for category in current_page_categories:
                kb.row(InlineKeyboardButton(
                    text=category.name,
                    callback_data=f'shop_category_{category.id}'
                ))

            nav_buttons = []

            if page > 0:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(400, user),
                    callback_data=f'shop_categories_page_{page-1}'
                ))

            if page < len(paginated_categories) - 1:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(401, user),
                    callback_data=f'shop_categories_page_{page+1}'
                ))

            if nav_buttons:
                kb.row(*nav_buttons)

        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data='shop_main'))

        return kb.as_markup()

    def shop_category_products(self, user, products, category_id, page=0, page_size=5):
        kb = InlineKeyboardBuilder()

        paginated_products = self.paginate(products, page_size)

        if paginated_products:
            current_page_products = paginated_products[page]

            for product in current_page_products:
                kb.row(InlineKeyboardButton(
                    text=f"{product.name} - ${product.price:.2f} (x{product.quantity})",
                    callback_data=f'shop_product_{product.id}'
                ))

            nav_buttons = []

            if page > 0:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(400, user),
                    callback_data=f'shop_category_{category_id}_page_{page-1}'
                ))

            if page < len(paginated_products) - 1:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(401, user),
                    callback_data=f'shop_category_{category_id}_page_{page+1}'
                ))

            if nav_buttons:
                kb.row(*nav_buttons)

        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data='shop_categories'))

        return kb.as_markup()

    def shop_product_details(self, user, product):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(
            text=self.get_text(816, user).format(price=product.price),
            callback_data=f'shop_buy_{product.id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(0, user),
            callback_data=f'shop_category_{product.category_id}'
        ))

        return kb.as_markup()

    def shop_insufficient_balance(self, user):
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text='💰 Пополнить баланс', callback_data='getTopUpBalance'))
        kb.row(InlineKeyboardButton(text=self.get_text(1, user), callback_data='shop_main'))
        return kb.as_markup()

    def shop_confirm_purchase(self, user, product):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(
            text=self.get_text(816, user).format(price=product.price),
            callback_data=f'shop_confirm_buy_{product.id}'
        ))

        if user.balance < product.price:
            kb.row(InlineKeyboardButton(
                text=self.get_text(817, user),
                callback_data='getTopUpBalance'
            ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(1, user),
            callback_data=f'shop_product_{product.id}'
        ))

        return kb.as_markup()

    def shop_my_orders(self, user, orders, page=0, page_size=5):
        kb = InlineKeyboardBuilder()

        paginated_orders = self.paginate(orders, page_size)

        if paginated_orders:
            current_page_orders = paginated_orders[page]

            for order in current_page_orders:
                status_text = ""
                if order.status == "pending":
                    status_text = "🔄 Processing"
                elif order.status == "completed":
                    status_text = "✅ Completed"
                elif order.status == "cancelled":
                    status_text = "❌ Cancelled"

                kb.row(InlineKeyboardButton(
                    text=f"Order #{order.id} - {status_text}",
                    callback_data=f'shop_order_{order.id}'
                ))

            nav_buttons = []

            if page > 0:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(400, user),
                    callback_data=f'shop_my_orders_page_{page-1}'
                ))

            if page < len(paginated_orders) - 1:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(401, user),
                    callback_data=f'shop_my_orders_page_{page+1}'
                ))

            if nav_buttons:
                kb.row(*nav_buttons)

        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data='shop_main'))

        return kb.as_markup()

    def shop_order_details(self, user, order, show_key=False):
        kb = InlineKeyboardBuilder()

        if order.status == "completed" and not show_key:
            kb.row(InlineKeyboardButton(
                text=self.get_text(826, user),
                callback_data=f'shop_order_show_key_{order.id}'
            ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(0, user),
            callback_data='shop_my_orders'
        ))

        return kb.as_markup()

    def admin_shop_menu(self, user):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(text=self.get_text(800, user), callback_data='admin_shop_categories'))
        kb.row(InlineKeyboardButton(text=self.get_text(801, user), callback_data='admin_shop_products'))
        kb.row(InlineKeyboardButton(text=self.get_text(809, user), callback_data='admin_shop_stats'))
        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data='admin'))

        return kb.as_markup()

    def admin_shop_categories(self, user, categories, page=0, page_size=5):
        kb = InlineKeyboardBuilder()

        paginated_categories = self.paginate(categories, page_size)

        if paginated_categories:
            current_page_categories = paginated_categories[page]

            for category in current_page_categories:
                kb.row(InlineKeyboardButton(
                    text=category.name,
                    callback_data=f'admin_shop_category_{category.id}'
                ))

            nav_buttons = []

            if page > 0:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(400, user),
                    callback_data=f'admin_shop_categories_page_{page-1}'
                ))

            if page < len(paginated_categories) - 1:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(401, user),
                    callback_data=f'admin_shop_categories_page_{page+1}'
                ))

            if nav_buttons:
                kb.row(*nav_buttons)

        kb.row(InlineKeyboardButton(
            text=self.get_text(808, user) + " " + self.get_text(800, user),
            callback_data='admin_shop_add_category'
        ))

        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data='admin_shop'))

        return kb.as_markup()

    def admin_shop_category_options(self, user, category_id):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(
            text=self.get_text(801, user),
            callback_data=f'admin_shop_category_products_{category_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(806, user),
            callback_data=f'admin_shop_edit_category_{category_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(807, user),
            callback_data=f'admin_shop_delete_category_{category_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(0, user),
            callback_data='admin_shop_categories'
        ))

        return kb.as_markup()

    def admin_shop_products(self, user, products, page=0, page_size=5):
        kb = InlineKeyboardBuilder()

        paginated_products = self.paginate(products, page_size)

        if paginated_products:
            current_page_products = paginated_products[page]

            for product in current_page_products:
                kb.row(InlineKeyboardButton(
                    text=f"{product.name} - ${product.price:.2f} (x{product.quantity})",
                    callback_data=f'admin_shop_product_{product.id}'
                ))

            nav_buttons = []

            if page > 0:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(400, user),
                    callback_data=f'admin_shop_products_page_{page-1}'
                ))

            if page < len(paginated_products) - 1:
                nav_buttons.append(InlineKeyboardButton(
                    text=self.get_text(401, user),
                    callback_data=f'admin_shop_products_page_{page+1}'
                ))

            if nav_buttons:
                kb.row(*nav_buttons)

        kb.row(InlineKeyboardButton(
            text=self.get_text(808, user) + " " + self.get_text(801, user),
            callback_data='admin_shop_add_product'
        ))

        kb.row(InlineKeyboardButton(text=self.get_text(0, user), callback_data='admin_shop'))

        return kb.as_markup()

    def admin_shop_product_options(self, user, product_id):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(
            text="🔑 Product inventory",
            callback_data=f'admin_shop_product_inventory_{product_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(806, user),
            callback_data=f'admin_shop_edit_product_{product_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(807, user),
            callback_data=f'admin_shop_delete_product_{product_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(0, user),
            callback_data='admin_shop_products'
        ))

        return kb.as_markup()

    def admin_shop_inventory(self, user, product_id, inventory_items, page=0, page_size=5):
        kb = InlineKeyboardBuilder()

        available_items = sum(1 for item in inventory_items if not item.is_sold)

        kb.row(InlineKeyboardButton(
            text="Add Product Quantity",
            callback_data=f'admin_shop_add_inventory_{product_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(0, user),
            callback_data=f'admin_shop_product_{product_id}'
        ))

        return kb.as_markup()

    def admin_shop_inventory_item_options(self, user, item_id, product_id):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(
            text=self.get_text(806, user),
            callback_data=f'admin_shop_edit_inventory_{item_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(807, user),
            callback_data=f'admin_shop_delete_inventory_{item_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(0, user),
            callback_data=f'admin_shop_product_inventory_{product_id}'
        ))

        return kb.as_markup()

    def admin_shop_confirm_delete(self, user, item_type, item_id, return_callback):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(
            text=self.get_text(807, user),
            callback_data=f'admin_shop_confirm_delete_{item_type}_{item_id}'
        ))

        kb.row(InlineKeyboardButton(
            text=self.get_text(1, user),
            callback_data=return_callback
        ))

        return kb.as_markup()

    def admin_shop_stats(self, user):
        kb = InlineKeyboardBuilder()

        kb.row(InlineKeyboardButton(
            text=self.get_text(0, user),
            callback_data='admin_shop'
        ))

        return kb.as_markup()
