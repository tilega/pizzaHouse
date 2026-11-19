"""Weekly featured dish for the guest/customer menu.

A rolling seven-day window is used. Orders with a canceled status are
excluded, and drinks/sauces can never become the featured dish.
"""
from datetime import datetime, timedelta
from database import db_connection


ELIGIBLE_CATEGORIES = ('Піца', 'Закуска')


def get_weekly_special(reference_time=None):
    """Return a dict describing the most-ordered pizza/snack or None.

    Sort by total portions, then distinct orders, then name and ID to
    make tied rankings deterministic. Reads current menu images and names.
    """
    now = reference_time or datetime.now()
    start = now - timedelta(days=7)
    with db_connection() as conn:
        row = conn.execute('''
            SELECT m.id, m.name, m.category, m.image_path,
                   SUM(lines.quantity) AS portions,
                   COUNT(DISTINCT o.order_id) AS order_count
            FROM order_lines AS lines
            JOIN orders AS o ON o.order_id = lines.order_id
            JOIN menu_items AS m ON m.id = lines.menu_id
            WHERE o.order_date >= ? AND o.order_date <= ?
              AND o.status <> 'Скасоване'
              AND m.category IN (?, ?)
            GROUP BY m.id
            ORDER BY portions DESC, order_count DESC,
                     m.name COLLATE NOCASE ASC, m.id ASC
            LIMIT 1
        ''', (start.strftime('%Y-%m-%d %H:%M:%S'),
              now.strftime('%Y-%m-%d %H:%M:%S'),
              *ELIGIBLE_CATEGORIES)).fetchone()
    return dict(row) if row else None
