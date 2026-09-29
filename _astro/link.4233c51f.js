function c(){
  const n=new URLSearchParams(window.location.search),
        e=(n.get("target")||n.get("url")||"").trim(),
        o=document.getElementById("status-text");
  let i=!1;
  try{
    if(e){
      const t=new URL(e);
      (t.protocol==="http:"||t.protocol==="https:")&&(i=!0)
    }
  }catch{}
  if(!i){
    o&&(o.innerText="无效的目标网址");
    const t=document.querySelector(".ring-spinner");
    t&&(t.style.animationPlayState="paused");
    return
  }
  console.log(`[TGSOU] Redirecting to: ${e}`);
  setTimeout(()=>{window.location.replace(e)},500)
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c();
