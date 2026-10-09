const $ = (selector) => document.querySelector(selector);
const labels = {profile_agent:'Profile extraction',clarification_agent:'Follow-up question',recommender_agent:'Reference retrieval',checker_agent:'Knowledge graph review',final_responder:'Response routing',tool_node:'Regional stock lookup',final_response_generator:'Final response'};
const state = {mode:'demo',scenario:'consultation',turn:0,session:null,busy:false,complete:false,profile:{},candidates:[],checker_feedback:null,steps:[],history:[],examples:{},live:false};
const node = (tag, className, text) => {const el=document.createElement(tag); if(className)el.className=className;if(text!==undefined)el.textContent=text;return el;};
function renderMessage(role,text){const message=node('article',`message ${role}`);message.append(node('span','avatar',role==='user'?'YOU':'✚'));const body=node('div','message-body');body.append(node('div','message-name',role==='user'?'You':'Pharmacy Assistant'),node('p','message-content',text));message.append(body);$('#messages').append(message);}
function render(){
  $('#messages').replaceChildren();
  if(!state.history.length){renderMessage('assistant',state.mode==='demo'?'Welcome to the consultation workspace. Explore how specialized agents gather context, retrieve product references and review a pharmacy enquiry.':'Hello. Tell me about your pharmacy enquiry, your age and any relevant health background.');const welcome=node('div','welcome-card');welcome.append(node('h3','',state.mode==='demo'?'A conversation, step by step.':'Start with your context.'),node('p','',state.mode==='demo'?'Choose an example above, then continue through the conversation. The context and workflow panels update with each step.':'Your messages run through the configured LangGraph workflow. Results and the executed stages appear alongside the conversation.'));$('#messages').append(welcome);}
  state.history.forEach(m=>renderMessage(m.role,m.text));
  $('#profile').replaceChildren();
  for(const [key,label] of Object.entries({age:'Age',condition:'Enquiry',health_background:'Background',region:'Region'})){const row=node('div');row.append(node('dt','',label),node('dd','',key==='region'?({'港岛':'Hong Kong Island','九龙':'Kowloon','新界':'New Territories'}[state.profile[key]]||state.profile[key]||'Awaiting context'):(state.profile[key]||'Awaiting context')));$('#profile').append(row);}
  $('#review').replaceChildren();
  if(!state.candidates.length&&!state.checker_feedback)$('#review').append(node('p','empty','Reference candidates and review notes appear as the conversation develops.'));
  state.candidates.forEach(c=>{const card=node('div','candidate',c.drug_name);card.append(node('small','',c.reason));$('#review').append(card);});
  if(state.checker_feedback)$('#review').append(node('div',`review-status ${state.checker_feedback.is_safe?'':'caution'}`,state.checker_feedback.conclusion));
  $('#trace').replaceChildren();
  const steps=state.steps.length?state.steps:['profile_agent','recommender_agent','checker_agent','tool_node'];
  steps.forEach(s=>$('#trace').append(node('li',state.steps.length?'done':'',labels[s]||s)));
  $('#trace-description').textContent=state.mode==='demo'?'Illustrated stages in this guided example':'Executed nodes in the latest API response';
  $('#demo-controls').hidden=state.mode!=='demo';$('#next-step').hidden=state.mode!=='demo';
  const total=state.examples[state.scenario]?.length||0;
  $('#demo-progress').textContent=`STEP ${state.turn} OF ${total}`;
  $('#next-step').textContent=state.complete?'Example complete ✓':state.turn?'Continue example →':'Start example →';$('#next-step').disabled=state.complete||!total;
  $('#conversation-state').textContent=state.busy?'Working through your enquiry…':state.complete?'Completed':state.history.length?'In progress':'Ready to begin';
  $('#query').disabled=state.mode==='demo'||state.busy||state.complete;$('#send').disabled=$('#query').disabled;
  $('#query').placeholder=state.mode==='demo'?'Use “Start example” to explore this conversation…':state.complete?'Start a new consultation to ask another question.':'Type your pharmacy enquiry…';
  $('#composer-note').textContent=state.mode==='demo'?'Curated example · product names retain their source spelling.':state.complete?'Consultation complete. Start a new consultation for another enquiry.':'Your conversation runs through the configured agents.';
  $('#mode-description').textContent=state.mode==='demo'?'Curated conversations · simulated inventory':'Connected agents · local references · simulated inventory';
  $('#demo-mode').classList.toggle('selected',state.mode==='demo');$('#live-mode').classList.toggle('selected',state.mode==='live');
  $('#reset').disabled=state.busy;$('#demo-mode').disabled=state.busy;$('#live-mode').disabled=!state.live||state.busy;
}
async function reset(){if(state.session){try{await fetch(`/sessions/${encodeURIComponent(state.session)}`,{method:'DELETE'});}catch{ /* A new ID also starts a fresh consultation. */ }}Object.assign(state,{turn:0,session:null,complete:false,profile:{},candidates:[],checker_feedback:null,steps:[],history:[]});$('#error').textContent='';$('#query').value='';render();}
$('#reset').addEventListener('click',reset);
$('#scenario').addEventListener('change',async e=>{state.scenario=e.target.value;await reset();});
$('#demo-mode').addEventListener('click',async()=>{if(state.mode!=='demo'){await reset();state.mode='demo';render();}});
$('#live-mode').addEventListener('click',async()=>{if(state.mode!=='live'){await reset();state.mode='live';render();$('#query').focus();}});
$('#next-step').addEventListener('click',()=>{const turn=state.examples[state.scenario][state.turn++];state.history.push({role:'user',text:turn.query},{role:'assistant',text:turn.reply});Object.assign(state,{profile:turn.profile||{},candidates:turn.candidates||[],checker_feedback:turn.checker_feedback||null,steps:turn.steps,complete:!!turn.session_complete});render();});
$('#chat-form').addEventListener('submit',async e=>{e.preventDefault();const query=$('#query').value.trim();if(!query||state.busy||state.complete||state.mode!=='live')return;state.busy=true;$('#error').textContent='';state.history.push({role:'user',text:query});render();try{const response=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query,session_id:state.session})});const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Please check your message and try again.');Object.assign(state,{session:data.session_id,profile:data.profile,candidates:data.candidates,checker_feedback:data.checker_feedback,steps:data.steps,complete:data.session_complete});state.history.push({role:'assistant',text:data.reply});$('#query').value='';}catch(error){state.history.pop();$('#error').textContent=error.message;}finally{state.busy=false;render();if(!state.complete)$('#query').focus();}});
$('#query').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('#chat-form').requestSubmit();}});
document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{const view=button.dataset.view;$('#consultation-view').hidden=view!=='consultation';$('#workflow-view').hidden=view!=='workflow';$('#page-name').textContent=view==='consultation'?'CONSULTATION':'KNOWLEDGE & WORKFLOW';document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b===button));window.scrollTo({top:0,left:0});}));
async function start(){try{const [statusResponse,demoResponse]=await Promise.all([fetch('/status'),fetch('demo.json')]);if(!statusResponse.ok||!demoResponse.ok)throw new Error('The workspace could not load. Refresh to retry.');const status=await statusResponse.json();state.examples=await demoResponse.json();state.live=status.live_chat;$('#server-status').textContent=state.live?'● Live API connected':'● Guided demo ready';render();}catch(error){$('#server-status').textContent='Connection unavailable';$('#error').textContent=error.message;}}
render();start();
