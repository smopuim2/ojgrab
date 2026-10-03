from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
import re

md=(
    MarkdownIt("commonmark",{"html":False,"linkify":True,"breaks":True})
    .enable("table")
    .use(dollarmath_plugin,allow_space=True)
)

def render_tag(text):
    return rf"<span class='tag'>{text}</span>"

def render_ptag(text):
    return rf"<span class='ptag'>{text}</span>"

def render_md(text):
    text=md.render(text)
    text=re.sub(r"\s*\[\[\s*(.*?)\s*\]\]\s*",lambda x:render_tag(x.group(1)),text)
    text=re.sub(r"\s*\[#\s*(.*?)\s*#\]\s*",lambda x:render_ptag(x.group(1)),text)
    return text

def render_tags(tags):
    return "".join(render_tag(i) for i in tags)
