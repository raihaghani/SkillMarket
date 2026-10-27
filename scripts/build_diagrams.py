"""Create clearly identified local diagram drafts; not Lucidchart exports."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import simpleSplit
import pypdfium2 as pdfium

OUT=Path('submission/03_Marketplace')
GREEN=HexColor('#285d49'); GRAY=HexColor('#64746a')
def start(name,title,subtitle):
    c=canvas.Canvas(str(OUT/name),pagesize=(842,595))
    c.setTitle(title); c.setFillColor(GREEN);c.setFont('Helvetica-Bold',25);c.drawString(40,545,title)
    c.setFillColor(GRAY);c.setFont('Helvetica',10);c.drawString(40,522,subtitle)
    return c
def text(c,x,y,lines,size=10,width=740):
    c.setFillColor(GRAY);c.setFont('Helvetica',size)
    for paragraph in lines:
        for line in simpleSplit(paragraph,'Helvetica',size,width):
            c.drawString(x,y,line);y-=15
        y-=6
def box(c,x,y,w,h,title,lines):
    c.setFillColor(HexColor('#f1f4ed'));c.setStrokeColor(HexColor('#c9d5c4'));c.roundRect(x,y,w,h,7,fill=1,stroke=1)
    c.setFillColor(GREEN);c.setFont('Helvetica-Bold',12);c.drawString(x+12,y+h-23,title)
    text(c,x+12,y+h-44,lines,9,w-24)
def arrow(c,x1,y1,x2,y2,label=''):
    import math
    c.setStrokeColor(GREEN);c.setLineWidth(1.4);c.line(x1,y1,x2,y2)
    a=math.atan2(y2-y1,x2-x1)
    for offset in [-.45,.45]:c.line(x2,y2,x2-8*math.cos(a+offset),y2-8*math.sin(a+offset))
    if label:
        c.setFillColor(GRAY);c.setFont('Helvetica',8);c.drawString((x1+x2)/2+5,(y1+y2)/2+6,label)
def end(c):
    c.setStrokeColor(HexColor('#dce4d6'));c.line(40,47,802,47)
    text(c,40,31,['LOCAL DRAFT | Not a Lucidchart export. Editable Lucidchart URL pending. | SkillMarket | 2026-10-25'],8)
    c.save()

c=start('architecture.pdf','SkillMarket architecture','Django monolith with separate browser and PostgreSQL deployment boundaries')
box(c,40,350,150,115,'Browser',['Templates + CSS + JS','Session cookie / CSRF','Buyers, sellers, admins'])
box(c,245,390,210,75,'Django HTML views',['Forms, templates, admin'])
box(c,245,285,210,75,'Django REST API',['Serializers; scoped querysets'])
box(c,510,330,150,115,'Shared services',['Role + ownership checks','Atomic offer transitions','Review eligibility'])
box(c,510,205,150,75,'Django ORM',['psycopg; migrations'])
box(c,705,205,100,160,'Supabase',['PostgreSQL','TLS connection','Constraints','Indexes','Backups'])
arrow(c,190,430,245,430,'HTTPS');arrow(c,190,370,245,320,'JSON');arrow(c,455,420,510,395);arrow(c,455,320,510,360);arrow(c,585,330,585,280);arrow(c,660,240,705,240,'TLS')
text(c,40,160,['App host: HTTPS reverse proxy -> Gunicorn -> Django. WhiteNoise serves compiled assets. Session and CSRF middleware protect both interfaces.','External integration: PostgreSQL only at runtime. GitHub, Lucidchart and Drive are engineering/submission tools. No payment or email provider.','A monolith keeps auth, deployment and transactions in one place. Larger deployments may scale app instances without splitting the domain into microservices.'],10)
end(c)
c=start('database-design.pdf','Database relationships','Built-in Django User and Group plus three marketplace models')
box(c,40,350,165,130,'auth_user',['PK id; username unique','Password hash; staff flags','Seller / buyer identities'])
box(c,280,350,190,130,'Listing',['PK id; FK seller -> User','title; description; category','starting_price > 0','ACTIVE / INACTIVE; timestamps'])
box(c,540,350,235,130,'Offer',['PK id; FK listing -> Listing','FK buyer -> User; price > 0','message; status; timestamps','PENDING / ACCEPTED / REJECTED / COMPLETED'])
box(c,280,145,190,140,'Review',['PK id; unique FK offer -> Offer','FK reviewer -> User','FK seller -> User','rating 1..5; comment; created_at'])
box(c,40,145,165,140,'Auth membership',['auth_group','auth_user_groups join (M:N)','auth_group_permissions','auth_permission + content type'])
arrow(c,205,420,280,420,'1:N seller');arrow(c,470,420,540,420,'1:N');arrow(c,655,350,470,250,'1:0..1');arrow(c,122,350,122,285,'M:N')
c.setStrokeColor(GREEN);c.line(175,480,175,495);c.line(175,495,650,495);arrow(c,650,495,650,480)
c.setFillColor(GRAY);c.setFont('Helvetica',8);c.drawString(360,499,'User 1:N Offer (buyer)')
text(c,510,260,['Review identities reference User separately. All domain foreign keys use PROTECT.','Indexes: listing(status, category), listing(seller, status), title; offer(buyer, status), offer(listing, status). FK indexes are automatic.','Constraints: positive prices, valid statuses, rating range and unique review/offer. Cross-row role/eligibility rules live in services.'],9,280)
text(c,40,105,['The B-tree title index does not optimize arbitrary substring search. Add PostgreSQL trigram indexes only after measuring the workload.'],9)
end(c)
c=start('api-workflows.pdf','Offer and review workflows','Session + CSRF -> serializer/form -> shared service -> PostgreSQL transaction')
xs=[75,275,485,715]
for x,name in zip(xs,['Buyer / seller','Django / DRF','Service + authorization','PostgreSQL']):
    c.setFillColor(GREEN);c.setFont('Helvetica-Bold',10);c.drawCentredString(x+25,475,name)
    c.setStrokeColor(HexColor('#d7dfd1'));c.line(x+25,455,x+25,160)
events=[(440,0,1,'Buyer: POST offer'),(410,1,2,'Validate input + role'),(380,2,3,'Lock active listing; insert PENDING'),(350,3,0,'201: offer created'),(310,0,2,'Seller: accept; owner + status check'),(280,2,3,'Lock offer; ACCEPTED'),(240,0,2,'Seller completes ACCEPTED offer'),(210,2,3,'COMPLETED; commit'),(175,0,3,'Buyer review: lock offer, eligibility, unique insert')]
for y,a,b,label in events:
    arrow(c,xs[a]+25,y,xs[b]+25,y)
    c.setFillColor(GRAY);c.setFont('Helvetica',8);c.drawString(min(xs[a],xs[b])+30,y+7,label)
text(c,40,125,['Failure paths: missing/hidden object -> 404; wrong role or owner -> 403; invalid price/rating/state or duplicate review -> 400.','Concurrent review requests serialize on the offer row; the unique offer FK is a second guard. Repeated accept returns 400 and preserves ACCEPTED. All failed transactions roll back.'],9)
end(c)
for name in ['architecture','database-design','api-workflows']:
    doc=pdfium.PdfDocument(str(OUT/f'{name}.pdf'))
    doc[0].render(scale=1.4).to_pil().save(OUT/'evidence'/f'{name}.png')
print('Created and rendered three local draft PDFs.')
