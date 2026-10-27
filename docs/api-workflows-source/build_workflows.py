"""Generate matching editable sequence diagrams and a vector PDF preview."""
from pathlib import Path
import math, xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import pypdfium2 as pdfium

OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1]
W=1500;H=1250
for n,f in [('Arial','arial.ttf'),('Arial-Bold','arialbd.ttf')]:pdfmetrics.registerFont(TTFont(n,'C:/Windows/Fonts/'+f))
c=canvas.Canvas(str(OUT.parent/'api-workflows.pdf'),pagesize=(W,H));c.setTitle('SkillMarket API workflows')
mx=ET.Element('mxfile',host='app.diagrams.net');root=None;seq=1
def cell(value,style,x,y,w,h):
    global seq
    seq+=1;e=ET.SubElement(root,'mxCell',id=str(seq),value=value,style=style,vertex='1',parent='1')
    ET.SubElement(e,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
def text(x,y,s,size=12,bold=False,background=False):
    font='Arial-Bold' if bold else 'Arial';width=pdfmetrics.stringWidth(s,font,size)
    if background:
        c.setFillColor(HexColor('#ffffff'));c.rect(x-2,H-y-size-2,width+4,size+3,fill=1,stroke=0)
    c.setFont(font,size);c.setFillColor(HexColor('#303840'));c.drawString(x,H-y-size,s)
    cell(s,f'text;html=0;align=left;verticalAlign=top;fontFamily=Arial;fontSize={size};fontStyle={int(bold)};'+('fillColor=#ffffff;' if background else ''),x,y,width+5,size+5)
def rect(x,y,w,h,fill='#eff3f6'):
    c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor('#85929b'));c.setLineWidth(.7);c.rect(x,H-y-h,w,h,fill=1,stroke=1)
    cell('',f'rounded=0;fillColor={fill};strokeColor=#85929b;',x,y,w,h)
def line(pts,dashed=False,arrow=True):
    global seq
    c.setStrokeColor(HexColor('#526779'));c.setFillColor(HexColor('#526779'));c.setLineWidth(.8)
    c.setDash(4,3) if dashed else c.setDash()
    for (a,b),(d,e) in zip(pts,pts[1:]):c.line(a,H-b,d,H-e)
    c.setDash()
    if arrow:
        a,b=pts[-2],pts[-1];ang=math.atan2(b[1]-a[1],b[0]-a[0]);p=c.beginPath();p.moveTo(b[0],H-b[1])
        for off in [-.45,.45]:p.lineTo(b[0]-7*math.cos(ang+off),H-b[1]+7*math.sin(ang+off))
        p.close();c.drawPath(p,fill=1,stroke=0)
    seq+=1;e=ET.SubElement(root,'mxCell',id=str(seq),edge='1',parent='1',style=f'edgeStyle=none;endArrow={"block" if arrow else "none"};endFill=1;dashed={int(dashed)};strokeColor=#526779;')
    g=ET.SubElement(e,'mxGeometry',relative='1',attrib={'as':'geometry'})
    for k,pt in [('sourcePoint',pts[0]),('targetPoint',pts[-1])]:ET.SubElement(g,'mxPoint',x=str(pt[0]),y=str(pt[1]),attrib={'as':k})
    if len(pts)>2:
        arr=ET.SubElement(g,'Array',attrib={'as':'points'})
        for x,y in pts[1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
def page(title,n,height):
    global root,seq,H
    H=height;c.setPageSize((W,H))
    d=ET.SubElement(mx,'diagram',id=f'workflow-{n}',name=title);m=ET.SubElement(d,'mxGraphModel',page='1',pageWidth=str(W),pageHeight=str(H));root=ET.SubElement(m,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0');seq=1
    text(30,20,title,18,True)
    text(30,49,'SkillMarket | Django REST Framework + session authentication | verified local SQLite implementation',12)
    text(30,H-28,'FalconXoft | 27 October 2026 | Local PDF preview; final Lucidchart export and editable link still required',10)
    text(1450,H-28,str(n),10)
def participants(xs,names,end):
    for x,labels in zip(xs,names):
        rect(x-78,82,156,49)
        for i,s in enumerate(labels):text(x-pdfmetrics.stringWidth(s,'Arial-Bold',11)/2,91+15*i,s,11,True)
        line([(x,131),(x,end)],True,False)
def activation(x,y1,y2):rect(x-4,y1,8,y2-y1,'#e5ebf0')
def msg(xs,a,b,y,label,response=False):
    x1,x2=xs[a],xs[b]
    if a==b:
        line([(x1,y),(x1+26,y),(x1+26,y+7),(x1,y+7)],response)
        text(x1+33,y-13,label,10.5,background=True)
    else:
        line([(x1,y),(x2,y)],response)
        width=pdfmetrics.stringWidth(label,'Arial',10.5)
        # Center within a message span; long labels may cross lifelines, as in standard UML.
        xx=max(18,min(W-width-18,(x1+x2-width)/2))
        text(xx,y-17,label,10.5,background=True)

page('Workflow 1 - Buyer Submits Offer and Seller Accepts',1,1250)
xs=[90,275,470,665,865,1060,1245,1420]
participants(xs,[['Buyer'],['Browser / API Client'],['Django REST API'],['Authentication &','Permissions'],['Marketplace','Business Logic'],['Django ORM'],['Database','SQLite'],['Seller']],1148)
events=[
 (0,1,'Submit listing, price and message',False),
 (1,2,'POST /api/offers/ + session cookie + CSRF token',False),
 (2,3,'SessionAuthentication; CSRF; IsAuthenticated',False),
 (3,2,'Authenticated Buyer session',True),
 (2,5,'OfferSerializer: resolve listing ID',False),
 (5,6,'READ listing by primary key',False),
 (5,2,'Existing listing',True),
 (2,2,'Validate price and message',False),
 (2,4,'submit_offer(user, listing, data); atomic',False),
 (4,3,'require_role(user, Buyer)',False),
 (3,4,'Buyer membership verified',True),
 (4,5,'Reread listing (select_for_update)',False),
 (5,6,'READ listing inside transaction',False),
 (5,4,'Current listing',True),
 (4,4,'ACTIVE; other seller; model full_clean()',False),
 (4,5,'Create Offer; buyer=current user; PENDING',False),
 (5,6,'WRITE INSERT Offer; commit on service exit',False),
 (4,2,'Created Offer instance',True),
 (2,1,'201 Created; Offer JSON, status=PENDING',True),
 (1,0,'Offer created; id available',True),
 (7,1,'Accept offer using a separate Seller session',False),
 (1,2,'POST /api/offers/{id}/accept/; empty body',False),
 (2,3,'Seller session; CSRF; IsAuthenticated',False),
 (3,2,'Authenticated Seller session',True),
 (2,5,'get_object(): scope to listing__seller=user',False),
 (5,6,'READ Offer by ID within seller queryset',False),
 (5,2,'Owned Offer found',True),
 (2,4,'transition(user, offer, accept); atomic',False),
 (4,5,'Reread offer + listing (select_for_update)',False),
 (5,6,'READ Offer with related Listing',False),
 (4,4,'Seller role; ownership; status=PENDING',False),
 (4,5,'Save status=ACCEPTED and updated_at',False),
 (5,6,'WRITE UPDATE Offer; commit on service exit',False),
 (4,2,'Updated Offer instance',True),
 (2,1,'200 OK; full Offer JSON, status=ACCEPTED',True),
 (1,7,'Acceptance confirmed',True),
]
activation(xs[2],187,651);activation(xs[2],727,1105)
activation(xs[4],376,619);activation(xs[4],889,1078)
for i,(a,b,label,r) in enumerate(events):msg(xs,a,b,160+27*i,label,r)
text(30,1160,'Request body: {"listing":1,"offered_price":"100.00","message":"Please build a portfolio website."}',11)
text(30,1180,'Offer JSON: id, listing, buyer, offered_price, message, status, created_at, updated_at. Auth/logic lifelines are in-process concerns.',11)
text(30,1200,'Solid = call/request; dashed = return. Internal query returns abbreviated. SQLite does not provide PostgreSQL row-level locks.',11)
c.showPage()

page('Workflow 2 - Unauthorized Seller Attempts to Accept an Offer',2,850)
xs=[105,365,625,875,1130,1395]
participants(xs,[['Unauthorized Seller'],['Browser / API Client'],['Django REST API'],['Authentication &','Permissions'],['Marketplace','Business Logic'],['Django ORM /','Database']],660)
activation(xs[2],210,535);activation(xs[3],250,290);activation(xs[5],370,410)
events=[
 (0,1,'Attempt to accept another seller\'s PENDING offer',False),
 (1,2,'POST /api/offers/{id}/accept/ + valid session / CSRF',False),
 (2,3,'SessionAuthentication; CSRF; IsAuthenticated',False),
 (3,2,'Authenticated Seller; request allowed to proceed',True),
 (2,2,'get_queryset(): listing__seller=current user',False),
 (2,5,'READ Offer by ID from owner-scoped queryset',False),
 (5,2,'No matching row in scoped queryset',True),
 (2,2,'get_object() raises Http404',False),
 (2,1,'404 Not Found: {"detail":"No Offer matches the given query."}',True),
 (1,0,'Offer is inaccessible',True)
]
for i,(a,b,label,r) in enumerate(events):msg(xs,a,b,170+40*i,label,r)
rect(995,560,270,65,'#f5f5f5');text(1008,573,'transition() is NOT invoked.',12,True);text(1008,595,'No business-logic activation.',11)
text(30,689,'Result: offer remains PENDING. Only reads occur; there is no status UPDATE and no unauthorized write.',13,True)
text(30,720,'Why 404: ownership is enforced here by queryset visibility before the transition service is called.',12)
text(30,745,'Different case: Buyer accepting their own visible offer reaches require_role(Seller) and receives 403 Forbidden.',12)
text(30,770,'Verified error: {"detail":"A seller account is required."}. Both scenarios are covered by the existing tests and isolated probes.',11)
c.showPage();c.save()
ET.indent(mx);ET.ElementTree(mx).write(OUT/'api-workflows.drawio',encoding='utf-8',xml_declaration=True)
assert len(ET.parse(OUT/'api-workflows.drawio').findall('diagram'))==2
pdf=pdfium.PdfDocument(str(OUT.parent/'api-workflows.pdf'))
temp=ROOT/'tmp/pdfs';temp.mkdir(parents=True,exist_ok=True)
for i in range(len(pdf)):pdf[i].render(scale=1).to_pil().save(temp/f'api-workflow-{i+1}.png')
print('Created two sequence diagrams in PDF and editable draw.io source.')
