from grab import Grab
from llm import LLM
import asyncio
import re
import json
import glob
import traceback
from collections import Counter
from config import TRUSTED_USERS
import random

class Database:
    def __init__(self,path="data/"):
        self.path=path if path.endswith("/") or path.endswith("\\") else path+"/"
        self.llm_fmt=LLM(r"""你是一名算法竞赛题解总结助手。我将输入题目描述和正解的代码图片。
依次输出：
1. 核心切入点，用`<<ENTRY>>`和`<</ENTRY>>`包裹。
   应当为较难以想到的步骤，如**问题转化或重要观察**。
2. 分步思路，用`<<SOLUTION>>`和`<</SOLUTION>>`包裹。
3. 代码实现，用`<<CODE>>`和`<</CODE>>`包裹。
   不要使用markdown的代码标记！

同时，对于任何**思维模式，转化技巧，数据结构**等，打上标签。
- 标签用`[[`和`]]`包裹。
- 标签只能出现在`<<ENTRY>>`或`<<SOLUTION>>`部分的内部。
- 标签应当出现在有关文本附近，如每步末尾。
- 建议使用输入中推荐的标签。
- 可以新增标签，但标签内容应该具体。
  如不要`[[关键转化]]`，用`[[dfs序]][[树状数组]]`。
""")
        self.llm_tags=LLM(r"""你是一名算法竞赛标签标注员。我将输入一段描述。
每一行依次输出可能的标签。
- 标签应该具体，如**思维模式，转化技巧，数据结构**等。
  如：`dfs序``树状数组`。
- 尽可能多的输出相关的标签，包括中英文名，别名等变体，但不超过50个。
- 不要使用markdown标记！
""")
        self.llm_post=LLM(r"""你是一名算法竞赛教研员。我将输入若干道题目的信息，以及当前的讨论成果。
依次输出：
1. 题目的总览。
   题目之间如果有相似处或关联，进行总结。
   `[[`和`]]`包裹的标签可以使用，但不能修改其内容。
2. 题目之间的不同之处。
   区分出每道题的不同点，逐题列出。
3. 更新讨论成果。
   重复已经有的内容，或进行增补或修正。

**注意：如果有题目与当前讨论无关，忽略这些题，不要输出任何信息。**

同时，如果需要引用题目，采用特殊格式：
- 题目编号用`[#`和`#]`包裹。
- 可以出现在任何地方，例如作为名词使用。
  比如：`这个知识点也在[#123#]中出现`。
""")
    def get_block(self,text,name):
        x=re.search(rf"<<{name}>>(.*?)<</{name}>>",text,re.S)
        return x.group(1).strip() if x else None
    def get_tags(self,text):
        return set(re.findall(r"\[\[\s*(.*?)\s*\]\]",text))
    def get_ptags(self,text):
        return set(int(i) for i in re.findall(r"\[#\s*(.*?)\s*#\]",text))
    def unique_probs(self,*probs):
        pids=set()
        res=[]
        for prob in probs:
            if prob["pid"] not in pids:
                pids.add(prob["pid"])
                res.append(prob)
        return res
    async def grab_prob(self,grab,pid):
        data=await grab.get_prob(pid)
        for i in TRUSTED_USERS:
            std=await grab.get_std(pid,i)
            if std:
                break
        tags=set(i["name"] for i in data["tags"])
        text=rf"""{data["statement"]}

---

推荐标签：
```
{chr(10).join(str(i) for i in tags)}
```
"""
        imgs=["data:image/jpeg;base64,"+await grab.get_sub(i) for i in std]
        resp=await self.llm_fmt.ask(text,imgs)
        prob={}
        prob["title"]=data["meta"]["title"]
        prob["desc"]=data["statement"]
        for i in ("entry","solution","code"):
            prob[i]=self.get_block(resp,i.upper())
        tags.update(self.get_tags(resp))
        prob["tags"]=list(tags)
        self.tags.update(tags)
        return prob
    def load_tags(self):
        self.tags=set()
        for prob in self.load_probs():
            self.tags.update(prob["tags"])
    def load_prefixes(self,prefix):
        res=[]
        for i in glob.iglob(self.path+prefix+"*.json"):
            num=i.split('/')[-1].split('\\')[-1].strip(prefix+'.json')
            if not num.isdigit():
                continue
            res.append(int(num))
        return res
    def load_probs(self,pids=None):
        if pids==None:
            pids=self.load_prefixes("p")
        return [{**self.load_prob(pid),"pid":pid} for pid in pids]
    def load_prob(self,pid):
        with open(self.path+f"p{pid}.json","r",encoding="utf-8") as f:
            return json.load(f)
    async def store_prob(self,browser,pid):
        page=await browser.new_page()
        grab=Grab(page)
        await grab.login()
        prob=await self.grab_prob(grab,pid)
        with open(self.path+f"p{pid}.json","w",encoding="utf-8") as f:
            json.dump(prob,f)
        await grab.logout()
        await page.close()
    async def store_probs(self,browser,pids,on_start=None,on_done=None,concurr=4):
        sem=asyncio.Semaphore(concurr)
        async def one(pid):
            async with sem:
                try:
                    if on_start:
                        on_start(pid)
                    await self.store_prob(browser,pid)
                    if on_done:
                        on_done(pid,None)
                except Exception:
                    if on_done:
                        on_done(pid,traceback.format_exc())
        await asyncio.gather(*(one(i) for i in pids))
    def search_from_tags(self,tags):
        stags=set(tags)
        def ok(x):
            return stags&set(x["tags"])
        return list(filter(ok,self.load_probs()))
    async def tags_from_desc(self,desc,text_sim=0.7):
        probs=self.load_probs()
        llm_desc=await self.llm_tags.ask(desc,[])
        def two_grams(text):
            return set(text[i:i+2] for i in range(len(text)-1))
        desc_grams=set()
        for line in llm_desc.splitlines():
            desc_grams.update(two_grams(line))
        def ok(tag):
            if len(tag)<=2:
                return tag in llm_desc
            return len(two_grams(tag)&desc_grams)/(len(tag)-1)>=text_sim
        return list(filter(ok,self.tags))
    def load_discs(self):
        return [{**self.load_disc(did),"did":did} for did in self.load_prefixes("d")]
    def load_disc(self,did):
        with open(self.path+f"d{did}.json","r",encoding="utf-8") as f:
            return json.load(f)
    def store_disc(self,did,disc):
        with open(self.path+f"d{did}.json","w",encoding="utf-8") as f:
            json.dump(disc,f)
    async def make_post(self,must_probs,probs,disc,more_probs=50):
        focus=must_probs+random.sample(probs,k=min(len(probs),more_probs))
        def build_prob(prob):
            return rf"""编号：{prob["pid"]}

题目：
{prob["desc"]}

题解：
{prob["solution"]}"""
        prob_str="\n---\n".join(build_prob(p) for p in focus)
        text=rf"""{prob_str}

---

讨论标题：{disc["title"]}

{disc["posts"][-1]}
"""
        return await self.llm_post.ask(text,[])
    def new_disc(self,title,post):
        did=random.randint(1e9,1e10-1)
        self.store_disc(did,{"title":title,"posts":[post]})
        return did
    async def add_post(self,did,post=None):
        disc=self.load_disc(did)
        if post==None:
            user_post=disc["title"]+disc["posts"][0]
            llm_post=''.join(disc["posts"][1:])
            must_probs=self.load_probs(self.get_ptags(user_post))
            probs=self.unique_probs(
                    *self.load_probs(self.get_ptags(llm_post)),
                    *self.search_from_tags(await self.tags_from_desc(user_post))
                )
            post=await self.make_post(must_probs,probs,disc)
        disc["posts"].append(post)
        self.store_disc(did,disc)
