(()=>{var ge="http://localhost:8080";var q=null;function j(c){q=c}function v(c){if(!c)return null;if(typeof c=="object"&&!Array.isArray(c))return{v1:Array.isArray(c.v1)?c.v1:[],v2:Array.isArray(c.v2)?c.v2:[]};if(typeof c=="string")try{return v(JSON.parse(c))}catch{return null}return null}function M(){let c=window.ZeusTraceConfig||{},d=q||document.currentScript;return{zeusApiUrl:(c.zeusApiUrl||d?.dataset?.zeusApiUrl||ge||"").replace(/\/$/,""),zeusAuthToken:c.zeusAuthToken||d?.dataset?.zeusAuthToken||""||"",toolOrder:v(c.toolOrder??d?.dataset?.toolOrder)}}function B(c){return{zeusApiUrl:c.zeusApiUrl,toolOrder:c.toolOrder}}function K(c,d,l={}){let h={};d.zeusAuthToken&&(h.Authorization=`Bearer ${d.zeusAuthToken}`);let p={headers:h};return l.signal&&(p.signal=l.signal),fetch(`${d.zeusApiUrl}${c}`,p)}var L="https://cdn.jsdelivr.net/npm/jsnview@3.0.0/dist/index.min.js",_=null;function X(){return window.jsnview?Promise.resolve(window.jsnview):_||(_=new Promise((c,d)=>{let l=()=>{if(window.jsnview){c(window.jsnview);return}_=null,d(new Error("jsnview loaded but window.jsnview is missing"))},h=m=>{_=null,d(new Error(m||"Failed to load jsnview"))};document.querySelectorAll(`script[src="${L}"]`).forEach(m=>{if(m.dataset.jsnviewFailed==="1")try{m.remove()}catch{}});let p=document.querySelector(`script[src="${L}"]`);if(p){if(window.jsnview){l();return}let m=()=>{p.removeEventListener("error",g),l()},g=()=>{p.dataset.jsnviewFailed="1",p.removeEventListener("load",m);try{p.remove()}catch{}h("Failed to load jsnview")};if(p.addEventListener("load",m),p.addEventListener("error",g),p.dataset.loaded==="1"){p.removeEventListener("load",m),p.removeEventListener("error",g),p.dataset.jsnviewFailed="1";try{p.remove()}catch{}W(l,h)}return}W(l,h)}),_)}function W(c,d){let l=document.createElement("script");l.src=L,l.async=!0,l.onload=()=>{l.dataset.loaded="1",c()},l.onerror=()=>{l.dataset.jsnviewFailed="1";try{l.remove()}catch{}d("Failed to load jsnview")},document.head.appendChild(l)}function Q(c,d={}){let l=s=>c.querySelector(`#${s}`),p=v(d.toolOrder)??{v1:[],v2:[]},m=[],g=0,w=[],A=null;function z(){let s=l("debug-panel"),t=l("debug-toggle");s.classList.remove("is-hidden"),s.setAttribute("aria-hidden","false"),t?.setAttribute("aria-expanded","true")}function C(){let s=l("debug-panel"),t=l("debug-toggle");s.classList.add("is-hidden"),s.setAttribute("aria-hidden","true"),t?.setAttribute("aria-expanded","false")}function ee(){l("debug-panel").classList.contains("is-hidden")?z():C()}function S(s,t){let e=l("toast"),n=e?.querySelector(".alert"),a=l("toast-msg");!e||!a||(a.textContent=s,n.className="alert text-sm py-2 "+(t==="warning"?"alert-warning":"alert-success"),e.classList.remove("hidden"),setTimeout(()=>e.classList.add("hidden"),2200))}function b(s){return String(s).replace(/[&<>]/g,t=>({"&":"&amp;","<":"&lt;",">":"&gt;"})[t])}function $(s){return s>=1e3?(s/1e3).toFixed(2)+"s":s+"ms"}function N(s){return s<1024?s+"B":s<1024*1024?(s/1024).toFixed(1)+"kB":(s/(1024*1024)).toFixed(1)+"MB"}function O(s,t){if(t=t||10,!s)return"";let e=String(s);return e.length>t?e.slice(0,t)+"\u2026":e}function F(s){return String(s||"v2").toLowerCase()==="v1"?"v1":"v2"}function U(s){let t=v(s);t&&(p=t)}async function te(){let s=v(d.toolOrder);if(s){p=s;return}if(!d.zeusApiUrl)return;let t=Number(d.toolOrderTimeoutMs),e=Number.isFinite(t)&&t>0?t:3e3,n=typeof AbortController<"u"?new AbortController:null,a=n?setTimeout(()=>{try{n.abort()}catch{}},e):null;try{let o=await K("/api/tool-order",d,n?{signal:n.signal}:{}),i=v(await o.json());i&&(p=i)}catch{}finally{a!=null&&clearTimeout(a)}}function R(s,t){let e=t&&t.session||{},n=s.session_id||e.id,a=s.session_round||e.round,o=s.contract_status||e.contract_status||t&&t.contract_status,i=t&&t.contract&&t.contract.id||s.contract_id,r=s.session_error||e.error||t&&t.session_error,u=!!(e&&e.disabled),f="";if(o&&(f+=`<span class="badge badge-sm ${o==="match"?"badge-success":o==="drift"?"badge-warning":"badge-ghost"}">contract:${b(o)}</span>`),i&&(f+=`<span class="badge badge-sm badge-info">${b(O(i,14))}</span>`),u)f+='<span class="badge badge-sm badge-ghost">sessions: off</span>';else if(r)f+='<span class="badge badge-sm badge-error">session: failed</span>';else if(n){let E=a?` r${a}`:"";f+=`<span class="badge badge-sm badge-ghost">sess:${b(O(n))}${E}</span>`}return f}function D(s){let t=0,e=0,n=0,a=0;(s.steps||[]).forEach(r=>{(r.type==="llm"||r.type==="llm_error")&&(t+=r.ms||0),r.type==="tool"&&(e+=r.ms||0,a+=r.bytes||0),r.usage&&r.usage.total_tokens&&(n+=r.usage.total_tokens)});let o=s.total_ms||t+e,i=Math.max(0,o-t-e);return{total:o,aiMs:t,zeusMs:e,other:i,tokens:n,bytes:a}}function se(s){let t=D(s),e=t.total||1,n=o=>Math.round(o/e*100),a=document.createElement("div");return a.className="msg-metrics",a.innerHTML=`<span class="mm-bar"><i class="mm-ai" style="width:${(t.aiMs/e*100).toFixed(1)}%"></i><i class="mm-zeus" style="width:${(t.zeusMs/e*100).toFixed(1)}%"></i><i class="mm-other" style="width:${(t.other/e*100).toFixed(1)}%"></i></span><span class="mm-total">${$(t.total)}</span><span class="mm-sep">=</span><span class="mm-ai">${$(t.aiMs)}/${n(t.aiMs)}% AI</span><span class="mm-sep">+</span><span class="mm-zeus">${$(t.zeusMs)}/${n(t.zeusMs)}% Zeus</span><span class="mm-sep">+</span><span class="mm-other">${$(t.other)}/${n(t.other)}% Other</span><span class="mm-sep">\xB7</span><span class="mm-meta">Tokens: ${t.tokens||"?"}</span><span class="mm-sep">\xB7</span><span class="mm-meta">Bytes: ${N(t.bytes)}</span>`,a}function ae(){let s=l("trace-total");if(!w.length){s.style.display="none";return}let t=w.reduce((n,a)=>({total:n.total+a.total,aiMs:n.aiMs+a.aiMs,zeusMs:n.zeusMs+a.zeusMs,other:n.other+a.other,tokens:n.tokens+a.tokens,bytes:n.bytes+a.bytes}),{total:0,aiMs:0,zeusMs:0,other:0,tokens:0,bytes:0}),e=t.total||1;s.style.display="flex",s.innerHTML=`<span class="tt-label">TOTAL \xB7 ${w.length} turn${w.length===1?"":"s"}</span><span class="mm-bar"><i class="mm-ai" style="width:${(t.aiMs/e*100).toFixed(1)}%"></i><i class="mm-zeus" style="width:${(t.zeusMs/e*100).toFixed(1)}%"></i><i class="mm-other" style="width:${(t.other/e*100).toFixed(1)}%"></i></span><span class="mm-total">${$(t.total)}</span>`}function H(s,t,e){let n=e?.pipeline_step_costs;if(!n?.length)try{n=JSON.parse(e?.result_full||e?.result||"{}")?.meta?.step_costs}catch{n=null}if(!Array.isArray(n)||!n.length)return null;let a={};(e?.args?.steps||e?.pipeline_json?.steps||[]).forEach(r=>{r?.name&&(a[r.name]=r.verb||"")});let o=[],i=0;return n.forEach(r=>{let u=r.as||r.name||"step",f=a[u]||"";o.push({name:`pipeline.${u}`+(f?`.${f}`:""),cls:"tool",at:(s||0)+i,ms:r.ms||0,detail:r.status||null,pipeline:!0}),i+=r.ms||0}),o}function ne(s,t){let e=(t||[]).filter(o=>o.type==="tool"&&o.name==="pipeline"),n=0,a=[];return(s||[]).forEach(o=>{if(o.name!=="tool.pipeline"){a.push(o);return}let i=H(o.at,o.ms,e[n++]);i?a.push(...i):a.push(o)}),a}function oe(s,t,e){let n=ne(s,e);if(!n.length)return"";let a=t||n.reduce((i,r)=>Math.max(i,(r.at||0)+(r.ms||0)),0)||1,o='<div class="trace-waterfall">';return n.forEach(i=>{let r=Math.max(0,Math.min(100,(i.at||0)/a*100)),u=Math.max(.5,Math.min(100-r,(i.ms||0)/a*100)),f=i.pipeline?"tw-lab tw-lab-pipeline":"tw-lab";o+=`<div class="${f}" title="${b(i.name)}">${b(i.name)}</div><div class="tw-track"><i class="${i.cls}" style="left:${r.toFixed(2)}%;width:${u.toFixed(2)}%"></i></div><div class="tw-dur">${i.ms||0} ms</div>`}),o+="</div>",o}function re(s){let t={},e={},n=(a,o)=>{t[a]=(t[a]||0)+1;let i=o?.status;(i===0||typeof i=="number"&&i>=400)&&(e[a]=(e[a]||0)+1)};return(s||[]).forEach(a=>{if(a.type==="tool"){if(a.name==="pipeline"){(a.args?.steps||a.pipeline_json?.steps||[]).forEach(o=>{o?.verb&&n(o.verb,a)});return}n(a.name||"?",a)}}),{counts:t,errs:e}}function ie(s,t){let{counts:e,errs:n}=re(s),a=Object.keys(e);if(!a.length)return"";let o=F(t),i=p[o]||[],r=new Set(i),u=i.slice();a.forEach(x=>{r.has(x)||u.push(x)});let f=0;u.forEach(x=>{f=Math.max(f,e[x]||0)});let E=78,Z="",J="";return u.forEach(x=>{let y=e[x]||0,fe=f>0&&y>0?Math.max(2,Math.round(y/f*E)):0,he=n[x]?"b err":r.has(x)?"b":"b unknown";Z+=`<div class="vbar-col"><div class="${y>0?"n":"n zero"}">${y>0?y:""}</div><div class="${he}" style="height:${fe}px"></div></div>`,J+=`<div class="${y>0?"l":"l zero"}">${b(x)}</div>`}),`<div class="trace-vbar mt-3"><h3 class="trace-vbar-title">Tool-call frequency</h3><div class="vbar-wrap">${Z}</div><div class="vbar-labels">${J}</div></div>`}function le(s){let t=[];return(s.notes||[]).forEach(e=>t.push("\u2022 "+e)),(s.steps||[]).forEach(e=>{let n=e.round!=null?e.round:"?";if(e.type==="llm"){let a=e.usage||{},o=a.total_tokens?`  tok=${a.total_tokens} (in ${a.prompt_tokens||"?"}/out ${a.completion_tokens||"?"})`:"";t.push(`[r${n}] LLM ${e.ms||0}ms \u2192 ${e.finish_reason||""}  calls=[${(e.tool_calls||[]).join(", ")}]${o}`)}else if(e.type==="tool")if(e.name==="pipeline"){let a=H(0,e.ms,e);t.push(`[r${n}] PIPELINE ${e.ms||0}ms \u2192 ${e.status} ${N(e.bytes||0)}`),a&&a.forEach(o=>{t.push(`  \xB7 ${o.name} ${o.ms||0}ms${o.detail!=null?" \u2192 "+o.detail:""}`)})}else t.push(`[r${n}] TOOL ${e.name} \u2192 ${e.status} ${e.ms||0}ms`);else e.type==="llm_error"&&t.push(`[r${n}] LLM_ERROR ${e.ms||0}ms ${e.detail||""}`)}),!t.some(e=>e.startsWith("[r"))&&(s.tool_calls||[]).length&&(s.tool_calls||[]).forEach(e=>{let n=e.round!=null?e.round:"?";t.push(`[r${n}] TOOL ${e.name||"?"} \u2192 ${e.status} ${e.ms||0}ms`)}),t.join(`
`)}function I(s){try{return JSON.stringify(s,null,2)}catch{return String(s)}}async function ce(s,t,e){try{let n=await X(),a=new n(t,{showType:!0,collapsed:!e,maxDepth:1/0});s.appendChild(a.getElement())}catch{let n=document.createElement("pre");n.className="trace-pre",n.textContent=I(t),s.appendChild(n)}}function de(s,t,e,n=!1){let a=document.createElement("div");a.className="collapse collapse-plus trace-dump bg-base-200 rounded border border-base-300";let o=document.createElement("input");o.type="checkbox",o.setAttribute("aria-label",t),n&&(o.checked=!0);let i=document.createElement("div");i.className="collapse-title text-xs font-bold py-2 min-h-0",i.textContent=t;let r=document.createElement("div");r.className="collapse-content";let u=document.createElement("pre");u.className="trace-pre bg-base-300 rounded p-2 mt-1",u.textContent=e,r.appendChild(u),a.append(o,i,r),s.appendChild(a)}async function T(s,t,e,n){let a=document.createElement("div");a.className="collapse collapse-plus trace-dump bg-base-200 rounded border border-base-300";let o=document.createElement("input");o.type="checkbox",o.setAttribute("aria-label",t),n&&(o.checked=!0);let i=document.createElement("div");i.className="collapse-title text-xs font-bold py-2 min-h-0",i.textContent=t;let r=document.createElement("div");r.className="collapse-content";let u=document.createElement("div");u.className="trace-dump-viewer",r.appendChild(u),a.append(o,i,r),s.appendChild(a),await ce(u,e,n)}function P(s){let t=Array.isArray(s)?s.length:Number(s)||0;return`${t} round${t===1?"":"s"}`}async function pe(s,t,e,n){let a=document.createElement("div");a.className="trace-dump-wrap",s.appendChild(a);let o=n.ai_requests||[],i=n.ai_responses||[],r=n.tool_calls||[];await Promise.all([T(a,`AI requests \xB7 ${P(o)}`,o),T(a,`AI responses \xB7 ${P(i)}`,i),T(a,`Tool calls \xB7 ${r.length}`,r,r.length>0),T(a,"Raw turn bundle",{question:t,answer:e.answer,target:e.target,api_version:e.api_version||n.api_version,session_id:e.session_id,session_round:e.session_round,contract_status:e.contract_status,trace:n})])}function ue(s,t){let e=t.trace;if(!e)return;U(t.tool_order),A=t.chat_id||A,m.includes(t)||m.push(t);let n=l("trace-list"),a=l("trace-empty");a&&a.remove(),g++;let o=document.createElement("div");o.className="trace-card";let i=document.createElement("div");i.className="trace-card-head",i.innerHTML=`<span class="tc-n">#${g}</span><span class="tc-q" title="${b(s)}">${b(s)}</span><span class="tc-meta">${b(F(t.api_version||e.api_version).toUpperCase())} \xB7 ${b(t.target||"")} \xB7 ${e.rounds||0} rounds</span>`+(R(t,e)?`<span class="tc-badges">${R(t,e)}</span>`:""),o.appendChild(i),o.appendChild(se(e));let r=document.createElement("div");r.innerHTML=oe(e.spans,e.total_ms,e.steps),r.firstChild&&o.appendChild(r.firstChild);let u=document.createElement("div");u.innerHTML=ie(e.steps,t.api_version||e.api_version||"v2"),u.firstChild&&o.appendChild(u.firstChild);let f=le(e);for(f&&de(o,"Hash Traces",f),pe(o,s,t,e),n.prepend(o),w.push(D(e));n.children.length>12;)n.removeChild(n.lastChild),w.shift();ae()}l("debug-toggle")?.addEventListener("click",ee),l("debug-close")?.addEventListener("click",C),l("trace-copy-full")?.addEventListener("click",()=>{let s=m.slice(-12);if(!s.length){S("No trace to copy yet","warning");return}navigator.clipboard.writeText(I({chat_id:A,traces:s})).then(()=>S("Trace copied"))});let me=te();return{appendTraceCard:ue,openDebugPanel:z,closeDebugPanel:C,setToolOrder:U,readyToolOrder:me}}var V=`<button
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
    <h2 class="font-bold text-sm">Zeus Trace</h2>
    <div class="flex gap-2">
      <button type="button" id="trace-copy-full" class="btn btn-xs btn-ghost">Copy all</button>
      <button type="button" id="debug-close" class="btn btn-xs btn-ghost" aria-label="Close">\xD7</button>
    </div>
  </header>
  <div id="trace-total" class="trace-total" style="display:none"></div>
  <div id="trace-list" class="trace-list">
    <div id="trace-empty" class="opacity-50 text-sm p-4">No search run yet.</div>
  </div>
</aside>

<div id="toast" class="toast toast-bottom toast-end z-high hidden">
  <div class="alert alert-success text-sm py-2"><span id="toast-msg"></span></div>
</div>`;var Y=`/* Trace widget layout \u2014 DaisyUI handles btn/badge/alert/collapse */

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
}`;j(document.currentScript);var ve="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css",k=[],G=!1;function we(){G||(window.appendTraceCard=(...c)=>k.push({type:"card",args:c}),window.openDebugPanel=()=>k.push({type:"open"}))}function ye(c){for(let d of k)d.type==="open"?c.openDebugPanel():d.type==="card"&&c.appendTraceCard(...d.args);k.length=0}function _e(){let c=M(),d=document.createElement("div");d.id="zeus-trace-host",d.style.cssText="all:initial;position:fixed;inset:0;z-index:99999;pointer-events:none;",document.body.appendChild(d);let l=d.attachShadow({mode:"open"}),h=document.createElement("link");h.rel="stylesheet",h.href=ve;let p=document.createElement("style");p.textContent=Y;let m=document.createElement("div");m.className="zeus-trace-root",m.setAttribute("data-theme","light"),m.style.pointerEvents="auto",m.innerHTML=V,l.append(h,p,m);let g=Q(m,c);return window.appendTraceCard=g.appendTraceCard,window.openDebugPanel=g.openDebugPanel,ye(g),G=!0,{api:g,config:c}}we();var $e=new Promise(c=>{let d=()=>{try{let{api:l,config:h}=_e();c({api:l,config:h})}catch(l){console.error("[ZeusTrace] Failed to mount widget:",l),c({api:null,config:null,error:l})}};document.body?d():document.addEventListener("DOMContentLoaded",d)});window.ZeusTrace={ready:$e,get config(){return B(M())}};})();
//# sourceMappingURL=zeus_client_chat_trace.js.map
