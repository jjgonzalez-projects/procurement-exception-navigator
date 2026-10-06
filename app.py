import streamlit as st
import pandas as pd
from model import load_data, filter_data, metrics, capacity, SNAPSHOT, compare_case
st.set_page_config(page_title='Procurement Exception Navigator | JJ González',page_icon='🧭',layout='wide')
st.markdown('''<style>
.block-container {max-width:1200px;padding-top:3.5rem;}
h1 {letter-spacing:-1.4px;} h2 {letter-spacing:-.7px;}
[data-testid="stMetric"] {background:#f0f5f8;border:1px solid #dce5ed;border-radius:12px;padding:16px;}
.hero {padding:26px 30px;border-radius:16px;background:#f6f3ee;color:#17324d;border-top:5px solid #005b96;margin-bottom:20px;}
.hero h1 {color:#17324d;margin:6px 0 10px;font-size:34px;}
.hero p {color:#3d5366;font-size:17px;margin:0;}
.eyebrow {font-size:12px;letter-spacing:2px;color:#005b96;font-weight:700;}
</style>''',unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="eyebrow">PROCUREMENT × TECHNOLOGY × BUSINESS VALUE</div><h1>Procurement Exception Navigator</h1><p>Turn invoice discrepancies into clear ownership, prioritized action and a measurable improvement pilot.</p></div>''',unsafe_allow_html=True)
st.caption('Independent portfolio project by Juan José González, PMP • Synthetic transactions • Snapshot: 30 Sep 2026 • No Nestlé affiliation or internal data')
@st.cache_data
def get_data(): return load_data()
po,inv,receipts=get_data()
st.subheader('What does this demo solve?')
st.write('When an invoice differs from a purchase order or recorded receipt, procurement and finance need to understand the discrepancy, identify an owner and follow up. This demo turns those records into a focused action queue.')
a,b,c=st.columns(3)
a.markdown('**1 · Understand purchasing**  \nSee purchase commitments and the share of invoices requiring review. Filter by country, category and supplier.')
b.markdown('**2 · Review a case**  \nCompare the order, receipt and invoice. See a proposed owner and simulate routing the case.')
c.markdown('**3 · Assess the improvement**  \nAdjust assumptions to estimate potential capacity and define how to validate a pilot.')
with st.expander('How to use the demo and interpret the results'):
    st.write('Start with all filters set to All. Open Review a case and inspect INV452 for a calculated price difference or INV271 to validate a seeded quantity label against the records. Then open Assess the improvement and change the minutes avoided per case.')
    st.write('Figures describe a synthetic demonstration at 30 Sep 2026. A seeded exception label is a scenario input; calculated price and quantity checks provide supporting evidence and may reveal additional differences. This is not a production matching engine.')
    st.write('Routing is a simulation. No notifications are sent, no ERP is connected and no payment is authorized.')
st.markdown('#### Explore the purchasing scope')
a,b,c=st.columns(3)
country=a.selectbox('Buying country',['All']+sorted(po.BuyingCountry.unique()),key='country_filter')
country_po=po if country=='All' else po.loc[po.BuyingCountry.eq(country)]
category_options=['All']+sorted(country_po.Category.unique())
if st.session_state.get('category_filter','All') not in category_options:
    st.session_state['category_filter']='All'
category=b.selectbox('Category',category_options,key='category_filter')
category_po=country_po if category=='All' else country_po.loc[country_po.Category.eq(category)]
supplier_options=['All']+sorted(category_po.SupplierName.unique())
if st.session_state.get('supplier_filter','All') not in supplier_options:
    st.session_state['supplier_filter']='All'
supplier=c.selectbox('Supplier',supplier_options,key='supplier_filter')
st.caption('Categories follow the selected country; suppliers follow country and category. Incompatible selections reset to All.')
p,i=filter_data(po,inv,country,category,supplier)
m=metrics(p,i)
t1,t2,t3=st.tabs(['01 · Understand purchasing','02 · Review a case','03 · Assess the improvement'])
with t1:
    cols=st.columns(4)
    for col,label,value in zip(cols,['Purchase orders','Ordered value · USD','Invoices with exceptions','Open exceptions'],[f'{m["orders"]:,}',f'${m["ordered"]/1e6:.2f}m',(f'{m["exception_rate"]:.1%}' if m['invoices'] else 'N/A'),str(m['open_count'])]): col.metric(label,value)
    st.caption('Purchase orders = order count; ordered value = purchase commitments; open exceptions = unresolved invoice cases. Historical Exception rate includes resolved and unresolved exceptions in the filtered invoice cohort.')
    left,right=st.columns(2)
    with left:
        st.subheader('Where procurement is concentrated')
        if len(p): st.bar_chart(p.groupby('BuyingCountry').OrderValueUSD.sum().rename('Ordered USD'),color='#005b96',horizontal=True)
        else: st.info('No purchase orders match these filters.')
    with right:
        st.subheader('What creates rework')
        issues=i.loc[i.ExceptionType.ne('None')].groupby('ExceptionType').size().rename('Invoices')
        if len(issues): st.bar_chart(issues,color='#dca53b',horizontal=True)
        else: st.info('No historical exceptions match these filters.')
    st.metric('Unresolved exception value · USD',f'${m["open_value"]:,.2f}')
    st.caption('Invoice value requiring review; not realized savings, losses or confirmed blocked payments.')
with t2:
    queue=i.loc[i.Open].sort_values(['AgeDays','InvoiceValueUSD'],ascending=False)
    st.subheader('From insight to ownership')
    st.write('Proposed pilot rule: review cases aged 10 days or more first, then use age and invoice value to organize follow-up.')
    if queue.empty:
        st.success('No unresolved exceptions in this selection.')
    else:
        st.dataframe(queue[['Invoice_ID','ExceptionType','AgeDays','InvoiceValueUSD','Owner','Priority']].rename(columns={'Invoice_ID':'Invoice','ExceptionType':'Exception','AgeDays':'Age · days','InvoiceValueUSD':'Value · USD','Owner':'Proposed owner'}),hide_index=True,width='stretch')
        selected=st.selectbox('Inspect a case',queue.Invoice_ID.tolist())
        row=queue.loc[queue.Invoice_ID.eq(selected)].iloc[0]
        st.markdown('### Order → receipt → invoice evidence')
        evidence=compare_case(row,receipts)
        st.dataframe(pd.DataFrame({
            'Record':['Purchase order','Receipt recorded by invoice date','Invoice'],
            'Quantity':[f"{row.OrderedQty:,.0f}",f"{evidence['received_qty']:,.0f}" if evidence['has_receipt'] else 'No receipt recorded',f"{row.InvoiceQty:,.0f}"],
            'Unit price · USD':[f"${row.UnitPriceUSD:,.2f}",'Not applicable',f"${row.InvoiceUnitPriceUSD:,.2f}"]
        }),hide_index=True,width='stretch')
        e1,e2,e3=st.columns(3)
        e1.metric('Invoice minus PO price · USD/unit',f"${evidence['price_delta']:,.2f}")
        e2.metric('Invoice minus received · units',f"{evidence['quantity_delta']:,.0f}" if evidence['has_receipt'] else 'N/A')
        e3.metric('Price variance × invoiced units · USD',f"${evidence['price_variance']:,.2f}")
        findings=[]
        if abs(evidence['price_delta'])>.005: findings.append('Unit price differs from the PO price.')
        if not evidence['has_receipt']: findings.append('No receipt recorded by invoice date; verify receiving evidence.')
        elif evidence['quantity_delta']>0: findings.append('Invoiced quantity exceeds recorded received quantity.')
        elif evidence['quantity_delta']<0: findings.append('Invoice covers fewer units than received; partial billing may explain this.')
        else: findings.append('Invoiced and recorded received quantities match.')
        if row.ExceptionType=='Quantity mismatch' and evidence['has_receipt'] and evidence['quantity_delta']==0:
            findings.append('The seeded quantity-exception label is not supported by this invoice/receipt comparison; validate its classification before taking action.')
        st.info(' '.join(findings))
        st.caption('Quantity compares receipts recorded on or before invoice date. Unit price tolerance is $0.005 for this demo. Price variance is a review signal, not savings or a confirmed overpayment. Document completeness is a seeded scenario label and cannot be verified from these tables. Tax, FX, credits and contract tolerances are outside scope.')
        l,r=st.columns([1,1])
        with l:
            st.markdown(f'### {selected} · {row.ExceptionType}')
            st.write(f'**{row.SupplierName}** · {row.BuyingCountry} · {row.Category}')
            st.write(f'PO: **{row.PO_ID}** · Invoice: **${row.InvoiceValueUSD:,.2f}** · Age: **{row.AgeDays} days**')
            action={'Price mismatch':'Buyer verifies the agreed PO price and requests a correction or an approved change.','Quantity mismatch':'Receiving checks delivery evidence and reconciles received and invoiced quantities.','Missing documentation':'Accounts payable requests and validates the missing supporting documents.'}[row.ExceptionType]
            st.info(action)
        with r:
            st.markdown('### Routing simulation')
            st.write(f'Proposed owner: **{row.Owner}**')
            st.write(f'Priority: **{row.Priority}**')
            if st.button('Simulate routing',type='primary'):
                st.session_state['routed_case']=selected
            if st.session_state.get('routed_case')==selected:
                st.success(f'Simulation: {selected} would be routed to {row.Owner}.')
                st.caption('No message sent and no source record changed. A production flow would need duplicate prevention, an audit log, approved owners and failure handling.')
    st.download_button('Download filtered action queue',queue.to_csv(index=False).encode(),'exception_queue.csv','text/csv')
with t3:
    st.subheader('A small, testable improvement')
    st.write('Hypothesis: assigning ownership automatically could reduce manual follow-up and shorten the time to first action. Validate this with procurement, accounts payable, receiving and IT.')
    with st.expander('Proposed workflow',expanded=True):
        st.write('Daily exception feed → check for an existing case → assign owner by exception type → track status → escalate at an agreed SLA → human validates correction and closure.')
        st.caption('Proposed Power Automate pilot. Not deployed. No automatic payment release. The 10-day threshold is a demo assumption, not company policy.')
    st.markdown('### Capacity scenario — adjustable assumptions')
    st.caption('Independent hypothetical annual scenario. These are not Nestlé volumes or measured benefits. Global baseline exception rate in the synthetic sample: 20.29%.')
    c1,c2,c3=st.columns(3)
    volume=c1.number_input('Annual invoice volume',min_value=0,value=10000,step=1000)
    rate=c2.slider('Exception rate · %',0,100,20)/100
    eligible=c3.slider('Eligible for routing · %',0,100,80)/100
    c1,c2,c3=st.columns(3)
    adoption=c1.slider('Adoption · %',0,100,75)/100
    minutes=c2.number_input('Minutes avoided per eligible case',min_value=0,value=15)
    hourly=c3.number_input('Assumed hourly cost · USD',min_value=0,value=25)
    hours,value=capacity(volume,rate,eligible,adoption,minutes,hourly)
    c1,c2=st.columns(2)
    c1.metric('Potential capacity · hours/year',f'{hours:,.1f}')
    c2.metric('Capacity value proxy · USD/year',f'${value:,.0f}')
    st.caption('Volume × exception rate × eligibility × adoption × minutes ÷ 60. Capacity value is not cash savings or ROI; implementation and operating costs are excluded. Filters above do not change this independent scenario.')
    st.markdown('### How to validate the pilot')
    st.write('Measure manual minutes per exception, time to first owner assignment, closure time, incorrect routing and cases over SLA. Test all exception types, duplicate reruns, missing owners and failed notifications before expansion.')
with st.expander('Data, definitions and relevance to the role'):
    st.write('500 synthetic POs, 483 invoices, 490 receipt records and 14 fictional suppliers across seven buying countries. One line per PO and at most one invoice and receipt per PO. USD values exclude taxes and FX. Exception classifications are seeded input labels. The case view calculates price and quantity differences from the records; document completeness and production matching rules are outside scope.')
    st.write('The case is aligned with the supplied Procurement Digital Innovation PM description: global Procure-to-Pay, stakeholder coordination, data-driven decisions and practical automation. It demonstrates an approach, not knowledge of Nestlé internal systems.')
    st.markdown('Public context: [Nestlé supply-chain disclosures](https://www.nestle.com/sustainability/responsible-sourcing/supply-chain-disclosure) · [Nestlé annual reporting](https://www.nestle.com/investors/annual-report). These sources provide context only; they do not supply the transactions or performance figures in this demo.')
st.caption('Juan José González · Connecting operations, finance & technology')
