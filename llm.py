from openai import AsyncOpenAI
from config import API_KEY,MODEL

class LLM:
    def __init__(self,systext):
        self.client=AsyncOpenAI(api_key=API_KEY,base_url="https://api.deepseek.com")
        self.systext=systext
    async def ask(self,text,image_urls):
        data=[{"type":"text","text":text}]
        for i in image_urls:
            data.append({"type":"image_url","image_url":{"url":i}})
        resp=await self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"system","content":self.systext},{"role":"user","content":data}],
        )
        return resp.choices[0].message.content
