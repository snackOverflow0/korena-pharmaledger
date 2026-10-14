"""Fictional school-demo transactions, NOT pharmacy-provided receipt values."""
from datetime import date
from sqlalchemy import select
from models import Entry
from accounting import post_journal

EXAMPLES = [
    ('OPEN-001', '2026-08-31', 'Illustrative opening owner capital', [('1000',100000,0), ('3000',0,100000)]),
    ('DEMO-01', '2026-09-01', 'Cash purchase of pharmacy medicines', [('1100',15000,0), ('1000',0,15000)]),
    ('DEMO-02', '2026-09-02', 'Cash sales of medicines', [('1000',6500,0), ('4000',0,6500)]),
    ('DEMO-03', '2026-09-04', 'Medicines purchased on supplier credit', [('1100',12000,0), ('2000',0,12000)]),
    ('DEMO-04', '2026-09-06', 'Cash sales of medicines and pharmacy products', [('1000',7250,0), ('4000',0,7250)]),
    ('DEMO-05', '2026-09-08', 'Paid medicine supplier', [('2000',5000,0), ('1000',0,5000)]),
    ('DEMO-06', '2026-09-10', 'Electricity and utility payment', [('5100',3200,0), ('1000',0,3200)]),
    ('DEMO-07', '2026-09-12', 'Paid pharmacy employee wages', [('5200',6000,0), ('1000',0,6000)]),
    ('DEMO-08', '2026-09-15', 'Cash medicine stock replenishment', [('1100',10000,0), ('1000',0,10000)]),
    ('DEMO-09', '2026-09-20', 'Expired or damaged medicine write-off', [('5500',1200,0), ('1100',0,1200)]),
    ('DEMO-10', '2026-09-30', 'Cash sales of pharmacy products', [('1000',8500,0), ('4000',0,8500)]),
]

def seed_demo(db):
    if db.scalar(select(Entry.id).limit(1)):
        raise ValueError('The database already has journal entries; sample data was NOT inserted. This protects your existing records.')
    for ref, raw_date, desc, lines in EXAMPLES:
        post_journal(db, posted_on=date.fromisoformat(raw_date), reference=ref,
                     description=desc, lines=lines)
