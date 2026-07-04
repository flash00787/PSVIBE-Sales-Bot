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


class SaleItemReq(BaseModel):
    variant_id: int
    qty: int
    unit_price: float


class SaleCreate(BaseModel):
    customer_id: Optional[int] = None
    items: List[SaleItemReq]
    discount_amount: float = 0
    discount_type: str = 'flat'
    payment_method: str = 'Cash'
    paid_amount: float = 0
    notes: Optional[str] = None
    payment_breakdown: Optional[List[PaymentBreakdownItem]] = None


class CreditPayment(BaseModel):
    customer_id: int
    amount: float
    payment_method: str = 'Cash'
    notes: Optional[str] = None


@router.get('')
def list_sales(
    date_from: str = Query(None), date_to: str = Query(None),
    customer_id: int = Query(None), product_id: int = Query(None),
    payment_status: str = Query(None),
    page: int = 1, limit: int = 50,
    user=Depends(get_current_user)
):
    with get_db() as db:
        cur = db.cursor()
        where = ['s.is_void=0']
        params = []
        if date_from: where.append('DATE(s.sale_date)>=%s'); params.append(date_from)
        if date_to: where.append('DATE(s.sale_date)<=%s'); params.append(date_to)
        if customer_id: where.append('s.customer_id=%s'); params.append(customer_id)
        if payment_status: where.append('s.payment_status=%s'); params.append(payment_status)
        if product_id:
            where.append('s.id IN (SELECT DISTINCT si.sale_id FROM sale_items si JOIN product_variants pv ON si.variant_id=pv.id WHERE pv.product_id=%s)')
            params.append(product_id)
        w = ' AND '.join(where)
        cur.execute(f'SELECT COUNT(*) as total FROM sales s WHERE {w}', params)
        total = cur.fetchone()['total']
        cur.execute(f'''
            SELECT s.*, c.name as customer_name
            FROM sales s LEFT JOIN customers c ON s.customer_id=c.id
            WHERE {w} ORDER BY s.id DESC LIMIT %s OFFSET %s
        ''', params + [limit, (page-1)*limit])
        items = cur.fetchall()
        # Parse payment_breakdown JSON for each sale
        for s in items:
            if s.get('payment_breakdown') and isinstance(s['payment_breakdown'], str):
                try:
                    s['payment_breakdown'] = json.loads(s['payment_breakdown'])
                except:
                    pass
        return {'items': items, 'total': total, 'page': page}


@router.get('/{sale_id}')
def get_sale(sale_id: int, user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        cur.execute('''SELECT s.*, c.name as customer_name, c.phone as customer_phone
                       FROM sales s LEFT JOIN customers c ON s.customer_id=c.id WHERE s.id=%s''', (sale_id,))
        sale = cur.fetchone()
        if not sale: raise HTTPException(404, 'Sale not found')
        cur.execute('''SELECT si.*, pv.size, pv.color, p.name as product_name, p.code as product_code
                       FROM sale_items si
                       JOIN product_variants pv ON si.variant_id=pv.id
                       JOIN products p ON pv.product_id=p.id
                       WHERE si.sale_id=%s''', (sale_id,))
        sale['items'] = cur.fetchall()
        # Parse payment_breakdown JSON
        if sale.get('payment_breakdown') and isinstance(sale['payment_breakdown'], str):
            try:
                sale['payment_breakdown'] = json.loads(sale['payment_breakdown'])
            except:
                pass
        return sale


@router.post('')
def create_sale(data: SaleCreate, user=Depends(get_current_user)):
    if not data.items: raise HTTPException(400, 'No items in sale')
    with get_db() as db:
        cur = db.cursor()
        # Generate invoice number
        cur.execute("SELECT COUNT(*) as cnt FROM sales WHERE DATE(sale_date)=CURDATE()")
        today_count = cur.fetchone()['cnt'] + 1
        invoice = f"AKT-{datetime.now().strftime('%Y%m%d')}-{today_count:04d}"

        # Calculate subtotal + validate stock
        subtotal = 0
        cost_total = 0
        for item in data.items:
            cur.execute('SELECT stock_qty, product_id FROM product_variants WHERE id=%s', (item.variant_id,))
            v = cur.fetchone()
            if not v: raise HTTPException(404, f'Variant {item.variant_id} not found')
            if v['stock_qty'] < item.qty: raise HTTPException(400, f'Insufficient stock for variant {item.variant_id}')
            subtotal += item.qty * item.unit_price
            cur.execute('SELECT cost_price FROM products WHERE id=%s', (v['product_id'],))
            p = cur.fetchone()
            cost_total += item.qty * float(p['cost_price'])

        # Discount
        disc = data.discount_amount
        if data.discount_type == 'percent':
            disc = subtotal * data.discount_amount / 100
        total = subtotal - disc

        # Payment breakdown handling
        breakdown_json = None
        if data.payment_breakdown:
            breakdown_total = sum(pb.amount for pb in data.payment_breakdown)
            # Validate breakdown totals match grand total
            if abs(breakdown_total - total) > 0.01:
                raise HTTPException(400, f'Payment breakdown total ({breakdown_total}) must equal grand total ({total})')
            breakdown_json = json.dumps([pb.model_dump() for pb in data.payment_breakdown])
            # Determine payment method string from breakdown
            methods = list(set(pb.method for pb in data.payment_breakdown))
            pmethod = ' + '.join(methods) if len(methods) <= 2 else 'Split'
        else:
            pmethod = data.payment_method

        # Payment status
        pstatus = 'Paid' if data.paid_amount >= total else ('Partial' if data.paid_amount > 0 else 'Unpaid')
        is_credit = pstatus in ('Partial', 'Unpaid')

        cur.execute('''INSERT INTO sales (invoice_number,customer_id,sale_date,subtotal,discount_amount,discount_type,
                       total_amount,payment_method,payment_status,paid_amount,notes,payment_breakdown)
                       VALUES (%s,%s,NOW(),%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (invoice, data.customer_id, subtotal, disc, data.discount_type,
                     total, pmethod, pstatus, data.paid_amount, data.notes, breakdown_json))
        sale_id = cur.lastrowid

        for item in data.items:
            cur.execute('INSERT INTO sale_items (sale_id,variant_id,qty,unit_price,cost_at_sale) VALUES (%s,%s,%s,%s,0)',
                        (sale_id, item.variant_id, item.qty, item.unit_price))
            # Deduct stock
            cur.execute('UPDATE product_variants SET stock_qty=stock_qty-%s WHERE id=%s', (item.qty, item.variant_id))
            cur.execute('SELECT stock_qty FROM product_variants WHERE id=%s', (item.variant_id,))
            new_qty = cur.fetchone()['stock_qty']
            cur.execute('INSERT INTO stock_movements (variant_id,movement_type,reference_type,reference_id,qty_change,qty_after) VALUES (%s,%s,%s,%s,%s,%s)',
                        (item.variant_id, 'sale', 'sale', sale_id, -item.qty, new_qty))

        # Handle credit
        if is_credit and data.customer_id:
            credit_due = total - data.paid_amount
            cur.execute('UPDATE customers SET current_credit=current_credit+%s WHERE id=%s', (credit_due, data.customer_id))

        # Record payment transactions per account
        try:
            from app.routes.payment_accounts import record_payment_transaction
            if data.payment_breakdown:
                for pb in data.payment_breakdown:
                    record_payment_transaction(db, cur, pb.method, pb.amount, 'sale',
                                              'sale', sale_id, f'Sale {invoice}')
            else:
                record_payment_transaction(db, cur, data.payment_method, data.paid_amount or total, 'sale',
                                          'sale', sale_id, f'Sale {invoice}')
        except Exception:
            pass  # Don't fail sale if payment account tracking isn't set up

        return {'id': sale_id, 'invoice': invoice, 'total': total, 'message': 'Sale created'}


@router.put('/{sale_id}/void')
def void_sale(sale_id: int, reason: str = Query(''), user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        cur.execute('SELECT * FROM sales WHERE id=%s AND is_void=0', (sale_id,))
        sale = cur.fetchone()
        if not sale: raise HTTPException(404, 'Sale not found or already voided')
        cur.execute('SELECT * FROM sale_items WHERE sale_id=%s', (sale_id,))
        items = cur.fetchall()
        for item in items:
            cur.execute('UPDATE product_variants SET stock_qty=stock_qty+%s WHERE id=%s', (item['qty'], item['variant_id']))
            cur.execute('SELECT stock_qty FROM product_variants WHERE id=%s', (item['variant_id'],))
            new_qty = cur.fetchone()['stock_qty']
            cur.execute('INSERT INTO stock_movements (variant_id,movement_type,reference_type,reference_id,qty_change,qty_after,notes) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                        (item['variant_id'], 'sale_return', 'void', sale_id, item['qty'], new_qty, f'Void sale {sale["invoice_number"]}'))
        if sale['customer_id'] and sale['payment_status'] in ('Partial', 'Unpaid'):
            credit_return = sale['total_amount'] - sale['paid_amount']
            cur.execute('UPDATE customers SET current_credit=GREATEST(0,current_credit-%s) WHERE id=%s', (credit_return, sale['customer_id']))
        cur.execute('UPDATE sales SET is_void=1, void_reason=%s WHERE id=%s', (reason, sale_id))
        return {'message': 'Sale voided'}


# ── Credit Payments ──
@router.post('/credit-payments')
def add_credit_payment(data: CreditPayment, user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        cur.execute('INSERT INTO credit_payments (customer_id,amount,payment_method,payment_date,notes) VALUES (%s,%s,%s,NOW(),%s)',
                    (data.customer_id, data.amount, data.payment_method, data.notes))
        cur.execute('UPDATE customers SET current_credit=GREATEST(0,current_credit-%s) WHERE id=%s', (data.amount, data.customer_id))
        cpid = cur.lastrowid
        # Track in payment accounts
        try:
            from app.routes.payment_accounts import record_payment_transaction
            record_payment_transaction(db, cur, data.payment_method, data.amount, 'sale',
                                      'credit_payment', cpid, f'Credit payment from customer {data.customer_id}')
        except Exception:
            pass
        return {'id': cpid, 'message': 'Payment recorded'}


@router.get('/credit-payments/list')
def list_credit_payments(customer_id: int = Query(None), date_from: str = Query(None), date_to: str = Query(None),
                         page: int = 1, limit: int = 50, user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        where = ['1=1']; params = []
        if customer_id: where.append('cp.customer_id=%s'); params.append(customer_id)
        if date_from: where.append('DATE(cp.payment_date)>=%s'); params.append(date_from)
        if date_to: where.append('DATE(cp.payment_date)<=%s'); params.append(date_to)
        w = ' AND '.join(where)
        cur.execute(f'SELECT COUNT(*) as total FROM credit_payments cp WHERE {w}', params)
        total = cur.fetchone()['total']
        cur.execute(f'''
            SELECT cp.*, c.name as customer_name FROM credit_payments cp
            JOIN customers c ON cp.customer_id=c.id
            WHERE {w} ORDER BY cp.id DESC LIMIT %s OFFSET %s
        ''', params + [limit, (page-1)*limit])
        return {'items': cur.fetchall(), 'total': total, 'page': page}
