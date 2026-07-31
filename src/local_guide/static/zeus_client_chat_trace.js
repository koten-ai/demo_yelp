(()=>{var $e="http://localhost:8080";var Te="0.1.2",j=null;function G(c){j=c}function C(){return Te||"dev"}function y(c){if(!c)return null;if(typeof c=="object"&&!Array.isArray(c))return{v1:Array.isArray(c.v1)?c.v1:[],v2:Array.isArray(c.v2)?c.v2:[]};if(typeof c=="string")try{return y(JSON.parse(c))}catch{return null}return null}function Q(c,d){if(!c||!d)return"";let i=String(c).replace(/\/$/,""),f=String(d).trim();return f?`${i}/hub/debug/req/${encodeURIComponent(f)}`:""}function M(){let c=window.ZeusTraceConfig||{},d=j||document.currentScript,i=(c.zeusApiUrl||d?.dataset?.zeusApiUrl||$e||"").replace(/\/$/,""),f=(c.hubBaseUrl||d?.dataset?.hubBaseUrl||"").replace(/\/$/,"");return{zeusApiUrl:i,hubBaseUrl:f,zeusAuthToken:c.zeusAuthToken||d?.dataset?.zeusAuthToken||""||"",toolOrder:y(c.toolOrder??d?.dataset?.toolOrder)}}function I(c){return{zeusApiUrl:c.zeusApiUrl,hubBaseUrl:c.hubBaseUrl,toolOrder:c.toolOrder,version:C()}}function Y(c,d,i={}){let f={};d.zeusAuthToken&&(f.Authorization=`Bearer ${d.zeusAuthToken}`);let m={headers:f};return i.signal&&(m.signal=i.signal),fetch(`${d.zeusApiUrl}${c}`,m)}var U="https://cdn.jsdelivr.net/npm/jsnview@3.0.0/dist/index.min.js",$=null;function te(){return window.jsnview?Promise.resolve(window.jsnview):$||($=new Promise((c,d)=>{let i=()=>{if(window.jsnview){c(window.jsnview);return}$=null,d(new Error("jsnview loaded but window.jsnview is missing"))},f=h=>{$=null,d(new Error(h||"Failed to load jsnview"))};document.querySelectorAll(`script[src="${U}"]`).forEach(h=>{if(h.dataset.jsnviewFailed==="1")try{h.remove()}catch{}});let m=document.querySelector(`script[src="${U}"]`);if(m){if(window.jsnview){i();return}let h=()=>{m.removeEventListener("error",g),i()},g=()=>{m.dataset.jsnviewFailed="1",m.removeEventListener("load",h);try{m.remove()}catch{}f("Failed to load jsnview")};if(m.addEventListener("load",h),m.addEventListener("error",g),m.dataset.loaded==="1"){m.removeEventListener("load",h),m.removeEventListener("error",g),m.dataset.jsnviewFailed="1";try{m.remove()}catch{}ee(i,f)}return}ee(i,f)}),$)}function ee(c,d){let i=document.createElement("script");i.src=U,i.async=!0,i.onload=()=>{i.dataset.loaded="1",c()},i.onerror=()=>{i.dataset.jsnviewFailed="1";try{i.remove()}catch{}d("Failed to load jsnview")},document.head.appendChild(i)}function se(c,d={}){let i=s=>c.querySelector(`#${s}`),m=y(d.toolOrder)??{v1:[],v2:[]},h=[],g=0,_=[],L=null,R=null;function D(){let s=i("debug-panel"),t=i("debug-toggle");s.classList.remove("is-hidden"),s.setAttribute("aria-hidden","false"),t?.setAttribute("aria-expanded","true")}function O(){let s=i("debug-panel"),t=i("debug-toggle");s.classList.add("is-hidden"),s.setAttribute("aria-hidden","true"),t?.setAttribute("aria-expanded","false")}function oe(){i("debug-panel").classList.contains("is-hidden")?D():O()}function F(s,t){let e=i("toast"),a=e?.querySelector(".alert"),n=i("toast-msg");!e||!n||(n.textContent=s,a.className="alert text-sm py-2 "+(t==="warning"?"alert-warning":"alert-success"),e.classList.remove("hidden"),setTimeout(()=>e.classList.add("hidden"),2200))}function v(s){return String(s).replace(/[&<>]/g,t=>({"&":"&amp;","<":"&lt;",">":"&gt;"})[t])}function T(s){return s>=1e3?(s/1e3).toFixed(2)+"s":s+"ms"}function q(s){return s<1024?s+"B":s<1024*1024?(s/1024).toFixed(1)+"kB":(s/(1024*1024)).toFixed(1)+"MB"}function H(s,t){if(t=t||10,!s)return"";let e=String(s);return e.length>t?e.slice(0,t)+"\u2026":e}function ie(s){if(!s||typeof s!="object")return"";let t=n=>!Array.isArray(n)||!n.length?"":String(n[n.length-1]||"").trim(),e=n=>{if(!Array.isArray(n)||!n.length)return"";for(let r=n.length-1;r>=0;r--){let o=n[r],l=o&&(o.req_id||o.request_id);if(l)return String(l).trim()}return""},a=s.trace&&typeof s.trace=="object"?s.trace:null;return String(s.req_id||s.request_id||s.zeus_req_id||a?.req_id||a?.request_id||t(s.req_ids)||t(s.meta?.req_ids)||t(a?.req_ids)||e(a?.tool_calls)||e(a?.steps)||a?.session_turn?.req_id||a?.session?.create_req_id||"").trim()}function P(s){let t=i("debug-panel-title"),e=i("debug-detective-link"),a=(s||"").trim();if(t&&(t.textContent=a?`Zeus Tracer: ${a}`:"Zeus Tracer",a?t.setAttribute("title",a):t.removeAttribute("title")),!e)return;let n=Q(d.hubBaseUrl,a);n?(e.href=n,e.hidden=!1,e.classList.remove("is-disabled"),e.setAttribute("aria-disabled","false"),e.setAttribute("title",`Open Hub Detective for ${a}`)):(e.href="#",e.hidden=!0,e.classList.add("is-disabled"),e.setAttribute("aria-disabled","true"),e.setAttribute("title","Open Hub Detective for this request"))}function Z(s){return String(s||"v2").toLowerCase()==="v1"?"v1":"v2"}function B(s){let t=y(s);t&&(m=t)}async function le(){let s=y(d.toolOrder);if(s){m=s;return}if(!d.zeusApiUrl)return;let t=Number(d.toolOrderTimeoutMs),e=Number.isFinite(t)&&t>0?t:3e3,a=typeof AbortController<"u"?new AbortController:null,n=a?setTimeout(()=>{try{a.abort()}catch{}},e):null;try{let r=await Y("/api/tool-order",d,a?{signal:a.signal}:{}),o=y(await r.json());o&&(m=o)}catch{}finally{n!=null&&clearTimeout(n)}}function J(s,t){let e=t&&t.session||{},a=s.session_id||e.id,n=s.session_round||e.round,r=s.contract_status||e.contract_status||t&&t.contract_status,o=t&&t.contract&&t.contract.id||s.contract_id,l=s.session_error||e.error||t&&t.session_error,p=!!(e&&e.disabled),u="";if(r&&(u+=`<span class="badge badge-sm ${r==="match"?"badge-success":r==="drift"?"badge-warning":"badge-ghost"}">contract:${v(r)}</span>`),o&&(u+=`<span class="badge badge-sm badge-info">${v(H(o,14))}</span>`),p)u+='<span class="badge badge-sm badge-ghost">sessions: off</span>';else if(l)u+='<span class="badge badge-sm badge-error">session: failed</span>';else if(a){let x=n?` r${n}`:"";u+=`<span class="badge badge-sm badge-ghost">sess:${v(H(a))}${x}</span>`}return u}function W(s){let t=0,e=0,a=0,n=0,r=0,o=0,l=!1,p=!1,u=!1;(s.steps||[]).forEach(w=>{(w.type==="llm"||w.type==="llm_error")&&(t+=w.ms||0),w.type==="tool"&&(e+=w.ms||0,o+=w.bytes||0);let b=w.usage;b&&(b.total_tokens!=null&&(a+=Number(b.total_tokens)||0,l=!0),b.prompt_tokens!=null&&(n+=Number(b.prompt_tokens)||0,p=!0),b.completion_tokens!=null&&(r+=Number(b.completion_tokens)||0,u=!0))}),!l&&(p||u)&&(a=n+r,l=!0);let x=s.total_ms||t+e,A=Math.max(0,x-t-e);return{total:x,aiMs:t,zeusMs:e,other:A,bytes:o,tokens:a,tokensIn:n,tokensOut:r,hasTokens:l,hasIn:p,hasOut:u}}function S(s,t){return t?String(s):"?"}function ce(s){return`<div class="stats stats-horizontal mm-token-stats" title="Token usage (prompt / completion / total)"><div class="stat"><div class="stat-title">in</div><div class="stat-value">${S(s.tokensIn,s.hasIn)}</div></div><div class="stat"><div class="stat-title">out</div><div class="stat-value">${S(s.tokensOut,s.hasOut)}</div></div><div class="stat"><div class="stat-title">total</div><div class="stat-value">${S(s.tokens,s.hasTokens)}</div></div></div>`}function de(s){let t=W(s),e=t.total||1,a=r=>Math.round(r/e*100),n=document.createElement("div");return n.className="msg-metrics",n.innerHTML=`<span class="mm-bar"><i class="mm-ai" style="width:${(t.aiMs/e*100).toFixed(1)}%"></i><i class="mm-zeus" style="width:${(t.zeusMs/e*100).toFixed(1)}%"></i><i class="mm-other" style="width:${(t.other/e*100).toFixed(1)}%"></i></span><span class="mm-total">${T(t.total)}</span><span class="mm-sep">=</span><span class="mm-ai">${T(t.aiMs)}/${a(t.aiMs)}% AI</span><span class="mm-sep">+</span><span class="mm-zeus">${T(t.zeusMs)}/${a(t.zeusMs)}% Zeus</span><span class="mm-sep">+</span><span class="mm-other">${T(t.other)}/${a(t.other)}% Other</span><span class="mm-sep">\xB7</span><span class="mm-meta">Tokens</span>${ce(t)}<span class="mm-sep">\xB7</span><span class="mm-meta">Bytes: ${q(t.bytes)}</span>`,n}function pe(){let s=i("trace-total");if(!_.length){s.style.display="none";return}let t=_.reduce((a,n)=>({total:a.total+n.total,aiMs:a.aiMs+n.aiMs,zeusMs:a.zeusMs+n.zeusMs,other:a.other+n.other,tokens:a.tokens+n.tokens,tokensIn:a.tokensIn+n.tokensIn,tokensOut:a.tokensOut+n.tokensOut,hasTokens:a.hasTokens||n.hasTokens,hasIn:a.hasIn||n.hasIn,hasOut:a.hasOut||n.hasOut,bytes:a.bytes+n.bytes}),{total:0,aiMs:0,zeusMs:0,other:0,bytes:0,tokens:0,tokensIn:0,tokensOut:0,hasTokens:!1,hasIn:!1,hasOut:!1}),e=t.total||1;s.style.display="flex",s.innerHTML=`<span class="tt-label">TOTAL \xB7 ${_.length} turn${_.length===1?"":"s"}</span><span class="mm-bar"><i class="mm-ai" style="width:${(t.aiMs/e*100).toFixed(1)}%"></i><i class="mm-zeus" style="width:${(t.zeusMs/e*100).toFixed(1)}%"></i><i class="mm-other" style="width:${(t.other/e*100).toFixed(1)}%"></i></span><span class="mm-total">${T(t.total)}</span>`}function V(s,t,e){let a=e?.pipeline_step_costs;if(!a?.length)try{a=JSON.parse(e?.result_full||e?.result||"{}")?.meta?.step_costs}catch{a=null}if(!Array.isArray(a)||!a.length)return null;let n={};(e?.args?.steps||e?.pipeline_json?.steps||[]).forEach(l=>{l?.name&&(n[l.name]=l.verb||"")});let r=[],o=0;return a.forEach(l=>{let p=l.as||l.name||"step",u=n[p]||"";r.push({name:`pipeline.${p}`+(u?`.${u}`:""),cls:"tool",at:(s||0)+o,ms:l.ms||0,detail:l.status||null,pipeline:!0}),o+=l.ms||0}),r}function ue(s,t){let e=(t||[]).filter(r=>r.type==="tool"&&r.name==="pipeline"),a=0,n=[];return(s||[]).forEach(r=>{if(r.name!=="tool.pipeline"){n.push(r);return}let o=V(r.at,r.ms,e[a++]);o?n.push(...o):n.push(r)}),n}function me(s,t,e){let a=ue(s,e);if(!a.length)return"";let n=t||a.reduce((o,l)=>Math.max(o,(l.at||0)+(l.ms||0)),0)||1,r='<div class="trace-waterfall">';return a.forEach(o=>{let l=Math.max(0,Math.min(100,(o.at||0)/n*100)),p=Math.max(.5,Math.min(100-l,(o.ms||0)/n*100)),u=o.pipeline?"tw-lab tw-lab-pipeline":"tw-lab";r+=`<div class="${u}" title="${v(o.name)}">${v(o.name)}</div><div class="tw-track"><i class="${o.cls}" style="left:${l.toFixed(2)}%;width:${p.toFixed(2)}%"></i></div><div class="tw-dur">${o.ms||0} ms</div>`}),r+="</div>",r}function he(s){let t={},e={},a=(n,r)=>{t[n]=(t[n]||0)+1;let o=r?.status;(o===0||typeof o=="number"&&o>=400)&&(e[n]=(e[n]||0)+1)};return(s||[]).forEach(n=>{if(n.type==="tool"){if(n.name==="pipeline"){(n.args?.steps||n.pipeline_json?.steps||[]).forEach(r=>{r?.verb&&a(r.verb,n)});return}a(n.name||"?",n)}}),{counts:t,errs:e}}function fe(s,t){let{counts:e,errs:a}=he(s),n=Object.keys(e);if(!n.length)return"";let r=Z(t),o=m[r]||[],l=new Set(o),p=o.slice();n.forEach(b=>{l.has(b)||p.push(b)});let u=0;p.forEach(b=>{u=Math.max(u,e[b]||0)});let x=78,A="",w="";return p.forEach(b=>{let k=e[b]||0,_e=u>0&&k>0?Math.max(2,Math.round(k/u*x)):0,ke=a[b]?"b err":l.has(b)?"b":"b unknown";A+=`<div class="vbar-col"><div class="${k>0?"n":"n zero"}">${k>0?k:""}</div><div class="${ke}" style="height:${_e}px"></div></div>`,w+=`<div class="${k>0?"l":"l zero"}">${v(b)}</div>`}),`<div class="trace-vbar mt-3"><h3 class="trace-vbar-title">Tool-call frequency</h3><div class="vbar-wrap">${A}</div><div class="vbar-labels">${w}</div></div>`}function be(s){let t=[];return(s.notes||[]).forEach(e=>t.push("\u2022 "+e)),(s.steps||[]).forEach(e=>{let a=e.round!=null?e.round:"?";if(e.type==="llm"){let n=e.usage||{},r=n.total_tokens?`  tok=${n.total_tokens} (in ${n.prompt_tokens||"?"}/out ${n.completion_tokens||"?"})`:"";t.push(`[r${a}] LLM ${e.ms||0}ms \u2192 ${e.finish_reason||""}  calls=[${(e.tool_calls||[]).join(", ")}]${r}`)}else if(e.type==="tool")if(e.name==="pipeline"){let n=V(0,e.ms,e);t.push(`[r${a}] PIPELINE ${e.ms||0}ms \u2192 ${e.status} ${q(e.bytes||0)}`),n&&n.forEach(r=>{t.push(`  \xB7 ${r.name} ${r.ms||0}ms${r.detail!=null?" \u2192 "+r.detail:""}`)})}else t.push(`[r${a}] TOOL ${e.name} \u2192 ${e.status} ${e.ms||0}ms`);else e.type==="llm_error"&&t.push(`[r${a}] LLM_ERROR ${e.ms||0}ms ${e.detail||""}`)}),!t.some(e=>e.startsWith("[r"))&&(s.tool_calls||[]).length&&(s.tool_calls||[]).forEach(e=>{let a=e.round!=null?e.round:"?";t.push(`[r${a}] TOOL ${e.name||"?"} \u2192 ${e.status} ${e.ms||0}ms`)}),t.join(`
`)}function K(s){try{return JSON.stringify(s,null,2)}catch{return String(s)}}async function ge(s,t,e){try{let a=await te(),n=new a(t,{showType:!0,collapsed:!e,maxDepth:1/0});s.appendChild(n.getElement())}catch{let a=document.createElement("pre");a.className="trace-pre",a.textContent=K(t),s.appendChild(a)}}function ve(s,t,e,a=!1){let n=document.createElement("div");n.className="collapse collapse-plus trace-dump bg-base-200 rounded border border-base-300";let r=document.createElement("input");r.type="checkbox",r.setAttribute("aria-label",t),a&&(r.checked=!0);let o=document.createElement("div");o.className="collapse-title text-xs font-bold py-2 min-h-0",o.textContent=t;let l=document.createElement("div");l.className="collapse-content";let p=document.createElement("pre");p.className="trace-pre bg-base-300 rounded p-2 mt-1",p.textContent=e,l.appendChild(p),n.append(r,o,l),s.appendChild(n)}async function E(s,t,e,a){let n=document.createElement("div");n.className="collapse collapse-plus trace-dump bg-base-200 rounded border border-base-300";let r=document.createElement("input");r.type="checkbox",r.setAttribute("aria-label",t),a&&(r.checked=!0);let o=document.createElement("div");o.className="collapse-title text-xs font-bold py-2 min-h-0",o.textContent=t;let l=document.createElement("div");l.className="collapse-content";let p=document.createElement("div");p.className="trace-dump-viewer",l.appendChild(p),n.append(r,o,l),s.appendChild(n),await ge(p,e,a)}function X(s){let t=Array.isArray(s)?s.length:Number(s)||0;return`${t} round${t===1?"":"s"}`}async function xe(s,t,e,a){let n=document.createElement("div");n.className="trace-dump-wrap",s.appendChild(n);let r=a.ai_requests||[],o=a.ai_responses||[],l=a.tool_calls||[];await Promise.all([E(n,`AI requests \xB7 ${X(r)}`,r),E(n,`AI responses \xB7 ${X(o)}`,o),E(n,`Tool calls \xB7 ${l.length}`,l,l.length>0),E(n,"Raw turn bundle",{question:t,answer:e.answer,target:e.target,api_version:e.api_version||a.api_version,session_id:e.session_id,session_round:e.session_round,contract_status:e.contract_status,trace:a})])}function we(s,t){let e=t.trace;if(!e)return;B(t.tool_order),L=t.chat_id||L;let a=ie(t);a&&(R=a,P(a)),h.includes(t)||h.push(t);let n=i("trace-list"),r=i("trace-empty");r&&r.remove(),g++;let o=document.createElement("div");o.className="trace-card";let l=document.createElement("div");l.className="trace-card-head",l.innerHTML=`<span class="tc-n">#${g}</span><span class="tc-q" title="${v(s)}">${v(s)}</span><span class="tc-meta">${v(Z(t.api_version||e.api_version).toUpperCase())} \xB7 ${v(t.target||"")} \xB7 ${e.rounds||0} rounds</span>`+(J(t,e)?`<span class="tc-badges">${J(t,e)}</span>`:""),o.appendChild(l),o.appendChild(de(e));let p=document.createElement("div");p.innerHTML=me(e.spans,e.total_ms,e.steps),p.firstChild&&o.appendChild(p.firstChild);let u=document.createElement("div");u.innerHTML=fe(e.steps,t.api_version||e.api_version||"v2"),u.firstChild&&o.appendChild(u.firstChild);let x=be(e);for(x&&ve(o,"Hash Traces",x),xe(o,s,t,e),n.prepend(o),_.push(W(e));n.children.length>12;)n.removeChild(n.lastChild),_.shift();pe()}i("debug-toggle")?.addEventListener("click",oe),i("debug-close")?.addEventListener("click",O),i("trace-copy-full")?.addEventListener("click",()=>{let s=h.slice(-12);if(!s.length){F("No trace to copy yet","warning");return}navigator.clipboard.writeText(K({chat_id:L,traces:s})).then(()=>F("Trace copied"))}),P(R);let N=i("debug-panel-version");if(N){let s=C();N.textContent=s.startsWith("v")?s:`v${s}`,N.setAttribute("title",`zeus_client_chat_trace ${s}`)}let ye=le();return{appendTraceCard:we,openDebugPanel:D,closeDebugPanel:O,setToolOrder:B,readyToolOrder:ye,version:C()}}var ne=`<button
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
`;var ae=`/* Trace widget layout \u2014 DaisyUI handles btn/badge/alert/collapse */

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
  margin: 4px 0 6px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
}

.msg-metrics .mm-total { font-weight: 600; opacity: 0.7; }
.msg-metrics .mm-ai { color: #f97316; }
.msg-metrics .mm-zeus { color: #10b981; }
.msg-metrics .mm-other { color: #6366f1; }
.msg-metrics .mm-sep { opacity: 0.35; }
.msg-metrics .mm-meta { opacity: 0.65; }
.msg-metrics .mm-bar,
.trace-total .mm-bar {
  display: inline-flex;
  height: 7px;
  width: 120px;
  border-radius: 3px;
  overflow: hidden;
  background: hsl(var(--b3));
}
.msg-metrics .mm-bar > i,
.trace-total .mm-bar > i { display: block; height: 100%; }
.msg-metrics .mm-bar > i.mm-ai,
.trace-total .mm-bar > i.mm-ai { background: #f97316; }
.msg-metrics .mm-bar > i.mm-zeus,
.trace-total .mm-bar > i.mm-zeus { background: #10b981; }
.msg-metrics .mm-bar > i.mm-other,
.trace-total .mm-bar > i.mm-other { background: #6366f1; }

.trace-total .mm-total { font-weight: 600; opacity: 0.7; }
.trace-total .mm-sep { opacity: 0.35; }
.trace-total .mm-meta { opacity: 0.65; }

/* DaisyUI-style token stats (in / out / total) \u2014 sized for the metrics strip */
.mm-token-stats {
  display: inline-flex;
  width: auto;
  min-height: 0;
  background: hsl(var(--b1));
  box-shadow: 0 1px 2px hsl(var(--bc) / 0.08);
  border: 1px solid hsl(var(--bc) / 0.14);
  border-radius: 0.5rem;
  overflow: hidden;
  vertical-align: middle;
  flex-shrink: 0;
}
.mm-token-stats .stat {
  display: inline-grid;
  grid-template-rows: auto auto;
  justify-items: center;
  align-content: center;
  padding: 0.4rem 0.85rem;
  min-width: 3.75rem;
  gap: 0.15rem;
  background: transparent;
}
.mm-token-stats .stat + .stat {
  border-inline-start: 1px solid hsl(var(--bc) / 0.12);
}
.mm-token-stats .stat-title {
  font-size: 11px;
  font-weight: 500;
  line-height: 1.15;
  text-transform: lowercase;
  letter-spacing: 0.03em;
  color: hsl(var(--bc) / 0.55);
  opacity: 1;
  grid-column-start: auto;
  white-space: nowrap;
}
.mm-token-stats .stat-value {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.15;
  color: hsl(var(--bc) / 0.92);
  grid-column-start: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-variant-numeric: tabular-nums;
}

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
}`;G(document.currentScript);var Ce="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css",z=[],re=!1;function Me(){re||(window.appendTraceCard=(...c)=>z.push({type:"card",args:c}),window.openDebugPanel=()=>z.push({type:"open"}))}function ze(c){for(let d of z)d.type==="open"?c.openDebugPanel():d.type==="card"&&c.appendTraceCard(...d.args);z.length=0}function Le(){let c=M(),d=document.createElement("div");d.id="zeus-trace-host",d.style.cssText="all:initial;position:fixed;inset:0;z-index:99999;pointer-events:none;",document.body.appendChild(d);let i=d.attachShadow({mode:"open"}),f=document.createElement("link");f.rel="stylesheet",f.href=Ce;let m=document.createElement("style");m.textContent=ae;let h=document.createElement("div");h.className="zeus-trace-root",h.setAttribute("data-theme","light"),h.style.pointerEvents="auto",h.innerHTML=ne,i.append(f,m,h);let g=se(h,c);return window.appendTraceCard=g.appendTraceCard,window.openDebugPanel=g.openDebugPanel,ze(g),re=!0,{api:g,config:c}}Me();var Oe=new Promise(c=>{let d=()=>{try{let{api:i,config:f}=Le();c({api:i,config:f})}catch(i){console.error("[ZeusTrace] Failed to mount widget:",i),c({api:null,config:null,error:i})}};document.body?d():document.addEventListener("DOMContentLoaded",d)});window.ZeusTrace={ready:Oe,get config(){return I(M())},get version(){return I(M()).version}};})();
//# sourceMappingURL=zeus_client_chat_trace.js.map
