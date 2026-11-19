"""Статистика на основі реальних замовлень Pizza House."""
from datetime import datetime, timedelta
from database import db_connection

def get_statistics(days=None):
    since = ((datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
             if days is not None else None)
    condition = "WHERE order_date >= ?" if since else ""
    params = (since,) if since else ()
    with db_connection() as conn:
        totals = conn.execute(f"""
            SELECT COUNT(*) AS count_all,
                   COALESCE(SUM(CASE WHEN status='Виконане' THEN total_cents ELSE 0 END),0) AS revenue,
                   SUM(CASE WHEN status='Виконане' THEN 1 ELSE 0 END) AS count_done,
                   SUM(CASE WHEN status='Скасоване' THEN 1 ELSE 0 END) AS count_cancelled
            FROM orders {condition}""",params).fetchone()
        status = conn.execute(f"""
            SELECT status, COUNT(*) AS qty FROM orders {condition}
            GROUP BY status ORDER BY qty DESC""",params).fetchall()
        # Продані порції, а не кількість чеків. Скасовані замовлення виключені.
        top = conn.execute(f"""
            SELECT l.item_name AS name, SUM(l.quantity) AS qty,
                   COUNT(DISTINCT o.order_id) AS orders_count
            FROM order_lines l JOIN orders o ON o.order_id=l.order_id
            WHERE o.status <> 'Скасоване' {'AND o.order_date >= ?' if since else ''}
            GROUP BY l.item_name ORDER BY qty DESC, name COLLATE NOCASE LIMIT 10
        """,params).fetchall()
        daily = conn.execute(f"""
            SELECT substr(order_date,1,10) AS day, COUNT(*) AS qty
            FROM orders {condition}
            GROUP BY substr(order_date,1,10) ORDER BY day DESC LIMIT 14
        """,params).fetchall()
        kinds = conn.execute(f"""
            SELECT order_type, COUNT(*) AS qty FROM orders {condition}
            GROUP BY order_type ORDER BY qty DESC
        """,params).fetchall()
    count = totals['count_all'] or 0
    done = totals['count_done'] or 0
    return {'count':count,'completed':done,'cancelled':totals['count_cancelled'] or 0,
            'revenue_cents':totals['revenue'] or 0,
            'average_cents':round(totals['revenue']/done) if done else 0,
            'top':[dict(r) for r in top],
            'statuses':[dict(r) for r in status],
            'daily':list(reversed([dict(r) for r in daily])),
            'kinds':[dict(r) for r in kinds]}
