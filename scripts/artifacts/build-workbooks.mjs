import fs from 'node:fs/promises';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const out='submission/03_Marketplace';
await fs.mkdir(`${out}/evidence`,{recursive:true});
function sheet(wb,name,title,headers,rows,widths){
  const s=wb.worksheets.add(name); s.showGridLines=false;
  s.getCell(1,0).values=[[title]];
  s.getRangeByIndexes(1,0,1,headers.length).format.font={name:'Arial',size:15,bold:true,color:'#285D49'};
  s.getRangeByIndexes(3,0,1,headers.length).values=[headers];
  s.getRangeByIndexes(4,0,rows.length,headers.length).values=rows;
  const all=s.getRangeByIndexes(3,0,rows.length+1,headers.length);
  all.format.font={name:'Arial',size:10}; all.format.wrapText=true; all.format.verticalAlignment='center';
  all.format.rowHeight=58;
  s.getRangeByIndexes(3,0,1,headers.length).format={fill:'#285D49',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:32,wrapText:true};
  widths.forEach((w,i)=>s.getRangeByIndexes(0,i,rows.length+4,1).format.columnWidth=w);
  for(let i=0;i<rows.length;i++)if(i%2===0)s.getRangeByIndexes(i+4,0,1,headers.length).format.fill='#F1F4ED';
  s.freezePanes.freezeRows(4); return s;
}
async function finish(wb,name,previews){
  wb.recalculate();
  console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:20},summary:name})).ndjson);
  for(const [sheetName,range] of previews){
    const image=await wb.render({sheetName,range,scale:1,format:'png'});
    await fs.writeFile(`${out}/evidence/${sheetName.replaceAll(' ','-')}.png`,new Uint8Array(await image.arrayBuffer()));
  }
  await (await SpreadsheetFile.exportXlsx(wb)).save(`${out}/${name}.xlsx`);
}
const evidence=JSON.parse(await fs.readFile(`${out}/evidence/test-results.json`,'utf8'));
const cases=[
['Seller listing','Seller authenticated','POST /api/listings/','Valid listing','201; seller assigned'],
['Buyer permission','Buyer authenticated','POST /api/listings/','Valid listing','403'],
['Listing ownership','Other seller authenticated','PATCH listing','Changed title','403'],
['Owner update','Owner authenticated','PATCH listing','Changed title','200'],
['Listing deletion','No offers; owner','DELETE listing','Listing ID','204'],
['History retention','Listing has offer','DELETE listing as owner','Listing ID','400; offer retained'],
['Buyer offer','Buyer; active listing','POST offer with forged buyer/status','0.01; forged COMPLETED','201; own buyer; PENDING'],
['Price validation','Buyer authenticated','POST each invalid amount','0, -1, overflow, abc, NaN, 0.001','400 for each'],
['Seller offer denied','Seller authenticated','POST offer','Valid payload','403'],
['Draft privacy','Inactive listing','GET detail; POST offer','Inactive listing ID','404 detail; 400 offer'],
['Lifecycle','Buyer offer pending','Accept, complete, review','Valid offer and rating 5','ACCEPTED; COMPLETED; 201'],
['Rejected terminal','Pending offer','Reject then complete','Offer ID','200 then 400'],
['Transition guard','Pending offer','Complete directly','Offer ID','400'],
['Retry','Pending offer','Accept twice','Same offer ID','200 then 400'],
['Buyer status denied','Own pending offer','Accept as buyer','Offer ID','403'],
['Other seller status','Unrelated seller','Accept offer','Private offer ID','404'],
['Private offer list','Another buyer has offer','GET offers as stranger','No filters','Count 0'],
['Premature review','Pending engagement','POST review','Rating 5','400'],
['Review ownership','Completed engagement','POST as unrelated buyer','Valid review','403'],
['Duplicate review','Completed engagement','POST twice','Same offer','201 then 400; one review'],
['Valid boundary','Two completed offers','POST reviews','Ratings 1 and 5','201 for both'],
['Invalid boundary','Completed engagement','POST reviews','0, 6, -1, 1.5','400 for each'],
['Search regression','Completed lifecycle','Search keyword and category','django; Web Development; unknown; SEO','Counts 1, 0, 0'],
['Anonymous access','No session','POST listing; GET offers','Valid payload','403 for both'],
['CSRF','Real seller session','POST without CSRF token','Valid listing','403'],
['Registration','New usernames','Register Buyer and Seller','Forged staff/superuser flags','Correct groups; no privilege escalation'],
['HTML pages','Guest then seller','GET pages and buyer dashboard','Home, auth, details, seller forms','200 pages; 403 wrong role'],
['HTML lifecycle','Buyer and seller sessions','Submit, accept, complete, review','Valid forms','Redirects; review shown in dashboard'],
['Invalid content','Buyer authenticated','Missing detail; blank message; short review','9999; whitespace; short','404; 400; 400'],
['HTML authorization','Other seller then owner','Delete/edit other listing; GET delete','Existing listing ID','403; 403; 405']];
const testWb=Workbook.create();
const rows=evidence.results.map((r,i)=>[`TC-${String(i+1).padStart(2,'0')}`,cases[i][0],cases[i][1],cases[i][2],cases[i][3],cases[i][4],r.actual,r.status,r.status==='PASS'?'None':'Investigate',`evidence/test-output.txt (${r.test})`]);
const t=sheet(testWb,'Executed tests','SkillMarket test execution — 2026-10-25', ['Test ID','Feature','Preconditions','Steps','Input','Expected Result','Actual Result','Status','Defect ID','Evidence Link'],rows,[11,23,26,36,30,30,30,12,15,65]);
t.getCell(2,0).values=[[`Database: ${evidence.database}. Sequential workflow tests; concurrent stress and external integration checks are pending.`]];
await finish(testWb,'test-cases',[['Executed tests','A1:H9']]);
const host='https://www.hostinger.com/vps-hosting',aws='https://aws.amazon.com/lightsail/pricing/',sup='https://supabase.com/pricing';
const costs=[];
for(const option of ['A: Hostinger','B: AWS']){
 const a=option.startsWith('A');
 costs.push([option,'Compute',a?'KVM 1 renewal; 1 vCPU, 4 GB':'Lightsail Linux IPv4; 2 vCPU, 4 GB','US (assumed)',1,a?11.99:24,null,'instance/month','Verified public price',a?host:aws,'2026-10-25']);
 costs.push([option,'Database','Supabase Pro; one Micro instance','US East (assumed)',1,25,null,'project/month','Verified; includes compute credit',sup,'2026-10-25']);
 costs.push([option,'Storage',a?'50 GB NVMe included':'80 GB SSD included','US (assumed)',1,0,null,'included','Included in compute',a?host:aws,'2026-10-25']);
 costs.push([option,'Backups',a?'Weekly VPS + daily DB included':'20 GB Lightsail snapshots; DB backup included','US (assumed)',a?1:20,a?0:0.05,null,a?'included':'GB/month',a?'Verified inclusion':'Verified unit; assumed volume',a?host:aws,'2026-10-25']);
 costs.push([option,'Bandwidth','Within 4 TB app / 250 GB DB allowances','US (assumed)',1,0,null,'included','Assumed no overage',`${a?host:aws}; ${sup}`,'2026-10-25']);
 costs.push([option,'Monitoring','Basic metrics / local logs','US (assumed)',1,0,null,'month','Assumption: no paid monitoring','Not purchased','2026-10-25']);
 costs.push([option,'Domain','Annual domain allowance amortized','Global',1,1.25,null,'month','Assumption: USD 15/year','Budget assumption, not vendor quote','2026-10-25']);
 costs.push([option,'Third-party services','GitHub / diagrams / submission free tiers','Global',1,0,null,'month','Assumption: free tier adequate','No paid subscription assumed','2026-10-25']);
 costs.push([option,'Background workers','None in MVP','US (assumed)',0,0,null,'month','Not implemented','Project scope','2026-10-25']);
}
const wb=Workbook.create();
const c=sheet(wb,'Hosting costs','Monthly hosting comparison (USD; tax and labor excluded)',['Option','Cost category','Service and specification','Region','Quantity','Unit price USD','Monthly USD','Unit','Price basis / usage','Source URL','Access date'],costs,[22,20,44,24,13,16,17,20,35,65,17]);
for(let i=5;i<=22;i++)c.getRange(`G${i}`).formulas=[[`=E${i}*F${i}`]];
c.getRange('F5:G22').setNumberFormat('$#,##0.00');
c.getRange('A25:B26').values=[['Hostinger monthly total',null],['AWS monthly total',null]];
c.getRange('B25:B26').formulas=[['=SUM(G5:G13)'],['=SUM(G14:G22)']];c.getRange('B25:B26').setNumberFormat('$#,##0.00');
c.getRange('A28').values=[['Hostinger promo $6.49/mo differs from renewal used here; commitment and regional checkout must be confirmed.']];
const scenarios=[
[100,.2,20,30,100,null,null,null,1,'Single app; Supabase Micro',1,11.99,24,25,0,null,null,'Operational setup; no HA'],
[1000,.2,20,30,100,null,null,null,2,'Indexes; pooling; tune queries',1,14.99,24,25,5,null,null,'Connections; sequential substring search'],
[10000,.2,20,30,100,null,null,null,10,'Two app instances; cache; monitoring',2,28.99,44,75,55,null,null,'DB reads; load balancer; cache invalidation'],
[1000000,.2,20,30,100,null,null,null,250,'8 app instances; LB/CDN; DB replicas; queues',8,49.99,164,2000,1200,null,null,'Write throughput, DB HA, cache, egress']];
const s=sheet(wb,'Scaling','Capacity scenarios — planning assumptions, not load-tested guarantees',['Registered users','Daily active %','Requests / active / day','Days / month','KB / response','Requests / month','Traffic GB / month','Peak req / sec (10x)','DB GB','Proposed architecture','App instances','VPS unit USD','AWS unit USD','DB budget USD','Other budget USD','VPS monthly USD','AWS monthly USD','Bottleneck / changes'],scenarios,[22,18,20,18,18,23,24,23,15,50,18,18,18,20,22,22,22,52]);
for(let r=5;r<=8;r++){
 s.getRange(`F${r}:H${r}`).formulas=[[`=A${r}*B${r}*C${r}*D${r}`,`=F${r}*E${r}/1000000`,`=F${r}/(D${r}*86400)*10`]];
 s.getRange(`P${r}:Q${r}`).formulas=[[`=K${r}*L${r}+N${r}+O${r}+1.25`,`=K${r}*M${r}+N${r}+O${r}+1.25`]];
}
s.getRange('B5:B8').setNumberFormat('0%');s.getRange('F5:F8').setNumberFormat('#,##0');s.getRange('G5:H8').setNumberFormat('#,##0.00');s.getRange('L5:Q8').setNumberFormat('$#,##0.00');
s.getRange('A11').values=[['All scaling rates and budgets are assumptions. 10x peak factor; decimal GB; no user-uploaded media.']];
s.getRange('A13').values=[['100-user DB: 1 GB; 1,000: 2 GB; 10,000: 10 GB; 1,000,000: 250 GB incl. indexes and history. Validate retention and growth.']];
s.getRange('A15').values=[['Other budgets: monitoring, snapshots, load balancing, CDN/cache and workers at larger scales. Large-scale DB budget includes replicas and backup allowance.']];
s.getRange('A17').values=[['US region is assumed for both app and DB. Pricing sources are on Hosting costs; larger-scale budgets require vendor quotes and a load test.']];
s.getRange('A19').values=[['Django authentication does not use Supabase Auth MAU pricing. Database-to-app traffic differs from browser traffic; measure it before estimating egress.']];
wb.recalculate();
const totals=c.getRange('B25:B26').values.flat();
if(Math.abs(totals[0]-38.24)>0.001 || Math.abs(totals[1]-51.25)>0.001)throw new Error(`Incorrect hosting totals: ${totals}`);
const original=c.getRange('E5').values[0][0]; c.getRange('E5').values=[[2]]; wb.recalculate();
if(Math.abs(c.getRange('B25').values[0][0]-50.23)>0.001)throw new Error('Hosting quantities do not recalculate');
c.getRange('E5').values=[[original]];
await finish(wb,'cost-and-scaling',[['Hosting costs','A1:I8'],['Scaling','A1:I8']]);
console.log('Exported two workbooks.');
