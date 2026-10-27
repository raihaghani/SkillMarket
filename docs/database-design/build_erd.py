"""Build documentation from a read-only schema snapshot; never writes the database."""
from pathlib import Path
import json, math, xml.etree.ElementTree as ET
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import pypdfium2 as pdfium

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
schema=json.loads((OUT/'schema-verification.json').read_text())
W,H=1190,842
for name,file in [('Arial','arial.ttf'),('Arial-Bold','arialbd.ttf')]:pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
c=canvas.Canvas(str(OUT/'database-design.pdf'),pagesize=(W,H));c.setTitle('SkillMarket database design and ERD')
mx=ET.Element('mxfile',host='app.diagrams.net');root=None;seq=1
def cell(value,style,x,y,w,h):
    global seq
    seq+=1;e=ET.SubElement(root,'mxCell',id=str(seq),value=value,style=style,vertex='1',parent='1')
    ET.SubElement(e,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
def text(x,y,s,size=11,bold=False):
    font='Arial-Bold' if bold else 'Arial';c.setFont(font,size);c.setFillColor(HexColor('#303840'));c.drawString(x,H-y-size,s)
    cell(s,f'text;html=0;align=left;verticalAlign=top;fontFamily=Arial;fontSize={size};fontStyle={int(bold)};',x,y,pdfmetrics.stringWidth(s,font,size)+4,size+5)
def rect(x,y,w,h,fill='#ffffff'):
    c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor('#7c8790'));c.setLineWidth(.7);c.rect(x,H-y-h,w,h,fill=1,stroke=1)
    cell('',f'rounded=0;fillColor={fill};strokeColor=#7c8790;',x,y,w,h)
def line(pts):
    global seq
    c.setStrokeColor(HexColor('#637784'));c.setLineWidth(.8)
    for (a,b),(d,e) in zip(pts,pts[1:]):c.line(a,H-b,d,H-e)
    seq+=1;el=ET.SubElement(root,'mxCell',id=str(seq),edge='1',parent='1',style='edgeStyle=none;endArrow=none;strokeColor=#637784;')
    g=ET.SubElement(el,'mxGeometry',relative='1',attrib={'as':'geometry'})
    for k,p in [('sourcePoint',pts[0]),('targetPoint',pts[-1])]:ET.SubElement(g,'mxPoint',x=str(p[0]),y=str(p[1]),attrib={'as':k})
    if len(pts)>2:
        arr=ET.SubElement(g,'Array',attrib={'as':'points'})
        for x,y in pts[1:-1]:ET.SubElement(arr,'mxPoint',x=str(x),y=str(y))
def rel(pts,label,x,y):line(pts);text(x,y,label,11,True)
def page(title,n):
    global root,seq
    d=ET.SubElement(mx,'diagram',id=f'p{n}',name=title);m=ET.SubElement(d,'mxGraphModel',page='1',pageWidth=str(W),pageHeight=str(H));root=ET.SubElement(m,'root');ET.SubElement(root,'mxCell',id='0');ET.SubElement(root,'mxCell',id='1',parent='0');seq=1
    text(35,22,'SkillMarket | '+title,18,True)
    text(35,55,'SQLite schema verified against Django models, migrations and the local database | 27 October 2026',11)
    text(35,815,'FalconXoft | Local vector preview, not a Lucidchart export | PK: primary key; FK: foreign key; UQ: unique; ?: nullable',9)
    text(1145,815,str(n),10)
def table(t,x,y,w=350,subset=None):
    fields=schema[t]['fields'];fields=[f for f in fields if subset is None or f['column'] in subset]
    h=39+len(fields)*23
    rect(x,y,w,h);rect(x,y,w,32,'#eaf1f7' if t.startswith('marketplace') else '#eeeeee')
    text(x+10,y+8,t,12,True)
    for i,f in enumerate(fields):
        yy=y+39+23*i
        flags=('PK ' if f['primary_key'] else '')+('FK ' if f['related_table'] else '')+('UQ' if f['unique'] and not f['primary_key'] else '')
        text(x+8,yy,flags,9)
        text(x+62,yy,f['column']+(' ?' if f['null'] else ''),10.5)
        text(x+w-132,yy,f['resolved_type'].upper(),10)
    return h

page('Marketplace entities',1)
text(35,82,'Relationship notation: parent (1) -- child (0..N), or (0..1). Every child FK is required. No role column exists.',11)
table('auth_user',35,135,345)
table('marketplace_listing',805,135,350)
table('marketplace_offer',420,445,350)
table('marketplace_review',805,515,350)
rel([(380,185),(805,185)],'User (1) -- Listing (0..N): seller_id',425,164)
rel([(380,280),(595,280),(595,445)],'User (1) -- Offer (0..N): buyer_id',405,258)
# Label points to the bent relation through a clear adjacent gutter.
rel([(980,381),(980,415),(785,415),(785,480),(770,480)],'Listing (1) -- Offer (0..N): listing_id',805,440)
rel([(650,668),(650,705),(805,705)],'1 : 0..1 (offer_id UQ)',665,682)
rel([(35,390),(8,390),(8,788),(1080,788),(1080,715)],'User (1) -- Review (0..N): seller_id',400,790)
rel([(35,370),(20,370),(20,763),(940,763),(940,715)],'User (1) -- Review (0..N): reviewer_id',400,744)
text(35,470,'Built-in auth.User',11,True)
text(35,491,'Buyer / Seller membership: see page 2.',10)
text(35,518,'All marketplace FK fields use Django PROTECT.',10)
text(35,535,'Database FK actions: NO ACTION (SQLite).',10)
text(35,562,'Types are actual SQLite declarations.',10)
text(35,579,'Domain IDs: BigAutoField -> INTEGER PK.',10)
text(35,596,'Domain references: BIGINT; user IDs: INTEGER.',10)
text(35,623,'DECIMAL fields: Django max_digits=10,',10)
text(35,640,'decimal_places=2; SQLite does not enforce',10)
text(35,657,'fixed decimal precision or VARCHAR lengths.',10)
c.showPage()

page('Authentication and permissions',2)
text(35,82,'Each connector is parent (1) -- join/child (0..N). Composite UQ constraints prevent duplicate memberships.',11)
table('auth_user',35,135,280,['id','username'])
table('auth_user_groups',405,135,350)
table('auth_group',855,135,300)
rel([(315,188),(405,188)],'1 : 0..N',325,165)
rel([(855,188),(755,188)],'1 : 0..N',768,165)
text(415,259,'UQ (user_id, group_id)',10)
text(865,233,'Buyer and Seller are group rows.',10)
table('auth_user_user_permissions',35,410,350)
table('auth_group_permissions',430,410,350)
table('auth_permission',825,410,330)
rel([(175,220),(175,410)],'1 : 0..N',185,320)
rel([(1120,220),(1120,332),(605,332),(605,410)],'1 : 0..N',620,308)
rel([(825,470),(780,470)],'1 : 0..N',785,445)
rel([(1040,541),(1040,605),(210,605),(210,518)],'Permission (1) -- direct grant (0..N)',400,610)
text(45,540,'UQ (user_id, permission_id)',10)
text(440,540,'UQ (group_id, permission_id)',10)
text(835,558,'UQ (content_type_id, codename)',10)
table('django_content_type',825,680,330)
rel([(1120,680),(1120,541)],'1 : 0..N',1130,630)
text(835,792,'UQ (app_label, model)',10)
text(35,670,'Role and permission implementation',12,True)
text(35,697,'0002_roles creates Buyer/Seller groups and grants model permissions.',11)
text(35,719,'Marketplace authorization checks group membership and record ownership.',11)
text(35,741,'Django Admin uses staff/model permissions. Direct user grants are supported',11)
text(35,763,'by Django; their join table exists, but role seeding uses group grants.',11)
c.showPage()

page('Constraints, indexes and verification',3)
sections=[
 ('Database-enforced integrity',[
 'Listing: starting_price > 0; status IN (ACTIVE, INACTIVE).',
 'Offer: offered_price > 0; status IN (PENDING, ACCEPTED, REJECTED, COMPLETED).',
 'Review: 1 <= rating <= 5; offer_id UNIQUE and NOT NULL; all domain foreign keys NOT NULL.',
 'All tables shown have primary keys. auth_user.username and auth_group.name are unique.',
 'Auth join pairs, permission (content_type_id, codename), and content type (app_label, model) are unique.'
 ]),
 ('Explicit marketplace indexes (all confirmed in SQLite)',[
 'marketplace_status_a6670d_idx: Listing(status, category) - published/category discovery.',
 'marketplace_seller__639ce1_idx: Listing(seller_id, status) - seller listings, optionally by status.',
 'marketplace_title_7bdd5a_idx: Listing(title) - ordered/equality access; not an arbitrary substring-search accelerator.',
 'marketplace_buyer_i_b1e5a0_idx: Offer(buyer_id, status) - buyer dashboard and status filtering.',
 'marketplace_listing_6b4340_idx: Offer(listing_id, status) - listing offers and status filtering.',
 'Django also creates FK indexes; Review.offer_id uses its unique index. Full inventory is in the notes.',
 'SQLite INTEGER PRIMARY KEY uses the rowid B-tree; it does not require a separate PK index.'
 ]),
 ('Application rules, defaults and delete behavior',[
 'Ownership, Buyer/Seller eligibility, valid state transitions, completed-offer reviews and cross-table author/seller',
 'consistency are checked in services.py. Foreign keys alone do not enforce these business rules.',
 'Django defaults: Listing.status=ACTIVE; Offer.status=PENDING. Timestamps use auto_now_add / auto_now.',
 'These are ORM behavior, not database DEFAULT clauses or automatic database update triggers.',
 'Domain relationships: Django PROTECT. Auth/content-type relationships shown: Django CASCADE.',
 'SQLite reports NO ACTION FK actions; Django implements PROTECT/CASCADE in its deletion collector.'
 ]),
 ('Verification and known gaps',[
 'All migrations applied, including marketplace.0001_initial and 0002_roles; no pending model migrations.',
 'Live column types, nullability, FKs, checks, unique constraints and indexes inspected; PRAGMA foreign_key_check: 0 violations.',
 'SQLite is active locally. PostgreSQL is supported by settings but Supabase is not configured.',
 'Category membership, text lengths, decimal precision and exact one-role-per-user are not database constraints.',
 'Review author/seller consistency and completed status have no cross-table database check; direct writes can bypass services.',
 'No application code, migrations or database schema changed. Internal session/admin-log tables are omitted from the main ERD.'
 ])]
y=105
for title,lines in sections:
    text(35,y,title,13,True);y+=29
    for s in lines:text(45,y,s,11);y+=20
    y+=12
c.showPage();c.save()
ET.indent(mx);ET.ElementTree(mx).write(OUT/'database-design.drawio',encoding='utf-8',xml_declaration=True)
assert len(ET.parse(OUT/'database-design.drawio').findall('diagram'))==3
pdf=pdfium.PdfDocument(str(OUT/'database-design.pdf'))
for i in range(len(pdf)):pdf[i].render(scale=1.2).to_pil().save(ROOT/f'tmp/pdfs/erd-page-{i+1}.png')
print('Created 3-page PDF and editable draw.io source.')
