const $ = id => document.getElementById(id);
const number = n => new Intl.NumberFormat('en-IN').format(n);
const money = n => `Rs ${number(n)}`;
const pct = n => n == null ? 'Pending' : `${(n * 100).toFixed(1)}%`;
const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateLabel = date => new Intl.DateTimeFormat('en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(`${date}T00:00:00Z`));

function table(id, columns, rows) {
  const heading = columns.map(c => `<th>${safe(c.label)}</th>`).join('');
  const body = rows.map(row => `<tr>${columns.map(c => `<td>${c.html ? c.html(row) : safe(c.value(row))}</td>`).join('')}</tr>`).join('');
  $(id).innerHTML = `<table><thead><tr>${heading}</tr></thead><tbody>${body}</tbody></table>`;
}

function bars(id, rows, label, value, display, color='blue', maximum) {
  const cap = maximum || Math.max(...rows.map(value), 1);
  $(id).innerHTML = rows.map(row => {
    const width = Math.max(2, value(row) / cap * 100);
    return `<div class="bar-row ${color}" title="${safe(label(row))}: ${safe(display(row))}"><span class="label">${safe(label(row))}</span><div class="bar-track"><i class="bar-fill" style="width:${width}%"></i></div><span class="value">${safe(display(row))}</span></div>`;
  }).join('');
}

function render(snapshot, index) {
  const week = snapshot.weeks[index];
  const history = snapshot.weeks.slice(Math.max(0,index-11),index+1);
  $('kpi-tickets').textContent = number(week.tickets);
  $('kpi-ticket-note').textContent = `Week of ${dateLabel(week.week)}`;
  $('kpi-repeat').textContent = pct(week.repeat_rate);
  $('kpi-repeat-note').textContent = week.repeat_rate == null ? '30-day window still open' : 'Mature completed cases';
  $('kpi-sla').textContent = pct(week.sla_rate);
  $('kpi-sla-note').textContent = `${number(week.sla_breaches)} breached tickets`;
  $('kpi-transfers').textContent = number(week.transfers);

  table('trend-table',[
    {label:'Week beginning',value:r=>dateLabel(r.week)},
    {label:'Tickets',value:r=>number(r.tickets)},
    {label:'SLA breach',value:r=>pct(r.sla_rate)}
  ],history.slice().reverse());
  const trendMax = Math.max(...history.map(r=>r.tickets),1);
  $('trend-chart').innerHTML = history.map((r,i) => `<div class="column ${i===history.length-1?'selected':''}" title="${safe(dateLabel(r.week))}: ${number(r.tickets)} tickets"><i style="height:${Math.max(3,r.tickets/trendMax*100)}%"></i>${i%2===0||i===history.length-1?`<span>${safe(new Intl.DateTimeFormat('en-IN',{day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(`${r.week}T00:00:00Z`)))}</span>`:''}</div>`).join('');

  const complaints=week.categories.slice(0,8);
  table('complaint-table',[
    {label:'Complaint',value:r=>r.category},
    {label:'Tickets',value:r=>number(r.tickets)},
    {label:'WoW',html:r=>`<span class="${r.change>=0?'positive':'negative'}">${r.change>0?'+':''}${r.change}</span>`}
  ],complaints);
  bars('complaint-chart',complaints,r=>r.category,r=>r.tickets,r=>number(r.tickets));

  const repeats=snapshot.category_repeats.slice(0,8);
  table('repeat-table',[
    {label:'Complaint',value:r=>r.category},
    {label:'Mature cases',value:r=>number(r.completed)},
    {label:'Repeat rate',value:r=>pct(r.rate)}
  ],repeats);
  bars('repeat-chart',repeats,r=>r.category,r=>r.rate,r=>pct(r.rate),'teal',0.20);

  const products=snapshot.product_hotspots.slice(0,7);
  table('product-table',[
    {label:'Product / complaint',value:r=>`${r.sku} · ${r.category}`},
    {label:'Cases',value:r=>number(r.completed)},
    {label:'Repeat',value:r=>pct(r.rate)}
  ],products);
  bars('product-chart',products,r=>`${r.sku} · ${r.category}`,r=>r.excess,r=>`+${r.excess}`,'orange');

  const channels=week.channels.slice().sort((a,b)=>b.rate-a.rate);
  table('sla-table',[
    {label:'Channel',value:r=>r.channel},
    {label:'Breaches',value:r=>`${r.breaches} / ${r.tickets}`},
    {label:'Rate',value:r=>pct(r.rate)}
  ],channels);
  bars('sla-chart',channels,r=>r.channel,r=>r.rate,r=>pct(r.rate),'orange',0.20);

  const agents=week.agents.slice(0,8);
  table('agent-table',[
    {label:'Agent ID',value:r=>r.agent},
    {label:'Team',value:r=>r.team},
    {label:'Closed',value:r=>number(r.closed)}
  ],agents);
  bars('agent-chart',agents,r=>r.agent,r=>r.closed,r=>number(r.closed),'teal');
}

async function main() {
  try {
    const response=await fetch('./data.json');
    if(!response.ok) throw new Error(`Data request returned ${response.status}`);
    const snapshot=await response.json();
    $('as-of').textContent=`· ${dateLabel(snapshot.meta.as_of)}`;
    $('method-date').textContent=dateLabel(snapshot.meta.as_of);
    $('baseline').textContent=pct(snapshot.meta.repeat_rate);
    $('quarter-value').textContent=money(snapshot.meta.quarterly_value_inr);
    $('baseline-bar').style.width=`${Math.min(snapshot.meta.repeat_rate/0.2*100,100)}%`;
    $('target-marker').style.left=`${snapshot.meta.target_rate/0.2*100}%`;
    const select=$('week-select');
    snapshot.weeks.forEach((week,index)=>{
      const option=document.createElement('option');
      option.value=String(index);
      option.textContent=`${dateLabel(week.week)} · ${week.tickets} tickets`;
      select.append(option);
    });
    select.value=String(snapshot.weeks.length-1);
    select.addEventListener('change',()=>render(snapshot,Number(select.value)));
    render(snapshot,snapshot.weeks.length-1);
  } catch(error) {
    document.querySelector('main').innerHTML=`<div class="method"><div><strong>Dashboard could not load</strong><p>${safe(error.message)}. Run scripts/export_public_dashboard.py to regenerate web/data.json.</p></div></div>`;
  }
}

main();
