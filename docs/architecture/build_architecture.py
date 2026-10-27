"""Generate matching vector PDF and editable draw.io documentation, without app changes."""
from pathlib import Path
import math
import xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import pypdfium2 as pdfium

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
W,H = 1190,842
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
c = canvas.Canvas(str(OUT/'architecture.pdf'), pagesize=(W,H))
c.setTitle('SkillMarket - System Architecture')
c.setAuthor('SkillMarket')
mx = ET.Element('mxfile', host='app.diagrams.net', version='24.7.17')
root = None
seq=0

def cell(value,style,x,y,w,h):
    global seq
    seq+=1
    e=ET.SubElement(root,'mxCell',id=str(seq),value=value,style=style,vertex='1',parent='1')
    ET.SubElement(e,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
    return str(seq)

def text(x,y,s,size=11,bold=False,color='#303840',align='left'):
    c.setFillColor(HexColor(color));c.setFont('Arial-Bold' if bold else 'Arial',size)
    getattr(c, {'left':'drawString','center':'drawCentredString','right':'drawRightString'}[align])(x,H-y-size,s)
    # Separate text objects keep labels fully editable.
    tw=pdfmetrics.stringWidth(s,'Arial-Bold' if bold else 'Arial',size)+4
    tx=x if align=='left' else x-tw/2 if align=='center' else x-tw
    cell(s,f'text;html=0;align=left;verticalAlign=top;whiteSpace=wrap;overflow=visible;fontFamily=Arial;fontSize={size};fontColor={color};fontStyle={1 if bold else 0};',tx,y,tw,size+6)

def rect(x,y,w,h,fill='#ffffff',stroke='#74818d',dash=False):
    c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(stroke));c.setLineWidth(.8);c.setDash(4,3) if dash else c.setDash()
    c.rect(x,H-y-h,w,h,fill=1,stroke=1);c.setDash()
    cell('',f'rounded=0;whiteSpace=wrap;html=0;fillColor={fill};strokeColor={stroke};dashed={int(dash)};',x,y,w,h)

def box(x,y,w,h,title,lines=(),fill='#f2f5f8'):
    rect(x,y,w,h,fill)
    text(x+w/2,y+10,title,12,True,align='center')
    for i,line in enumerate(lines):text(x+w/2,y+32+16*i,line,10.5,align='center')

def arrow(points,label=None,lx=None,ly=None,dash=False,both=False):
    global seq
    c.setStrokeColor(HexColor('#526779'));c.setFillColor(HexColor('#526779'));c.setLineWidth(.9)
    c.setDash(4,3) if dash else c.setDash()
    for (x1,y1),(x2,y2) in zip(points,points[1:]):c.line(x1,H-y1,x2,H-y2)
    c.setDash()
    def tip(a,b):
        angle=math.atan2(b[1]-a[1],b[0]-a[0]);p=c.beginPath();p.moveTo(b[0],H-b[1])
        for off in (-.45,.45):p.lineTo(b[0]-7*math.cos(angle+off),H-(b[1]-7*math.sin(angle+off)))
        p.close();c.drawPath(p,fill=1,stroke=0)
    tip(points[-2],points[-1])
    if both:tip(points[1],points[0])
    seq+=1
    e=ET.SubElement(root,'mxCell',id=str(seq),value='',edge='1',parent='1',style=f'edgeStyle=none;html=0;endArrow=block;endFill=1;startArrow={"block" if both else "none"};startFill=1;strokeColor=#526779;dashed={int(dash)};')
    g=ET.SubElement(e,'mxGeometry',relative='1',attrib={'as':'geometry'})
    for key,pt in [('sourcePoint',points[0]),('targetPoint',points[-1])]:ET.SubElement(g,'mxPoint',x=str(pt[0]),y=str(pt[1]),attrib={'as':key})
    if len(points)>2:
        arr=ET.SubElement(g,'Array',attrib={'as':'points'})
        for x,y in points[1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
    if label:text(lx,ly,label,10)

def start(name,n):
    global root,seq
    d=ET.SubElement(mx,'diagram',id=f'page-{n}',name=name)
    model=ET.SubElement(d,'mxGraphModel',dx=str(W),dy=str(H),grid='1',gridSize='10',page='1',pageScale='1',pageWidth=str(W),pageHeight=str(H))
    root=ET.SubElement(model,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0');seq=1
    text(35,20,'SkillMarket | '+name,18,True)
    text(1155,25,'FalconXoft Weekend Engineering Assignment',10,align='right')
    text(35,811,'Verified local configuration | 27 October 2026 | Vector preview; not a Lucidchart export',9,color='#63717b')
    text(1155,811,str(n),9,align='right')

start('System architecture',1)
rect(35,65,1120,115,stroke='#526779')
text(50,76,'CLIENT DEVICE',11,True)
text(600,77,'Buyer / Seller / Administrator',12,True,align='center')
arrow([(600,96),(600,115)])
box(350,115,500,45,'Web browser',fill='#ffffff')
box(925,115,200,45,'API client',fill='#ffffff')
rect(35,200,1120,585,stroke='#526779')
text(50,211,'LOCAL DEVELOPMENT ENVIRONMENT | Django application + local database file',11,True)
box(350,245,500,55,'Django URL routing', ['config/urls.py | HTML routes / api/ / admin/'])
arrow([(600,160),(600,245)],'HTTP requests',610,181)
arrow([(1025,160),(1025,270),(850,270)],'HTTP / JSON',1040,183)
box(350,340,150,65,'HTML views',['Django forms','marketplace/views.py'])
box(525,340,150,65,'DRF endpoints',['Serializers / permissions','listings, offers, reviews'])
box(700,340,150,65,'Django Admin',['Staff / model permissions','ModelAdmin forms'])
for x in [425,600,775]:arrow([(x,300),(x,340)])

box(65,340,240,112,'Presentation',['Django templates -> HTML','Tailwind CSS 4 / static/app.css','Vanilla JS / static/app.js','Staticfiles; WhiteNoise configured'])
arrow([(350,370),(305,370)],'render',309,350)
arrow([(185,340),(185,235),(48,235),(48,140),(350,140)],'HTML / CSS / JS',65,182,dash=True)
text(65,467,'Templates run on the server;',10)
text(65,482,'HTML, CSS and JS run in the browser.',10)
text(65,507,'Local entry point: manage.py runserver',10)
text(65,522,'Staticfiles serves local development assets.',10)

box(350,455,500,73,'Shared business logic | marketplace/services.py',['Listing discovery and mutations; offer lifecycle; review eligibility','Role / ownership checks; validation; atomic offer and review writes'])
arrow([(425,405),(425,455)])
arrow([(600,405),(600,455)])
arrow([(775,405),(775,455)])
text(785,421,'offer actions',9)

box(925,325,200,230,'Auth and authorization',[
    'Django Authentication + Sessions','Session / auth / CSRF middleware','Buyer / Seller groups',
    'Django Groups and Permissions','Listing ownership','Offer actor + state checks',
    'Completed, own, unique review','Staff / admin permission checks',
    'Cross-cutting; not a service'
])
text(925,565,'Applies across views, API and admin.',10)

box(350,580,500,65,'Django models / ORM',['Listing, Offer, Review | User, Group, Permission, Session','Queries, validation, constraints, migrations and transactions'])
arrow([(600,528),(600,580)],'read / write',610,546,both=True)
arrow([(850,375),(885,375),(885,612),(850,612)],'admin ORM',890,620)

rect(325,685,550,80,fill='#f7f7f7')
text(340,693,'LOCAL DATABASE STORAGE',10,True)
box(350,715,500,38,'SQLite | db.sqlite3',fill='#ffffff')
arrow([(600,645),(600,715)],'SQLite adapter / file I/O',610,662,both=True)
text(65,690,'Deployment support (not active)',11,True)
text(65,712,'PostgreSQL via psycopg / DATABASE_URL.',10)
text(65,729,'Gunicorn entry point in Procfile (Linux).',10)
text(65,746,'No configured Supabase connection.',10)
text(925,690,'Solid: request / data access',10)
text(925,708,'Dashed: rendered response / assets',10)
text(925,735,'Detailed return paths: page 2.',10)
c.showPage()

start('Request and response flows',2)
text(35,57,'All application boxes execute in the same local Django process. SQLite is a file on that machine.',11)

def flow(y,title,labels,desc,returnlabel):
    text(35,y,title,13,True)
    n=len(labels);x=35;gap=27;w=(1120-gap*(n-1))/n;by=y+29;bh=61
    for i,(heading,sub) in enumerate(labels):
        bx=x+i*(w+gap);box(bx,by,w,bh,heading,sub,fill='#f2f5f8' if i else '#ffffff')
        if i<n-1:arrow([(bx+w,by+30),(bx+w+gap,by+30)])
    ry=by+88
    arrow([(x+(n-1)*(w+gap)+w/2,by+bh),(x+(n-1)*(w+gap)+w/2,ry),(x+w/2,ry),(x+w/2,by+bh)],dash=True)
    text(595,ry+7,returnlabel,10,align='center')
    text(35,ry+29,desc,10)

flow(96,'A | Browse listings',[
 ('Buyer / Seller',['Web browser']),('Routing / view',['GET /; home()']),('Browse + ORM',['Filters / pagination']),('SQLite',['Published listings'])
], 'Public discovery needs no login. home() calls services.browse(), annotates ratings and renders home.html.',
 'SQLite rows -> ORM / view -> Django template renders HTML -> browser')
flow(267,'B | Submit an offer',[
 ('Buyer',['Browser POST']),('Session + CSRF',['Routing / HTML view']),('Validate / authorize',['OfferForm; Buyer role']),('Service + ORM',['submit_offer(); atomic']),('SQLite',['Insert Offer'])
], 'Requires an active listing owned by another seller. Model validation runs before saving; invalid requests return errors.',
 'Save result -> view -> redirect to buyer dashboard -> follow-up GET -> rendered HTML in browser')
flow(438,'C | REST API request',[
 ('API client',['HTTP / JSON']),('DRF router',['/api/ endpoints']),('Serializer / access',['Session auth; CSRF']),('Service / ORM',['Writes via services']),('SQLite',['Queries / mutations'])
], 'Public listing reads allow anonymous clients. Protected requests enforce roles/ownership; reads may query the ORM directly.',
 'Database result -> service / viewset -> serializer -> JSON response to API client')
flow(609,'D | Administration',[
 ('Administrator',['Web browser']),('Django Admin',['/admin/; session auth']),('Admin permissions',['Staff + model access']),('Models / ORM',['Offer actions: services']),('SQLite',['Application / auth data'])
], 'Listings and reviews use ModelAdmin; offer status actions use services.transition(). Admin pages render HTML.',
 'Database result -> ModelAdmin -> admin templates -> HTML response to administrator')
c.showPage();c.save()
ET.indent(mx)
ET.ElementTree(mx).write(OUT/'architecture.drawio',encoding='utf-8',xml_declaration=True)
# Validate source and render both PDF pages for visual inspection.
assert len(ET.parse(OUT/'architecture.drawio').findall('diagram'))==2
pdf=pdfium.PdfDocument(str(OUT/'architecture.pdf'))
temp=ROOT/'tmp/pdfs';temp.mkdir(parents=True,exist_ok=True)
for i in range(len(pdf)):pdf[i].render(scale=1.2).to_pil().save(temp/f'architecture-page-{i+1}.png')
print('Generated architecture.pdf and architecture.drawio; 2 pages each.')
