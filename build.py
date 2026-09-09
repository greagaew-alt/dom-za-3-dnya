# -*- coding: utf-8 -*-
"""
Генератор вайрфрейм-прототипа лендинга «Дом за 3 дня» (Казань).
Запуск:  py build.py     →  собирает HTML в папку prototype/
"""
import io, os, re, sys, shutil
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# режим client: сборка для клиента — без служебных аннотаций,
# комментарии-пины с сохранением на сервере (comments.php).
# режим pages: то же, но в docs/ и без PHP — комментарии в localStorage
# (запасная площадка на GitHub Pages, пока хостинг под фильтром).
CLIENT = "client" in sys.argv or "pages" in sys.argv
PAGES_MODE = "pages" in sys.argv
OUT = "docs" if (PAGES_MODE or not CLIENT) else "client"

# ── ТИПОГРАФ: неразрывные пробелы после предлогов/союзов, в числах, инициалах
_PREP = (r"в|во|на|над|под|перед|при|про|за|из|изо|из-за|из-под|с|со|к|ко|у|о|"
         r"об|обо|от|ото|до|по|для|без|безо|через|около|между|среди|против|"
         r"и|а|но|да|не|ни|что|чтоб|чтобы|как|так|же|бы|б|ли|то|или|либо|если|"
         r"это|уже|ещё|еще|вы|мы|он|она|они")


_TPRE = r"(?i)(^|[\s(«\"'>—–-]|&\w+;|&#\d+;)(%s)\s+" % _PREP


def _typo_text(t):
    t = re.sub(_TPRE, "\\1\\2\u00a0", t)
    t = re.sub(_TPRE, "\\1\\2\u00a0", t)
    t = re.sub(r"(\d)\s+(?=\d{3}\b)", "\\1\u00a0", t)
    t = re.sub(r"(\d)\s+(?=\d{3}\b)", "\\1\u00a0", t)
    t = re.sub(r"(\d)\s+(₽|&#8381;|м²|м³|м2|км|мм|см|кг|т|%|дн\w*|дней|день|"
               r"лет|год\w*|года|мес\w*|шт\w*|чел\w*)", "\\1\u00a0\\2", t)
    t = re.sub(r"([А-ЯЁ])\.\s+(?=[А-ЯЁ])", "\\1.\u00a0", t)
    t = re.sub(r"\bт\.\s*([дпек])\.", "т.\u00a0\\1.", t)
    t = re.sub(r"\s+(—|&mdash;)", "\u00a0\\1", t)
    return t


def typo(html):
    out = []
    for ch in re.split(r"(<style[\s\S]*?</style>|<script[\s\S]*?</script>)", html):
        if ch[:6] in ("<style", "<scrip"):
            out.append(ch)
            continue
        parts = re.split(r"(<[^>]+>)", ch)
        for i, p in enumerate(parts):
            if p[:1] != "<":
                parts[i] = _typo_text(p)
        out.append("".join(parts))
    return "".join(out)

# ─────────────────────────────────────────────────────────────── СТИЛИ

CSS = """
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#fff;color:#111;overflow-x:hidden;
  font:15px/1.6 -apple-system,'Segoe UI',Roboto,Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:inherit}
img{max-width:100%}
h1,h2,h3{overflow-wrap:break-word}

/* шапка */
.top{position:sticky;top:0;z-index:50;background:#fff;border-bottom:1px solid #e5e5e5}
.top-in{max-width:1320px;margin:0 auto;padding:12px 20px;
  display:flex;align-items:center;gap:20px}
.logo{font-weight:700;font-size:17px;letter-spacing:-.02em;white-space:nowrap}
.logo small{display:block;font-weight:400;font-size:10.5px;color:#888;letter-spacing:0}
.nav{display:flex;gap:18px;font-size:13.5px;color:#555;margin-left:auto;flex-wrap:wrap}
.nav a{text-decoration:none}
.nav a:hover{color:#111}
.top-phone{font-weight:600;font-size:14.5px;white-space:nowrap}
.burger{display:none;margin-left:auto;border:1px solid #ccc;background:#fff;
  border-radius:8px;padding:7px 10px;font-size:13px;cursor:pointer}

/* каркас страницы */
main{max-width:1320px;margin:0 auto;padding:22px 20px 90px}
.crumb{font-size:12.5px;color:#999;margin:0 0 14px}
.crumb a{color:#666}

/* секция-карточка */
section{position:relative;background:#fafafa;border:1px solid #ddd;border-radius:14px;
  padding:44px 26px 22px;margin:0 0 18px}
.sec-label{position:absolute;top:12px;left:16px;font-size:10.5px;letter-spacing:.09em;
  text-transform:uppercase;color:#8a8a8a;font-weight:600}
.note{margin:20px 0 0;padding-top:14px;border-top:1px dashed #d5d5d5;
  font-size:12.5px;line-height:1.5;color:#7a7a7a;font-style:italic}

/* типографика внутри секций */
h1{font-size:33px;line-height:1.15;letter-spacing:-.02em;margin:0 0 12px;font-weight:700}
h2{font-size:23px;line-height:1.22;letter-spacing:-.015em;margin:0 0 8px;font-weight:700}
h3{font-size:15.5px;line-height:1.3;margin:0 0 5px;font-weight:700}
.lead{font-size:16.5px;line-height:1.5;color:#444;margin:0 0 16px;max-width:60ch}
.sub{font-size:13.5px;color:#666;margin:0 0 14px;max-width:66ch}
p{margin:0 0 10px}
ul{margin:8px 0 0;padding-left:19px}
li{margin:4px 0}
.small{font-size:12.5px;color:#777}

/* заглушки — то, что ждём от клиента */
.stub{background:#fff3c4;border-bottom:1px solid #e3c85a;padding:0 3px;
  border-radius:3px;font-style:normal}

/* кнопки */
.btn{display:inline-block;background:#111;color:#fff;text-decoration:none;
  border:2px solid #111;border-radius:9px;padding:12px 20px;font-size:14px;
  font-weight:600;cursor:pointer}
.btn.ghost{background:#fff;color:#111}
.btn.sm{padding:8px 14px;font-size:13px}
.btns{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0 0}

/* фото-плейсхолдер */
.ph{border:1.5px dashed #bbb;border-radius:10px;color:#8a8a8a;font-size:12.5px;
  display:flex;align-items:center;justify-content:center;text-align:center;
  padding:14px;min-height:150px;
  background:repeating-linear-gradient(45deg,#f2f2f2,#f2f2f2 7px,#e9e9e9 7px,#e9e9e9 14px)}
.ph.tall{min-height:260px}
.ph.wide{min-height:190px}
.ph.sq{min-height:120px}
.ph.gal{min-height:300px}

/* галерея-заглушка со стрелками листания */
.gallery{position:relative}
.arw{position:absolute;top:50%;transform:translateY(-50%);z-index:2;
  width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,.75);
  border:1px solid #dcdcdc;display:flex;align-items:center;justify-content:center;
  font-size:17px;line-height:1;color:#8a8a8a;text-decoration:none;opacity:.45}
.arw:hover{opacity:1;color:#333}
.arw.l{left:9px}
.arw.r{right:9px}

/* сетки */
.g{display:grid;gap:12px}
.g2{grid-template-columns:repeat(2,1fr)}
.g3{grid-template-columns:repeat(3,1fr)}
.g4{grid-template-columns:repeat(4,1fr)}
.g5{grid-template-columns:repeat(5,1fr)}
.split{display:grid;grid-template-columns:1.05fr .95fr;gap:24px;align-items:start}
.split-stretch{align-items:stretch}
.split-stretch>div{min-width:0}
.split-stretch .ph{height:100%}

/* карточка */
.card{background:#fff;border:1px solid #e0e0e0;border-radius:11px;padding:15px}
.card .num{font-size:11px;font-weight:700;color:#999;letter-spacing:.06em}
.price{font-size:19px;font-weight:700;letter-spacing:-.01em;margin:8px 0 0}
.price small{display:block;font-size:11.5px;font-weight:400;color:#888;letter-spacing:0}

/* кликабельная карточка → другая страница */
.click{background:#fff;border:2px solid #111;border-radius:11px;padding:15px;
  box-shadow:0 2px 0 #111;text-decoration:none;display:block;
  transition:transform .12s ease,box-shadow .12s ease}
.click:hover{transform:translateY(-3px);box-shadow:0 5px 0 #111}
.click .badge{display:inline-block;font-size:9.5px;letter-spacing:.08em;font-weight:700;
  text-transform:uppercase;background:#111;color:#fff;border-radius:4px;padding:3px 6px;
  margin:0 0 8px}
.click .go{margin:10px 0 0;font-weight:700;font-size:13.5px}

/* чипсы */
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 0}
.chip{background:#fff;border:1px solid #d8d8d8;border-radius:999px;
  padding:6px 13px;font-size:12.5px;color:#444}
.hero-geo{display:inline-block;margin:0 0 10px;padding:5px 12px 5px 10px;
  background:#f2f2f2;border:1px solid #e0e0e0;border-radius:999px;
  font-size:12px;color:#555;letter-spacing:.01em}
.hero-geo::before{content:"";display:inline-block;width:6px;height:6px;
  border-radius:50%;background:#111;margin:0 7px 1px 0;vertical-align:middle}

/* таблица */
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch;
  border:1px solid #e0e0e0;border-radius:10px}
table{width:100%;border-collapse:collapse;background:#fff;font-size:13.5px}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #ededed;
  white-space:nowrap}
th{background:#f4f4f4;font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;color:#666}
tr:last-child td{border-bottom:0}

/* шаги-процесс */
.steps{counter-reset:s;display:grid;gap:10px}
.step{counter-increment:s;background:#fff;border:1px solid #e0e0e0;border-radius:11px;
  padding:14px 15px 14px 52px;position:relative}
.step::before{content:counter(s);position:absolute;left:15px;top:13px;width:24px;height:24px;
  background:#111;color:#fff;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:12.5px;font-weight:700}

/* форма */
.form{background:#fff;border:1px solid #e0e0e0;border-radius:11px;padding:16px;max-width:430px}
.field{border:1px solid #d5d5d5;border-radius:8px;padding:11px 12px;font-size:13.5px;
  color:#999;margin:0 0 9px;background:#fcfcfc}
.consent{font-size:11.5px;color:#999;margin:9px 0 0}

/* квиз */
.quiz{background:#fff;border:2px solid #111;border-radius:12px;padding:18px}
.qstep{border-bottom:1px dashed #ddd;padding:0 0 14px;margin:0 0 14px}
.qstep:last-of-type{border-bottom:0;margin-bottom:0}
.qnum{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:#999;font-weight:700}
.qq{font-weight:700;font-size:14.5px;margin:3px 0 9px}
.opts{display:flex;gap:7px;flex-wrap:wrap}
.opt{border:1px solid #ccc;border-radius:8px;padding:7px 12px;font-size:13px;background:#fcfcfc}
.gift{background:#fff3c4;border:1px solid #e3c85a;border-radius:9px;padding:11px 13px;
  font-size:13px;margin:14px 0 0}

/* акценты */
.hl{background:#fff;border-left:3px solid #111;border-radius:0 9px 9px 0;
  padding:12px 15px;margin:14px 0 0;font-size:14px}
.rating{display:flex;align-items:baseline;gap:9px;margin:0 0 12px}
.rating b{font-size:30px;letter-spacing:-.02em}

/* футер */
footer{border-top:1px solid #e5e5e5;background:#fafafa}
.foot-in{max-width:1320px;margin:0 auto;padding:26px 20px;display:grid;
  grid-template-columns:1.5fr 1fr 1.4fr 1.2fr;gap:22px;font-size:13px;color:#666}
.foot-in b{color:#111;display:block;margin:0 0 7px;font-size:13px}
.foot-in a{text-decoration:none;display:block;margin:0 0 5px}
.foot-in .social{margin-top:11px}
.foot-in .social a{display:flex;margin:0}
.foot-bottom{max-width:1320px;margin:0 auto;padding:13px 20px 4px;
  border-top:1px solid #ececec;display:flex;justify-content:space-between;
  gap:12px;flex-wrap:wrap;font-size:12px;color:#999}

/* комментарии (из скилла) */
.cmt-btn{position:absolute;top:8px;right:10px;background:#fff;border:1px solid #ccc;
  border-radius:8px;padding:5px 10px;font-size:11.5px;cursor:pointer;color:#555}
.cmt-btn:hover{border-color:#111;color:#111}
.cmt-form{margin:14px 0 0;background:#fff;border:1px solid #111;border-radius:10px;padding:12px}
.cmt-form textarea{width:100%;min-height:74px;border:1px solid #d5d5d5;border-radius:7px;
  padding:9px;font:inherit;font-size:13.5px;resize:vertical}
.cmt-row{display:flex;align-items:center;gap:12px;margin:9px 0 0}
.cmt-row button{background:#111;color:#fff;border:0;border-radius:7px;padding:8px 15px;
  font-size:13px;font-weight:600;cursor:pointer}
.cmt-x{font-size:12.5px;color:#888;cursor:pointer}
.cmt-list{margin:12px 0 0;display:grid;gap:7px}
.cmt-item{background:#fffbe8;border:1px solid #ecdca0;border-radius:9px;padding:9px 11px}
.cmt-item span{font-size:11px;color:#9a8b52;display:block;margin:0 0 3px}
.cmt-item p{margin:0;font-size:13.5px}
.cmt-fab{position:fixed;right:16px;bottom:16px;z-index:60;background:#111;color:#fff;
  border:0;border-radius:999px;padding:12px 18px;font-size:13.5px;font-weight:600;
  cursor:pointer;box-shadow:0 6px 20px rgba(0,0,0,.25)}
#cmt-page-panel{position:relative;background:#fafafa;border:1px dashed #ccc;
  border-radius:14px;padding:16px;margin:0 0 18px}
.cmt-panel-title{font-size:12.5px;color:#777;margin:0 0 8px;font-weight:600}

/* соцсети */
.social{display:flex;gap:7px;align-items:center}
.social a{width:32px;height:32px;border:1px solid #d5d5d5;border-radius:8px;
  display:flex;align-items:center;justify-content:center;color:#333;
  text-decoration:none;flex:none}
.social a:hover{border-color:#111;color:#111}
.social svg{width:17px;height:17px;fill:currentColor}
.social .ismax{font-size:9px;font-weight:800;letter-spacing:.02em}
.foot-social{margin-top:11px}

/* каталог: фильтры слева, карточки справа */
.catwrap{display:grid;grid-template-columns:236px 1fr;gap:24px;align-items:start}
.filters{position:sticky;top:74px;background:#fff;border:1px solid #e0e0e0;
  border-radius:12px;padding:6px 15px 15px;display:flex;flex-direction:column}
.fg{border-bottom:1px solid #eee;padding:14px 0}
.fg:last-child{border-bottom:0;padding-bottom:2px}
.fg h4{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#8a8a8a;
  font-weight:700;margin:0 0 9px}
.fnav{display:flex;flex-direction:column;gap:2px}
.fnav a{display:block;padding:8px 10px;border-radius:8px;font-size:13.5px;
  text-decoration:none;color:#333}
.fnav a:hover{background:#f2f2f2}
.fnav a.act{background:#111;color:#fff;font-weight:600}
.fopt{display:flex;align-items:center;gap:9px;font-size:13px;color:#444;padding:5px 0;cursor:pointer}
.fopt::before{content:"";width:15px;height:15px;border:1.5px solid #bcbcbc;
  border-radius:4px;flex:none;background:#fcfcfc}
.fopt.rad::before{border-radius:50%}
.fopt.on::before{background:#111;border-color:#111;box-shadow:inset 0 0 0 3px #fff}
.slider{height:4px;background:#dedede;border-radius:2px;position:relative;margin:16px 6px 8px}
.slider span{position:absolute;top:50%;width:15px;height:15px;background:#111;
  border-radius:50%;transform:translate(-50%,-50%);border:2px solid #fff;
  box-shadow:0 0 0 1px #111}
.slider span:first-child{left:8%}.slider span:last-child{left:88%}
.srow{display:flex;justify-content:space-between;font-size:11.5px;color:#8a8a8a}
.fbtns{display:flex;flex-direction:column;gap:7px;margin-top:14px}
.catmain{min-width:0}
.catbar{display:flex;justify-content:space-between;align-items:center;gap:12px;
  flex-wrap:wrap;padding:0 0 14px;margin:0 0 18px;border-bottom:1px solid #eee}
.catbar .cnt{font-size:13.5px;color:#555;font-weight:600}
.catbar .sort{border:1px solid #d5d5d5;border-radius:8px;padding:8px 12px;
  font-size:12.5px;color:#555;background:#fcfcfc}
.ctype{margin:0 0 30px}
.ctype:last-child{margin-bottom:0}
.ctype > h3{font-size:16.5px;margin:0 0 3px}
.ctype .pnote{font-size:12.5px;color:#8a8a8a;margin:0 0 13px}
.filters-m{display:none}

/* планшет */
@media(max-width:900px){
  .split{grid-template-columns:1fr;gap:18px}
  .g4,.g5{grid-template-columns:repeat(2,1fr)}
  .g3{grid-template-columns:repeat(2,1fr)}
  main{max-width:none}

  /* каталог: фильтры наверх, навигация по типам — лентой */
  .foot-in{grid-template-columns:1fr 1fr}
  .catwrap{grid-template-columns:1fr;gap:16px}
  .filters{position:static;padding:12px}
  .fg{border-bottom:0;padding:0 0 4px}
  .fg.desk{display:none}
  .fnav{flex-direction:row;overflow-x:auto;-webkit-overflow-scrolling:touch;
    gap:7px;padding-bottom:2px}
  .fnav a{white-space:nowrap;border:1px solid #ddd}
  .fnav a span{display:none}
  .fnav a.act{border-color:#111}
  .filters-m{display:block;margin-top:10px;border:1px solid #d5d5d5;
    border-radius:8px;padding:9px 12px;font-size:12.5px;color:#666;background:#fcfcfc}
}
/* телефон */
@media(max-width:640px){
  main{padding:14px 12px 78px}
  section{padding:42px 14px 16px;border-radius:12px}
  .sec-label{left:13px}
  h1{font-size:25px;line-height:1.18}
  h2{font-size:20px}
  h3{font-size:15px}
  .lead{font-size:15.5px}
  .sub{font-size:13px}
  .g2,.g3,.g4,.g5{grid-template-columns:1fr}
  .split{gap:16px}

  /* шапка: логотип слева, телефон и бургер — справа */
  .top-in{gap:10px;padding:10px 13px;flex-wrap:wrap}
  .logo{order:1}
  .top .btn.sm{display:none}
  .top .social{display:none}
  .top-phone{font-size:13.5px;order:2;margin-left:auto}
  .burger{display:block;order:3;margin-left:0}
  .nav{display:none}
  .nav.open{display:flex;flex-direction:column;width:100%;order:4;gap:2px;
    padding:8px 0 0;border-top:1px solid #eee;margin-left:0}
  .nav.open a{padding:9px 4px;border-bottom:1px solid #f0f0f0}

  /* кнопки — на всю ширину, удобно тапать */
  .btns{flex-direction:column;align-items:stretch}
  .btns .btn{width:100%;text-align:center;padding:13px 16px}
  .hero-geo{font-size:11.5px}

  /* фото-плейсхолдеры компактнее */
  .ph{min-height:120px;padding:12px}
  .ph.tall{min-height:180px}
  .ph.wide{min-height:150px}
  .ph.gal{min-height:190px}
  .split-stretch .ph{height:auto;min-height:170px}

  /* формы и квиз */
  .form{max-width:none}
  .quiz{padding:14px}
  .opt{font-size:12.5px}

  /* карточки-ссылки категорий */
  .click{box-shadow:0 2px 0 #111}
  .click:hover{transform:none}

  .steps{gap:8px}
  .step{padding:13px 13px 13px 46px}
  .step::before{left:12px}

  .foot-in{grid-template-columns:1fr;gap:16px;text-align:center}
  .foot-in .social{justify-content:center}
  .foot-bottom{flex-direction:column;align-items:center;text-align:center;gap:6px}
  .cmt-fab{right:10px;bottom:10px;padding:10px 14px;font-size:12.5px}
  .cmt-btn{position:static;display:block;margin:12px 0 0;width:100%}
}
@media(max-width:380px){
  h1{font-size:22px}
  .logo{font-size:15.5px}
  .logo small{font-size:10px}
  section{padding:40px 12px 14px}
}
"""

# ────────────────────────────────────────────────────── ХЕЛПЕРЫ

_n = [0]


def reset():
    _n[0] = 0


def sec(label, inner, note):
    """Секция-карточка со сквозным номером, лейблом и аннотацией."""
    _n[0] += 1
    note_html = "" if CLIENT else '  <p class="note">%s</p>\n' % note
    return (
        '<section>\n'
        '  <div class="sec-label">%d &middot; %s</div>\n'
        '%s\n'
        '%s'
        '</section>\n' % (_n[0], label.upper(), inner, note_html)
    )


def ph(text, cls=""):
    return '<div class="ph %s">%s</div>' % (cls, text)


def btn(text, ghost=False, href="#"):
    return '<a class="btn%s" href="%s">%s</a>' % (" ghost" if ghost else "", href, text)


def btns(*items):
    return '<div class="btns">%s</div>' % "".join(items)


def card(title, body, extra=""):
    return '<div class="card"><h3>%s</h3><div class="small">%s</div>%s</div>' % (
        title, body, extra)


def click(badge, title, body, go="Смотреть &rarr;", href="#"):
    return ('<a class="click" href="%s"><span class="badge">%s</span>'
            '<h3>%s</h3><div class="small">%s</div><div class="go">%s</div></a>'
            % (href, badge, title, body, go))


def grid(cols, items):
    return '<div class="g g%d">%s</div>' % (cols, "".join(items))


def chips(*items):
    return '<div class="chips">%s</div>' % "".join(
        '<span class="chip">%s</span>' % i for i in items)


def steps(items):
    return '<div class="steps">%s</div>' % "".join(
        '<div class="step"><h3>%s</h3><div class="small">%s</div></div>' % (t, b)
        for t, b in items)


def table(headers, rows):
    h = "".join('<th>%s</th>' % x for x in headers)
    r = "".join('<tr>%s</tr>' % "".join('<td>%s</td>' % c for c in row) for row in rows)
    return '<div class="tbl"><table><tr>%s</tr>%s</table></div>' % (h, r)


def form(title, fields, button, consent=True):
    f = "".join('<div class="field">%s</div>' % x for x in fields)
    c = ('<p class="consent">Нажимая кнопку, вы соглашаетесь с политикой '
         'обработки персональных данных</p>') if consent else ""
    head = '<h3>%s</h3>' % title if title else ''
    return ('<div class="form">%s<div style="margin:%s0 0">%s</div>'
            '%s%s</div>' % (head, "11px " if title else "", f, btn(button), c))


S = lambda t: '<span class="stub">%s</span>' % t  # заглушка

_TG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9.78 18.65l.28-4.23'
       ' 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3'
       'l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71'
       'L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z"/></svg>')


def social(cls=""):
    return ('<div class="social %s">'
            '<a href="#" title="Telegram" aria-label="Telegram">%s</a>'
            '<a href="#" title="MAX" aria-label="MAX" class="ismax">MAX</a>'
            '</div>' % (cls, _TG))


def r(n):
    """1149000 -> 1 149 000 ₽"""
    return "{:,}".format(n).replace(",", "&nbsp;") + "&nbsp;&#8381;"


# ─── ПРАЙС с сайта клиента, лист «Дачные дома 03.2026г.»
# порядок значений: (каркас, Оптимальная, Стандарт, Зимняя дача)
SIZES = ["4x4", "4x5", "5x5", "4x6", "5x6", "6x6", "6x7", "6x8", "6x9"]
AREA = {"4x4": 16, "4x5": 20, "5x5": 25, "4x6": 24, "5x6": 30,
        "6x6": 36, "6x7": 42, "6x8": 48, "6x9": 54}

PRICES = {
    "Одноэтажный": {
        "4x4": (324000, 590000, 639000, 678000),
        "4x5": (378000, 692000, 749000, 796000),
        "5x5": (448000, 794000, 861000, 918000),
        "4x6": (434000, 763000, 826000, 876000),
        "5x6": (502000, 853000, 924000, 965000),
        "6x6": (592000, 969000, 1048000, 1114000),
        "6x7": (683000, 1149000, 1243000, 1316000),
        "6x8": (759000, 1161000, 1365000, 1443000),
        "6x9": (823000, 1359000, 1470000, 1553000),
    },
    "С двухскатной мансардой": {
        "4x4": (413000, 761000, 826000, 881000),
        "4x5": (498000, 921000, 997000, 1057000),
        "5x5": (591000, 1083000, 1172000, 1237000),
        "4x6": (567000, 1026000, 1110000, 1175000),
        "5x6": (663000, 1175000, 1274000, 1345000),
        "6x6": (762000, 1344000, 1454000, 1535000),
        "6x7": (879000, 1546000, 1672000, 1777000),
        "6x8": (971000, 1687000, 1825000, 1948000),
        "6x9": (1058000, 1834000, 1982000, 2134000),
    },
    "Полутораэтажный": {
        "4x4": (426000, 857000, 928000, 988000),
        "4x5": (500000, 1021000, 1107000, 1176000),
        "5x5": (593000, 1178000, 1274000, 1345000),
        "4x6": (562000, 1118000, 1209000, 1279000),
        "5x6": (663000, 1281000, 1386000, 1485000),
        "6x6": (780000, 1469000, 1593000, 1699000),
        "6x7": (890000, 1675000, 1813000, 1936000),
        "6x8": (986000, 1821000, 1969000, 2121000),
        "6x9": (1060000, 1994000, 2157000, 2320000),
    },
    "С четырёхскатной кровлей": {
        "4x4": (499000, 945000, 1019000, 1075000),
        "4x5": (567000, 999000, 1186000, 1258000),
        "5x5": (640000, 1245000, 1347000, 1425000),
        "4x6": (648000, 1212000, 1314000, 1386000),
        "5x6": (717000, 1355000, 1468000, 1571000),
        "6x6": (823000, 1538000, 1665000, 1775000),
        "6x7": (944000, 1765000, 1907000, 2035000),
        "6x8": (1042000, 1937000, 2096000, 2266000),
        "6x9": (1133000, 2101000, 2275000, 2335000),
    },
}


def price_table(kind):
    """Таблица цен по одному типу дома."""
    rows = []
    for s in SIZES:
        k, o, st, z = PRICES[kind][s]
        rows.append([
            "<b>%s</b> м" % s.replace("x", "&times;"),
            "%d м&sup2;" % AREA[s],
            r(k), r(o), r(st), r(z),
        ])
    return table(["Размер", "Площадь", "Каркас", "Оптимальная",
                  "Стандарт", "Зимняя дача"], rows)


TYPES = ["Одноэтажный", "С двухскатной мансардой",
         "Полутораэтажный", "С четырёхскатной кровлей"]
TYPE_SHORT = {
    "Одноэтажный": "одноэтажный",
    "С двухскатной мансардой": "с мансардой",
    "Полутораэтажный": "полутораэтажный",
    "С четырёхскатной кровлей": "с 4-скатной кровлей",
}
TYPE_SLUG = {
    "Одноэтажный": "odno",
    "С двухскатной мансардой": "mansarda",
    "Полутораэтажный": "poltora",
    "С четырёхскатной кровлей": "chetyre-skata",
}
TYPE_FLOORS = {
    "Одноэтажный": "1 этаж",
    "С двухскатной мансардой": "1 этаж + мансарда",
    "Полутораэтажный": "1,5 этажа",
    "С четырёхскатной кровлей": "1 этаж",
}


def type_min(kind):
    return min(PRICES[kind][s][1] for s in SIZES)


def dom_card(kind, size):
    k, o, st, z = PRICES[kind][size]
    return (
        '<div class="card">'
        + ph("Фото: дом " + size.replace("x", "&times;"), "sq")
        + '<h3 style="margin-top:10px">Дом %s %s</h3>' % (
            size.replace("x", "&times;"), TYPE_SHORT[kind])
        + '<div class="small">%d м&sup2; &middot; %s &middot; срок %s</div>' % (
            AREA[size], TYPE_FLOORS[kind], S("N дней"))
        + '<div class="price">от %s<small>под ключ, «Оптимальная»</small></div>' % r(o)
        + '<div class="btns"><a class="btn sm" href="dom.html">Подробнее</a></div>'
        + '</div>')


# ─── СОСТАВ КОМПЛЕКТАЦИЙ (со сканов прайса клиента)
KOMPL = [
    ("Стойки каркаса", "50&times;100 мм", "50&times;100 мм", "40&times;150 мм"),
    ("Утепление стен", "100 мм", "100 мм", "150 мм"),
    ("Наружная отделка", "вагонка 90&times;14 мм", "вагонка 90&times;14 мм",
     "имитация бруса 16&times;135 мм"),
    ("Утепление пола", "100 мм", "150 мм", "200 мм"),
    ("Утепление потолка", "100 мм", "150 мм", "200 мм"),
    ("Высота потолка 1 этажа", "от 2300 мм", "от 2450 мм", "от 2450 мм"),
    ("Высота потолка 2 этажа", "от 2150 мм", "от 2300 мм", "от 2300 мм"),
    ("Перегородки", "одна по короткой стороне", "сколько нужно", "сколько нужно"),
    ("Кровля", "профнастил оцинкованный", "профнастил окрашенный",
     "профнастил окрашенный"),
]

# что входит во все три комплектации одинаково
KOMPL_ALL = [
    "Согласование проекта дома &mdash; по типовому или по вашему планировочному решению",
    "Выезд прораба на участок: осмотр, подъездные пути, разметка места под дом",
    "Фундамент: буронабивные бетонные армированные сваи 2200&times;200&times;200 мм",
    "Обвязка фундамента брусом 150&times;150 мм или доской 50&times;150 мм",
    "Половая доска шпунтованная 35&times;135 мм, обработка антисептиком (Сенеж, Акватекс)",
    "Внутренняя отделка: евровагонка хвойных пород 14 мм, сорт АВ",
    "Лестница на мансарду с забежными ступенями (если мансарда есть)",
    "Окна пластиковые со стеклопакетом + москитные сетки, отливы, подоконники",
    "Дверь входная металлическая 860&times;2000 мм с контуром утепления",
    "Карнизы 270 мм, подшивка вагонкой, доборные элементы кровли",
    "Погрузка на складе компании и разгрузка на вашем участке",
    "Ответственность за сохранность материала до подписания акта приёма-передачи",
]

# ────────────────────────────────────────────────────── КАРКАС СТРАНИЦЫ

NAV = [
    ("Дома и цены", "index.html#doma"),
    ("Каталог", "catalog.html"),
    ("Комплектации", "index.html#komplektacii"),
    ("Наши объекты", "index.html#objekty"),
    ("Как строим", "index.html#kak"),
    ("Бани", "bani.html"),
    ("Отзывы", "index.html#otzyvy"),
]


def shell(title, body, crumb=""):
    nav = "".join('<a href="%s">%s</a>' % (h, t) for t, h in NAV)
    return """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<style>%s</style>
</head>
<body>

<header class="top">
  <div class="top-in">
    <div class="logo">Дом за 3 дня<small>каркасные дома и бани &middot; Казань</small></div>
    <button class="burger" onclick="document.querySelector('.nav').classList.toggle('open')">Меню</button>
    <nav class="nav">%s</nav>
    <div class="top-phone">+7 (843) 203-82-82</div>
    %s
    <a class="btn sm" href="index.html#quiz">Рассчитать стоимость</a>
  </div>
</header>

<main>
%s%s
</main>

<footer>
  <div class="foot-in">
    <div>
      <b>Дом за 3 дня</b>
      Каркасные дома и бани<br>Казань и область, выезд до 100 км<br>
      <span style="color:#999">12 лет на рынке &middot; 1 500+ построенных объектов</span>
    </div>
    <div>
      <b>Разделы</b>
      %s
    </div>
    <div>
      <b>Контакты</b>
      +7 (843) 203-82-82<br>+7 (843) 260-88-87<br>+7 (903) 305-62-44<br>
      г. Казань, ул. М. Миля, д. 59<br>
      andr0000@yandex.ru
      %s
    </div>
    <div>
      <b>Часы работы</b>
      Пн–Пт: с 8:00 до 17:00<br>Сб–Вс: с 8:00 до 15:00<br>
      <span style="color:#999">WhatsApp: +7 903 305-62-44</span>
    </div>
  </div>
  <div class="foot-bottom">
    <span>Политика обработки персональных данных</span>
    <span>Разработка сайта</span>
  </div>
</footer>

<script src="comments.js"></script>
</body>
</html>
""" % (title, CSS, nav, social(""), crumb, body,
       "".join('<a href="%s">%s</a>' % (h, t) for t, h in NAV),
       social("foot-social"))


# ══════════════════════════════════════════════════════ ГЛАВНАЯ

def page_index():
    reset()
    b = []

    # 1 ─ ПЕРВЫЙ ЭКРАН
    b.append(sec("Первый экран &mdash; оффер", """
  <div class="split">
    <div>
      <p class="hero-geo">Казань и область &middot; выезд до 100 км</p>
      <h1>Каркасные дома от 590 000 &#8381; с постройкой от 3 дней</h1>
      <p class="lead">Назовём точную стоимость по телефону без планировки
      и долгих расчётов. Цена фиксируется до начала строительства.</p>
      %s
      %s
    </div>
    <div>%s</div>
  </div>""" % (
        chips("12 лет на рынке", "1 500+ домов построено",
              "Фиксированная цена в договоре"),
        btns(btn("Рассчитать стоимость", href="#quiz"),
             btn("Посмотреть варианты домов", ghost=True, href="#doma")),
        ph("Фото: одноэтажный каркасный дом,<br>общий план с участком", "tall")),
        "Экран за три секунды отвечает: что строим, за сколько, как быстро. "
        "Цена в оффере отсекает нецелевой трафик и снимает «наверное, дорого». "
        "Подзаголовок держит один аргумент &mdash; цену сразу в разговоре, чего "
        "не делает ни один конкурент. Остальные преимущества идут ниже, "
        "по одному на блок. <b>Уточнить:</b> фото для первого экрана."))

    # 2 ─ ПРЕИМУЩЕСТВА
    b.append(sec("Преимущества компании", """
  <h2>Почему выбирают нас</h2>
  <p class="sub">Всё, что важно при выборе надёжной строительной компании.</p>
  %s""" % grid(3, [
        card("Цена известна сразу",
             "Назовите размеры дома и пожелания, и мы сразу скажем стоимость."),
        card("Цена фиксируется",
             "Стоимость прописывается в договоре и не меняется после согласования."),
        card("Собственные материалы",
             "У компании собственный магазин и склады стройматериалов."),
        card("Свои бригады",
             "Строим своими силами без привлечения подрядчиков."),
        card("12 лет работы",
             "Работаем с " + S("2014") + " года и построили более 1 500 домов."),
        card("Строим круглый год",
             "Каркасная технология позволяет заниматься строительством "
             "в любое время года."),
    ]),
        "Формулировки взяты из созвона и переупакованы на язык выгоды клиента. "
        "Блок закрывает базовое «а почему вы?» до того, как человек начнёт сравнивать. "
        "<b>Уточнить:</b> год основания компании."))

    # 3 ─ КВИЗ
    b.append(sec("Квиз &mdash; расчёт стоимости", """
  <div id="quiz"></div>
  <h2>Узнайте цену своего дома</h2>
  <p class="sub">Ответьте на 5 вопросов &mdash; и мы назовём цену с учётом
  размера, назначения и фундамента. Это займёт минуту.</p>
  <div class="quiz">
    <div class="qstep"><div class="qnum">Шаг 1 из 5</div>
      <div class="qq">Для чего нужен дом?</div>
      <div class="opts"><span class="opt">Дача, сезонное проживание</span>
      <span class="opt">Для постоянного проживания</span>
      <span class="opt">Баня</span></div></div>
    <div class="qstep"><div class="qnum">Шаг 2 из 5</div>
      <div class="qq">Какой размер планируете?</div>
      <div class="opts"><span class="opt">3&times;4</span><span class="opt">4&times;4</span>
      <span class="opt">4&times;6</span><span class="opt">6&times;6</span>
      <span class="opt">6&times;8</span><span class="opt">Свой размер</span></div></div>
    <div class="qstep"><div class="qnum">Шаг 3 из 5</div>
      <div class="qq">Этажность</div>
      <div class="opts"><span class="opt">Одноэтажный</span>
      <span class="opt">С мансардой</span><span class="opt">Полутораэтажный</span>
      <span class="opt">Пока не решил</span></div></div>
    <div class="qstep"><div class="qnum">Шаг 4 из 5</div>
      <div class="qq">Нужен ли фундамент?</div>
      <div class="opts"><span class="opt">Нужен</span>
      <span class="opt">Уже есть</span><span class="opt">Не знаю, подскажите</span></div></div>
    <div class="qstep"><div class="qnum">Шаг 5 из 5</div>
      <div class="qq">Когда планируете строить?</div>
      <div class="opts"><span class="opt">В этом сезоне</span>
      <span class="opt">В следующем</span><span class="opt">Пока просто узнаю цену</span></div></div>
    <div class="qstep"><div class="qnum">Последний шаг</div>
      <div class="qq">Куда отправить расчёт?</div>
      <div class="field">Ваше имя</div>
      <div class="field">Телефон</div>
      %s
      <div class="gift"><b>Бонус за расчёт:</b> %s</div>
    </div>
  </div>""" % (btn("Получить расчёт"),
               S("подарок / скидка — придумать вместе с клиентом. "
                 "У конкурентов: дверь в подарок, окна, скидка 3%, "
                 "заморозка цены на 6 месяцев")),
        "Квиз стоит третьим блоком: по кейсам Директа он собирает больше заявок "
        "и дешевле лида, чем обычная форма. Человек отвечает по шагам и "
        "оставляет телефон вместе с параметрами дома, а не пустой номер. "
        "<b>Уточнить:</b> что даём в подарок и от чего зависит итоговая цена."))

    # 4 ─ КАТАЛОГ
    b.append(sec("Каталог домов", """
  <div id="doma"></div>
  <h2>Каталог домов</h2>
  %s
  <div class="btns">%s%s</div>""" % (
        grid(2, [
            click("Клик &middot; каталог",
                  "Одноэтажные",
                  "9 размеров от 3&times;4 до 6&times;9<br>"
                  "<span class='price'>от " + r(type_min("Одноэтажный")) + "</span>",
                  href="catalog.html#odno"),
            click("Клик &middot; каталог",
                  "С мансардой",
                  "Спальни на втором уровне, вдвое больше площади<br>"
                  "<span class='price'>от "
                  + r(type_min("С двухскатной мансардой")) + "</span>",
                  href="catalog.html#mansarda"),
            click("Клик &middot; каталог",
                  "Полутораэтажные",
                  "Для круглогодичного проживания семьёй<br>"
                  "<span class='price'>от "
                  + r(type_min("Полутораэтажный")) + "</span>",
                  href="catalog.html#poltora"),
            click("Клик &middot; каталог",
                  "С четырёхскатной кровлей",
                  "Вальмовая крыша, аккуратный вид<br>"
                  "<span class='price'>от "
                  + r(type_min("С четырёхскатной кровлей")) + "</span>",
                  href="catalog.html#chetyre-skata"),
        ]),
        btn("Открыть каталог", href="catalog.html"),
        btn("Построить по своим размерам", ghost=True, href="#quiz")),
        "Классический каталог: на лендинге четыре категории для быстрого выбора, "
        "по клику &mdash; полный список из 36 проектов с ценами и таблицами прайса. "
        "Карточка проекта ведёт на страницу дома. "
        "<b>Нужно от клиента:</b> фото по каждому типу и подтверждение прайса 03.2026."))

    # 5 ─ КОМПЛЕКТАЦИИ
    b.append(sec("Комплектации", """
  <div id="komplektacii"></div>
  <h2>Выберите комплектацию под свой дом</h2>
  <p class="sub">От летней дачи до тёплого дома для круглогодичного проживания.
  Отличие комплектаций в утеплении, отделке и уровне комфорта.</p>
  %s
  <h3 style="margin:22px 0 8px">Чем именно отличаются</h3>
  %s""" % (
        grid(3, [
            card("Оптимальная",
                 "Для летнего отдыха и выходных на даче.<br><br>"
                 "Стены, пол и потолок утеплены на 100 мм. "
                 "Снаружи вагонка, кровля из оцинкованного профнастила.",
                 '<div class="price">от ' + r(590000) +
                 '<small>дом 4×4 одноэтажный</small></div>'),
            card("Стандарт",
                 "Для сезонного проживания. Теплее и потолки выше.<br><br>"
                 "Пол и потолок утеплены на 150 мм, кровля &mdash; окрашенный "
                 "профнастил, перегородок сколько нужно.",
                 '<div class="price">от ' + r(639000) +
                 '<small>дом 4×4 одноэтажный</small></div>'),
            card("Зимняя дача",
                 "Тёплый дом, в котором можно жить зимой.<br><br>"
                 "Стойки каркаса 40&times;150 мм, стены утеплены на 150 мм, "
                 "пол и потолок &mdash; на 200 мм. Снаружи имитация бруса.",
                 '<div class="price">от ' + r(678000) +
                 '<small>дом 4×4 одноэтажный</small></div>'),
        ]),
        table(["Параметр", "Оптимальная", "Стандарт", "Зимняя дача"],
              [[a, b, c, d] for a, b, c, d in KOMPL])),
        "Состав взят с реальных сканов прайса на старом сайте &mdash; там он лежит "
        "картинками, я его расшифровал. Сравнительная таблица работает лучше трёх "
        "отдельных списков: разница видна за секунду, и человек обычно берёт средний "
        "вариант. Полный состав каждой комплектации раскроется на странице дома. "
        "<b>Уточнить:</b> что считается отдельно (доставка, терраса, септик, электрика) "
        "и по каким ценам."))

    # 6 ─ ПОЧЕМУ ТАКАЯ ЦЕНА
    b.append(sec("Почему такая цена", """
  <h2>Почему наши дома стоят дешевле</h2>
  <p class="sub">Мы контролируем строительство сами, закупаем материалы напрямую
  и не переплачиваем посредникам. Поэтому можем держать доступную цену
  без лишних наценок.</p>
  %s""" % grid(2, [
        card("Закупаем материалы напрямую",
             "Получаем выгодные цены от поставщиков благодаря большим "
             "объёмам закупок."),
        card("Не платим посредникам",
             "Все основные процессы контролируем внутри компании."),
        card("Большой объём строительства",
             "За сезон можем построить до 20 домов, поэтому можем работать "
             "с большими объёмами материалов."),
        card("Оптимизированная технология",
             "Строим типовые одноэтажные и полутораэтажные дома "
             "без лишних усложнений."),
    ]),
        "Такого блока почти нет у конкурентов. Он снимает недоверие "
        "«слишком дёшево, значит подвох». Текст карточек прислал клиент."))

    # 7 ─ СРОКИ
    b.append(sec("Сроки строительства", """
  <h2>За сколько построим дом</h2>
  %s
  <p class="small" style="margin-top:12px">Срок считается с момента завоза
  материалов на участок. Свайный фундамент входит в комплектацию и делается
  в эти же сроки.</p>""" % (
        table(["Размер дома", "Площадь", "Срок строительства"], [
            ["3&times;4, 4&times;4", "12&ndash;16 м&sup2;", "<b>3 дня</b>"],
            ["4&times;6, 5&times;6", "24&ndash;30 м&sup2;", S("N дней")],
            ["6&times;6, 6&times;8", "36&ndash;48 м&sup2;", S("N дней")],
            ["6&times;6 и больше с мансардой", "от 54 м&sup2;", S("15–20 дней")],
        ])
        ),
        "Срок &mdash; второй аргумент после цены сразу. Конкуренты в Москве и "
        "Питере пишут «60&ndash;70 дней», у вас маленький дом готов за три. "
        "Таблица делит по размерам, чтобы клиент не ждал трёх дней от дома 6&times;9. "
        "<b>Уточнить:</b> сроки по каждому размеру."))

    # 8 ─ ОБЪЕКТЫ
    b.append(sec("Реализованные объекты", """
  <div id="objekty"></div>
  <h2>Дома, которые мы построили</h2>
  %s""" % (
        grid(3, [
            '<div class="card">%s<h3 style="margin-top:10px">Дом %s</h3>'
            '<div class="small">Комплектация: %s &middot; Срок: %s<br>%s</div>'
            '<div class="price">%s</div></div>' % (
                ph("Фото объекта " + str(i), "sq"), S("6×6"), S("Стандарт"),
                S("N дней"), S("Казань, N-й район"), S("N ₽"))
            for i in range(1, 7)
        ])),
        "В стройке доверие держится на фото готовых домов. Показываем сетку "
        "объектов с размером, комплектацией, сроком и ценой. "
        "<b>Нужно от клиента:</b> фото объектов и параметры к каждому."))

    # 9 ─ КАК ПРОХОДИТ СТРОИТЕЛЬСТВО
    b.append(sec("Как проходит строительство", """
  <div id="kak"></div>
  <h2>Как проходит строительство</h2>
  <p class="sub">Пять понятных шагов от первого разговора до готового дома.
  Без долгого ожидания расчёта и лишней бюрократии.</p>
  %s
  <div class="hl"><b>Как платить:</b> %s</div>""" % (
        steps([
            ("Заявка или звонок",
             "Рассказываете, какой дом хотите, называете размеры и пожелания. "
             "Сразу обсуждаем стоимость и подходящую комплектацию."),
            ("Расчёт и выбор комплектации",
             "Подбираем комплектацию под ваши задачи и бюджет. Обсуждаем "
             "планировку, материалы и всё, что будет входить в стоимость."),
            ("Договор и дата строительства",
             "Фиксируем стоимость и условия в договоре. Согласовываем дату "
             "начала строительства и готовим всё необходимое."),
            ("Строительство на участке",
             "Доставляем материалы и собираем дом на вашем участке. "
             "Показываем ход работ, чтобы вы могли контролировать "
             "строительство."),
            ("Приёмка и документы",
             "Осматриваете готовый дом, подписываете акт приёмки "
             "и получаете все необходимые документы."),
        ]),
        S("предоплата / поэтапная оплата — уточнить у клиента. У сильных конкурентов "
          "это «0% предоплаты, 70% при доставке, 30% при приёмке» — сильный аргумент, "
          "если вы можете так же")),
        "Блок отвечает на «как всё пойдёт и когда платить». Текст шагов прислал "
        "клиент. Условия оплаты стоит усилить: сильные конкуренты выносят "
        "«без предоплаты» на первый экран. <b>Уточнить:</b> схему оплаты."))

    # 10 ─ ГАРАНТИИ И ДОГОВОР
    b.append(sec("Гарантии и договор", """
  <h2>Чем вы защищены</h2>
  <p class="sub">В стройке вы отдаёте деньги вперёд незнакомой компании.
  Показываем, что стоит за нашими обещаниями.</p>
  %s""" % grid(3, [
        card("Всё зафиксировано в договоре",
             "Сумма, состав работ, сроки и ответственность сторон. "
             "Договор подписываем до завоза материалов."),
        card("Гарантия 5 лет",
             "Прописана в договоре. Распространяется на конструктив дома: "
             "каркас, кровлю и качество работ."),
        card("Всё остаётся у вас на руках",
             "Договор, смета, акт приёма-передачи и гарантийный талон &mdash; "
             "полный комплект документов."),
        card("Приёмка по акту",
             "Акт подписываем, когда у вас нет замечаний. Есть замечания &mdash; "
             "устраняем и показываем снова."),
        card("Материал под нашей ответственностью",
             "За сохранность материалов на участке до подписания акта "
             "отвечает компания, а не вы."),
        card("Если возникла проблема",
             "Свяжитесь с нами. Разберёмся в ситуации и поможем решить "
             "вопрос по гарантии."),
    ]),
        "У сильных конкурентов такой блок содержит 5&ndash;6 пунктов: эскроу, "
        "штраф за просрочку, технадзор. Без него низкая цена читается как риск. "
        "Пункты не повторяют блоки про цену и преимущества &mdash; тут только то, "
        "что закреплено на бумаге. "
        "<b>Уточнить:</b> порядок действий по гарантийному случаю."))

    # 11 ─ СВОЯ ПЛАНИРОВКА
    b.append(sec("Со своей планировкой", """
  <div class="split split-stretch">
    <div>
      <h2>Проект не нужен, достаточно вашего эскиза</h2>
      <p class="lead">Готовый проект не нужен. Покажите, каким вы хотите видеть
      свой дом, а мы поможем подобрать планировку и подготовим её
      к строительству.</p>
      <ul>
        <li>Не нужно отдельно оплачивать проектирование</li>
        <li>Не нужно ждать готовый проект</li>
        <li>Планировку можно обсудить с нами</li>
        <li>Подскажем, если что-то лучше изменить</li>
      </ul>
      %s
    </div>
    <div>%s</div>
  </div>""" % (
        btns(btn("Обсудить проект", href="#quiz")),
        ph("Фото: рукописный чертёж клиента<br>рядом с готовым домом по нему", "wide")),
        "Закрывает возражение с созвона: у конкурентов «пришлите проект», "
        "и человек уходит. Вы строите по рисунку от руки, но на сайте "
        "этого нет. Блок выносит вашу особенность в аргумент."))

    # 12 ─ ОТЗЫВЫ
    b.append(sec("Отзывы", """
  <div id="otzyvy"></div>
  <h2>Что говорят клиенты</h2>
  <div class="rating"><b>%s</b><span class="small">средняя оценка на основе
  %s отзывов в Яндекс Картах и 2ГИС</span></div>
  %s""" % (
        S("4,9"), S("N"),
        grid(3, [
            '<div class="card"><div class="small"><b>%s</b></div>'
            '<p style="margin-top:9px">%s</p><div class="small">%s</div></div>' % (n, t, m)
            for n, t, m in [
                ("Ирина",
                 "Строили дом 6&times;6 на даче. Цену назвали сразу по телефону, "
                 "по факту всё совпало с договором, доплат не было. Собрали "
                 "за неделю, бригада аккуратная, за собой убрали.",
                 "Дом 6&times;6, лето 2025"),
                ("Алексей",
                 "Обзвонил несколько компаний &mdash; везде «пришлите планировку, "
                 "потом посчитаем». Здесь стоимость сказали в первом же разговоре. "
                 "Построили дом 5&times;6 под ключ, заехали к осени.",
                 "Дом 5&times;6, сентябрь 2025"),
                ("Марат",
                 "Ставили баню 3&times;4. По срокам не сдвинулись, по деньгам "
                 "как договаривались. Пару мелочей по отделке поправили без "
                 "вопросов уже после приёмки.",
                 "Баня 3&times;4, весна 2025"),
            ]
        ])),
        "Тексты отзывов написал в стиле реальных отзывов о каркасном "
        "строительстве &mdash; клиент заменит на настоящие из карт. Кнопки "
        "на профили в Яндекс Картах и 2ГИС добавим, когда будут ссылки. "
        "<b>Нужно от клиента:</b> ссылки на профили и оценка/число отзывов."))

    # 13 ─ БАНИ
    b.append(sec("Бани", """
  <h2>Строим и бани</h2>
  <p class="sub">Каркасные бани под ключ по вашим размерам и пожеланиям.</p>
  %s
  <div class="btns">%s</div>""" % (
        grid(3, [
            '<div class="card">%s<h3 style="margin-top:10px">Баня %s</h3>'
            '<div class="small">%s</div><div class="price">%s</div></div>' % (
                ph("Фото бани", "sq"), S("3×4"), S("парная, мойка, комната отдыха"),
                S("от N ₽"))
            for _ in range(3)
        ]),
        btn("Все бани и цены", ghost=True, href="bani.html")),
        "Три карточки, как договорились на созвоне: бани оставляем, "
        "акцент сайта на домах. Подробности &mdash; на отдельной странице."))

    # 14 ─ FAQ
    b.append(sec("Вопросы и ответы", """
  <h2>Частые вопросы</h2>
  %s""" % grid(2, [
        card("Нужен ли готовый проект дома?",
             "Нет. Можно прийти со своим эскизом или наброском от руки. "
             "Обсудим планировку, размеры и ваши пожелания и подготовим "
             "вариант для строительства."),
        card("Можно ли построить дом по своему проекту?",
             "Да. Если у вас уже есть проект или собственная планировка, "
             "мы можем обсудить её и построить дом по вашим требованиям."),
        card("Сколько стоит строительство дома?",
             "Стоимость зависит от размеров дома, планировки и выбранной "
             "комплектации. Точную цену можно узнать уже во время первого "
             "разговора, без долгого ожидания расчёта."),
        card("Может ли цена измениться после заключения договора?",
             "Нет. После согласования стоимости она фиксируется в договоре. "
             "Все необходимые работы и материалы заранее учитываются "
             "в расчёте."),
        card("Сколько времени занимает строительство?",
             "Небольшие дачные дома можем построить от 3 дней. Более крупные "
             "дома строятся дольше в зависимости от размера и комплектации."),
        card("Можно ли строить дом зимой?",
             "Да. Строительство каркасных домов возможно круглый год."),
        card("Из чего строите дома?",
             "Мы используем собственные материалы и работаем своими "
             "бригадами. Материалы закупаем напрямую, а строительство "
             "и логистику контролируем самостоятельно."),
        card("Подойдёт ли каркасный дом для постоянного проживания?",
             "Да. Мы строим не только дачные дома. При выборе подходящей "
             "комплектации каркасный дом можно использовать для постоянного "
             "проживания."),
        card("Как проходит строительство?",
             "Сначала определяем, какой дом вам нужен, согласовываем размеры "
             "и комплектацию, рассчитываем стоимость и фиксируем её "
             "в договоре. После этого организуем доставку материалов "
             "и приступаем к строительству."),
        card("Какую гарантию вы даёте на дом?",
             "Гарантия прописывается в договоре. Все условия "
             "и ответственность сторон фиксируются до начала строительства."),
    ]),
        "Текст FAQ клиент прислал целиком. Часть ответов перекликается с блоками "
        "выше (сроки, гарантия, из чего строим, для ПМЖ, как проходит) &mdash; "
        "это ок для FAQ, люди читают его выборочно. "
        "<b>Уточнить:</b> согласовать формулировку про гарантию (сейчас без срока)."))

    # 15 ─ ФИНАЛЬНЫЙ CTA
    b.append(sec("Финальный призыв", """
  <div class="split split-stretch">
    <div>
      <h2>Постройте свой дом<br>по понятной и фиксированной цене</h2>
      <p class="lead">Расскажите, какой дом вы хотите. Рассчитаем стоимость
      по вашим размерам и сразу скажем, сколько будет стоить строительство
      без долгих расчётов и скрытых доплат.</p>
      %s
    </div>
    <div>%s</div>
  </div>""" % (
        form("", ["Ваше имя", "Телефон"], "Рассчитать стоимость"),
        ph("Фото: готовый дом компании,<br>общий план с участком", "wide")),
        "Форма для тех, кто дочитал, но не прошёл квиз: два поля, остальное "
        "&mdash; в разговоре. Контакты и карта &mdash; в подвале."))

    return shell("Прототип — Дом за 3 дня", "".join(b))


# ══════════════════════════════════════════════════════ СТРАНИЦА ДОМА

def page_dom():
    reset()
    b = []

    b.append(sec("Шапка карточки дома", """
  <div class="split">
    <div>%s<div class="g g4" style="margin-top:9px">%s%s%s%s</div></div>
    <div>
      <h1>Дом 6&times;6</h1>
      <p class="lead">36 м&sup2; &middot; одноэтажный &middot; срок %s<br>
      Две комнаты и кухня &mdash; самый частый выбор семей.</p>
      <div class="price" style="font-size:27px">%s<small>цена зафиксируется в договоре</small></div>
      %s
      %s
    </div>
  </div>""" % (
        ph("Главное фото дома", "tall"),
        ph("Фото 2", "sq"), ph("Фото 3", "sq"), ph("Фото 4", "sq"), ph("Фото 5", "sq"),
        S("N дней"), "от " + r(969000) + "",
        chips("Гарантия 5 лет", "Фиксированная цена", "Свои бригады"),
        btns(btn("Узнать точную цену", href="index.html#quiz"),
             btn("Заказать звонок", ghost=True))),
        "Страница, куда проваливается карточка с главной. Задача та же, что "
        "и у первого экрана: цена, срок, размер &mdash; сразу и крупно. "
        "<b>Нужно от клиента:</b> по 4&ndash;5 фото на каждый ходовой размер."))

    b.append(sec("Планировка", """
  <h2>Планировка</h2>
  <p class="sub">Показываем базовую планировку и сразу говорим, что её можно менять.</p>
  <div class="split">
    <div>%s</div>
    <div>
      <h3>Что можно изменить</h3>
      <ul>
        <li>Расположение и количество перегородок</li>
        <li>Количество и размер окон</li>
        <li>Расположение двери и крыльца</li>
        <li>Добавить террасу или веранду</li>
      </ul>
      <div class="hl">Или постройте по своей планировке &mdash; достаточно чертежа
      от руки. Цену назовём в тот же день.</div>
      %s
    </div>
  </div>""" % (
        ph("Схема планировки 6&times;6:<br>комнаты, кухня, вход, окна", "wide"),
        btns(btn("Прислать свой чертёж", ghost=True, href="index.html#quiz"))),
        "Планировка &mdash; то, ради чего человек и открывает карточку дома. "
        "Здесь же гасим страх «а если мне нужно по-другому»: сразу показываем "
        "гибкость и повторяем сильный аргумент про чертёж от руки. "
        "<b>Нужно:</b> схемы планировок хотя бы на ходовые размеры."))

    b.append(sec("Комплектации для этого дома", """
  <h2>Сколько стоит в разных комплектациях</h2>
  <p class="sub">Одна и та же коробка, разное утепление и отделка.</p>
  %s
  <p class="small" style="margin-top:11px">Отдельно считаются: %s</p>""" % (
        table(["Комплектация", "Для чего", "Стены", "Пол и потолок", "Цена"], [
            ["Оптимальная", "Лето, выходные на даче", "100 мм", "100 мм", r(969000)],
            ["Стандарт", "Сезонное проживание", "100 мм", "150 мм", r(1048000)],
            ["Зимняя дача", "Круглый год, морозы", "150 мм", "200 мм", r(1114000)],
        ]),
        S("доставка, терраса, септик, электрика")),
        "Сравнительная таблица работает лучше трёх отдельных блоков: человек "
        "видит разницу в одну секунду и обычно берёт средний вариант. "
        "<b>Нужно от клиента:</b> прайс текстом."))

    b.append(sec("Похожие дома", """
  <h2>Другие размеры</h2>
  %s""" % grid(3, [
        click("Клик &middot; страница дома", "Дом 4&times;6",
              "24 м&sup2; &middot; от " + r(763000), href="dom.html"),
        click("Клик &middot; страница дома", "Дом 6&times;8",
              "48 м&sup2; &middot; от " + r(1161000), href="dom.html"),
        click("Клик &middot; страница дома", "Дом 6&times;6 с мансардой",
              "36 м&sup2; + мансарда &middot; от " + r(1344000), href="dom.html"),
    ]),
        "Перелинковка: если этот размер не подошёл, человек не уходит с сайта, "
        "а идёт смотреть соседний."))

    b.append(sec("Заявка со страницы дома", """
  <div class="split">
    <div>
      <h2>Узнайте точную цену дома 6&times;6</h2>
      <p class="lead">Назовём стоимость с учётом комплектации, фундамента и доставки
      до вашего участка &mdash; в первую минуту разговора.</p>
    </div>
    <div>%s</div>
  </div>""" % form("Оставьте заявку", ["Ваше имя", "Телефон"], "Узнать цену"),
        "Форма на каждой странице дома &mdash; иначе трафик, который пришёл "
        "по запросу «каркасный дом 6х6 Казань», упрётся в тупик."))

    return shell("Прототип — страница дома",
                 "".join(b),
                 '<p class="crumb"><a href="index.html">Главная</a> &rarr; '
                 '<a href="catalog.html">Каталог</a> &rarr; Дом 6&times;6</p>')


# ══════════════════════════════════════════════════════ СТРАНИЦА БАНЬ

def page_bani():
    reset()
    b = []

    b.append(sec("Первый экран — бани", """
  <div class="split">
    <div>
      <h1>Каркасные бани под ключ по фиксированной цене</h1>
      <p class="lead">Рассчитаем стоимость по вашим размерам и сразу назовём
      точную цену. После согласования зафиксируем её в договоре
      без неожиданных доплат.</p>
      %s
      %s
    </div>
    <div>%s</div>
  </div>""" % (
        chips("Срок " + S("N") + " дней", "Свои материалы", "Гарантия 5 лет"),
        btns(btn("Рассчитать стоимость", href="index.html#quiz")),
        ph("Фото: готовая баня компании,<br>общий план", "tall")),
        "Отдельная страница нужна, чтобы не раздувать главную, но при этом ловить "
        "поисковый и рекламный трафик по баням. Структура повторяет главную "
        "в сжатом виде. <b>Нужно от клиента:</b> фото бань и цены."))

    b.append(sec("Размеры и цены", """
  <h2>Размеры и цены</h2>
  <p class="sub">Сравнение размеров, состава, сроков и стоимости.</p>
  %s""" % table(["Размер", "Состав", "Срок", "Цена"], [
        ["3&times;4", "Парная, моечная и комната отдыха", S("N дней"), S("от N ₽")],
        ["3&times;5", "Парная, моечная, комната отдыха с окном и небольшой тамбур",
         S("N дней"), S("от N ₽")],
        ["4&times;6", "Парная, моечная, просторная комната отдыха и крытая терраса",
         S("N дней"), S("от N ₽")],
    ]),
        "Таблицей, а не карточками: бань немного, и человеку важно быстро "
        "сравнить размер и цену. Состав написал от себя &mdash; клиент поправит. "
        "<b>Нужно от клиента:</b> сроки и цены по каждому размеру."))

    b.append(sec("Что входит в стоимость", """
  <h2>Что входит в стоимость</h2>
  %s
  <p class="small" style="margin-top:11px">Отдельно считаются: фундамент под
  тяжёлую печь, доставка дальше 100 км, купель, подключение воды и слива,
  электрика.</p>""" % (
        grid(3, [
            card("Каркас и кровля",
                 "Каркас из строганой доски естественной влажности, обвязка "
                 "на сваях, стропильная система и кровля из профнастила "
                 "с карнизами и подшивкой."),
            card("Внутренняя отделка",
                 "Парная обшита липовой вагонкой, моечная и комната отдыха "
                 "&mdash; хвойной. Полки в парной из липы, в моечной пол "
                 "с уклоном к трапу."),
            card("Печь и дымоход",
                 "Дровяная банная печь с баком для воды, дымоход с проходом "
                 "через кровлю и разделкой, защитный экран у печи."),
        ])),
        "Состав карточек написал от себя по типовой каркасной бане &mdash; "
        "клиент даст правки. Принцип тот же, что в комплектациях домов: "
        "явно разделяем «входит» и «считается отдельно»."))

    b.append(sec("Реальные бани", """
  <h2>Реальные бани</h2>
  <p class="sub">Фотографии готовых объектов.</p>
  %s""" % grid(3, [
        '<div class="card"><div class="gallery">'
        '<a class="arw l" href="#" aria-label="Предыдущее фото">&lsaquo;</a>'
        '%s'
        '<a class="arw r" href="#" aria-label="Следующее фото">&rsaquo;</a>'
        '</div><h3 style="margin-top:10px">Баня %s</h3>'
        '<div class="small">%s &middot; срок %s</div>'
        '<div class="price">%s</div></div>' % (
            ph("Фото бани " + str(i), "gal"), sz, comp, S("N дней"), S("от N ₽"))
        for i, (sz, comp) in enumerate([
            ("3&times;4", "Парная, моечная, комната отдыха"),
            ("3&times;5", "С тамбуром и окном в комнате отдыха"),
            ("4&times;6", "С крытой террасой под общей крышей"),
        ], 1)
    ]),
        "Блок доверия: показываем реально построенные бани. Подписи написал "
        "от себя. <b>Нужно от клиента:</b> фото бань и цены."))

    b.append(sec("Как проходит строительство", """
  <h2>Как проходит строительство</h2>
  <p class="sub">4 понятных шага.</p>
  %s""" % steps([
        ("Заявка или звонок",
         "Расскажете, какая баня нужна: размер, что внутри. Сразу назовём "
         "стоимость и подходящий вариант."),
        ("Договор и дата",
         "Фиксируем цену и состав работ в договоре. Согласовываем дату "
         "начала строительства."),
        ("Строительство на участке",
         "Привозим материалы и собираем баню на вашем участке. "
         "Показываем ход работ."),
        ("Приёмка и документы",
         "Осматриваете готовую баню, подписываете акт приёмки, "
         "получаете документы и гарантию."),
    ]),
        "Короткая версия процесса с главной: для бани четыре шага вместо пяти."))

    b.append(sec("Финальная заявка", """
  <div class="split">
    <div>
      <h2>Узнайте точную стоимость своей бани</h2>
      <p class="lead">Назовите размер и что нужно внутри &mdash; рассчитаем
      стоимость и назовём точную цену в разговоре.</p>
    </div>
    <div>%s</div>
  </div>""" % form("", ["Ваше имя", "Телефон"], "Рассчитать стоимость"),
        "Замыкающая точка захвата на странице бань."))

    return shell("Прототип — бани", "".join(b),
                 '<p class="crumb"><a href="index.html">Главная</a> &rarr; Бани</p>')


# ══════════════════════════════════════════════════════ СБОРКА

def page_catalog():
    reset()
    b = []

    b.append(sec("Каталог — шапка", """
  <h1>Каталог каркасных домов</h1>
  <p class="lead">36 проектов: четыре типа домов и девять размеров, каждый &mdash;
  в трёх комплектациях. Цена указана за каждый проект. Актуально на %s.</p>
  %s
  %s""" % (
        S("03.2026 — подтвердить у клиента"),
        chips("Фундамент в цене", "Цена в договоре не меняется",
              "Строим по своей планировке"),
        btns(btn("Рассчитать свой дом", href="index.html#quiz"),
             btn("Сравнить комплектации", ghost=True,
                 href="index.html#komplektacii"))),
        "Отдельная страница каталога: ловит поиск по запросам "
        "«каркасный дом Казань цена», держит все проекты и прайс в одном месте, "
        "не растягивает лендинг. Ссылка на неё &mdash; в меню и в блоке «Каталог» "
        "на главной."))

    # ── КАТАЛОГ: фильтры слева, карточки справа ──────────────────
    fnav = "".join(
        '<a href="#%s"%s>%s <span style="opacity:.6">&middot; от %s</span></a>' % (
            TYPE_SLUG[k], ' class="act"' if i == 0 else '', k, r(type_min(k)))
        for i, k in enumerate(TYPES))

    filters = """
  <aside class="filters">
    <div class="fg">
      <h4>Тип дома</h4>
      <nav class="fnav">%s</nav>
    </div>
    <div class="fg desk">
      <h4>Этажность</h4>
      <label class="fopt on">Одноэтажный</label>
      <label class="fopt">С мансардой</label>
      <label class="fopt">Полутора этажа</label>
    </div>
    <div class="fg desk">
      <h4>Площадь, м&sup2;</h4>
      <div class="slider"><span></span><span></span></div>
      <div class="srow"><b>12</b><b>54</b></div>
    </div>
    <div class="fg desk">
      <h4>Цена, &#8381;</h4>
      <div class="slider"><span></span><span></span></div>
      <div class="srow"><b>590 000</b><b>2 335 000</b></div>
    </div>
    <div class="fg desk">
      <h4>Комплектация</h4>
      <label class="fopt rad on">Оптимальная</label>
      <label class="fopt rad">Стандарт</label>
      <label class="fopt rad">Зимняя дача</label>
    </div>
    <div class="fg desk">
      <div class="fbtns">%s%s</div>
    </div>
    <div class="filters-m">На телефоне фильтры сворачиваются в кнопку
    «Параметры», разделы выбираются лентой сверху.</div>
  </aside>""" % (
        fnav,
        btn("Показать 36 домов", href="#odno"),
        btn("Сбросить", ghost=True, href="#odno"))

    types_html = ""
    for kind in TYPES:
        cards = grid(3, [dom_card(kind, sz) for sz in SIZES])
        types_html += """
    <div class="ctype" id="%s">
      <h3>%s</h3>
      <p class="pnote">9 размеров, от %s. В карточке цена за «Оптимальную»,
      расклад по трём комплектациям &mdash; в таблице под сеткой.</p>
      %s
      <h4 style="font-size:13px;color:#888;margin:18px 0 8px;text-transform:uppercase;letter-spacing:.05em">Цены по комплектациям</h4>
      %s
    </div>""" % (TYPE_SLUG[kind], kind, r(type_min(kind)), cards, price_table(kind))

    b.append(sec("Каталог домов", """
  <div class="catwrap">
    %s
    <div class="catmain">
      <div class="catbar">
        <span class="cnt">Найдено 36 проектов</span>
        <span class="sort">Сортировка: сначала дешевле &#9662;</span>
      </div>
      %s
    </div>
  </div>""" % (filters, types_html),
        "Стандартная раскладка каталога: слева панель фильтров (тип дома, "
        "этажность, площадь, цена, комплектация), справа &mdash; сетка карточек "
        "по разделам. Клик по типу в панели прокручивает к нужному разделу. "
        "Фильтры на прототипе &mdash; заглушки: рабочая логика делается в вёрстке. "
        "<b>Нужно:</b> фото домов по каждому типу, подтверждение прайса 03.2026."))

    b.append(sec("Каталог — что не входит в цену", """
  <h2>Что считается отдельно</h2>
  <p class="sub">Это называют сразу вместе с ценой дома, а не по ходу стройки.</p>
  %s
  <div class="hl">Фундамент (буронабивные сваи 2200&times;200&times;200 мм)
  <b>входит</b> в цену всех трёх комплектаций.</div>""" % grid(2, [
        card("Доставка", S("цена за км сверх N км — уточнить")),
        card("Терраса, веранда, крыльцо", S("цены — уточнить")),
        card("Септик и водоснабжение", S("делаете или нет, цены — уточнить")),
        card("Электрика и отопление", S("делаете или нет, цены — уточнить")),
    ]),
        "Список «что сверху» работает на аргумент про цену сразу: вы называете "
        "полную сумму, а не заманиваете низкой. "
        "<b>Нужно от клиента:</b> перечень допуслуг и цены."))

    b.append(sec("Каталог — свой проект", """
  <div class="split">
    <div>
      <h2>Нужен дом по своим размерам или планировке?</h2>
      <p class="lead">Пришлите свой эскиз или расскажите, какой дом хотите.
      Обсудим ваши пожелания и сразу рассчитаем стоимость строительства.</p>
      %s
    </div>
    <div>%s</div>
  </div>""" % (
        btns(btn("Прислать чертёж", href="index.html#quiz")),
        form("Заявка на расчёт", ["Ваше имя", "Телефон"], "Узнать цену")),
        "Замыкающая точка захвата каталога: человек, который просмотрел проекты "
        "и не нашёл свой размер, всё равно оставляет заявку."))

    return shell("Прототип — каталог", "".join(b),
                 '<p class="crumb"><a href="index.html">Главная</a> &rarr; Каталог</p>')


PAGES = {
    "index.html": page_index,
    "catalog.html": page_catalog,
    "dom.html": page_dom,
    "bani.html": page_bani,
}

TITLES = {
    "index.html": "Главная",
    "catalog.html": "Каталог",
    "dom.html": "Страница дома",
    "bani.html": "Страница бань",
}


def collect_questions(pages_html):
    """Собирает все заглушки прототипа в один чек-лист для созвона с клиентом."""
    out = [
        "# Что нужно получить от клиента\n\n",
        "Собрано автоматически из прототипа — всё, что помечено жёлтым.\n",
        "Обновляется при каждом запуске `py build.py`.\n",
    ]
    ENT = {"mdash": "—", "ndash": "–", "times": "×", "middot": "·",
           "nbsp": " ", "rarr": "→", "#8381": "₽"}

    def clean(x):
        x = re.sub(r"<[^>]+>", "", x)
        for k, v in ENT.items():
            x = re.sub("&%s;" % re.escape(k), v, x, flags=re.I)
        return re.sub(r"\s+", " ", x).strip()

    def meaningful(s):
        """Отсеиваем немые плейсхолдеры вроде «N», «N мм», «от N ₽», «6×6»."""
        return len(s) > 18 or "уточн" in s.lower()

    seen = set()
    for name in ["index.html", "catalog.html", "dom.html", "bani.html"]:
        html = pages_html[name]
        blocks = re.findall(
            r'<div class="sec-label">(.*?)</div>(.*?)<p class="note">', html, re.S)
        rows = []
        for label, body in blocks:
            label = clean(label)
            uniq = []
            for s in re.findall(r'<span class="stub">(.*?)</span>', body, re.S):
                s = clean(s)
                if s and meaningful(s) and s not in seen:
                    seen.add(s)
                    uniq.append(s)
            if uniq:
                rows.append((label, uniq))
        if rows:
            out.append("\n## %s\n" % TITLES[name])
            for label, items in rows:
                out.append("\n**%s**\n\n" % label)
                for s in items:
                    out.append("- [ ] %s\n" % s)

    out.append("\n---\n\n## Отдельно и обязательно\n\n")
    for s in [
        "**Прайс текстом.** На старом сайте он лежит картинками — состав всех трёх "
        "комплектаций и цены по размерам нужны текстом, иначе половина сайта на заглушках.",
        "**Фотографии объектов.** Побольше, с разных домов и ракурсов.",
        "**Ссылки на отзывы** в Яндекс Картах и 2ГИС + ссылка на профиль Авито.",
        "**Схема оплаты:** предоплата или поэтапно и в каких долях.",
        "**Реальные сроки** по каждому размеру (до какого размера это честные 3 дня).",
        "**Год основания компании** — от какого года считаем «12 лет».",
        "**Подарок или акция за заявку** — что даём за прохождение квиза.",
        "**Контакты:** точный адрес офиса, режим работы, мессенджеры.",
    ]:
        out.append("- [ ] %s\n" % s)
    return "".join(out)


# ─── КОНТРОЛЬ ПОВТОРОВ
# Клиент читает лендинг сверху вниз. Если одна и та же мысль повторяется
# в трёх блоках подряд — он устаёт и перестаёт читать. Каждая тема должна
# иметь ОДИН дом, остальные блоки её максимум упоминают.
THEMES = {
    "цена сразу в разговоре": [r"перву. минут", r"прямо в разговоре",
                               r"сразу в разговоре", r"в тот же день"],
    "фикс. цена в договоре": [r"фиксирован", r"зафиксир", r"не мен.ется"],
    "свои материалы, склад, магазин": [r"свои материал", r"магазин стройматериал",
                                       r"склад"],
    "свои бригады, без подрядчиков": [r"бригад", r"подрядчик"],
    "12 лет и 1 500 объектов": [r"12 лет", r"1&nbsp;500", r"1 500"],
    "гарантия": [r"гарант"],
    "строим круглый год": [r"круглый год", r"зимой строим"],
    "приехать на объект": [r"на объект вживую", r"приехать и посмотреть",
                           r"доступ на объект"],
    "проект не нужен, чертёж от руки": [r"от руки", r"проект не нужен"],
    "сроки 3 дня": [r"за 3 дня", r"3 дня"],
    "фундамент входит": [r"фундамент вход", r"буронабивные"],
}


def check_repeats(html, page):
    text_blocks = re.findall(
        r'<div class="sec-label">(.*?)</div>(.*?)<p class="note">', html, re.S)
    bodies = []
    for lab, body in text_blocks:
        body = re.sub(r"<[^>]+>", " ", body)
        bodies.append(re.sub(r"\s+", " ", body).lower())
    warn = []
    for theme, pats in THEMES.items():
        hits = [i + 1 for i, t in enumerate(bodies)
                if any(re.search(p, t) for p in pats)]
        if len(hits) > 2:
            warn.append("     · %-32s блоки %s" % (theme, ", ".join(map(str, hits))))
    if warn:
        print("  ! %s — темы в 3+ блоках:" % page)
        print("\n".join(warn))
    return len(warn)


if __name__ == "__main__":
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    if PAGES_MODE:
        shutil.copy("client_comments.js", os.path.join(OUT, "comments.js"))
        open(os.path.join(OUT, ".nojekyll"), "w").close()
        for junk in ("comments.php", "comments.json"):
            jp = os.path.join(OUT, junk)
            if os.path.exists(jp):
                os.remove(jp)
    elif CLIENT:
        shutil.copy("client_comments.js", os.path.join(OUT, "comments.js"))
        shutil.copy("comments.php", os.path.join(OUT, "comments.php"))
        if not os.path.exists(os.path.join(OUT, "comments.json")):
            io.open(os.path.join(OUT, "comments.json"), "w",
                    encoding="utf-8").write("[]")
    else:
        shutil.copy("comments.js", os.path.join(OUT, "comments.js"))
        open(os.path.join(OUT, ".nojekyll"), "w").close()

    built = {}
    for name, fn in PAGES.items():
        html = typo(fn())
        built[name] = html
        with io.open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(html)
        stubs = len(re.findall(r'class="stub"', html))
        secs = len(re.findall(r"<section>", html))
        print("  %-12s  %2d блоков, %2d заглушек" % (name, secs, stubs))

    if CLIENT:
        print("\nOK -> %s/ (клиентская версия, комментарии-пины)" % OUT)
        sys.exit(0)

    print()
    total = sum(check_repeats(built[n], n) for n in ("index.html",))
    if not total:
        print("  повторов нет: каждая тема живёт в 1-2 блоках")
    print()

    q = collect_questions(built)
    with io.open("ВОПРОСЫ-КЛИЕНТУ.md", "w", encoding="utf-8") as f:
        f.write(q)
    print("  %-12s  %2d пунктов" % ("вопросы", q.count("- [ ]")))
    print("\nГотово → %s/" % OUT)
