from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime

from tables.users import Users
from tables.shop_categories import ShopCategories
from tables.shop_products import ShopProducts
from tables.shop_inventory import ShopInventory
from tables.shop_orders import ShopOrders
from init import kb_user, convert, logger, database, bot_main as bot, config
from peewee import fn

class ShopStates(StatesGroup):
    browsing = State()
    product_view = State()
    purchase_confirm = State()
    order_view = State()


router_shop = Router()

async def get_active_categories():
    return await ShopCategories.select().where(
        ShopCategories.is_active == True
    ).order_by(
        ShopCategories.sort_order
    ).aio_execute()

async def get_products_by_category(category_id):
    return await ShopProducts.select().where(
        (ShopProducts.category_id == category_id) &
        (ShopProducts.is_active == True)
    ).order_by(
        ShopProducts.sort_order
    ).aio_execute()

async def get_product(product_id):
    return await ShopProducts.aio_get(ShopProducts.id == product_id)

async def get_available_inventory_item(product_id):
    items = await ShopInventory.select().where(
        (ShopInventory.product_id == product_id) &
        (ShopInventory.is_sold == False)
    ).limit(1).aio_execute()

    return items[0] if items else None

async def get_user_orders(user_id):
    return await ShopOrders.select().where(
        ShopOrders.user_id == user_id
    ).order_by(
        ShopOrders.created_at.desc()
    ).aio_execute()

async def get_order(order_id):
    return await ShopOrders.aio_get(ShopOrders.id == order_id)

async def get_inventory_item(item_id):
    return await ShopInventory.aio_get(ShopInventory.id == item_id)

@router_shop.message(F.text.in_(['🛒 Shop', '🛒 Магазин']))
async def shop_command(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ShopStates.browsing)

    user = await Users.aio_get(Users.user_id == message.from_user.id)

    await message.answer(
        "🛒 <b>Welcome to the Elvisescrow Shop</b>\n\n"
        "Browse our selection of Elvisescrow products including keys, accounts and more.\n"
        "All products are delivered instantly after purchase.",
        reply_markup=kb_user.shop_main_menu(user)
    )

@router_shop.callback_query(F.data == "shop_categories")
async def show_categories(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ShopStates.browsing)

    user = await Users.aio_get(Users.user_id == callback.from_user.id)
    categories = await get_active_categories()

    if not categories:
        await callback.message.edit_text(
            "🏪 <b>Categories</b>\n\n"
            "No categories available at the moment. Please check back later.",
            reply_markup=kb_user.shop_main_menu(user)
        )
        return

    await callback.message.edit_text(
        "🏪 <b>Categories</b>\n\n"
        "Please select a category to view products:",
        reply_markup=kb_user.shop_categories(user, categories)
    )

    await callback.answer()

@router_shop.callback_query(F.data.startswith("shop_categories_page_"))
async def categories_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)
    categories = await get_active_categories()

    await callback.message.edit_text(
        "🏪 <b>Categories</b>\n\n"
        "Please select a category to view products:",
        reply_markup=kb_user.shop_categories(user, categories, page)
    )

    await callback.answer()

@router_shop.callback_query(F.data.startswith("shop_category_"))
async def show_category_products(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    if "page" in callback.data:
        category_id = int(parts[2])
        page = int(parts[4])
    else:
        category_id = int(parts[2])
        page = 0

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    try:
        category = await ShopCategories.aio_get(ShopCategories.id == category_id)
        products = await get_products_by_category(category_id)

        if not products:
            await callback.message.edit_text(
                f"📦 <b>{category.name}</b>\n\n"
                f"{category.description or ''}\n\n"
                "No products available in this category at the moment.",
                reply_markup=kb_user.shop_main_menu(user)
            )
            return

        await callback.message.edit_text(
            f"📦 <b>{category.name}</b>\n\n"
            f"{category.description or ''}\n\n"
            "Please select a product to view details:",
            reply_markup=kb_user.shop_category_products(user, products, category_id, page)
        )
    except Exception as e:
        logger.error(f"Error showing category products: {e}")
        await callback.message.edit_text(
            "An error occurred while retrieving products. Please try again.",
            reply_markup=kb_user.shop_main_menu(user)
        )

    await callback.answer()

@router_shop.callback_query(F.data.startswith("shop_product_"))
async def show_product_details(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])

    await state.set_state(ShopStates.product_view)
    await state.update_data(product_id=product_id)

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    try:
        product = await get_product(product_id)

        inventory_count_result = await ShopInventory.select(fn.COUNT(ShopInventory.id).alias('cnt')).where(
            (ShopInventory.product_id == product_id) &
            (ShopInventory.is_sold == False)
        ).aio_execute()
        inventory_count = inventory_count_result[0].cnt

        product_info = (
            f"🔑 <b>{product.name}</b>\n\n"
            f"{product.description or 'No description available.'}\n\n"
            f"💰 <b>Price:</b> ${product.price:.2f}\n"
            f"📦 <b>Available:</b> {inventory_count} items\n"
            f"🏷️ <b>Product Type:</b> {product.product_type.capitalize()}\n\n"
            f"Click the button below to purchase this product."
        )

        await callback.message.edit_text(
            product_info,
            reply_markup=kb_user.shop_product_details(user, product)
        )
    except Exception as e:
        logger.error(f"Error showing product details: {e}")
        await callback.message.edit_text(
            "An error occurred while retrieving product details. Please try again.",
            reply_markup=kb_user.shop_main_menu(user)
        )

    await callback.answer()

@router_shop.callback_query(F.data.startswith("shop_buy_"))
async def buy_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])

    await state.set_state(ShopStates.purchase_confirm)
    await state.update_data(product_id=product_id)

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    try:
        product = await get_product(product_id)

        inventory_item = await get_available_inventory_item(product_id)
        if not inventory_item:
            await callback.message.edit_text(
                "Sorry, this product is currently out of stock.",
                reply_markup=kb_user.shop_main_menu(user)
            )
            return

        if user.balance < product.price:
            purchase_text = (
                f"🛍️ <b>Confirm Purchase</b>\n\n"
                f"Product: <b>{product.name}</b>\n"
                f"Price: <b>${product.price:.2f}</b>\n\n"
                f"❌ <b>Insufficient balance</b>\n"
                f"Your current balance: <b>${user.balance:.2f}</b>\n"
                f"You need: <b>${product.price - user.balance:.2f}</b> more.\n\n"
                f"Please top up your balance to complete this purchase."
            )
            await callback.message.edit_text(
                purchase_text,
                reply_markup=kb_user.shop_insufficient_balance(user)
            )
        else:
            purchase_text = (
                f"🛍️ <b>Confirm Purchase</b>\n\n"
                f"Product: <b>{product.name}</b>\n"
                f"Price: <b>${product.price:.2f}</b>\n"
                f"Your balance: <b>${user.balance:.2f}</b>\n\n"
                f"After purchase, your balance will be: <b>${user.balance - product.price:.2f}</b>\n\n"
                f"Click 'Pay' to complete your purchase."
            )
            await callback.message.edit_text(
                purchase_text,
                reply_markup=kb_user.shop_confirm_purchase(user, product)
            )
    except Exception as e:
        logger.error(f"Error preparing purchase: {e}")
        await callback.message.edit_text(
            "An error occurred while preparing your purchase. Please try again.",
            reply_markup=kb_user.shop_main_menu(user)
        )

    await callback.answer()

@router_shop.callback_query(F.data.startswith("shop_confirm_buy_"))
async def confirm_buy_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    try:
        product = await get_product(product_id)

        inventory_item = await get_available_inventory_item(product_id)
        if not inventory_item:
            await callback.message.edit_text(
                "Sorry, this product is currently out of stock.",
                reply_markup=kb_user.shop_main_menu(user)
            )
            return

        if user.balance < product.price:
            await callback.answer(convert.cv(831, user), show_alert=True)
            return

        async with database.aio_atomic():
            inventory_item.is_sold = True
            inventory_item.sold_to = user.user_id
            inventory_item.sold_at = datetime.now()
            await inventory_item.aio_save()

            order = ShopOrders(
                user_id=user.user_id,
                product_id=product_id,
                product_name=product.name,
                product_type=product.product_type,
                inventory_id=inventory_item.id,
                inventory_content=inventory_item.content,
                amount=product.price,
                status="completed",
                completed_at=datetime.now()
            )
            await order.aio_save()

            product.quantity -= 1
            await product.aio_save()

            user.balance -= product.price
            await user.aio_save()

            logs_channel_id = int(config['CHATS_ID']['logs'])
            username = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {user.user_id}"
            await bot.send_message(
                logs_channel_id,
                f"Пользователь {username} купил {product.name}"
            )

        purchase_success = (
            f"✅ <b>Purchase Successful!</b>\n\n"
            f"Thank you for your purchase of <b>{product.name}</b>.\n\n"
            f"<b>Your {product.product_type}:</b>\n"
            f"<code>{inventory_item.content}</code>\n\n"
            f"Your new balance: <b>${user.balance:.2f}</b>\n\n"
            f"You can view your purchase history in the 'My Orders' section."
        )

        await callback.message.edit_text(
            purchase_success,
            reply_markup=kb_user.shop_main_menu(user)
        )

        logger.info(
            f"User {user.user_id} purchased product {product.id} ({product.name}) "
            f"for ${product.price:.2f}. Order ID: {order.id}"
        )

    except Exception as e:
        logger.error(f"Error completing purchase: {e}")
        await callback.message.edit_text(
            "An error occurred while processing your purchase. Please try again.",
            reply_markup=kb_user.shop_main_menu(user)
        )

    await callback.answer()

@router_shop.callback_query(F.data == "shop_my_orders")
async def show_my_orders(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ShopStates.browsing)

    user = await Users.aio_get(Users.user_id == callback.from_user.id)
    orders = await get_user_orders(user.user_id)

    if not orders:
        await callback.message.edit_text(
            "🛒 <b>My Orders</b>\n\n"
            "You don't have any orders yet.",
            reply_markup=kb_user.shop_main_menu(user)
        )
        return

    await callback.message.edit_text(
        "🛒 <b>My Orders</b>\n\n"
        "Here are your recent orders:",
        reply_markup=kb_user.shop_my_orders(user, orders)
    )

    await callback.answer()

@router_shop.callback_query(F.data.startswith("shop_my_orders_page_"))
async def my_orders_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)
    orders = await get_user_orders(user.user_id)

    await callback.message.edit_text(
        "🛒 <b>My Orders</b>\n\n"
        "Here are your recent orders:",
        reply_markup=kb_user.shop_my_orders(user, orders, page)
    )

    await callback.answer()

@router_shop.callback_query(F.data.startswith("shop_order_"))
async def show_order_details(callback: CallbackQuery, state: FSMContext):

    parts = callback.data.split("_")
    if "show_key" in callback.data:
        order_id = int(parts[-1])
        show_key = True
    else:
        order_id = int(parts[-1])
        show_key = False

    await state.set_state(ShopStates.order_view)
    await state.update_data(order_id=order_id)

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    try:
        order = await get_order(order_id)

        if order.user_id != user.user_id:
            await callback.answer("You don't have permission to view this order.", show_alert=True)
            return

        product_name = order.product_name or "Deleted Product"
        product_type = order.product_type or "product"

        status_text = ""
        if order.status == "pending":
            status_text = "🔄 Processing"
        elif order.status == "completed":
            status_text = "✅ Completed"
        elif order.status == "cancelled":
            status_text = "❌ Cancelled"

        date_text = order.created_at.strftime("%Y-%m-%d %H:%M:%S")

        order_info = (
            f"🧾 <b>Order #{order.id}</b>\n\n"
            f"Product: <b>{product_name}</b>\n"
            f"Price: <b>${order.amount:.2f}</b>\n"
            f"Status: <b>{status_text}</b>\n"
            f"Date: <b>{date_text}</b>\n"
        )

        if show_key and order.status == "completed":
            if order.inventory_content:
                order_info += (
                    f"\n<b>Your {product_type}:</b>\n"
                    f"<code>{order.inventory_content}</code>"
                )
            else:
                order_info += "\n❌ Product content is no longer available"

        await callback.message.edit_text(
            order_info,
            reply_markup=kb_user.shop_order_details(user, order, show_key)
        )
    except Exception as e:
        logger.error(f"Error showing order details: {e}")
        await callback.message.edit_text(
            "An error occurred while retrieving order details. Please try again.",
            reply_markup=kb_user.shop_main_menu(user)
        )

    await callback.answer()

@router_shop.callback_query(F.data == "shop_main")
async def back_to_shop_main(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ShopStates.browsing)

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    await callback.message.edit_text(
        "🛒 <b>Welcome to the Digital Shop</b>\n\n"
        "Browse our selection of digital products including keys, accounts and more.\n"
        "All products are delivered instantly after purchase.",
        reply_markup=kb_user.shop_main_menu(user)
    )

    await callback.answer()

@router_shop.callback_query(F.data == "go_to_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    await callback.message.answer(
        "You have returned to the main menu.",
        reply_markup=kb_user.main_menu(user)
    )

    await callback.answer()
