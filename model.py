from pathlib import Path
import pandas as pd
SNAPSHOT = pd.Timestamp('2026-09-30')

def load_data(path=None):
    sheets = pd.read_excel(path or Path(__file__).with_name('data.xlsx'), sheet_name=['PurchaseOrders','Suppliers','Receipts','Invoices'], keep_default_na=False, na_values=[''])
    po, suppliers, receipts, inv = (sheets[n] for n in ['PurchaseOrders','Suppliers','Receipts','Invoices'])
    po = po.merge(suppliers[['Supplier_ID','SupplierName']], on='Supplier_ID', validate='many_to_one')
    inv = inv.merge(po[['PO_ID','BuyingCountry','Category','Buyer','SupplierName','UnitPriceUSD','OrderedQty']],on='PO_ID',validate='many_to_one')
    inv['Open'] = inv.ExceptionType.ne('None') & inv.ClearanceDate.isna()
    inv['AgeDays'] = (SNAPSHOT - inv.InvoiceDate).dt.days
    inv['Owner'] = inv.ExceptionType.map({'Quantity mismatch':'Receiving team','Missing documentation':'Accounts payable','None':'No action'})
    inv.loc[inv.ExceptionType.eq('Price mismatch'),'Owner'] = inv.Buyer
    inv['Priority'] = inv.AgeDays.ge(10).map({True:'Escalate',False:'Follow up'})
    inv.loc[~inv.Open,'Priority'] = 'Closed / no exception'
    return po, inv, receipts

def filter_data(po, inv, country='All', category='All', supplier='All'):
    for field,value in [('BuyingCountry',country),('Category',category),('SupplierName',supplier)]:
        if value != 'All':
            po=po.loc[po[field].eq(value)]
            inv=inv.loc[inv[field].eq(value)]
    return po,inv

def metrics(po,inv):
    unresolved=inv.loc[inv.Open]
    overdue=inv.loc[inv.PaymentDate.isna() & inv.DueDate.lt(SNAPSHOT)]
    return {'orders':len(po),'ordered':float(po.OrderValueUSD.sum()),'invoices':len(inv),
            'exception_rate':float(inv.ExceptionType.ne('None').mean()) if len(inv) else 0,
            'open_count':len(unresolved),'open_value':float(unresolved.InvoiceValueUSD.sum()),
            'overdue_value':float(overdue.InvoiceValueUSD.sum())}

def capacity(volume,rate,eligible,adoption,minutes,hourly):
    hours=volume*rate*eligible*adoption*minutes/60
    return hours,hours*hourly


def compare_case(row,receipts):
    relevant=receipts.loc[receipts.PO_ID.eq(row.PO_ID) & receipts.ReceiptDate.le(row.InvoiceDate)]
    received=float(relevant.ReceivedQty.sum())
    delta=float(row.InvoiceUnitPriceUSD-row.UnitPriceUSD)
    return {'has_receipt':not relevant.empty,'received_qty':received,'price_delta':delta,
            'quantity_delta':float(row.InvoiceQty)-received,'price_variance':delta*float(row.InvoiceQty)}
