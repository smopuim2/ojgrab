from quart import Quart,jsonify,render_template,abort,request,redirect,url_for
from playwright.async_api import async_playwright
from database import Database
import asyncio
from render_md import render_md,render_tags
from config import BASE_URL,USERNAME,MODEL
import random

HEADLESS=True

app=Quart(__name__)

@app.before_serving
async def startup():
    global playw,browser,database,status
    playw=await async_playwright().start()
    browser=await playw.chromium.launch(headless=HEADLESS)
    database=Database()
    database.load_tags()
    status=[]

@app.route("/")
async def homepage():
    return await render_template(
        "homepage.html",
        base_url=BASE_URL,
        username=USERNAME,
        model=MODEL,
    )

@app.route("/p")
async def p_list():
    qtags=request.args.getlist("t")
    if qtags:
        probs=database.search_from_tags(qtags)
    else:
        probs=database.load_probs()
    return await render_template(
        "p_list.html",
        probs=probs,
        tags=render_tags(set(database.tags)-set(qtags)),
        qtags=render_tags(qtags),
    )

@app.route("/p/rand")
async def p_rand():
    return redirect("/p/"+str(random.choice(database.load_probs())["pid"]))

@app.route("/p/<int:pid>")
async def p_display(pid):
    try:
        prob=database.load_prob(pid)
    except FileNotFoundError:
        abort(404)
    return await render_template(
        "p_display.html",
        pid=pid,
        title=prob["title"],
        desc=render_md(prob["desc"]),
        tags=render_tags(prob["tags"]),
    )

@app.route("/api/p/search",methods=["POST"])
async def api_p_search():
    data=await request.form
    text=data.get("text")
    resp=await database.tags_from_desc(text)
    return redirect(url_for("p_list",t=resp))

@app.route("/api/s/grab",methods=["POST"])
async def api_s_grab():
    data=await request.form
    pids=[]
    for i in data.get("pids","").split():
        if i.isdigit():
            pids.append(int(i))
    status.append({"ok":True,"desc":f"{' '.join(map(str,pids))} 准备抓取"})
    def on_start(pid):
        status.append({"ok":True,"desc":f"{pid} 正在抓取"})
    def on_done(pid,err):
        global status
        if err:
            status.append({"ok":False,"desc":f"{pid} 抓取失败","err":err})
        else:
            status.append({"ok":True,"desc":f"{pid} 抓取成功"})
    asyncio.create_task(database.store_probs(browser,pids,on_start,on_done))
    return redirect("/s")

@app.route("/s")
async def s_list():
    return await render_template(
        "s_list.html",
        status=reversed(status),
    )

@app.route("/d")
async def d_list():
    return await render_template(
        "d_list.html",
        discs=database.load_discs(),
    )

@app.route("/d/new")
async def d_new():
    content=request.args.get("c")
    return await render_template(
        "d_new.html",
        content=content if content else "",
    )

@app.route("/d/<int:did>")
async def d_display(did):
    try:
        disc=database.load_disc(did)
    except FileNotFoundError:
        abort(404)
    return await render_template(
        "d_display.html",
        did=did,
        title=disc["title"],
        posts=(render_md(i) for i in disc["posts"]),
    )

@app.route("/d/p/<int:pid>")
async def d_p_display(pid):
    try:
        prob=database.load_prob(pid)
    except FileNotFoundError:
        abort(404)
    return await render_template(
        "d_p_display.html",
        pid=pid,
        title=prob["title"],
        desc=render_md(prob["desc"]),
        entry=render_md(prob["entry"]),
        solution=render_md(prob["solution"]),
        code=prob["code"],
    )

@app.route("/api/d/new",methods=["POST"])
async def api_d_new():
    data=await request.form
    title=data.get("title")
    post=data.get("post")
    did=database.new_disc(title,post)
    return redirect("/d/"+str(did))

@app.route("/api/d/post",methods=["POST"])
async def api_d_post():
    data=await request.form
    did=data.get("did")
    post=data.get("post")
    await database.add_post(did,post)
    return redirect("/d/"+str(did))

@app.route("/api/d/llm_post",methods=["POST"])
async def api_d_llm_post():
    data=await request.form
    did=data.get("did")
    await database.add_post(did,None)
    return redirect("/d/"+str(did))

@app.errorhandler(404)
async def not_found(e):
    return await app.send_static_file("not_found.html"),404

if __name__=="__main__":
    app.run()
