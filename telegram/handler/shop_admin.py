from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter, TelegramForbiddenError
from datetime import datetime, timedelta
from peewee import fn
import asyncio

from tables.users import Users
from tables.shop_categories import ShopCategories
from tables.shop_products import ShopProducts
from tables.shop_inventory import ShopInventory
from tables.shop_orders import ShopOrders
from init import kb_user, convert, logger, kb_admin, database, bot_main

class ShopAdminStates(StatesGroup):
    adding_category = State()
    editing_category = State()
    adding_product = State()
    editing_product = State()
    adding_inventory = State()
    editing_inventory = State()
    viewing_stats = State()
    setting_product_type = State()
    setting_product_price = State()


router_shop_admin = Router()

async def send_single_notification(user_id: int, notification_text: str):
    try:
        await bot_main.send_message(
            chat_id=user_id,
            text=notification_text,
            parse_mode='HTML'
        )
        return True
    except TelegramForbiddenError:
        logger.debug(f"User {user_id} has blocked the bot")
        return False
    except TelegramRetryAfter as e:
        logger.warning(f"Rate limit for user {user_id}, waiting {e.retry_after} seconds")
        await asyncio.sleep(e.retry_after)
        try:
            await bot_main.send_message(
                chat_id=user_id,
                text=notification_text,
                parse_mode='HTML'
            )
            return True
        except Exception:
            return False
    except Exception as e:
        logger.warning(f"Failed to send notification to user {user_id}: {e}")
        return False

async def notify_users_new_product(product_name: str, category_name: str, quantity: int, is_new_product: bool = False):
    try:
        logger.debug(
            f"Notifications disabled: product={product_name}, category={category_name}, quantity={quantity}, is_new={is_new_product}"
        )
    except Exception:
        pass


async def get_all_categories():
    return await ShopCategories.select().order_by(
        ShopCategories.sort_order
    ).aio_execute()

async def get_all_products():
    return await ShopProducts.select().order_by(
        ShopProducts.sort_order
    ).aio_execute()

async def get_inventory_by_product(product_id):
    return await ShopInventory.select().where(
        ShopInventory.product_id == product_id
    ).order_by(
        ShopInventory.id.desc()
    ).aio_execute()

async def get_shop_stats():
    from peewee import fn

    total_sales_result = await ShopOrders.select(fn.COUNT(ShopOrders.id).alias('cnt')).where(
        ShopOrders.status == "completed"
    ).aio_execute()
    total_sales = total_sales_result[0].cnt

    total_revenue_query = await ShopOrders.select(
        fn.SUM(ShopOrders.amount).alias('total')
    ).where(
        ShopOrders.status == "completed"
    ).aio_execute()
    total_revenue_result = [row.total for row in total_revenue_query]
    total_revenue = total_revenue_result[0] if total_revenue_result else 0

    week_ago = datetime.now() - timedelta(days=7)
    week_sales_result = await ShopOrders.select(fn.COUNT(ShopOrders.id).alias('cnt')).where(
        (ShopOrders.status == "completed") &
        (ShopOrders.created_at > week_ago)
    ).aio_execute()
    week_sales = week_sales_result[0].cnt

    week_revenue_query = await ShopOrders.select(
        fn.SUM(ShopOrders.amount).alias('total')
    ).where(
        (ShopOrders.status == "completed") &
        (ShopOrders.created_at > week_ago)
    ).aio_execute()
    week_revenue_result = [row.total for row in week_revenue_query]
    week_revenue = week_revenue_result[0] if week_revenue_result else 0

    best_sellers_query = await ShopOrders.select(
        ShopOrders.product_id,
        fn.COUNT(ShopOrders.id).alias('count')
    ).where(
        ShopOrders.status == "completed"
    ).group_by(
        ShopOrders.product_id
    ).order_by(
        fn.COUNT(ShopOrders.id).desc()
    ).limit(5).aio_execute()

    best_sellers = []
    for item in best_sellers_query:
        best_sellers.append({
            'product_id': item.product_id,
            'count': item.count
        })

    return {
        "total_sales": total_sales,
        "total_revenue": float(total_revenue or 0),
        "week_sales": week_sales,
        "week_revenue": float(week_revenue or 0),
        "best_sellers": best_sellers,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@router_shop_admin.callback_query(lambda c: c.data == "admin_shop")
async def admin_shop_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    await callback.message.edit_text(
        "📝 <b>Admin Shop Panel</b>\n\n"
        "Welcome to the shop administration panel.\n"
        "Here you can manage categories, products, and view statistics.",
        reply_markup=kb_user.admin_shop_menu(user)
    )

    await callback.answer()

@router_shop_admin.callback_query(lambda c: c.data == "admin_shop_categories")
async def admin_shop_categories(callback: CallbackQuery, state: FSMContext):
    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    categories = await get_all_categories()

    if not categories:
        await callback.message.edit_text(
            "🏪 <b>Categories</b>\n\n"
            "No categories available. Add your first category!",
            reply_markup=kb_user.admin_shop_categories(user, [])
        )
        return

    await callback.message.edit_text(
        "🏪 <b>Categories</b>\n\n"
        "Select a category to manage:",
        reply_markup=kb_user.admin_shop_categories(user, categories)
    )

    await callback.answer()

@router_shop_admin.callback_query(lambda c: c.data.startswith("admin_shop_categories_page_"))
async def admin_categories_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    categories = await get_all_categories()

    await callback.message.edit_text(
        "🏪 <b>Categories</b>\n\n"
        "Select a category to manage:",
        reply_markup=kb_user.admin_shop_categories(user, categories, page)
    )

    await callback.answer()

@router_shop_admin.callback_query(F.data == "admin_shop_add_category")
async def admin_add_category(callback: CallbackQuery, state: FSMContext):
    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to perform this action.", show_alert=True)
        return

    await state.set_state(ShopAdminStates.adding_category)

    await callback.message.edit_text(
        "➕ <b>Add Category</b>\n\n"
        "Please send the name for the new category.\n"
        "Send /cancel to cancel this operation.",
        reply_markup=kb_user.btn_cancel(user)
    )

    await callback.answer()

@router_shop_admin.message(ShopAdminStates.adding_category)
async def process_category_name(message: Message, state: FSMContext):
    user = await Users.aio_get(Users.user_id == message.from_user.id)

    if user.admin <= 0:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "Operation cancelled.",
            reply_markup=kb_user.main_menu(user)
        )
        return

    category_name = message.text.strip()

    try:
        category = ShopCategories(
            name=category_name,
            is_active=True
        )
        await category.aio_save()

        await message.answer(
            f"✅ Category '{category_name}' has been added successfully!\n\n"
            "Please send a description for this category, or send /skip to skip.",
            reply_markup=kb_user.btn_cancel(user)
        )

        await state.set_state(ShopAdminStates.editing_category)
        await state.update_data(category_id=category.id)

    except Exception as e:
        logger.error(f"Error adding category: {e}")
        await message.answer(
            "An error occurred while adding the category. Please try again.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()

@router_shop_admin.message(ShopAdminStates.editing_category)
async def process_category_description(message: Message, state: FSMContext):
    user = await Users.aio_get(Users.user_id == message.from_user.id)

    if user.admin <= 0:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "Operation cancelled.",
            reply_markup=kb_user.main_menu(user)
        )
        return

    data = await state.get_data()
    category_id = data.get("category_id")

    if not category_id:
        await message.answer(
            "An error occurred. Category ID not found.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
        return

    try:
        async with database.aio_atomic():
            category = await ShopCategories.aio_get(ShopCategories.id == category_id)

            if message.text == "/skip":
                description = None
            else:
                description = message.text.strip()

            category.description = description
            await category.aio_save()

            await message.answer(
                "✅ Category updated successfully!",
                reply_markup=kb_user.main_menu(user)
            )

            categories = await get_all_categories()
            await message.answer(
                "🏪 <b>Categories</b>\n\n"
                "Select a category to manage:",
                reply_markup=kb_user.admin_shop_categories(user, categories)
            )

            await state.clear()

    except ShopCategories.DoesNotExist:
        logger.error(f"Category {category_id} not found")
        await message.answer(
            "The category you're trying to edit no longer exists.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating category: {e}")
        await message.answer(
            "An error occurred while updating the category. Please try again.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_category_"))
async def admin_category_options(callback: CallbackQuery, state: FSMContext):

    parts = callback.data.split("_")

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    if "products" in callback.data:
        category_id = int(parts[-1])

        try:
            category = await ShopCategories.aio_get(ShopCategories.id == category_id)
            products = await ShopProducts.select().where(
                ShopProducts.category_id == category_id
            ).order_by(
                ShopProducts.sort_order
            ).aio_execute()

            if not products:
                await callback.message.edit_text(
                    f"📦 <b>Products in {category.name}</b>\n\n"
                    f"No products available in this category.",
                    reply_markup=kb_user.admin_shop_products(user, [])
                )
                return

            await callback.message.edit_text(
                f"📦 <b>Products in {category.name}</b>\n\n"
                f"Select a product to manage:",
                reply_markup=kb_user.admin_shop_products(user, products)
            )
        except Exception as e:
            logger.error(f"Error showing products in category: {e}")
            await callback.answer("An error occurred. Please try again.", show_alert=True)

    else:
        category_id = int(parts[-1])

        try:
            category = await ShopCategories.aio_get(ShopCategories.id == category_id)

            await callback.message.edit_text(
                f"🏪 <b>{category.name}</b>\n\n"
                f"{category.description or 'No description available.'}\n\n"
                f"What would you like to do with this category?",
                reply_markup=kb_user.admin_shop_category_options(user, category_id)
            )
        except Exception as e:
            logger.error(f"Error showing category options: {e}")
            await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_edit_category_"))
async def admin_edit_category(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    category_id = int(parts[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    try:
        category = await ShopCategories.aio_get(ShopCategories.id == category_id)

        await state.set_state(ShopAdminStates.editing_category)
        await state.update_data(category_id=category_id)

        await callback.message.edit_text(
            f"✏️ <b>Edit Category</b>\n\n"
            f"Current name: {category.name}\n"
            f"Current description: {category.description or 'None'}\n\n"
            f"Please send a new description for this category.\n"
            f"Send /cancel to cancel this operation.",
            reply_markup=kb_user.btn_cancel(user)
        )
    except Exception as e:
        logger.error(f"Error editing category: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_delete_category_"))
async def admin_delete_category(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    category_id = int(parts[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    try:
        category = await ShopCategories.aio_get(ShopCategories.id == category_id)

        await callback.message.edit_text(
            f"🗑️ <b>Delete Category</b>\n\n"
            f"Are you sure you want to delete the category '{category.name}'?\n\n"
            f"This will also delete all products in this category!",
            reply_markup=kb_user.admin_shop_confirm_delete(
                user,
                "category",
                category_id,
                f"admin_shop_category_{category_id}"
            )
        )
    except Exception as e:
        logger.error(f"Error preparing to delete category: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_confirm_delete_"))
async def admin_confirm_delete(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    item_type = parts[4]
    item_id = int(parts[5])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to perform this action.", show_alert=True)
        return

    try:
        if item_type == "category":
            category = await ShopCategories.aio_get(ShopCategories.id == item_id)

            products = await ShopProducts.select().where(
                ShopProducts.category_id == item_id
            ).aio_execute()

            for product in products:
                await ShopInventory.delete().where(
                    ShopInventory.product_id == product.id
                ).aio_execute()

            await ShopProducts.delete().where(
                ShopProducts.category_id == item_id
            ).aio_execute()

            await category.aio_delete_instance()

            await callback.message.edit_text(
                f"✅ Category '{category.name}' and all its products have been deleted.",
                reply_markup=kb_user.admin_shop_menu(user)
            )

        elif item_type == "product":
            product = await ShopProducts.aio_get(ShopProducts.id == item_id)

            await ShopInventory.delete().where(
                ShopInventory.product_id == item_id
            ).aio_execute()

            await product.aio_delete_instance()

            await callback.message.edit_text(
                f"✅ Product '{product.name}' and all its inventory items have been deleted.",
                reply_markup=kb_user.admin_shop_menu(user)
            )

        elif item_type == "inventory":
            inventory = await ShopInventory.aio_get(ShopInventory.id == item_id)
            product_id = inventory.product_id

            await inventory.aio_delete_instance()

            product = await ShopProducts.aio_get(ShopProducts.id == product_id)
            product.quantity -= 1
            await product.aio_save()

            await callback.message.edit_text(
                f"✅ Inventory item has been deleted.",
                reply_markup=kb_user.admin_shop_product_options(user, product_id)
            )

    except Exception as e:
        logger.error(f"Error deleting {item_type}: {e}")
        await callback.answer(f"An error occurred while deleting the {item_type}. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.callback_query(lambda c: c.data == "admin_shop_products")
async def admin_shop_products(callback: CallbackQuery, state: FSMContext):
    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    products = await get_all_products()

    if not products:
        await callback.message.edit_text(
            "📦 <b>Products</b>\n\n"
            "No products available. Add your first product!",
            reply_markup=kb_user.admin_shop_products(user, [])
        )
        return

    await callback.message.edit_text(
        "📦 <b>Products</b>\n\n"
        "Select a product to manage:",
        reply_markup=kb_user.admin_shop_products(user, products)
    )

    await callback.answer()

@router_shop_admin.callback_query(lambda c: c.data.startswith("admin_shop_products_page_"))
async def admin_products_pagination(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    products = await get_all_products()

    await callback.message.edit_text(
        "📦 <b>Products</b>\n\n"
        "Select a product to manage:",
        reply_markup=kb_user.admin_shop_products(user, products, page)
    )

    await callback.answer()

@router_shop_admin.callback_query(F.data == "admin_shop_add_product")
async def admin_add_product(callback: CallbackQuery, state: FSMContext):
    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to perform this action.", show_alert=True)
        return

    categories = await get_all_categories()

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    kb = InlineKeyboardBuilder()

    if not categories:
        kb.row(InlineKeyboardButton(
            text="➕ Create First Category",
            callback_data="admin_shop_add_category"
        ))

        await callback.message.edit_text(
            "⚠️ You need to create at least one category first!\n\n"
            "Click the button below to create your first category:",
            reply_markup=kb.as_markup()
        )
        return

    for category in categories:
        kb.row(InlineKeyboardButton(
            text=category.name,
            callback_data=f"admin_shop_select_category_{category.id}"
        ))

    kb.row(InlineKeyboardButton(
        text="↩️ Cancel",
        callback_data="admin_shop_products"
    ))

    await callback.message.edit_text(
        "➕ <b>Add Product</b>\n\n"
        "Please select a category for the new product:",
        reply_markup=kb.as_markup()
    )

    await callback.answer()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_select_category_"))
async def admin_select_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to perform this action.", show_alert=True)
        return

    try:
        category = await ShopCategories.aio_get(ShopCategories.id == category_id)

        await state.set_state(ShopAdminStates.adding_product)
        await state.update_data(category_id=category_id)

        await callback.message.edit_text(
            f"➕ <b>Add Product to {category.name}</b>\n\n"
            f"Please send the name for the new product.\n"
            f"Send /cancel to cancel this operation.",
            reply_markup=kb_user.btn_cancel(user)
        )

    except Exception as e:
        logger.error(f"Error selecting category: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.message(ShopAdminStates.adding_product)
async def process_product_name(message: Message, state: FSMContext):
    user = await Users.aio_get(Users.user_id == message.from_user.id)

    if user.admin <= 0:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "Operation cancelled.",
            reply_markup=kb_user.main_menu(user)
        )
        return

    data = await state.get_data()
    category_id = data.get("category_id")

    if not category_id:
        await message.answer(
            "An error occurred. Category ID not found.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
        return

    product_name = message.text.strip()
    await state.update_data(product_name=product_name)

    await message.answer(
        "Now please send a description for this product, or send /skip to skip.",
        reply_markup=kb_user.btn_cancel(user)
    )

    await state.set_state(ShopAdminStates.editing_product)

@router_shop_admin.message(ShopAdminStates.editing_product)
async def process_product_description(message: Message, state: FSMContext):
    user = await Users.aio_get(Users.user_id == message.from_user.id)

    if user.admin <= 0:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "Operation cancelled.",
            reply_markup=kb_user.main_menu(user)
        )
        return

    data = await state.get_data()
    category_id = data.get("category_id")
    product_name = data.get("product_name")

    if not category_id or not product_name:
        await message.answer(
            "An error occurred. Missing product information.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
        return

    if message.text == "/skip":
        description = None
    else:
        description = message.text.strip()

    try:
        category = await ShopCategories.aio_get(ShopCategories.id == category_id)

        await state.update_data(description=description)

        await message.answer(
            f"Adding product to category: {category.name}\n\n"
            f"Name: {product_name}\n"
            f"Description: {description or 'None'}\n\n"
            "Now please specify the product type (e.g. key, account, service, etc.):",
            reply_markup=kb_user.btn_cancel(user)
        )

        await state.set_state(ShopAdminStates.setting_product_type)

    except ShopCategories.DoesNotExist:
        logger.error(f"Category {category_id} not found during product creation")
        await message.answer(
            "The category you're trying to add the product to no longer exists.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error processing product description: {e}")
        await message.answer(
            "An error occurred while processing the product description. Please try again.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()

@router_shop_admin.message(ShopAdminStates.setting_product_type)
async def process_product_type(message: Message, state: FSMContext):
    user = await Users.aio_get(Users.user_id == message.from_user.id)

    if user.admin <= 0:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "Operation cancelled.",
            reply_markup=kb_user.main_menu(user)
        )
        return

    data = await state.get_data()
    category_id = data.get("category_id")
    product_name = data.get("product_name")
    description = data.get("description")

    if not category_id or not product_name:
        await message.answer(
            "An error occurred. Missing product information.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
        return

    product_type = message.text.strip().lower()

    try:
        category = await ShopCategories.aio_get(ShopCategories.id == category_id)

        await state.update_data(product_type=product_type)

        await message.answer(
            f"Adding product to category: {category.name}\n\n"
            f"Name: {product_name}\n"
            f"Description: {description or 'None'}\n"
            f"Product Type: {product_type}\n\n"
            "Now please send the price for this product (e.g. 9.99).",
            reply_markup=kb_user.btn_cancel(user)
        )

        await state.set_state(ShopAdminStates.setting_product_price)

    except ShopCategories.DoesNotExist:
        logger.error(f"Category {category_id} not found during product creation")
        await message.answer(
            "The category you're trying to add the product to no longer exists.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error processing product type: {e}")
        await message.answer(
            "An error occurred while processing the product type. Please try again.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()

@router_shop_admin.message(ShopAdminStates.setting_product_price)
async def process_product_price_input(message: Message, state: FSMContext):
    user = await Users.aio_get(Users.user_id == message.from_user.id)

    if user.admin <= 0:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "Operation cancelled.",
            reply_markup=kb_user.main_menu(user)
        )
        return

    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await message.answer(
            "Please enter a valid price (e.g. 9.99).",
            reply_markup=kb_user.btn_cancel(user)
        )
        return

    data = await state.get_data()
    category_id = data.get("category_id")
    product_name = data.get("product_name")
    description = data.get("description")
    product_type = data.get("product_type", "key")

    if not category_id:
        await message.answer(
            "Error: Category ID not found. Please try adding the product again.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
        return

    try:
        product = ShopProducts(
            name=product_name,
            description=description,
            price=price,
            category_id=category_id,
            is_active=True,
            quantity=0,
            product_type=product_type
        )
        await product.aio_save()

        await message.answer(
            f"✅ Product '{product_name}' has been added successfully!\n\n"
            f"Now you can add inventory items to this product.",
            reply_markup=kb_user.main_menu(user)
        )

        await message.answer(
            f"📦 <b>{product_name}</b>\n\n"
            f"Price: ${price:.2f}\n"
            f"Type: {product_type}\n"
            f"Description: {description or 'None'}\n\n"
            f"What would you like to do with this product?",
            reply_markup=kb_user.admin_shop_product_options(user, product.id)
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error adding product: {e}")
        await message.answer(
            "An error occurred while adding the product. Please try again.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_product_"))
async def admin_product_options(callback: CallbackQuery, state: FSMContext):

    parts = callback.data.split("_")

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    product_id = int(parts[-1])

    try:
        product = await ShopProducts.aio_get(ShopProducts.id == product_id)

        if "inventory" in callback.data:
            inventory_items = await get_inventory_by_product(product_id)

            available_count = sum(1 for item in inventory_items if not item.is_sold)

            await callback.message.edit_text(
                f"🔑 <b>Inventory for {product.name}</b>\n\n"
                f"Total items: {len(inventory_items)}\n"
                f"Available items: {available_count}\n\n"
                f"Add more product items:",
                reply_markup=kb_user.admin_shop_inventory(user, product_id, inventory_items)
            )

        else:
            category = await ShopCategories.aio_get(ShopCategories.id == product.category_id)
            inventory_count_result = await ShopInventory.select(fn.COUNT(ShopInventory.id).alias('cnt')).where(
                (ShopInventory.product_id == product_id) &
                (ShopInventory.is_sold == False)
            ).aio_execute()
            inventory_count = inventory_count_result[0].cnt

            await callback.message.edit_text(
                f"📦 <b>{product.name}</b>\n\n"
                f"Category: {category.name}\n"
                f"Price: ${product.price:.2f}\n"
                f"Available inventory: {inventory_count} items\n"
                f"Description: {product.description or 'None'}\n\n"
                f"What would you like to do with this product?",
                reply_markup=kb_user.admin_shop_product_options(user, product_id)
            )

    except Exception as e:
        logger.error(f"Error handling product action: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_edit_product_"))
async def admin_edit_product(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    product_id = int(parts[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    try:
        product = await ShopProducts.aio_get(ShopProducts.id == product_id)

        await state.set_state(ShopAdminStates.editing_product)
        await state.update_data(product_id=product_id)

        await callback.message.edit_text(
            f"✏️ <b>Edit Product</b>\n\n"
            f"Current name: {product.name}\n"
            f"Current price: ${product.price:.2f}\n"
            f"Current description: {product.description or 'None'}\n\n"
            f"Please send a new description for this product.\n"
            f"Send /skip to keep the current description.\n"
            f"Send /cancel to cancel this operation.",
            reply_markup=kb_user.btn_cancel(user)
        )
    except Exception as e:
        logger.error(f"Error editing product: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_delete_product_"))
async def admin_delete_product(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    product_id = int(parts[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    try:
        product = await ShopProducts.aio_get(ShopProducts.id == product_id)

        await callback.message.edit_text(
            f"🗑️ <b>Delete Product</b>\n\n"
            f"Are you sure you want to delete the product '{product.name}'?\n\n"
            f"This will also delete all inventory items!",
            reply_markup=kb_user.admin_shop_confirm_delete(
                user,
                "product",
                product_id,
                f"admin_shop_product_{product_id}"
            )
        )
    except Exception as e:
        logger.error(f"Error preparing to delete product: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_inventory_item_"))
async def admin_inventory_item_options(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split("_")[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    try:
        inventory = await ShopInventory.aio_get(ShopInventory.id == item_id)
        product = await ShopProducts.aio_get(ShopProducts.id == inventory.product_id)

        status = "✅ Available" if not inventory.is_sold else "❌ Sold"

        await callback.message.edit_text(
            f"🔑 <b>Inventory Item #{inventory.id}</b>\n\n"
            f"Product: {product.name}\n"
            f"Status: {status}\n"
            f"Content: {inventory.content}\n\n"
            f"What would you like to do with this inventory item?",
            reply_markup=kb_user.admin_shop_inventory_item_options(user, item_id, inventory.product_id)
        )

    except Exception as e:
        logger.error(f"Error showing inventory item options: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_add_inventory_"))
async def admin_add_inventory(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to perform this action.", show_alert=True)
        return

    try:
        product = await ShopProducts.aio_get(ShopProducts.id == product_id)

        await state.set_state(ShopAdminStates.adding_inventory)
        await state.update_data(product_id=product_id)

        await callback.message.edit_text(
            f"➕ <b>Add Product Quantity</b>\n\n"
            f"Product: {product.name}\n\n"
            f"Please send the product data. The data must be separated with colons (:).\n"
            f"For example: login:password or login:password:email\n"
            f"This will be delivered to customers when they purchase the product.\n"
            f"Send /cancel to cancel this operation.",
            reply_markup=kb_user.btn_cancel(user)
        )

    except Exception as e:
        logger.error(f"Error preparing to add inventory: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.callback_query(F.data.startswith("admin_shop_edit_inventory_"))
async def admin_edit_inventory(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data.split("_")[-1])

    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to perform this action.", show_alert=True)
        return

    try:
        inventory = await ShopInventory.aio_get(ShopInventory.id == item_id)

        await state.set_state(ShopAdminStates.editing_inventory)
        await state.update_data(inventory_id=item_id, product_id=inventory.product_id)

        await callback.message.edit_text(
            f"✏️ <b>Edit Inventory Item</b>\n\n"
            f"Current content: {inventory.content}\n\n"
            f"Please send the new content for this inventory item.\n"
            f"Send /skip to keep the current content.\n"
            f"Send /cancel to cancel this operation.",
            reply_markup=kb_user.btn_cancel(user)
        )

    except Exception as e:
        logger.error(f"Error editing inventory item: {e}")
        await callback.answer("An error occurred. Please try again.", show_alert=True)

    await callback.answer()

@router_shop_admin.message(ShopAdminStates.editing_inventory)
async def process_edit_inventory(message: Message, state: FSMContext):
    user = await Users.aio_get(Users.user_id == message.from_user.id)

    if user.admin <= 0:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "Operation cancelled.",
            reply_markup=kb_user.main_menu(user)
        )
        return

    data = await state.get_data()
    inventory_id = data.get("inventory_id")
    product_id = data.get("product_id")

    if not inventory_id or not product_id:
        await message.answer(
            "An error occurred. Missing inventory information.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
        return

    try:
        inventory = await ShopInventory.aio_get(ShopInventory.id == inventory_id)

        if message.text != "/skip":
            inventory.content = message.text.strip()
            await inventory.aio_save()

        await message.answer(
            "✅ Inventory item updated successfully!",
            reply_markup=kb_user.main_menu(user)
        )

        inventory_items = await get_inventory_by_product(product_id)
        product = await ShopProducts.aio_get(ShopProducts.id == product_id)

        await message.answer(
            f"🔑 <b>Inventory for {product.name}</b>\n\n"
            f"Total items: {len(inventory_items)}\n"
            f"Available items: {sum(1 for item in inventory_items if not item.is_sold)}\n\n"
            f"Select an item to manage or add more inventory items:",
            reply_markup=kb_user.admin_shop_inventory(user, product_id, inventory_items)
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Error updating inventory item: {e}")
        await message.answer(
            "An error occurred while updating the inventory item. Please try again.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()

@router_shop_admin.callback_query(lambda c: c.data == "admin_shop_stats")
async def admin_shop_stats(callback: CallbackQuery, state: FSMContext):
    user = await Users.aio_get(Users.user_id == callback.from_user.id)

    if user.admin <= 0:
        await callback.answer("You don't have permission to access this menu.", show_alert=True)
        return

    try:
        data = await state.get_data()
        cached_stats = data.get('shop_stats')
        cached_time = data.get('shop_stats_time')

        if cached_stats and cached_time and (datetime.now() - datetime.strptime(cached_time, "%Y-%m-%d %H:%M:%S")).total_seconds() < 300:
            stats = cached_stats
        else:
            stats = await get_shop_stats()
            await state.update_data(
                shop_stats=stats,
                shop_stats_time=stats['last_updated']
            )

        best_sellers_text = ""
        for i, item in enumerate(stats["best_sellers"]):
            try:
                product = await ShopProducts.aio_get(ShopProducts.id == item['product_id'])
                best_sellers_text += f"{i+1}. {product.name} - {item['count']} sales\n"
            except ShopProducts.DoesNotExist:
                best_sellers_text += f"{i+1}. Product ID {item['product_id']} (deleted) - {item['count']} sales\n"
            except Exception as e:
                logger.error(f"Error getting product {item['product_id']} for stats: {e}")
                best_sellers_text += f"{i+1}. Product ID {item['product_id']} (error) - {item['count']} sales\n"

        if not best_sellers_text:
            best_sellers_text = "No sales recorded yet"

        stats_text = (
            "📊 <b>Shop Statistics</b>\n\n"
            f"<b>Total Sales:</b> {stats['total_sales']}\n"
            f"<b>Total Revenue:</b> ${stats['total_revenue']:.2f}\n\n"
            f"<b>Last 7 Days Sales:</b> {stats['week_sales']}\n"
            f"<b>Last 7 Days Revenue:</b> ${stats['week_revenue']:.2f}\n\n"
            f"<b>Best Selling Products:</b>\n{best_sellers_text}\n\n"
            f"<i>Last Updated: {stats['last_updated']}</i>"
        )

        try:
            await callback.message.edit_text(
                stats_text,
                reply_markup=kb_user.admin_shop_stats(user)
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback.answer("Statistics are up to date")
            else:
                raise

    except Exception as e:
        logger.error(f"Error getting shop stats: {e}")
        await callback.message.edit_text(
            "An error occurred while retrieving shop statistics. Please try again.",
            reply_markup=kb_user.admin_shop_menu(user)
        )

    await callback.answer()

@router_shop_admin.message(ShopAdminStates.adding_inventory)
async def process_inventory_content(message: Message, state: FSMContext):
    user = await Users.aio_get(Users.user_id == message.from_user.id)

    if user.admin <= 0:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "Operation cancelled.",
            reply_markup=kb_user.main_menu(user)
        )
        return

    data = await state.get_data()
    product_id = data.get("product_id")

    if not product_id:
        await message.answer(
            "An error occurred. Product ID not found.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
        return

    content_lines = message.text.strip().split('\n')
    valid_lines = []
    invalid_lines = []

    for line in content_lines:
        if line.strip() and ":" in line:
            valid_lines.append(line.strip())
        elif line.strip():
            invalid_lines.append(line.strip())

    if invalid_lines:
        await message.answer(
            f"Found {len(invalid_lines)} invalid lines. Each line must contain colon (:) separators.\n"
            f"For example: login:password or login:password:email\n"
            f"Please try again with valid format.",
            reply_markup=kb_user.btn_cancel(user)
        )
        return

    if not valid_lines:
        await message.answer(
            "No valid data found. The product data must be separated with colons (:).\n"
            "For example: login:password or login:password:email",
            reply_markup=kb_user.btn_cancel(user)
        )
        return

    try:
        async with database.aio_atomic():
            product = await ShopProducts.aio_get(ShopProducts.id == product_id)
            original_quantity = product.quantity

            added_count = 0
            for content in valid_lines:
                inventory = ShopInventory(
                    product_id=product_id,
                    content=content,
                    is_sold=False
                )
                await inventory.aio_save()
                added_count += 1

            product.quantity += added_count
            await product.aio_save()

            category = await ShopCategories.aio_get(ShopCategories.id == product.category_id)

            await message.answer(
                f"✅ Added {added_count} product items successfully to '{product.name}'!\n\n"
                f"You can add more or go back to the product management.",
                reply_markup=kb_user.main_menu(user)
            )

            inventory_items = await get_inventory_by_product(product_id)

            await message.answer(
                f"🔑 <b>Inventory for {product.name}</b>\n\n"
                f"Total items: {len(inventory_items)}\n"
                f"Available items: {sum(1 for item in inventory_items if not item.is_sold)}\n\n"
                f"Add more product items:",
                reply_markup=kb_user.admin_shop_inventory(user, product_id, inventory_items)
            )

            await state.clear()

    except ShopProducts.DoesNotExist:
        logger.error(f"Product {product_id} not found during inventory creation")
        await message.answer(
            "The product you're trying to add inventory to no longer exists.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error adding inventory items: {e}")
        await message.answer(
            "An error occurred while adding the inventory items. Please try again.",
            reply_markup=kb_user.main_menu(user)
        )
        await state.clear()
