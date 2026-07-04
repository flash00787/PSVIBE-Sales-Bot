from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.auth import get_current_user
from datetime import datetime
import json

router = APIRouter()


class PaymentBreakdownItem(BaseModel):
    method: str
    amount: float


class PurchaseItemReq(BaseModel):
    variant_id: int
    qty: int
    unit_cost: float


class PurchaseCreate(BaseModel):
    supplier_id: Optional[int] = None
    purchase_date: str
    items: List[PurchaseItemReq]
    paid_amount: float = 0
    notes: Optional[str] = None
    payment_breakdown: Optional[List[PaymentBreakdownItem]] = None


@router.get('')
def list_purchases(date_from: str = Query(None), date_to: str = Query(None),
                   supplier_id: int = Query(None), page: int = 1, limit: int = 50,
                   user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        where = ['1=1']; params = []
        if date_from: where.append('p.purchase_date>=%s'); params.append(date_from)
        if date_to: where.append('p.purchase_date<=%s'); params.append(date_to)
        if supplier_id: where.append('p.supplier_id=%s'); params.append(supplier_id)
        w = ' AND '.join(where)
        cur.execute(f'SELECT COUNT(*) as total FROM purchases p WHERE {w}', params)
        total = cur.fetchone()['total']
        cur.execute(f'''
            SELECT p.*, s.name as supplier_name FROM purchases p
            LEFT JOIN suppliers s ON p.supplier_id=s.id
            WHERE {w} ORDER BY p.id DESC LIMIT %s OFFSET %s
        ''', params + [limit, (page-1)*limit])
        items = cur.fetchall()
        for p_item in items:
            if p_item.get('payment_breakdown') and isinstance(p_item['payment_breakdown'], str):
                try:
                    p_item['payment_breakdown'] = json.loads(p_item['payment_breakdown'])
                except:
                    pass
        return {'items': items, 'total': total, 'page': page}


@router.get('/{purchase_id}')
def get_purchase(purchase_id: int, user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        cur.execute('''SELECT p.*, s.name as supplier_name FROM purchases p
                       LEFT JOIN suppliers s ON p.supplier_id=s.id WHERE p.id=%s''', (purchase_id,))
        p = cur.fetchone()
        if not p: raise HTTPException(404, 'Purchase not found')
        cur.execute('''SELECT pi.*, pv.size, pv.color, pr.name as product_name, pr.code as product_code
                       FROM purchase_items pi
                       JOIN product_variants pv ON pi.variant_id=pv.id
                       JOIN products pr ON pv.product_id=pr.id
                       WHERE pi.purchase_id=%s''', (purchase_id,))
        p['items'] = cur.fetchall()
        if p.get('payment_breakdown') and isinstance(p['payment_breakdown'], str):
            try:
                p['payment_breakdown'] = json.loads(p['payment_breakdown'])
            except:
                pass
        return p


@router.post('')
def create_purchase(data: PurchaseCreate, user=Depends(get_current_user)):
    if not data.items: raise HTTPException(400, 'No items')
    with get_db() as db:
        cur = db.cursor()
        # GRN number
        cur.execute("SELECT COUNT(*) as cnt FROM purchases WHERE purchase_date=CURDATE()")
        today_count = cur.fetchone()['cnt'] + 1
        grn = f"GRN-{datetime.now().strftime('%Y%m%d')}-{today_count:04d}"

        total = sum(i.qty * i.unit_cost for i in data.items)

        # Payment breakdown
        breakdown_json = None
        if data.payment_breakdown:
            breakdown_total = sum(pb.amount for pb in data.payment_breakdown)
            if abs(breakdown_total - data.paid_amount) > 0.01:
                raise HTTPException(400,
                                    f'Payment breakdown total ({breakdown_total}) must equal paid amount ({data.paid_amount})')
            breakdown_json = json.dumps([pb.model_dump() for pb in data.payment_breakdown])

        cur.execute('''INSERT INTO purchases (grn_number,supplier_id,purchase_date,total_amount,paid_amount,notes,payment_breakdown)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)''',
                    (grn, data.supplier_id, data.purchase_date, total, data.paid_amount, data.notes, breakdown_json))
        pid = cur.lastrowid

        for item in data.items:
            cur.execute('INSERT INTO purchase_items (purchase_id,variant_id,qty,unit_cost) VALUES (%s,%s,%s,%s)',
                        (pid, item.variant_id, item.qty, item.unit_cost))
            # Add stock
            cur.execute('UPDATE product_variants SET stock_qty=stock_qty+%s WHERE id=%s', (item.qty, item.variant_id))
            cur.execute('SELECT stock_qty, product_id FROM product_variants WHERE id=%s', (item.variant_id,))
            v = cur.fetchone()
            cur.execute('INSERT INTO stock_movements (variant_id,movement_type,reference_type,reference_id,qty_change,qty_after) VALUES (%s,%s,%s,%s,%s,%s)',
                        (item.variant_id, 'purchase', 'purchase', pid, item.qty, v['stock_qty']))
            # Update product cost price if changed
            cur.execute('UPDATE products SET cost_price=%s WHERE id=%s', (item.unit_cost, v['product_id']))

        # Record payment transactions
        try:
            from app.routes.payment_accounts import record_payment_transaction
            if data.payment_breakdown:
                for pb in data.payment_breakdown:
                    record_payment_transaction(db, cur, pb.method, pb.amount, 'purchase',
                                              'purchase', pid, f'Purchase {grn}')
            elif data.paid_amount > 0:
                record_payment_transaction(db, cur, 'Cash Register', data.paid_amount, 'purchase',
                                          'purchase', pid, f'Purchase {grn}')
        except Exception:
            pass

        return {'id': pid, 'grn': grn, 'total': total, 'message': 'Purchase created'}
