document.querySelectorAll(".tag").forEach(e=>{
    e.addEventListener("click",()=>{
        location.href="/p?t="+encodeURIComponent(e.innerText);
    });
});

document.querySelectorAll(".ptag").forEach(e=>{
    e.addEventListener("click",()=>{
        location.href="/p/"+e.innerText;
    });
});
