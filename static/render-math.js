{
    const cfg={
        throwOnError:false,
        displayMode:false,
    };
    document.querySelectorAll('span.math.inline').forEach(e=>{
        katex.render(e.textContent,e,cfg);
    });
    document.querySelectorAll('div.math.block').forEach(e=>{
        katex.render(e.textContent,e,cfg);
    });
}
