"""Відгуки про страви. Один відгук від клієнта на одну позицію меню."""
from database import db_connection


def initialize_reviews_database():
    """Безпечне створення таблиці; існуючі дані не змінюються."""
    with db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS product_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_id INTEGER NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
                customer_id TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(menu_id, customer_id)
            )
        """)
        conn.execute('CREATE INDEX IF NOT EXISTS idx_product_reviews_menu ON product_reviews(menu_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_product_reviews_customer ON product_reviews(customer_id)')


def save_review(menu_id, customer_id, rating, comment):
    """Створити чи оновити свій відгук; не дозволяти підмінювати чужий."""
    if not customer_id:
        raise ValueError('Щоб залишити відгук, увійдіть у свій акаунт')
    if type(rating) is not int or not 1 <= rating <= 5:
        raise ValueError('Оберіть оцінку від 1 до 5')
    if not isinstance(comment, str):
        raise ValueError('Відгук має бути текстом')
    comment = comment.strip()
    if not 3 <= len(comment) <= 1000:
        raise ValueError('Коментар має містити від 3 до 1000 символів')
    with db_connection() as conn:
        if conn.execute('SELECT 1 FROM menu_items WHERE id=?', (menu_id,)).fetchone() is None:
            raise ValueError('Товар не знайдено')
        if conn.execute('SELECT 1 FROM customer_accounts WHERE customer_id=?',
                        (customer_id,)).fetchone() is None:
            raise ValueError('Потрібен зареєстрований акаунт')
        conn.execute("""
            INSERT INTO product_reviews (menu_id, customer_id, rating, comment)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(menu_id, customer_id) DO UPDATE SET
                rating=excluded.rating,
                comment=excluded.comment,
                updated_at=CURRENT_TIMESTAMP
        """, (menu_id, customer_id, rating, comment))


def get_own_review(menu_id, customer_id):
    if not customer_id:
        return None
    with db_connection() as conn:
        row = conn.execute('SELECT * FROM product_reviews WHERE menu_id=? AND customer_id=?',
                           (menu_id, customer_id)).fetchone()
        return dict(row) if row else None


def delete_own_review(menu_id, customer_id):
    if not customer_id:
        raise ValueError('Потрібна авторизація')
    with db_connection() as conn:
        result = conn.execute('DELETE FROM product_reviews WHERE menu_id=? AND customer_id=?',
                              (menu_id, customer_id))
        if result.rowcount == 0:
            raise ValueError('Ваш відгук не знайдено')


def list_product_reviews(menu_id):
    with db_connection() as conn:
        rows=conn.execute("""
            SELECT r.id, r.menu_id, r.customer_id, r.rating, r.comment,
                   r.created_at, r.updated_at,
                   c.first_name, c.last_name
            FROM product_reviews r JOIN customers c ON c.customer_id=r.customer_id
            WHERE r.menu_id=? ORDER BY r.updated_at DESC, r.id DESC
        """, (menu_id,)).fetchall()
    return [dict(row) for row in rows]


def review_stats_for_menu():
    """Підрахувати середню оцінку та кількість одразу для всіх товарів."""
    with db_connection() as conn:
        rows=conn.execute("""
            SELECT menu_id, COUNT(*) AS count, AVG(rating) AS average
            FROM product_reviews GROUP BY menu_id
        """).fetchall()
    return {row['menu_id']:{'count':row['count'],'average':row['average']} for row in rows}


def list_all_reviews():
    with db_connection() as conn:
        rows=conn.execute("""
            SELECT r.id,r.menu_id,r.customer_id,r.rating,r.comment,r.created_at,r.updated_at,
                   m.name AS product_name,c.first_name,c.last_name
            FROM product_reviews r
            JOIN menu_items m ON m.id=r.menu_id
            JOIN customers c ON c.customer_id=r.customer_id
            ORDER BY r.updated_at DESC,r.id DESC
        """).fetchall()
    return [dict(row) for row in rows]


def delete_review_as_admin(review_id):
    """Викликати тільки з адміністративного розділу додатка."""
    with db_connection() as conn:
        result=conn.execute('DELETE FROM product_reviews WHERE id=?', (review_id,))
        if result.rowcount == 0:
            raise ValueError('Відгук не знайдено')
