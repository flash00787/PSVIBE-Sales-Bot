from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.auth import get_current_user

router = APIRouter()


class PaymentAccountCreate(BaseModel):
    name: str
    type: str = 'cash'
    account_number: Optional[str] = None
    balance: float = 0


class PaymentAccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    account_number: Optional[str] = None
    is_active: Optional[int] = None


class AccountTransaction(BaseModel):
    account_id: int
    transaction_type: str
    amount: float
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: Optional[str] = None


@router.get('')
def list_accounts(user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        cur.execute('SELECT * FROM payment_accounts ORDER BY id')
        return {'items': cur.fetchall()}


@router.post('')
def create_account(data: PaymentAccountCreate, user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        cur.execute(
            'INSERT INTO payment_accounts (name, type, account_number, balance) VALUES (%s,%s,%s,%s)',
            (data.name, data.type, data.account_number, data.balance))
        return {'id': cur.lastrowid, 'message': 'Account created'}


@router.put('/{account_id}')
def update_account(account_id: int, data: PaymentAccountUpdate, user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        cur.execute('SELECT * FROM payment_accounts WHERE id=%s', (account_id,))
        if not cur.fetchone():
            raise HTTPException(404, 'Account not found')
        updates = []
        params = []
        if data.name is not None:
            updates.append('name=%s')
            params.append(data.name)
        if data.type is not None:
            updates.append('type=%s')
            params.append(data.type)
        if data.account_number is not None:
            updates.append('account_number=%s')
            params.append(data.account_number)
        if data.is_active is not None:
            updates.append('is_active=%s')
            params.append(data.is_active)
        if updates:
            params.append(account_id)
            cur.execute(f'UPDATE payment_accounts SET {", ".join(updates)} WHERE id=%s', params)
        return {'message': 'Account updated'}


@router.get('/{account_id}')
def get_account(account_id: int, user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        cur.execute('SELECT * FROM payment_accounts WHERE id=%s', (account_id,))
        acc = cur.fetchone()
        if not acc:
            raise HTTPException(404, 'Account not found')
        return acc


@router.get('/{account_id}/transactions')
def get_transactions(account_id: int, page: int = 1, limit: int = 50,
                     user=Depends(get_current_user)):
    with get_db() as db:
        cur = db.cursor()
        cur.execute('SELECT COUNT(*) as total FROM payment_transactions WHERE account_id=%s', (account_id,))
        total = cur.fetchone()['total']
        cur.execute(
            'SELECT * FROM payment_transactions WHERE account_id=%s ORDER BY id DESC LIMIT %s OFFSET %s',
            (account_id, limit, (page - 1) * limit))
        return {'items': cur.fetchall(), 'total': total, 'page': page}


@router.post('/transactions')
def add_transaction(data: AccountTransaction, user=Depends(get_current_user)):
    """Manual deposit or withdrawal"""
    with get_db() as db:
        cur = db.cursor()
        cur.execute('SELECT * FROM payment_accounts WHERE id=%s', (data.account_id,))
        acc = cur.fetchone()
        if not acc:
            raise HTTPException(404, 'Account not found')

        if data.transaction_type == 'deposit':
            new_balance = float(acc['balance']) + data.amount
        elif data.transaction_type == 'withdrawal':
            new_balance = float(acc['balance']) - data.amount
        else:
            new_balance = float(acc['balance'])

        cur.execute(
            'INSERT INTO payment_transactions (account_id, transaction_type, reference_type, reference_id, amount, balance_after, description) VALUES (%s,%s,%s,%s,%s,%s,%s)',
            (data.account_id, data.transaction_type, data.reference_type, data.reference_id,
             data.amount, new_balance, data.description))
        cur.execute('UPDATE payment_accounts SET balance=%s WHERE id=%s', (new_balance, data.account_id))
        return {'id': cur.lastrowid, 'balance_after': new_balance, 'message': 'Transaction recorded'}


# Helper function used by sale/purchase routes
def record_payment_transaction(db, cur, account_name: str, amount: float, txn_type: str,
                               ref_type: str, ref_id: int, description: str = None):
    """Record a payment transaction against a named account"""
    cur.execute('SELECT id, balance FROM payment_accounts WHERE name=%s AND is_active=1', (account_name,))
    acc = cur.fetchone()
    if not acc:
        return  # No matching account, skip
    if txn_type == 'sale':
        new_balance = float(acc['balance']) + amount
    elif txn_type == 'purchase':
        new_balance = float(acc['balance']) - amount
    else:
        new_balance = float(acc['balance'])
    cur.execute(
        'INSERT INTO payment_transactions (account_id, transaction_type, reference_type, reference_id, amount, balance_after, description) VALUES (%s,%s,%s,%s,%s,%s,%s)',
        (acc['id'], txn_type, ref_type, ref_id, amount, new_balance, description))
    cur.execute('UPDATE payment_accounts SET balance=%s WHERE id=%s', (new_balance, acc['id']))
