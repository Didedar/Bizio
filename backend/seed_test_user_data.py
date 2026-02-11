#!/usr/bin/env python3
"""
Seed script to create demo data for test@example.com user.
Creates 20 contacts, 20 products, 20 deals (4 in each stage), and realistic expenses.

Run: cd backend && python seed_test_user_data.py
"""
import asyncio
import sys
from decimal import Decimal
from datetime import datetime, timedelta, date, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

# 20 Realistic Kazakh business contacts
CONTACTS_DATA = [
    ("Айгуль Сериккызы Муратова", "ТОО Альфа Трейд", "aigul@alphatrade.kz", "+7 701 111 2233", "Алматы, ул. Абая, 150"),
    ("Арман Болатович Ким", "ИП Ким А.Б.", "arman.kim@mail.kz", "+7 702 222 3344", "Астана, пр. Мангилик Ел, 55"),
    ("Дана Ерболкызы Нурпеисова", "ТОО TechnoKaz", "dana@technokaz.kz", "+7 707 333 4455", "Шымкент, ул. Тауке хана, 10"),
    ("Бауыржан Кайратович Омаров", "ТОО OmarGroup", "baurzhan@omargroup.kz", "+7 777 444 5566", "Караганда, ул. Бухар-жырау, 80"),
    ("Гульнара Маратовна Жансеитова", "ИП Жансеитова Г.М.", "gulnara.j@inbox.kz", "+7 708 555 6677", "Павлодар, ул. Ленина, 25"),
    ("Нурсултан Серикович Абдрахманов", "ТОО НурТех", "nursultan@nurtech.kz", "+7 701 666 7788", "Атырау, мкр. Авангард, 12"),
    ("Мадина Ержанкызы Тулегенова", "ТОО MadinaStyle", "madina@madinastyle.kz", "+7 702 777 8899", "Актобе, пр. Санкибай батыра, 45"),
    ("Ерлан Бауыржанович Касымов", "АО КазТрансСервис", "erlan@kaztrans.kz", "+7 707 888 9900", "Тараз, ул. Толе би, 33"),
    ("Айнур Талгатовна Сапарова", "ТОО АйнурПлюс", "ainur@ainurplus.kz", "+7 777 999 0011", "Семей, ул. Абая, 100"),
    ("Дархан Маратович Жумабеков", "ИП Жумабеков Д.М.", "darkhan.j@gmail.com", "+7 708 000 1122", "Костанай, ул. Гоголя, 15"),
    ("Сауле Нурлановна Ахметова", "ТОО СаулеТрейд", "saule@sauletrade.kz", "+7 701 112 2334", "Уральск, ул. Курмангазы, 70"),
    ("Азамат Ерболович Нуржанов", "ТОО AzaTech", "azamat@azatech.kz", "+7 702 223 3445", "Петропавловск, ул. Интернациональная, 5"),
    ("Жанна Серикбаевна Муканова", "ИП Муканова Ж.С.", "zhanna.m@mail.kz", "+7 707 334 4556", "Кызылорда, ул. Жибек жолы, 20"),
    ("Руслан Кайратович Есенов", "ТОО RuslanBuild", "ruslan@ruslanbuild.kz", "+7 777 445 5667", "Актау, мкр. 5, дом 10"),
    ("Динара Асланқызы Байменова", "ТОО DinaGroup", "dinara@dinagroup.kz", "+7 708 556 6778", "Талдыкорган, ул. Кабанбай батыра, 35"),
    ("Кайрат Нурланович Жаксылыков", "АО КайратИнвест", "kairat@kairatinvest.kz", "+7 701 667 7889", "Кокшетау, ул. Ауэзова, 50"),
    ("Ляззат Маратовна Сейтова", "ТОО ЛяззатФуд", "lyazzat@lyazzatfood.kz", "+7 702 778 8990", "Экибастуз, ул. Машхур Жусупа, 8"),
    ("Сергей Викторович Ли", "ИП Ли С.В.", "sergey.li@company.kz", "+7 707 889 9001", "Темиртау, пр. Республики, 22"),
    ("Асель Ерлановна Каримова", "ТОО АсельСтиль", "asel@aselstyle.kz", "+7 777 990 0112", "Рудный, ул. Горняков, 17"),
    ("Тимур Бахытович Нургалиев", "ТОО ТимурТранс", "timur@timurtrans.kz", "+7 708 001 1223", "Туркестан, ул. Жибек жолы, 60"),
]

# 20 Realistic products
PRODUCTS_DATA = [
    # Electronics
    ("Ноутбук HP ProBook 450 G8", "ELEC-001", "Ноутбук для бизнеса 15.6 дюймов, Intel Core i5, 8GB RAM, 256GB SSD", "Electronics", Decimal("280000"), Decimal("420000")),
    ("Монитор Samsung 27'' 4K", "ELEC-002", "Профессиональный монитор 27 дюймов, разрешение 4K UHD", "Electronics", Decimal("95000"), Decimal("150000")),
    ("Принтер Canon PIXMA G3420", "ELEC-003", "МФУ для офиса с СНПЧ, печать/сканирование/копирование", "Electronics", Decimal("45000"), Decimal("75000")),
    ("Проектор Epson EH-TW740", "ELEC-004", "Проектор для презентаций, 3300 люмен, Full HD", "Electronics", Decimal("180000"), Decimal("280000")),
    # Office Supplies
    ("Кресло офисное Chairman 420", "OFF-001", "Эргономичное офисное кресло с подлокотниками", "Office Supplies", Decimal("25000"), Decimal("45000")),
    ("Стол рабочий IKEA BEKANT", "OFF-002", "Рабочий стол 160x80 см, регулируемая высота", "Office Supplies", Decimal("55000"), Decimal("95000")),
    ("Шкаф для документов", "OFF-003", "Металлический шкаф с замком, 4 полки", "Office Supplies", Decimal("35000"), Decimal("60000")),
    ("Канцелярский набор", "OFF-004", "Набор для офиса: степлер, дырокол, ножницы, скотч", "Office Supplies", Decimal("3000"), Decimal("5500")),
    # Services
    ("Разработка сайта", "SRV-001", "Создание корпоративного сайта под ключ", "Services", Decimal("200000"), Decimal("400000")),
    ("SEO оптимизация", "SRV-002", "Поисковая оптимизация сайта, 3 месяца", "Services", Decimal("120000"), Decimal("200000")),
    ("Настройка 1С:Бухгалтерия", "SRV-003", "Внедрение и настройка 1С под задачи клиента", "Services", Decimal("150000"), Decimal("280000")),
    ("Обслуживание ПК (месяц)", "SRV-004", "Техническое обслуживание компьютерного парка", "Services", Decimal("40000"), Decimal("80000")),
    # Equipment
    ("Кондиционер LG DualCool", "EQP-001", "Сплит-система 18000 BTU с инверторным компрессором", "Equipment", Decimal("180000"), Decimal("280000")),
    ("Сигнализация Ajax StarterKit", "EQP-002", "Комплект охранной сигнализации с датчиками", "Equipment", Decimal("85000"), Decimal("140000")),
    ("Видеонаблюдение 4 камеры", "EQP-003", "Система видеонаблюдения IP камеры + регистратор", "Equipment", Decimal("120000"), Decimal("200000")),
    ("APC Smart-UPS 1500VA", "EQP-004", "Источник бесперебойного питания для серверов", "Equipment", Decimal("95000"), Decimal("160000")),
    # Software
    ("Microsoft 365 Business (год)", "SOFT-001", "Подписка Microsoft 365 для бизнеса, 5 пользователей", "Software", Decimal("80000"), Decimal("120000")),
    ("Kaspersky Endpoint Security", "SOFT-002", "Антивирус для бизнеса, 10 устройств на год", "Software", Decimal("45000"), Decimal("75000")),
    ("AutoCAD LT (год)", "SOFT-003", "Лицензия AutoCAD LT для 2D проектирования", "Software", Decimal("150000"), Decimal("240000")),
    ("1С:Предприятие 8.3 ПРОФ", "SOFT-004", "Лицензия на 1С:Предприятие для 5 пользователей", "Software", Decimal("280000"), Decimal("450000")),
]

# Deal statuses - 4 deals per status
DEAL_STATUSES = ["new", "preparing_document", "prepaid_account", "at_work", "final_account"]

# Deal templates (title, price range multiplier, status index)
DEAL_TEMPLATES = [
    # new (index 0)
    ("Закупка офисной техники", 1.0),
    ("Обновление ПО", 0.8),
    ("Запрос на мебель", 0.6),
    ("Консультация по IT", 0.4),
    # preparing_document (index 1)
    ("Договор на поставку оборудования", 1.2),
    ("Оформление услуг SEO", 0.7),
    ("Подготовка ТЗ на разработку", 1.5),
    ("Контракт на обслуживание", 0.5),
    # prepaid_account (index 2)
    ("Предоплата за ноутбуки", 1.4),
    ("Аванс на монтаж системы", 0.9),
    ("Частичная оплата проекта", 1.1),
    ("Депозит на оборудование", 0.8),
    # at_work (index 3)
    ("Внедрение CRM системы", 1.6),
    ("Установка видеонаблюдения", 1.0),
    ("Разработка мобильного приложения", 2.0),
    ("Настройка серверной инфраструктуры", 1.3),
    # final_account (index 4)
    ("Завершен проект автоматизации", 1.8),
    ("Поставка техники выполнена", 1.5),
    ("Услуги оказаны полностью", 0.9),
    ("Закрытие годового контракта", 2.5),
]

# Expense categories with realistic amounts
EXPENSES_DATA = [
    # Fixed costs (is_fixed=True)
    ("Rent", "Аренда офиса, 150 кв.м", Decimal("450000"), True, 0),
    ("Salaries", "Зарплата сотрудников (7 человек)", Decimal("2800000"), True, 0),
    ("Salaries", "Налоги на ФОТ", Decimal("520000"), True, 5),
    ("Utilities", "Коммунальные услуги", Decimal("85000"), True, 10),
    ("IT Services", "Хостинг и домены", Decimal("25000"), True, 15),
    ("IT Services", "CRM подписка", Decimal("45000"), True, 20),
    ("Insurance", "Страхование офиса", Decimal("35000"), True, 30),
    # Variable costs (is_fixed=False)  
    ("Marketing", "Контекстная реклама Google", Decimal("180000"), False, 0),
    ("Marketing", "SMM продвижение", Decimal("120000"), False, 5),
    ("Marketing", "Печать рекламных материалов", Decimal("35000"), False, 10),
    ("Office Supplies", "Канцтовары и расходники", Decimal("15000"), False, 0),
    ("Office Supplies", "Картриджи для принтера", Decimal("8000"), False, 15),
    ("Transportation", "ГСМ служебный транспорт", Decimal("65000"), False, 0),
    ("Transportation", "Такси для сотрудников", Decimal("25000"), False, 10),
    ("Equipment Maintenance", "Ремонт техники", Decimal("40000"), False, 20),
    ("Professional Services", "Бухгалтерские услуги", Decimal("80000"), False, 25),
    ("Professional Services", "Юридические консультации", Decimal("50000"), False, 30),
    ("Utilities", "Интернет и связь", Decimal("35000"), False, 0),
    ("Training", "Обучение персонала", Decimal("100000"), False, 45),
    ("Other", "Представительские расходы", Decimal("55000"), False, 15),
]


async def seed_test_user_data():
    """Create demo data for test@example.com user."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("🚀 Создание демо-данных для test@example.com...")
        
        # Find or create test user
        result = await db.execute(text("SELECT id FROM users WHERE email = 'test@example.com'"))
        user_row = result.fetchone()
        
        if not user_row:
            print("❌ Пользователь test@example.com не найден! Создаем...")
            
            # Import password hashing
            from app.core.security import get_password_hash
            
            # Create tenant first
            await db.execute(text("""
                INSERT INTO tenants (name, code, timezone, currency, created_at, updated_at)
                VALUES ('Test Company', 'TEST123', 'Asia/Almaty', 'KZT', :now, :now)
            """), {"now": datetime.now(timezone.utc)})
            await db.commit()
            
            result = await db.execute(text("SELECT id FROM tenants WHERE code = 'TEST123'"))
            tenant_row = result.fetchone()
            tenant_id = tenant_row[0]
            
            # Create user
            hashed_password = get_password_hash("test123")
            await db.execute(text("""
                INSERT INTO users (email, full_name, hashed_password, role, is_active, created_at, updated_at)
                VALUES ('test@example.com', 'Test User', :password, 'admin', 1, :now, :now)
            """), {"password": hashed_password, "now": datetime.now(timezone.utc)})
            await db.commit()
            
            result = await db.execute(text("SELECT id FROM users WHERE email = 'test@example.com'"))
            user_row = result.fetchone()
            user_id = user_row[0]
            
            # Associate user with tenant
            await db.execute(text("""
                INSERT INTO user_tenant_association (user_id, tenant_id)
                VALUES (:uid, :tid)
            """), {"uid": user_id, "tid": tenant_id})
            await db.commit()
            
            print(f"✅ Создан пользователь test@example.com с tenant_id: {tenant_id}")
        else:
            user_id = user_row[0]
            # Get tenant for user
            result = await db.execute(text("""
                SELECT tenant_id FROM user_tenant_association WHERE user_id = :uid LIMIT 1
            """), {"uid": user_id})
            tenant_row = result.fetchone()
            if not tenant_row:
                print("❌ Пользователь не связан с tenant! Создаем tenant...")
                await db.execute(text("""
                    INSERT INTO tenants (name, code, timezone, currency, created_at, updated_at)
                    VALUES ('Test Company', 'TESTCO', 'Asia/Almaty', 'KZT', :now, :now)
                """), {"now": datetime.now(timezone.utc)})
                await db.commit()
                result = await db.execute(text("SELECT id FROM tenants ORDER BY id DESC LIMIT 1"))
                tenant_row = result.fetchone()
                tenant_id = tenant_row[0]
                await db.execute(text("""
                    INSERT INTO user_tenant_association (user_id, tenant_id)
                    VALUES (:uid, :tid)
                """), {"uid": user_id, "tid": tenant_id})
                await db.commit()
            else:
                tenant_id = tenant_row[0]
            print(f"✅ Найден пользователь test@example.com (user_id: {user_id}, tenant_id: {tenant_id})")
        
        # Check if all data already exists
        result = await db.execute(text("SELECT COUNT(*) FROM clients WHERE tenant_id = :tid"), {"tid": tenant_id})
        client_count = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM products WHERE tenant_id = :tid"), {"tid": tenant_id})
        product_count = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM deals WHERE tenant_id = :tid"), {"tid": tenant_id})
        deal_count = result.scalar()
        
        result = await db.execute(text("SELECT COUNT(*) FROM expenses WHERE tenant_id = :tid"), {"tid": tenant_id})
        expense_count = result.scalar()
        
        # Only skip if ALL data is complete
        if client_count >= 20 and product_count >= 20 and deal_count >= 20 and expense_count >= 20:
            print(f"ℹ️  Уже есть все данные: {client_count} контактов, {product_count} продуктов, {deal_count} сделок, {expense_count} расходов. Пропускаем создание.")
        else:
            # Delete existing data to start fresh
            print("🗑️  Очищаем существующие данные...")
            await db.execute(text("DELETE FROM deal_items WHERE deal_id IN (SELECT id FROM deals WHERE tenant_id = :tid)"), {"tid": tenant_id})
            await db.execute(text("DELETE FROM deals WHERE tenant_id = :tid"), {"tid": tenant_id})
            await db.execute(text("DELETE FROM expenses WHERE tenant_id = :tid"), {"tid": tenant_id})
            await db.execute(text("DELETE FROM inventory WHERE product_id IN (SELECT id FROM products WHERE tenant_id = :tid)"), {"tid": tenant_id})
            await db.execute(text("DELETE FROM products WHERE tenant_id = :tid"), {"tid": tenant_id})
            await db.execute(text("DELETE FROM clients WHERE tenant_id = :tid"), {"tid": tenant_id})
            await db.commit()
            
            # Create 20 contacts
            print("👥 Создаем 20 контактов...")
            client_ids = []
            for name, company, email, phone, address in CONTACTS_DATA:
                now = datetime.now(timezone.utc)
                await db.execute(text("""
                    INSERT INTO clients (tenant_id, name, company, email, phone, address, created_at, updated_at)
                    VALUES (:tid, :name, :company, :email, :phone, :address, :now, :now)
                """), {
                    "tid": tenant_id,
                    "name": name,
                    "company": company,
                    "email": email,
                    "phone": phone,
                    "address": address,
                    "now": now
                })
            await db.commit()
            
            result = await db.execute(text("SELECT id FROM clients WHERE tenant_id = :tid ORDER BY id"), {"tid": tenant_id})
            client_ids = [row[0] for row in result.fetchall()]
            print(f"   ✅ Создано {len(client_ids)} контактов")
            
            # Create 20 products
            print("📦 Создаем 20 продуктов...")
            product_ids = []
            for title, sku, description, category, cost, price in PRODUCTS_DATA:
                now = datetime.now(timezone.utc)
                await db.execute(text("""
                    INSERT INTO products (tenant_id, title, sku, description, category, default_cost, default_price, currency, created_at, updated_at)
                    VALUES (:tid, :title, :sku, :desc, :cat, :cost, :price, 'KZT', :now, :now)
                """), {
                    "tid": tenant_id,
                    "title": title,
                    "sku": sku,
                    "desc": description,
                    "cat": category,
                    "cost": float(cost),
                    "price": float(price),
                    "now": now
                })
            await db.commit()
            
            result = await db.execute(text("SELECT id, default_cost, default_price FROM products WHERE tenant_id = :tid ORDER BY id"), {"tid": tenant_id})
            products = [(row[0], row[1], row[2]) for row in result.fetchall()]
            product_ids = [p[0] for p in products]
            print(f"   ✅ Создано {len(product_ids)} продуктов")
            
            # Create 20 deals (4 per status)
            print("💼 Создаем 20 сделок (по 4 в каждом статусе)...")
            deal_count = 0
            now = datetime.now(timezone.utc)
            
            for status_idx, status in enumerate(DEAL_STATUSES):
                for i in range(4):
                    template_idx = status_idx * 4 + i
                    title, price_mult = DEAL_TEMPLATES[template_idx]
                    client_id = client_ids[template_idx % len(client_ids)]
                    
                    # Select 1-3 products for this deal
                    num_products = (template_idx % 3) + 1
                    deal_products = []
                    for j in range(num_products):
                        prod_idx = (template_idx + j) % len(products)
                        prod_id, prod_cost, prod_price = products[prod_idx]
                        qty = float((j % 3) + 1)  # 1, 2, or 3
                        deal_products.append((prod_id, float(prod_cost) if prod_cost else 0, float(prod_price) if prod_price else 0, qty))
                    
                    # Calculate totals
                    total_price = sum(p[2] * p[3] for p in deal_products)
                    total_cost = sum(p[1] * p[3] for p in deal_products)
                    margin = total_price - total_cost
                    
                    # Days ago for created_at
                    days_ago = 90 - (status_idx * 15) - (i * 3)
                    created_at = now - timedelta(days=max(1, days_ago))
                    
                    # Completion date for closed deals
                    closed_at = None
                    if status == "final_account":
                        closed_at = created_at + timedelta(days=10)
                    
                    await db.execute(text("""
                        INSERT INTO deals (tenant_id, client_id, title, total_price, total_cost, margin, currency, status, is_available_to_all, created_at, updated_at, closed_at)
                        VALUES (:tid, :cid, :title, :price, :cost, :margin, 'KZT', :status, 1, :created, :created, :closed)
                    """), {
                        "tid": tenant_id,
                        "cid": client_id,
                        "title": title,
                        "price": total_price,
                        "cost": total_cost,
                        "margin": margin,
                        "status": status,
                        "created": created_at,
                        "closed": closed_at
                    })
                    await db.commit()
                    
                    # Get the deal ID
                    result = await db.execute(text("SELECT id FROM deals WHERE tenant_id = :tid ORDER BY id DESC LIMIT 1"), {"tid": tenant_id})
                    deal_id = result.fetchone()[0]
                    
                    # Create deal items
                    for prod_id, prod_cost, prod_price, qty in deal_products:
                        item_total_price = prod_price * qty
                        item_total_cost = prod_cost * qty
                        await db.execute(text("""
                            INSERT INTO deal_items (deal_id, product_id, quantity, unit_price, unit_cost, total_price, total_cost, created_at, updated_at)
                            VALUES (:did, :pid, :qty, :uprice, :ucost, :tprice, :tcost, :now, :now)
                        """), {
                            "did": deal_id,
                            "pid": prod_id,
                            "qty": float(qty),
                            "uprice": float(prod_price),
                            "ucost": float(prod_cost),
                            "tprice": float(item_total_price),
                            "tcost": float(item_total_cost),
                            "now": now
                        })
                    await db.commit()
                    deal_count += 1
            
            print(f"   ✅ Создано {deal_count} сделок с товарами")
            
            # Create expenses
            print("💰 Создаем расходы...")
            expense_count = 0
            today = date.today()
            
            for category, description, amount, is_fixed, days_offset in EXPENSES_DATA:
                expense_date = today - timedelta(days=days_offset)
                await db.execute(text("""
                    INSERT INTO expenses (tenant_id, amount, currency, category, description, date, is_fixed, created_at)
                    VALUES (:tid, :amount, 'KZT', :cat, :desc, :date, :is_fixed, :now)
                """), {
                    "tid": tenant_id,
                    "amount": float(amount),
                    "cat": category,
                    "desc": description,
                    "date": expense_date,
                    "is_fixed": 1 if is_fixed else 0,
                    "now": datetime.now(timezone.utc)
                })
                expense_count += 1
            
            await db.commit()
            print(f"   ✅ Создано {expense_count} расходов")
        
        # Summary
        print("\n📊 Итоговая статистика:")
        
        result = await db.execute(text("SELECT COUNT(*) FROM clients WHERE tenant_id = :tid"), {"tid": tenant_id})
        print(f"   • Контакты: {result.scalar()}")
        
        result = await db.execute(text("SELECT COUNT(*) FROM products WHERE tenant_id = :tid"), {"tid": tenant_id})
        print(f"   • Продукты: {result.scalar()}")
        
        result = await db.execute(text("""
            SELECT status, COUNT(*) FROM deals WHERE tenant_id = :tid GROUP BY status ORDER BY status
        """), {"tid": tenant_id})
        print("   • Сделки по статусам:")
        for row in result.fetchall():
            status_name = {
                "new": "Новые",
                "preparing_document": "Подготовка документов",
                "prepaid_account": "Предоплата",
                "at_work": "В работе",
                "final_account": "Завершены"
            }.get(row[0], row[0])
            print(f"     - {status_name}: {row[1]}")
        
        result = await db.execute(text("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM expenses WHERE tenant_id = :tid"), {"tid": tenant_id})
        row = result.fetchone()
        print(f"   • Расходы: {row[0]} записей на сумму {row[1]:,.0f} KZT")
        
        print("\n✅ Демо-данные успешно созданы!")
        print("🔐 Войдите: test@example.com / test123")
        print("🌐 Откройте: http://localhost:5173")
    
    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(seed_test_user_data())
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
