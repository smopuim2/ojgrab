import base64
from config import USERNAME,PASSWORD,BASE_URL

API_URL=BASE_URL+"api/"

class Grab:
    def __init__(self,page):
        self.page=page
    async def login(self):
        await self.page.goto(BASE_URL+"login")
        await self.page.get_by_placeholder("用户名").fill(USERNAME)
        await self.page.get_by_placeholder("密码").fill(PASSWORD)
        await self.page.get_by_role("button",name="登录").last.click()
        await self.page.wait_for_url(BASE_URL)
    async def logout(self):
        await self.request("auth/logout",{},"POST")
    async def request(self,url,params,method="GET"):
        return await self.page.evaluate("""async ([url,params,method])=>{
            const qs=new URLSearchParams(params).toString();
            const tk=JSON.parse(localStorage["session-swr"]).token;
            const r=await fetch(url+"?"+qs,{
                method:method,
                headers:{"Authorization":"Bearer "+tk},
            });
            return await r.json();
        }""",[API_URL+url,params,method])
    async def get_prob(self,pid):
        return await self.request("problem/getProblem",{
            "id":pid,
            "statement":"true",
            "tags":"true",
            "judgeInfo":"true",
            "discussionCount":"true",
            "lastSubmissionAndLastAcceptedSubmission":"true",
            "contests":"true",
        })
    async def get_sub(self,sid):
        await self.page.goto(BASE_URL+"s/"+str(sid))
        await self.page.wait_for_selector("canvas",state="visible")
        await self.page.locator("#_mainMenuContainer_1xint_1").evaluate("e=>e.parentNode.parentNode.remove()")
        img=await self.page.locator("canvas").first.screenshot(type="jpeg",quality=90)
        return base64.b64encode(img).decode("utf-8")
    async def get_std(self,pid,user):
        x=await self.request("submission/querySubmission",{
            "problemId":pid,
            "submitter":user,
            "status":"Accepted",
            "takeCount":10,
        })
        return [i["id"] for i in x["submissions"]]
