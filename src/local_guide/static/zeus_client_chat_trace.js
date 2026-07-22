(()=>{var _e="http://localhost:8080";var $e="0.1.0",X=null;function G(c){X=c}function k(){return $e||"dev"}function w(c){if(!c)return null;if(typeof c=="object"&&!Array.isArray(c))return{v1:Array.isArray(c.v1)?c.v1:[],v2:Array.isArray(c.v2)?c.v2:[]};if(typeof c=="string")try{return w(JSON.parse(c))}catch{return null}return null}function Q(c,d){if(!c||!d)return"";let l=String(c).replace(/\/$/,""),h=String(d).trim();return h?`${l}/hub/debug/req/${encodeURIComponent(h)}`:""}function A(){let c=window.ZeusTraceConfig||{},d=X||document.currentScript,l=(c.zeusApiUrl||d?.dataset?.zeusApiUrl||_e||"").replace(/\/$/,""),h=(c.hubBaseUrl||d?.dataset?.hubBaseUrl||"").replace(/\/$/,"");return{zeusApiUrl:l,hubBaseUrl:h,zeusAuthToken:c.zeusAuthToken||d?.dataset?.zeusAuthToken||""||"",toolOrder:w(c.toolOrder??d?.dataset?.toolOrder)}}function S(c){return{zeusApiUrl:c.zeusApiUrl,hubBaseUrl:c.hubBaseUrl,toolOrder:c.toolOrder,version:k()}}function j(c,d,l={}){let h={};d.zeusAuthToken&&(h.Authorization=`Bearer ${d.zeusAuthToken}`);let p={headers:h};return l.signal&&(p.signal=l.signal),fetch(`${d.zeusApiUrl}${c}`,p)}var O="https://cdn.jsdelivr.net/npm/jsnview@3.0.0/dist/index.min.js",$=null;function ee(){return window.jsnview?Promise.resolve(window.jsnview):$||($=new Promise((c,d)=>{let l=()=>{if(window.jsnview){c(window.jsnview);return}$=null,d(new Error("jsnview loaded but window.jsnview is missing"))},h=f=>{$=null,d(new Error(f||"Failed to load jsnview"))};document.querySelectorAll(`script[src="${O}"]`).forEach(f=>{if(f.dataset.jsnviewFailed==="1")try{f.remove()}catch{}});let p=document.querySelector(`script[src="${O}"]`);if(p){if(window.jsnview){l();return}let f=()=>{p.removeEventListener("error",b),l()},b=()=>{p.dataset.jsnviewFailed="1",p.removeEventListener("load",f);try{p.remove()}catch{}h("Failed to load jsnview")};if(p.addEventListener("load",f),p.addEventListener("error",b),p.dataset.loaded==="1"){p.removeEventListener("load",f),p.removeEventListener("error",b),p.dataset.jsnviewFailed="1";try{p.remove()}catch{}Y(l,h)}return}Y(l,h)}),$)}function Y(c,d){let l=document.createElement("script");l.src=O,l.async=!0,l.onload=()=>{l.dataset.loaded="1",c()},l.onerror=()=>{l.dataset.jsnviewFailed="1";try{l.remove()}catch{}d("Failed to load jsnview")},document.head.appendChild(l)}function te(c,d={}){let l=s=>c.querySelector(`#${s}`),p=w(d.toolOrder)??{v1:[],v2:[]},f=[],b=0,y=[],M=null,N=null;function U(){let s=l("debug-panel"),t=l("debug-toggle");s.classList.remove("is-hidden"),s.setAttribute("aria-hidden","false"),t?.setAttribute("aria-expanded","true")}function L(){let s=l("debug-panel"),t=l("debug-toggle");s.classList.add("is-hidden"),s.setAttribute("aria-hidden","true"),t?.setAttribute("aria-expanded","false")}function re(){l("debug-panel").classList.contains("is-hidden")?U():L()}function R(s,t){let e=l("toast"),a=e?.querySelector(".alert"),n=l("toast-msg");!e||!n||(n.textContent=s,a.className="alert text-sm py-2 "+(t==="warning"?"alert-warning":"alert-success"),e.classList.remove("hidden"),setTimeout(()=>e.classList.add("hidden"),2200))}function g(s){return String(s).replace(/[&<>]/g,t=>({"&":"&amp;","<":"&lt;",">":"&gt;"})[t])}function E(s){return s>=1e3?(s/1e3).toFixed(2)+"s":s+"ms"}function D(s){return s<1024?s+"B":s<1024*1024?(s/1024).toFixed(1)+"kB":(s/(1024*1024)).toFixed(1)+"MB"}function F(s,t){if(t=t||10,!s)return"";let e=String(s);return e.length>t?e.slice(0,t)+"\u2026":e}function oe(s){if(!s||typeof s!="object")return"";let t=n=>!Array.isArray(n)||!n.length?"":String(n[n.length-1]||"").trim(),e=n=>{if(!Array.isArray(n)||!n.length)return"";for(let r=n.length-1;r>=0;r--){let o=n[r],i=o&&(o.req_id||o.request_id);if(i)return String(i).trim()}return""},a=s.trace&&typeof s.trace=="object"?s.trace:null;return String(s.req_id||s.request_id||s.zeus_req_id||a?.req_id||a?.request_id||a?.session_turn?.req_id||t(s.req_ids)||t(s.meta?.req_ids)||t(a?.req_ids)||e(a?.tool_calls)||e(a?.steps)||a?.session?.create_req_id||"").trim()}function q(s){let t=l("debug-panel-title"),e=l("debug-detective-link"),a=(s||"").trim();if(t&&(t.textContent=a?`Zeus Tracer: ${a}`:"Zeus Tracer",a?t.setAttribute("title",a):t.removeAttribute("title")),!e)return;let n=Q(d.hubBaseUrl,a);n?(e.href=n,e.hidden=!1,e.classList.remove("is-disabled"),e.setAttribute("aria-disabled","false"),e.setAttribute("title",`Open Hub Detective for ${a}`)):(e.href="#",e.hidden=!0,e.classList.add("is-disabled"),e.setAttribute("aria-disabled","true"),e.setAttribute("title","Open Hub Detective for this request"))}function I(s){return String(s||"v2").toLowerCase()==="v1"?"v1":"v2"}function H(s){let t=w(s);t&&(p=t)}async function ie(){let s=w(d.toolOrder);if(s){p=s;return}if(!d.zeusApiUrl)return;let t=Number(d.toolOrderTimeoutMs),e=Number.isFinite(t)&&t>0?t:3e3,a=typeof AbortController<"u"?new AbortController:null,n=a?setTimeout(()=>{try{a.abort()}catch{}},e):null;try{let r=await j("/api/tool-order",d,a?{signal:a.signal}:{}),o=w(await r.json());o&&(p=o)}catch{}finally{n!=null&&clearTimeout(n)}}function P(s,t){let e=t&&t.session||{},a=s.session_id||e.id,n=s.session_round||e.round,r=s.contract_status||e.contract_status||t&&t.contract_status,o=t&&t.contract&&t.contract.id||s.contract_id,i=s.session_error||e.error||t&&t.session_error,u=!!(e&&e.disabled),m="";if(r&&(m+=`<span class="badge badge-sm ${r==="match"?"badge-success":r==="drift"?"badge-warning":"badge-ghost"}">contract:${g(r)}</span>`),o&&(m+=`<span class="badge badge-sm badge-info">${g(F(o,14))}</span>`),u)m+='<span class="badge badge-sm badge-ghost">sessions: off</span>';else if(i)m+='<span class="badge badge-sm badge-error">session: failed</span>';else if(a){let x=n?` r${n}`:"";m+=`<span class="badge badge-sm badge-ghost">sess:${g(F(a))}${x}</span>`}return m}function Z(s){let t=0,e=0,a=0,n=0;(s.steps||[]).forEach(i=>{(i.type==="llm"||i.type==="llm_error")&&(t+=i.ms||0),i.type==="tool"&&(e+=i.ms||0,n+=i.bytes||0),i.usage&&i.usage.total_tokens&&(a+=i.usage.total_tokens)});let r=s.total_ms||t+e,o=Math.max(0,r-t-e);return{total:r,aiMs:t,zeusMs:e,other:o,tokens:a,bytes:n}}function le(s){let t=Z(s),e=t.total||1,a=r=>Math.round(r/e*100),n=document.createElement("div");return n.className="msg-metrics",n.innerHTML=`<span class="mm-bar"><i class="mm-ai" style="width:${(t.aiMs/e*100).toFixed(1)}%"></i><i class="mm-zeus" style="width:${(t.zeusMs/e*100).toFixed(1)}%"></i><i class="mm-other" style="width:${(t.other/e*100).toFixed(1)}%"></i></span><span class="mm-total">${E(t.total)}</span><span class="mm-sep">=</span><span class="mm-ai">${E(t.aiMs)}/${a(t.aiMs)}% AI</span><span class="mm-sep">+</span><span class="mm-zeus">${E(t.zeusMs)}/${a(t.zeusMs)}% Zeus</span><span class="mm-sep">+</span><span class="mm-other">${E(t.other)}/${a(t.other)}% Other</span><span class="mm-sep">\xB7</span><span class="mm-meta">Tokens: ${t.tokens||"?"}</span><span class="mm-sep">\xB7</span><span class="mm-meta">Bytes: ${D(t.bytes)}</span>`,n}function ce(){let s=l("trace-total");if(!y.length){s.style.display="none";return}let t=y.reduce((a,n)=>({total:a.total+n.total,aiMs:a.aiMs+n.aiMs,zeusMs:a.zeusMs+n.zeusMs,other:a.other+n.other,tokens:a.tokens+n.tokens,bytes:a.bytes+n.bytes}),{total:0,aiMs:0,zeusMs:0,other:0,tokens:0,bytes:0}),e=t.total||1;s.style.display="flex",s.innerHTML=`<span class="tt-label">TOTAL \xB7 ${y.length} turn${y.length===1?"":"s"}</span><span class="mm-bar"><i class="mm-ai" style="width:${(t.aiMs/e*100).toFixed(1)}%"></i><i class="mm-zeus" style="width:${(t.zeusMs/e*100).toFixed(1)}%"></i><i class="mm-other" style="width:${(t.other/e*100).toFixed(1)}%"></i></span><span class="mm-total">${E(t.total)}</span>`}function B(s,t,e){let a=e?.pipeline_step_costs;if(!a?.length)try{a=JSON.parse(e?.result_full||e?.result||"{}")?.meta?.step_costs}catch{a=null}if(!Array.isArray(a)||!a.length)return null;let n={};(e?.args?.steps||e?.pipeline_json?.steps||[]).forEach(i=>{i?.name&&(n[i.name]=i.verb||"")});let r=[],o=0;return a.forEach(i=>{let u=i.as||i.name||"step",m=n[u]||"";r.push({name:`pipeline.${u}`+(m?`.${m}`:""),cls:"tool",at:(s||0)+o,ms:i.ms||0,detail:i.status||null,pipeline:!0}),o+=i.ms||0}),r}function de(s,t){let e=(t||[]).filter(r=>r.type==="tool"&&r.name==="pipeline"),a=0,n=[];return(s||[]).forEach(r=>{if(r.name!=="tool.pipeline"){n.push(r);return}let o=B(r.at,r.ms,e[a++]);o?n.push(...o):n.push(r)}),n}function pe(s,t,e){let a=de(s,e);if(!a.length)return"";let n=t||a.reduce((o,i)=>Math.max(o,(i.at||0)+(i.ms||0)),0)||1,r='<div class="trace-waterfall">';return a.forEach(o=>{let i=Math.max(0,Math.min(100,(o.at||0)/n*100)),u=Math.max(.5,Math.min(100-i,(o.ms||0)/n*100)),m=o.pipeline?"tw-lab tw-lab-pipeline":"tw-lab";r+=`<div class="${m}" title="${g(o.name)}">${g(o.name)}</div><div class="tw-track"><i class="${o.cls}" style="left:${i.toFixed(2)}%;width:${u.toFixed(2)}%"></i></div><div class="tw-dur">${o.ms||0} ms</div>`}),r+="</div>",r}function ue(s){let t={},e={},a=(n,r)=>{t[n]=(t[n]||0)+1;let o=r?.status;(o===0||typeof o=="number"&&o>=400)&&(e[n]=(e[n]||0)+1)};return(s||[]).forEach(n=>{if(n.type==="tool"){if(n.name==="pipeline"){(n.args?.steps||n.pipeline_json?.steps||[]).forEach(r=>{r?.verb&&a(r.verb,n)});return}a(n.name||"?",n)}}),{counts:t,errs:e}}function me(s,t){let{counts:e,errs:a}=ue(s),n=Object.keys(e);if(!n.length)return"";let r=I(t),o=p[r]||[],i=new Set(o),u=o.slice();n.forEach(v=>{i.has(v)||u.push(v)});let m=0;u.forEach(v=>{m=Math.max(m,e[v]||0)});let x=78,V="",K="";return u.forEach(v=>{let _=e[v]||0,we=m>0&&_>0?Math.max(2,Math.round(_/m*x)):0,ye=a[v]?"b err":i.has(v)?"b":"b unknown";V+=`<div class="vbar-col"><div class="${_>0?"n":"n zero"}">${_>0?_:""}</div><div class="${ye}" style="height:${we}px"></div></div>`,K+=`<div class="${_>0?"l":"l zero"}">${g(v)}</div>`}),`<div class="trace-vbar mt-3"><h3 class="trace-vbar-title">Tool-call frequency</h3><div class="vbar-wrap">${V}</div><div class="vbar-labels">${K}</div></div>`}function fe(s){let t=[];return(s.notes||[]).forEach(e=>t.push("\u2022 "+e)),(s.steps||[]).forEach(e=>{let a=e.round!=null?e.round:"?";if(e.type==="llm"){let n=e.usage||{},r=n.total_tokens?`  tok=${n.total_tokens} (in ${n.prompt_tokens||"?"}/out ${n.completion_tokens||"?"})`:"";t.push(`[r${a}] LLM ${e.ms||0}ms \u2192 ${e.finish_reason||""}  calls=[${(e.tool_calls||[]).join(", ")}]${r}`)}else if(e.type==="tool")if(e.name==="pipeline"){let n=B(0,e.ms,e);t.push(`[r${a}] PIPELINE ${e.ms||0}ms \u2192 ${e.status} ${D(e.bytes||0)}`),n&&n.forEach(r=>{t.push(`  \xB7 ${r.name} ${r.ms||0}ms${r.detail!=null?" \u2192 "+r.detail:""}`)})}else t.push(`[r${a}] TOOL ${e.name} \u2192 ${e.status} ${e.ms||0}ms`);else e.type==="llm_error"&&t.push(`[r${a}] LLM_ERROR ${e.ms||0}ms ${e.detail||""}`)}),!t.some(e=>e.startsWith("[r"))&&(s.tool_calls||[]).length&&(s.tool_calls||[]).forEach(e=>{let a=e.round!=null?e.round:"?";t.push(`[r${a}] TOOL ${e.name||"?"} \u2192 ${e.status} ${e.ms||0}ms`)}),t.join(`
`)}function J(s){try{return JSON.stringify(s,null,2)}catch{return String(s)}}async function he(s,t,e){try{let a=await ee(),n=new a(t,{showType:!0,collapsed:!e,maxDepth:1/0});s.appendChild(n.getElement())}catch{let a=document.createElement("pre");a.className="trace-pre",a.textContent=J(t),s.appendChild(a)}}function be(s,t,e,a=!1){let n=document.createElement("div");n.className="collapse collapse-plus trace-dump bg-base-200 rounded border border-base-300";let r=document.createElement("input");r.type="checkbox",r.setAttribute("aria-label",t),a&&(r.checked=!0);let o=document.createElement("div");o.className="collapse-title text-xs font-bold py-2 min-h-0",o.textContent=t;let i=document.createElement("div");i.className="collapse-content";let u=document.createElement("pre");u.className="trace-pre bg-base-300 rounded p-2 mt-1",u.textContent=e,i.appendChild(u),n.append(r,o,i),s.appendChild(n)}async function T(s,t,e,a){let n=document.createElement("div");n.className="collapse collapse-plus trace-dump bg-base-200 rounded border border-base-300";let r=document.createElement("input");r.type="checkbox",r.setAttribute("aria-label",t),a&&(r.checked=!0);let o=document.createElement("div");o.className="collapse-title text-xs font-bold py-2 min-h-0",o.textContent=t;let i=document.createElement("div");i.className="collapse-content";let u=document.createElement("div");u.className="trace-dump-viewer",i.appendChild(u),n.append(r,o,i),s.appendChild(n),await he(u,e,a)}function W(s){let t=Array.isArray(s)?s.length:Number(s)||0;return`${t} round${t===1?"":"s"}`}async function ge(s,t,e,a){let n=document.createElement("div");n.className="trace-dump-wrap",s.appendChild(n);let r=a.ai_requests||[],o=a.ai_responses||[],i=a.tool_calls||[];await Promise.all([T(n,`AI requests \xB7 ${W(r)}`,r),T(n,`AI responses \xB7 ${W(o)}`,o),T(n,`Tool calls \xB7 ${i.length}`,i,i.length>0),T(n,"Raw turn bundle",{question:t,answer:e.answer,target:e.target,api_version:e.api_version||a.api_version,session_id:e.session_id,session_round:e.session_round,contract_status:e.contract_status,trace:a})])}function ve(s,t){let e=t.trace;if(!e)return;H(t.tool_order),M=t.chat_id||M;let a=oe(t);a&&(N=a,q(a)),f.includes(t)||f.push(t);let n=l("trace-list"),r=l("trace-empty");r&&r.remove(),b++;let o=document.createElement("div");o.className="trace-card";let i=document.createElement("div");i.className="trace-card-head",i.innerHTML=`<span class="tc-n">#${b}</span><span class="tc-q" title="${g(s)}">${g(s)}</span><span class="tc-meta">${g(I(t.api_version||e.api_version).toUpperCase())} \xB7 ${g(t.target||"")} \xB7 ${e.rounds||0} rounds</span>`+(P(t,e)?`<span class="tc-badges">${P(t,e)}</span>`:""),o.appendChild(i),o.appendChild(le(e));let u=document.createElement("div");u.innerHTML=pe(e.spans,e.total_ms,e.steps),u.firstChild&&o.appendChild(u.firstChild);let m=document.createElement("div");m.innerHTML=me(e.steps,t.api_version||e.api_version||"v2"),m.firstChild&&o.appendChild(m.firstChild);let x=fe(e);for(x&&be(o,"Hash Traces",x),ge(o,s,t,e),n.prepend(o),y.push(Z(e));n.children.length>12;)n.removeChild(n.lastChild),y.shift();ce()}l("debug-toggle")?.addEventListener("click",re),l("debug-close")?.addEventListener("click",L),l("trace-copy-full")?.addEventListener("click",()=>{let s=f.slice(-12);if(!s.length){R("No trace to copy yet","warning");return}navigator.clipboard.writeText(J({chat_id:M,traces:s})).then(()=>R("Trace copied"))}),q(N);let z=l("debug-panel-version");if(z){let s=k();z.textContent=s.startsWith("v")?s:`v${s}`,z.setAttribute("title",`zeus_client_chat_trace ${s}`)}let xe=ie();return{appendTraceCard:ve,openDebugPanel:U,closeDebugPanel:L,setToolOrder:H,readyToolOrder:xe,version:k()}}var se=`<button
  type="button"
  id="debug-toggle"
  class="btn btn-square shadow-lg debug-toggle-btn"
  title="Toggle Zeus trace panel"
  aria-expanded="false"
>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="40" height="40">
    <rect width="64" height="64" rx="10" ry="10" fill="#1f2937" />
    <path d="M36 6 L14 36 H28 L24 58 L50 26 H34 Z" fill="#facc15" stroke="#b45309" stroke-width="1.5" stroke-linejoin="round" />
  </svg>
</button>

<aside id="debug-panel" class="debug-panel is-hidden" aria-hidden="true">
  <header class="debug-panel-header">
    <div class="debug-panel-title-row">
      <h2 id="debug-panel-title" class="font-bold text-sm">Zeus Tracer</h2>
      <a
        id="debug-detective-link"
        class="debug-detective-link is-disabled"
        href="#"
        target="_blank"
        rel="noopener noreferrer"
        aria-disabled="true"
        title="Open Hub Detective for this request"
        hidden
      >Detective \u2197</a>
    </div>
    <div class="flex gap-2">
      <button type="button" id="trace-copy-full" class="btn btn-xs btn-ghost">Copy all</button>
      <button type="button" id="debug-close" class="btn btn-xs btn-ghost" aria-label="Close">\xD7</button>
    </div>
  </header>
  <div id="trace-total" class="trace-total" style="display:none"></div>
  <div id="trace-list" class="trace-list">
    <div id="trace-empty" class="opacity-50 text-sm p-4">No search run yet.</div>
  </div>
  <footer id="debug-panel-footer" class="debug-panel-footer" aria-label="Widget version">
    <span id="debug-panel-version" class="debug-panel-version">v\u2014</span>
  </footer>
</aside>

<div id="toast" class="toast toast-bottom toast-end z-high hidden">
  <div class="alert alert-success text-sm py-2"><span id="toast-msg"></span></div>
</div>
`;var ne=`/* Trace widget layout \u2014 DaisyUI handles btn/badge/alert/collapse */

:host, .zeus-trace-root {
  all: initial;
  font-family: ui-sans-serif, system-ui, sans-serif;
}

.flex { display: flex; }
.gap-2 { gap: 0.5rem; }
.font-bold { font-weight: 700; }
.text-sm { font-size: 0.875rem; line-height: 1.25rem; }
.text-xs { font-size: 0.75rem; line-height: 1rem; }
.hidden { display: none !important; }
.opacity-50 { opacity: 0.5; }
.p-4 { padding: 1rem; }
.p-2 { padding: 0.5rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-3 { margin-top: 0.75rem; }
.rounded { border-radius: 0.25rem; }
.z-high { z-index: 70; }

.debug-toggle-btn {
  position: fixed;
  bottom: 1rem;
  left: 1rem;
  z-index: 50;
}

.debug-panel {
  position: fixed;
  left: 1rem;
  bottom: 4.5rem;
  width: min(520px, 92vw);
  max-height: 70vh;
  z-index: 40;
  display: flex;
  flex-direction: column;
  background-color: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  box-shadow: rgba(0, 0, 0, 0.2) 0px 10px 25px;
  border-radius: 12px;
  overflow: hidden;
}

.debug-panel.is-hidden {
  display: none;
}

.debug-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid hsl(var(--b3));
  background: hsl(var(--b2) / 0.6);
  flex-shrink: 0;
  gap: 0.5rem;
}

.debug-panel-title-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  min-width: 0;
}

.debug-panel-title-row h2 {
  margin: 0;
  word-break: break-all;
}

.debug-detective-link {
  font-size: 0.75rem;
  line-height: 1;
  text-decoration: underline;
  color: hsl(var(--p));
  white-space: nowrap;
  cursor: pointer;
}

.debug-detective-link.is-disabled,
.debug-detective-link[aria-disabled="true"] {
  opacity: 0.45;
  pointer-events: none;
  cursor: not-allowed;
  text-decoration: none;
}

.trace-list {
  flex: 1;
  overflow: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.trace-pre {
  font-size: 11px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg-metrics {
  font: 11px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace;
  opacity: 0.85;
  margin: 2px 0 1px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
}

.msg-metrics .mm-total { font-weight: 600; opacity: 0.7; }
.msg-metrics .mm-ai { color: #f97316; }
.msg-metrics .mm-zeus { color: #10b981; }
.msg-metrics .mm-other { color: #6366f1; }
.msg-metrics .mm-sep { opacity: 0.35; }
.msg-metrics .mm-meta { opacity: 0.65; }
.msg-metrics .mm-bar {
  display: inline-flex;
  height: 7px;
  width: 120px;
  border-radius: 3px;
  overflow: hidden;
  background: hsl(var(--b3));
}
.msg-metrics .mm-bar > i { display: block; height: 100%; }
.msg-metrics .mm-bar > i.mm-ai { background: #f97316; }
.msg-metrics .mm-bar > i.mm-zeus { background: #10b981; }
.msg-metrics .mm-bar > i.mm-other { background: #6366f1; }

.trace-waterfall {
  display: grid;
  grid-template-columns: max-content 1fr max-content;
  gap: 3px 10px;
  align-items: center;
  font: 11px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace;
  margin-bottom: 12px;
}

.trace-waterfall .tw-lab {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
  opacity: 0.85;
}

.trace-waterfall .tw-lab-pipeline {
  padding-left: 0.65rem;
  border-left: 2px solid #10b981;
}

.trace-waterfall .tw-track {
  height: 14px;
  background: #dbeafe;
  border-radius: 3px;
  position: relative;
}

.trace-waterfall .tw-track > i {
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: 3px;
  min-width: 2px;
}

.trace-waterfall .tw-track > i.ai { background: #f97316; }
.trace-waterfall .tw-track > i.tool { background: #10b981; }
.trace-waterfall .tw-track > i.other { background: #6366f1; }

.trace-waterfall .tw-dur {
  text-align: right;
  opacity: 0.6;
  min-width: 64px;
}

.trace-vbar {
  border: 1px solid hsl(var(--b3));
  border-radius: 8px;
  background: hsl(var(--b2) / 0.45);
  padding: 10px 12px 8px;
}

.trace-vbar-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  opacity: 0.85;
  margin: 0 0 8px;
}

.vbar-wrap {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 90px;
  padding: 4px 0 0;
  border-bottom: 1px solid hsl(var(--b3));
  overflow-x: auto;
}

.vbar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  min-width: 14px;
  height: 100%;
}

.vbar-col .b {
  width: 10px;
  background: #6366f1;
  border-radius: 2px 2px 0 0;
}

.vbar-col .b.err { background: #ef4444; }
.vbar-col .b.unknown { background: #94a3b8; }

.vbar-col .n {
  font: 9px ui-monospace, monospace;
  margin-bottom: 1px;
}

.vbar-labels {
  display: flex;
  gap: 2px;
  margin-top: 2px;
  font: 9px ui-monospace, monospace;
  opacity: 0.75;
  overflow-x: auto;
}

.vbar-labels .l {
  min-width: 14px;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  height: 60px;
}

.trace-total {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  font: 12px ui-monospace, monospace;
  border-bottom: 1px solid hsl(var(--b3));
  background: hsl(var(--p) / 0.08);
  padding: 8px 12px;
  flex-shrink: 0;
}

.trace-total .tt-label {
  font-weight: 700;
  text-transform: uppercase;
  color: hsl(var(--p));
}

.debug-panel-footer {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 4px 10px 6px;
  border-top: 1px solid hsl(var(--b3));
  background: hsl(var(--b2) / 0.45);
}

.debug-panel-version {
  font: 10px/1.2 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: hsl(var(--bc) / 0.55);
  letter-spacing: 0.02em;
  user-select: text;
}

.trace-card {
  border: 1px solid hsl(var(--b3));
  border-radius: 8px;
  padding: 10px 12px;
  background: hsl(var(--b1));
}

.trace-card-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
  margin-bottom: 6px;
}

.trace-card-head .tc-n {
  font-weight: 700;
  color: hsl(var(--p));
  font-family: ui-monospace, monospace;
}

.trace-card-head .tc-q {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 45%;
}

.trace-card-head .tc-meta {
  margin-left: auto;
  opacity: 0.6;
  font: 11px ui-monospace, monospace;
}

.trace-card-head .tc-badges {
  display: inline-flex;
  gap: 3px;
  flex-wrap: wrap;
}

.trace-dump-wrap {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}

.trace-dump .collapse-title {
  font: 11px ui-monospace, monospace;
  list-style: none;
  min-height: 2.25rem;
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

/* Checkbox collapse (DaisyUI): keep title row clickable and content readable. */
.trace-dump > input[type="checkbox"] {
  min-height: 2.25rem;
}

.trace-dump-viewer {
  max-height: 280px;
  overflow: auto;
  padding: 8px;
  background: hsl(var(--b3) / 0.55);
  border-radius: 0 0 8px 8px;
  font-size: 11px;
}

.toast {
  position: fixed;
}

.toast-bottom {
  bottom: 1rem;
}

.toast-end {
  right: 1rem;
  left: auto;
}`;G(document.currentScript);var ke="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css",C=[],ae=!1;function Ae(){ae||(window.appendTraceCard=(...c)=>C.push({type:"card",args:c}),window.openDebugPanel=()=>C.push({type:"open"}))}function Ce(c){for(let d of C)d.type==="open"?c.openDebugPanel():d.type==="card"&&c.appendTraceCard(...d.args);C.length=0}function Me(){let c=A(),d=document.createElement("div");d.id="zeus-trace-host",d.style.cssText="all:initial;position:fixed;inset:0;z-index:99999;pointer-events:none;",document.body.appendChild(d);let l=d.attachShadow({mode:"open"}),h=document.createElement("link");h.rel="stylesheet",h.href=ke;let p=document.createElement("style");p.textContent=ne;let f=document.createElement("div");f.className="zeus-trace-root",f.setAttribute("data-theme","light"),f.style.pointerEvents="auto",f.innerHTML=se,l.append(h,p,f);let b=te(f,c);return window.appendTraceCard=b.appendTraceCard,window.openDebugPanel=b.openDebugPanel,Ce(b),ae=!0,{api:b,config:c}}Ae();var Le=new Promise(c=>{let d=()=>{try{let{api:l,config:h}=Me();c({api:l,config:h})}catch(l){console.error("[ZeusTrace] Failed to mount widget:",l),c({api:null,config:null,error:l})}};document.body?d():document.addEventListener("DOMContentLoaded",d)});window.ZeusTrace={ready:Le,get config(){return S(A())},get version(){return S(A()).version}};})();
//# sourceMappingURL=zeus_client_chat_trace.js.map
