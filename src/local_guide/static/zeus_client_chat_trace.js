(()=>{var Ce="http://localhost:8080";var Le="0.1.5",I=null;function G(i){I=i}function M(){return Le||"dev"}function _(i){if(!i)return null;if(typeof i=="object"&&!Array.isArray(i))return{v1:Array.isArray(i.v1)?i.v1:[],v2:Array.isArray(i.v2)?i.v2:[]};if(typeof i=="string")try{return _(JSON.parse(i))}catch{return null}return null}function Y(i,d){if(!i||!d)return"";let l=String(i).replace(/\/$/,""),f=String(d).trim();return f?`${l}/hub/debug/session/${encodeURIComponent(f)}`:""}function ee(i){if(i===!0||i===!1)return i;if(i==null||i==="")return null;let d=String(i).trim().toLowerCase();return["1","true","yes","on"].includes(d)?!0:["0","false","no","off"].includes(d)?!1:null}function Ne(i){try{let d=i!==void 0?i:typeof location<"u"?location.search:"",l=d.startsWith("?")||d===""?d:`?${d}`;return ee(new URLSearchParams(l).get("debug"))}catch{return null}}function Oe(i={}){let d=i.fromWindow!==void 0?i.fromWindow||{}:(typeof window<"u"?window.ZeusTraceConfig:null)||{},l=i.script!==void 0?i.script:I||(typeof document<"u"?document.currentScript:null),f=ee(d.enabled!==void 0?d.enabled:l?.dataset?.enabled);if(f!==null)return f;let u=Ne(i.search);return u!==null?u:!1}function C(i={}){let d=i.fromWindow!==void 0?i.fromWindow||{}:window.ZeusTraceConfig||{},l=i.script!==void 0?i.script:I||document.currentScript,f=(d.zeusApiUrl||l?.dataset?.zeusApiUrl||Ce||"").replace(/\/$/,""),u=(d.hubBaseUrl||l?.dataset?.hubBaseUrl||"").replace(/\/$/,"");return{zeusApiUrl:f,hubBaseUrl:u,zeusAuthToken:d.zeusAuthToken||l?.dataset?.zeusAuthToken||""||"",toolOrder:_(d.toolOrder??l?.dataset?.toolOrder),enabled:Oe({fromWindow:d,script:l,search:i.search})}}function F(i){return{zeusApiUrl:i.zeusApiUrl,hubBaseUrl:i.hubBaseUrl,toolOrder:i.toolOrder,enabled:!!i.enabled,version:M()}}function te(i,d,l={}){let f={};d.zeusAuthToken&&(f.Authorization=`Bearer ${d.zeusAuthToken}`);let u={headers:f};return l.signal&&(u.signal=l.signal),fetch(`${d.zeusApiUrl}${i}`,u)}var R="https://cdn.jsdelivr.net/npm/jsnview@3.0.0/dist/index.min.js",$=null;function se(){return window.jsnview?Promise.resolve(window.jsnview):$||($=new Promise((i,d)=>{let l=()=>{if(window.jsnview){i(window.jsnview);return}$=null,d(new Error("jsnview loaded but window.jsnview is missing"))},f=g=>{$=null,d(new Error(g||"Failed to load jsnview"))};document.querySelectorAll(`script[src="${R}"]`).forEach(g=>{if(g.dataset.jsnviewFailed==="1")try{g.remove()}catch{}});let u=document.querySelector(`script[src="${R}"]`);if(u){if(window.jsnview){l();return}let g=()=>{u.removeEventListener("error",y),l()},y=()=>{u.dataset.jsnviewFailed="1",u.removeEventListener("load",g);try{u.remove()}catch{}f("Failed to load jsnview")};if(u.addEventListener("load",g),u.addEventListener("error",y),u.dataset.loaded==="1"){u.removeEventListener("load",g),u.removeEventListener("error",y),u.dataset.jsnviewFailed="1";try{u.remove()}catch{}ne(l,f)}return}ne(l,f)}),$)}function ne(i,d){let l=document.createElement("script");l.src=R,l.async=!0,l.onload=()=>{l.dataset.loaded="1",i()},l.onerror=()=>{l.dataset.jsnviewFailed="1";try{l.remove()}catch{}d("Failed to load jsnview")},document.head.appendChild(l)}function ae(i,d={}){let l=e=>i.querySelector(`#${e}`),u=_(d.toolOrder)??{v1:[],v2:[]},g=[],y=0,w=[],L=null,D=null;function H(){let e=l("debug-panel"),n=l("debug-toggle");e.classList.remove("is-hidden"),e.setAttribute("aria-hidden","false"),n?.setAttribute("aria-expanded","true")}function N(){let e=l("debug-panel"),n=l("debug-toggle");e.classList.add("is-hidden"),e.setAttribute("aria-hidden","true"),n?.setAttribute("aria-expanded","false")}function ie(){l("debug-panel").classList.contains("is-hidden")?H():N()}function j(e,n){let t=l("toast"),a=t?.querySelector(".alert"),s=l("toast-msg");!t||!s||(s.textContent=e,a.className="alert text-sm py-2 "+(n==="warning"?"alert-warning":"alert-success"),t.classList.remove("hidden"),setTimeout(()=>t.classList.add("hidden"),2200))}function v(e){return String(e).replace(/[&<>]/g,n=>({"&":"&amp;","<":"&lt;",">":"&gt;"})[n])}function E(e){return e>=1e3?(e/1e3).toFixed(2)+"s":e+"ms"}function P(e){return e<1024?e+"B":e<1024*1024?(e/1024).toFixed(1)+"kB":(e/(1024*1024)).toFixed(1)+"MB"}function B(e,n){if(n=n||10,!e)return"";let t=String(e);return t.length>n?t.slice(0,n)+"\u2026":t}function le(e){if(!e||typeof e!="object")return"";let n=e.trace&&typeof e.trace=="object"?e.trace:null,t=n?.session&&typeof n.session=="object"?n.session:null;return String(e.session_id||n?.session_id||t?.id||t?.session_id||e.session?.id||"").trim()}function q(e){let n=l("debug-panel-title"),t=l("debug-detective-link"),a=(e||"").trim();if(n&&(n.textContent="Zeus Tracer",a?n.setAttribute("title",`session ${a}`):n.removeAttribute("title")),!t)return;let s=Y(d.hubBaseUrl,a);s?(t.href=s,t.hidden=!1,t.classList.remove("is-disabled"),t.setAttribute("aria-disabled","false"),t.setAttribute("title",`Open Hub Detective for session ${a}`)):(t.href="#",t.hidden=!0,t.classList.add("is-disabled"),t.setAttribute("aria-disabled","true"),t.setAttribute("title","Open Hub Detective for this session"))}function W(e){return String(e||"v2").toLowerCase()==="v1"?"v1":"v2"}function Z(e){let n=_(e);n&&(u=n)}async function ce(){let e=_(d.toolOrder);if(e){u=e;return}if(!d.zeusApiUrl)return;let n=Number(d.toolOrderTimeoutMs),t=Number.isFinite(n)&&n>0?n:3e3,a=typeof AbortController<"u"?new AbortController:null,s=a?setTimeout(()=>{try{a.abort()}catch{}},t):null;try{let r=await te("/api/tool-order",d,a?{signal:a.signal}:{}),o=_(await r.json());o&&(u=o)}catch{}finally{s!=null&&clearTimeout(s)}}function J(e,n){let t=n&&n.session||{},a=e.session_id||t.id,s=e.session_round||t.round,r=e.contract_status||t.contract_status||n&&n.contract_status,o=n&&n.contract&&n.contract.id||e.contract_id,c=e.session_error||t.error||n&&n.session_error,p=!!(t&&t.disabled),m="";if(r&&(m+=`<span class="badge badge-sm ${r==="match"?"badge-success":r==="drift"?"badge-warning":"badge-ghost"}">contract:${v(r)}</span>`),o&&(m+=`<span class="badge badge-sm badge-info">${v(B(o,14))}</span>`),p)m+='<span class="badge badge-sm badge-ghost">sessions: off</span>';else if(c)m+='<span class="badge badge-sm badge-error">session: failed</span>';else if(a){let x=s?` r${s}`:"";m+=`<span class="badge badge-sm badge-ghost">sess:${v(B(a))}${x}</span>`}return m}function V(e){let n=0,t=0,a=0,s=0,r=0,o=0,c=!1,p=!1,m=!1;(e.steps||[]).forEach(b=>{(b.type==="llm"||b.type==="llm_error")&&(n+=b.ms||0),b.type==="tool"&&(t+=b.ms||0,o+=b.bytes||0);let h=b.usage;h&&(h.total_tokens!=null&&(a+=Number(h.total_tokens)||0,c=!0),h.prompt_tokens!=null&&(s+=Number(h.prompt_tokens)||0,p=!0),h.completion_tokens!=null&&(r+=Number(h.completion_tokens)||0,m=!0))}),!c&&(p||m)&&(a=s+r,c=!0);let x=e.total_ms||n+t,T=Math.max(0,x-n-t);return{total:x,aiMs:n,zeusMs:t,other:T,bytes:o,tokens:a,tokensIn:s,tokensOut:r,hasTokens:c,hasIn:p,hasOut:m}}function O(e,n){if(!n)return"?";let t=Number(e);return Number.isFinite(t)?Math.round(t).toLocaleString("en-US"):String(e)}function de(e){return`<div id="tokens-total" class="trace-total" style="display:flex;align-items:center;justify-content:center;"><div class="stats shadow" title="Token usage (prompt / completion / total)"><div class="stat place-items-center"><div class="stat-title">Token In</div><div class="stat-value text-primary">${O(e.tokensIn,e.hasIn)}</div></div><div class="stat place-items-center"><div class="stat-title">Token Out</div><div class="stat-value text-secondary">${O(e.tokensOut,e.hasOut)}</div></div><div class="stat place-items-center"><div class="stat-title">Total Tokens</div><div class="stat-value text-success">${O(e.tokens,e.hasTokens)}</div></div></div></div>`}function pe(e){let n=V(e),t=n.total||1,a=r=>Math.round(r/t*100),s=document.createElement("div");return s.className="msg-metrics",s.innerHTML=`<span class="mm-bar"><i class="mm-ai" style="width:${(n.aiMs/t*100).toFixed(1)}%"></i><i class="mm-zeus" style="width:${(n.zeusMs/t*100).toFixed(1)}%"></i><i class="mm-other" style="width:${(n.other/t*100).toFixed(1)}%"></i></span><span class="mm-total">${E(n.total)}</span><span class="mm-sep">=</span><span class="mm-ai">${E(n.aiMs)}/${a(n.aiMs)}% AI</span><span class="mm-sep">+</span><span class="mm-zeus">${E(n.zeusMs)}/${a(n.zeusMs)}% Zeus</span><span class="mm-sep">+</span><span class="mm-other">${E(n.other)}/${a(n.other)}% Other</span><span class="mm-sep">\xB7</span><span class="mm-meta">Bytes: ${P(n.bytes)}</span>`,s}function ue(e){if(!e||typeof e!="object")return"";let n=e.catalog&&typeof e.catalog=="object"?e.catalog:null,t=n?.system_message;if(t&&typeof t=="object"&&t.content!=null)return String(t.content);if(typeof t=="string")return t;if(n?.system_message_content!=null)return String(n.system_message_content);let s=(e.detective&&typeof e.detective=="object"?e.detective:null)?.prompt?.inject;if(s&&typeof s=="object"){if(s.system_preview)return String(s.system_preview);if(s.brief_preview)return String(s.brief_preview)}for(let r of e.ai_requests||[]){let o=r?.messages||r?.body?.messages||[];if(Array.isArray(o)){for(let c of o)if(c&&c.role==="system"&&c.content!=null)return String(c.content)}}return""}function me(e){if(!e)return null;let n=/edges_total:\s*(\d+)/i.exec(e);if(!n)return null;let t=Number(n[1]);return Number.isFinite(t)?t:null}function fe(e){let n=e?.catalog&&typeof e.catalog=="object"?e.catalog:{},t=e?.detective?.prompt?.inject&&typeof e.detective.prompt.inject=="object"?e.detective.prompt.inject:{},a=ue(e),s=n.has_mini_schema===!0||t.has_mini_schema===!0||/##\s*MINI-SCHEMA\b/i.test(a),r=n.has_scope_brief===!0||t.has_scope_brief===!0||/##\s*SCOPE BRIEF\b/i.test(a),o=Number(e?.rounds);if(!Number.isFinite(o)||o<=0){let b=(e?.steps||[]).filter(k=>k&&(k.type==="llm"||k.type==="llm_error")).length,h=Array.isArray(e?.ai_requests)?e.ai_requests.length:0;o=b||h||0}let c=Array.isArray(e?.tool_calls)?e.tool_calls.length:0;c||(c=(e?.steps||[]).filter(b=>b&&b.type==="tool").length);let p=Number(e?.total_ms),m=Number.isFinite(p)&&p>0?p:(e?.steps||[]).reduce((b,h)=>b+(Number(h?.ms)||0),0),x=null;o>0&&m>0&&(x=m/o/1e3);let T=me(a);return{hasMiniSchema:s,hasScopeBrief:r,llmRounds:o,toolCalls:c,avgRoundSec:x,edges:T}}function he(e){return e==null||!Number.isFinite(e)?"\u2014":e<.01?`${(e*1e3).toFixed(0)}ms`:e<10?`${e.toFixed(2)}s`:`${e.toFixed(1)}s`}function ge(e){let n=fe(e),t={mini:"MINI-SCHEMA section present in system / catalog inject",brief:"SCOPE BRIEF section present in system / catalog inject",rounds:"Upstream LLM completion rounds this turn",tools:"Total Zeus tool invocations this turn",avg:"Wall time \xF7 LLM rounds (seconds)",edges:"edges_total parsed from SCOPE BRIEF (scope inventory, not this-turn graph rows)"},a=(o,c,p)=>`<div class="tc-km" title="${v(p)}"><div class="tc-km-l">${v(o)}<span class="tc-km-q" aria-hidden="true">?</span></div><div class="tc-km-v">${v(String(c))}</div></div>`,s=n.edges!=null?Number(n.edges).toLocaleString("en-US"):"\u2014",r=document.createElement("div");return r.className="tc-kpi-mini",r.setAttribute("aria-label","Turn inject and shape stats"),r.innerHTML=a("MINI-SCHEMA",n.hasMiniSchema?"Yes":"No",t.mini)+a("SCOPE BRIEF",n.hasScopeBrief?"Yes":"No",t.brief)+a("LLM Rounds",String(n.llmRounds),t.rounds)+a("Tool Calls",String(n.toolCalls),t.tools)+a("Avg / round",he(n.avgRoundSec),t.avg)+a("Edges",s,t.edges),r}function be(){let e=l("trace-total-wrapper");if(!w.length){e.style.display="none";return}let n=w.reduce((a,s)=>({total:a.total+s.total,aiMs:a.aiMs+s.aiMs,zeusMs:a.zeusMs+s.zeusMs,other:a.other+s.other,tokens:a.tokens+s.tokens,tokensIn:a.tokensIn+s.tokensIn,tokensOut:a.tokensOut+s.tokensOut,hasTokens:a.hasTokens||s.hasTokens,hasIn:a.hasIn||s.hasIn,hasOut:a.hasOut||s.hasOut,bytes:a.bytes+s.bytes}),{total:0,aiMs:0,zeusMs:0,other:0,bytes:0,tokens:0,tokensIn:0,tokensOut:0,hasTokens:!1,hasIn:!1,hasOut:!1}),t=n.total||1;e.style.display="block",e.innerHTML=de(n)+`<div id="trace-total" class="trace-total" style="display:flex;align-items:center;justify-content:center;"><span class="tt-label">TOTAL \xB7 ${w.length} turn${w.length===1?"":"s"}</span><span class="mm-bar"><i class="mm-ai" style="width:${(n.aiMs/t*100).toFixed(1)}%"></i><i class="mm-zeus" style="width:${(n.zeusMs/t*100).toFixed(1)}%"></i><i class="mm-other" style="width:${(n.other/t*100).toFixed(1)}%"></i></span><span class="mm-total">${E(n.total)}</span></div>`}function K(e,n,t){let a=t?.pipeline_step_costs;if(!a?.length)try{a=JSON.parse(t?.result_full||t?.result||"{}")?.meta?.step_costs}catch{a=null}if(!Array.isArray(a)||!a.length)return null;let s={};(t?.args?.steps||t?.pipeline_json?.steps||[]).forEach(c=>{c?.name&&(s[c.name]=c.verb||"")});let r=[],o=0;return a.forEach(c=>{let p=c.as||c.name||"step",m=s[p]||"";r.push({name:`pipeline.${p}`+(m?`.${m}`:""),cls:"tool",at:(e||0)+o,ms:c.ms||0,detail:c.status||null,pipeline:!0}),o+=c.ms||0}),r}function ve(e,n){let t=(n||[]).filter(r=>r.type==="tool"&&r.name==="pipeline"),a=0,s=[];return(e||[]).forEach(r=>{if(r.name!=="tool.pipeline"){s.push(r);return}let o=K(r.at,r.ms,t[a++]);o?s.push(...o):s.push(r)}),s}function xe(e,n,t){let a=ve(e,t);if(!a.length)return"";let s=n||a.reduce((o,c)=>Math.max(o,(c.at||0)+(c.ms||0)),0)||1,r='<div class="trace-waterfall">';return a.forEach(o=>{let c=Math.max(0,Math.min(100,(o.at||0)/s*100)),p=Math.max(.5,Math.min(100-c,(o.ms||0)/s*100)),m=o.pipeline?"tw-lab tw-lab-pipeline":"tw-lab";r+=`<div class="${m}" title="${v(o.name)}">${v(o.name)}</div><div class="tw-track"><i class="${o.cls}" style="left:${c.toFixed(2)}%;width:${p.toFixed(2)}%"></i></div><div class="tw-dur">${o.ms||0} ms</div>`}),r+="</div>",r}function ye(e){let n={},t={},a=(s,r)=>{n[s]=(n[s]||0)+1;let o=r?.status;(o===0||typeof o=="number"&&o>=400)&&(t[s]=(t[s]||0)+1)};return(e||[]).forEach(s=>{if(s.type==="tool"){if(s.name==="pipeline"){(s.args?.steps||s.pipeline_json?.steps||[]).forEach(r=>{r?.verb&&a(r.verb,s)});return}a(s.name||"?",s)}}),{counts:n,errs:t}}function we(e,n){let{counts:t,errs:a}=ye(e),s=Object.keys(t);if(!s.length)return"";let r=W(n),o=u[r]||[],c=new Set(o),p=o.slice();s.forEach(h=>{c.has(h)||p.push(h)});let m=0;p.forEach(h=>{m=Math.max(m,t[h]||0)});let x=78,T="",b="";return p.forEach(h=>{let k=t[h]||0,Ae=m>0&&k>0?Math.max(2,Math.round(k/m*x)):0,Me=a[h]?"b err":c.has(h)?"b":"b unknown";T+=`<div class="vbar-col"><div class="${k>0?"n":"n zero"}">${k>0?k:""}</div><div class="${Me}" style="height:${Ae}px"></div></div>`,b+=`<div class="${k>0?"l":"l zero"}">${v(h)}</div>`}),`<div class="trace-vbar mt-3"><h3 class="trace-vbar-title">Tool-call frequency</h3><div class="vbar-wrap">${T}</div><div class="vbar-labels">${b}</div></div>`}function ke(e){let n=[];return(e.notes||[]).forEach(t=>n.push("\u2022 "+t)),(e.steps||[]).forEach(t=>{let a=t.round!=null?t.round:"?";if(t.type==="llm"){let s=t.usage||{},r=s.total_tokens?`  tok=${s.total_tokens} (in ${s.prompt_tokens||"?"}/out ${s.completion_tokens||"?"})`:"";n.push(`[r${a}] LLM ${t.ms||0}ms \u2192 ${t.finish_reason||""}  calls=[${(t.tool_calls||[]).join(", ")}]${r}`)}else if(t.type==="tool")if(t.name==="pipeline"){let s=K(0,t.ms,t);n.push(`[r${a}] PIPELINE ${t.ms||0}ms \u2192 ${t.status} ${P(t.bytes||0)}`),s&&s.forEach(r=>{n.push(`  \xB7 ${r.name} ${r.ms||0}ms${r.detail!=null?" \u2192 "+r.detail:""}`)})}else n.push(`[r${a}] TOOL ${t.name} \u2192 ${t.status} ${t.ms||0}ms`);else t.type==="llm_error"&&n.push(`[r${a}] LLM_ERROR ${t.ms||0}ms ${t.detail||""}`)}),!n.some(t=>t.startsWith("[r"))&&(e.tool_calls||[]).length&&(e.tool_calls||[]).forEach(t=>{let a=t.round!=null?t.round:"?";n.push(`[r${a}] TOOL ${t.name||"?"} \u2192 ${t.status} ${t.ms||0}ms`)}),n.join(`
`)}function Q(e){try{return JSON.stringify(e,null,2)}catch{return String(e)}}async function _e(e,n,t){try{let a=await se(),s=new a(n,{showType:!0,collapsed:!t,maxDepth:1/0});e.appendChild(s.getElement())}catch{let a=document.createElement("pre");a.className="trace-pre",a.textContent=Q(n),e.appendChild(a)}}function Te(e,n,t,a=!1){let s=document.createElement("div");s.className="collapse collapse-plus trace-dump bg-base-200 rounded border border-base-300";let r=document.createElement("input");r.type="checkbox",r.setAttribute("aria-label",n),a&&(r.checked=!0);let o=document.createElement("div");o.className="collapse-title text-xs font-bold py-2 min-h-0",o.textContent=n;let c=document.createElement("div");c.className="collapse-content";let p=document.createElement("pre");p.className="trace-pre bg-base-300 rounded p-2 mt-1",p.textContent=t,c.appendChild(p),s.append(r,o,c),e.appendChild(s)}async function A(e,n,t,a){let s=document.createElement("div");s.className="collapse collapse-plus trace-dump bg-base-200 rounded border border-base-300";let r=document.createElement("input");r.type="checkbox",r.setAttribute("aria-label",n),a&&(r.checked=!0);let o=document.createElement("div");o.className="collapse-title text-xs font-bold py-2 min-h-0",o.textContent=n;let c=document.createElement("div");c.className="collapse-content";let p=document.createElement("div");p.className="trace-dump-viewer",c.appendChild(p),s.append(r,o,c),e.appendChild(s),await _e(p,t,a)}function X(e){let n=Array.isArray(e)?e.length:Number(e)||0;return`${n} round${n===1?"":"s"}`}async function $e(e,n,t,a){let s=document.createElement("div");s.className="trace-dump-wrap",e.appendChild(s);let r=a.ai_requests||[],o=a.ai_responses||[],c=a.tool_calls||[];await Promise.all([A(s,`AI requests \xB7 ${X(r)}`,r),A(s,`AI responses \xB7 ${X(o)}`,o),A(s,`Tool calls \xB7 ${c.length}`,c,c.length>0),A(s,"Raw turn bundle",{question:n,answer:t.answer,target:t.target,api_version:t.api_version||a.api_version,session_id:t.session_id,session_round:t.session_round,contract_status:t.contract_status,trace:a})])}function Ee(e,n){let t=n.trace;if(!t)return;Z(n.tool_order),L=n.chat_id||L;let a=le(n);a&&(D=a,q(a)),g.includes(n)||g.push(n);let s=l("trace-list"),r=l("trace-empty");r&&r.remove(),y++;let o=document.createElement("div");o.className="trace-card";let c=document.createElement("div");c.className="trace-card-head",c.innerHTML=`<span class="tc-n">#${y}</span><span class="tc-q" title="${v(e)}">${v(e)}</span><span class="tc-meta">${v(W(n.api_version||t.api_version).toUpperCase())} \xB7 ${v(n.target||"")} \xB7 ${t.rounds||0} rounds</span>`+(J(n,t)?`<span class="tc-badges">${J(n,t)}</span>`:""),o.appendChild(c),o.appendChild(ge(t)),o.appendChild(pe(t));let p=document.createElement("div");p.innerHTML=xe(t.spans,t.total_ms,t.steps),p.firstChild&&o.appendChild(p.firstChild);let m=document.createElement("div");m.innerHTML=we(t.steps,n.api_version||t.api_version||"v2"),m.firstChild&&o.appendChild(m.firstChild);let x=ke(t);for(x&&Te(o,"Hash Traces",x),$e(o,e,n,t),s.prepend(o),w.push(V(t));s.children.length>12;)s.removeChild(s.lastChild),w.shift();be()}l("debug-toggle")?.addEventListener("click",ie),l("debug-close")?.addEventListener("click",N),l("trace-copy-full")?.addEventListener("click",()=>{let e=g.slice(-12);if(!e.length){j("No trace to copy yet","warning");return}navigator.clipboard.writeText(Q({chat_id:L,traces:e})).then(()=>j("Trace copied"))}),q(D);let z=l("debug-panel-version");if(z){let e=M();z.textContent=e.startsWith("v")?e:`v${e}`,z.setAttribute("title",`zeus_client_chat_trace ${e}`)}let Se=ce();return{appendTraceCard:Ee,openDebugPanel:H,closeDebugPanel:N,setToolOrder:Z,readyToolOrder:Se,version:M()}}var re=`<button
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
        title="Open Hub Detective for this session"
        hidden
      >Detective \u2197</a>
    </div>
    <div class="flex gap-2">
      <button type="button" id="trace-copy-full" class="btn btn-xs btn-ghost">Copy all</button>
      <button type="button" id="debug-close" class="btn btn-xs btn-ghost" aria-label="Close">\xD7</button>
    </div>
  </header>
  <div id="trace-total-wrapper" style="display:none"></div>
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
`;var oe=`/* Trace widget layout \u2014 DaisyUI handles btn/badge/alert/collapse */

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

#tokens-total .stats .stat .stat-value {
  font-size: 1.81rem;
  line-height: 1.81rem;
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

/* Detective-style mini KPI grid under card head (inject + turn shape). */
.tc-kpi-mini {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 10px;
  margin: 0 0 8px;
}
.tc-kpi-mini .tc-km {
  cursor: help;
  padding: 6px 8px;
  border-radius: 6px;
  background: hsl(var(--b1));
  border: 1px solid hsl(var(--bc) / 0.14);
  min-width: 0;
}
.tc-kpi-mini .tc-km-l {
  font: 9px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
  color: hsl(var(--bc) / 0.55);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 4px;
}
.tc-kpi-mini .tc-km-q {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font: 700 9px/1 sans-serif;
  border: 1px solid #93c5fd;
  flex-shrink: 0;
}
.tc-kpi-mini .tc-km:hover .tc-km-q {
  background: #2563eb;
  color: #fff;
  border-color: #1d4ed8;
}
.tc-kpi-mini .tc-km-v {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.25rem;
  min-height: 1.75rem;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font: 600 12px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
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
}`;G(document.currentScript);var Fe="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css",S=[],U=!1;function Re(){return{appendTraceCard(){},openDebugPanel(){}}}function Ue(){U||(window.appendTraceCard=(...i)=>S.push({type:"card",args:i}),window.openDebugPanel=()=>S.push({type:"open"}))}function De(i){for(let d of S)d.type==="open"?i.openDebugPanel():d.type==="card"&&i.appendTraceCard(...d.args);S.length=0}function He(){let i=C();if(!i.enabled){let w=Re();return window.appendTraceCard=w.appendTraceCard,window.openDebugPanel=w.openDebugPanel,S.length=0,U=!0,{api:w,config:i}}let d=document.createElement("div");d.id="zeus-trace-host",d.style.cssText="all:initial;position:fixed;inset:0;z-index:99999;pointer-events:none;",document.body.appendChild(d);let l=d.attachShadow({mode:"open"}),f=document.createElement("link");f.rel="stylesheet",f.href=Fe;let u=document.createElement("style");u.textContent=oe;let g=document.createElement("div");g.className="zeus-trace-root",g.setAttribute("data-theme","light"),g.style.pointerEvents="auto",g.innerHTML=re,l.append(f,u,g);let y=ae(g,i);return window.appendTraceCard=y.appendTraceCard,window.openDebugPanel=y.openDebugPanel,De(y),U=!0,{api:y,config:i}}Ue();var je=new Promise(i=>{let d=()=>{try{let{api:l,config:f}=He();i({api:l,config:f})}catch(l){console.error("[ZeusTrace] Failed to mount widget:",l),i({api:null,config:null,error:l})}};document.body?d():document.addEventListener("DOMContentLoaded",d)});window.ZeusTrace={ready:je,get config(){return F(C())},get version(){return F(C()).version}};})();
//# sourceMappingURL=zeus_client_chat_trace.js.map
