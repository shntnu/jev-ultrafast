(() => {
  if (!document.body) return null;
  const cache = window.__jevFast ||= {ids:new WeakMap(), nodes:new Map(), next:1};
  const identity = e => {
    if (!cache.ids.has(e)) cache.ids.set(e,cache.next++);
    const id=cache.ids.get(e); cache.nodes.set(id,e); return id;
  };
  for (const [id,e] of cache.nodes) if (!e.isConnected) cache.nodes.delete(id);
  const safe = e => !['password','file','hidden'].includes(e.type);
  const visible = e => !e.closest('[aria-hidden="true"],[inert]') &&
    e.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
  const name = (e,seen=new Set()) => {
    if (!e || seen.has(e)) return '';
    seen.add(e);
    const referenced=(e.getAttribute('aria-labelledby')||'').split(/\s+/)
      .map(id=>name(document.getElementById(id),seen)).filter(Boolean).join(' ');
    return referenced || e.getAttribute('aria-label') ||
      [...(e.labels||[])].map(l=>name(l,seen)).filter(Boolean).join(' ') ||
      (['button','submit','reset'].includes(e.type) ? e.value : '') || e.getAttribute('alt') ||
      (e.tagName==='INPUT' ? '' : [...e.childNodes].map(n=>n.nodeType===3 ? n.textContent :
        n.nodeType===1 && n.getAttribute('aria-hidden')!=='true' ? name(n,seen) : '').join(' ').trim()) ||
      e.getAttribute('title') || e.getAttribute('placeholder') ||
      e.parentElement?.getAttribute('aria-label') || e.parentElement?.getAttribute('title') ||
      (e.matches('input') && e.id && !/^mui|^:/.test(e.id) ? e.id.replace(/[-_]/g,' ') : '') ||
      // Piximi's WithLabel uses a nearby Typography, not a native label element.
      (e.matches('input,[role="combobox"]') ? e.closest('.MuiFormControl-root')?.parentElement
        ?.querySelector(':scope > p,:scope > label')?.textContent?.trim() : '') ||
      (e.matches('button') ? e.parentElement?.querySelector(':scope > p')?.textContent?.trim() : '') || '';
  };
  const roles=['button','link','checkbox','radio','switch','tab','menuitem','menuitemradio',
    'option','gridcell','combobox','textbox','searchbox','spinbutton'];
  const selector='a[href],button,input,textarea,select,summary,[contenteditable="true"],'+
    roles.map(role=>'[role="'+role+'"]').join(',');
  const role = e => {
    const explicit=e.getAttribute('role');
    if (roles.includes(explicit)) return explicit;
    if (e.tagName==='BUTTON' || e.tagName==='SUMMARY') return 'button';
    if (e.tagName==='A') return 'link';
    if (e.tagName==='SELECT') return 'combobox';
    if (e.tagName==='TEXTAREA' || e.isContentEditable) return 'textbox';
    if (e.tagName==='INPUT') {
      if (['checkbox','radio'].includes(e.type)) return e.type;
      if (['button','submit','reset','image'].includes(e.type)) return 'button';
      if (e.type==='search') return 'searchbox';
      if (e.type==='number') return 'spinbutton';
      if (['text','email','url','tel'].includes(e.type)) return 'textbox';
    }
    return null;
  };
  cache.pageKey=()=>[performance.timeOrigin,location.href,scrollX,scrollY,innerWidth,innerHeight,
    [...document.querySelectorAll('input,textarea,select')].filter(safe)
      .map(e=>[identity(e),e.value,e.checked,e.selectedIndex,e.disabled,e.readOnly])];
  cache.guard=e=>{
    if (!e?.isConnected || !visible(e)) return null;
    const scope=e.closest('form,dialog,[role="dialog"],article,li,tr,[role="row"]') || e.parentElement;
    return [identity(e),role(e),name(e),e.value??null,e.checked??null,e.selectedIndex??null,
      e.readOnly??null,e.scrollTop,e.matches(':disabled'),e.getAttribute('aria-disabled'),
      e.getAttribute('aria-expanded'),e.getAttribute('aria-checked'),e.getAttribute('aria-selected'),
      e.getAttribute('href'),scope?.innerText?.slice(0,6000)||''];
  };
  const viewportRect = e => {
    const r=e.getBoundingClientRect();
    let left=Math.max(0,r.left), top=Math.max(0,r.top), right=Math.min(innerWidth,r.right), bottom=Math.min(innerHeight,r.bottom);
    for (let p=e.parentElement;p;p=p.parentElement) {
      const style=getComputedStyle(p), box=p.getBoundingClientRect();
      if (/auto|scroll|hidden|clip/.test(style.overflowY)) { top=Math.max(top,box.top); bottom=Math.min(bottom,box.bottom); }
      if (/auto|scroll|hidden|clip/.test(style.overflowX)) { left=Math.max(left,box.left); right=Math.min(right,box.right); }
    }
    return {x:left,y:top,w:right-left,h:bottom-top};
  };
  cache.rect=viewportRect;
  const actions=[];
  for (const e of document.querySelectorAll(selector)) {
    if (e.matches('a[href]') && new URL(e.href,location.href).origin!==location.origin) continue;
    if (!safe(e) || !visible(e) || e.matches(':disabled') || e.closest('[aria-disabled="true"]')) continue;
    const r=viewportRect(e), x=r.x+r.w/2, y=r.y+r.h/2, rname=role(e);
    if (!rname || r.w<=0 || r.h<=0 || !e.contains(document.elementFromPoint(x,y))) continue;
    if (rname==='gridcell' && e.querySelector('button,[role="button"]')) continue;
    const base={node:identity(e),role:rname,label:name(e)||rname,
      rect:r};
    for (const key of ['checked','selected','expanded']) {
      const value=e.getAttribute('aria-'+key);
      if (value!==null) base[key]=value;
    }
    if (['checkbox','radio'].includes(e.type)) base.checked=String(e.checked);
    if (e.tagName==='SELECT') {
      for (const o of e.options) if (!o.selected && !o.disabled && !o.closest('optgroup[disabled]'))
        actions.push({...base,kind:'select',value:o.value,
          current_value:[...e.selectedOptions].map(o=>o.label).join(', '),label:base.label+' -> '+o.label});
    } else {
      const editable=!e.readOnly && e.getAttribute('aria-readonly')!=='true' &&
        (['textbox','searchbox','spinbutton'].includes(rname) ||
          (rname==='combobox' && ['INPUT','TEXTAREA'].includes(e.tagName)));
      const value='value' in e ? String(e.value) :
        e.isContentEditable || rname==='combobox' ? e.innerText.trim() : '';
      actions.push({...base,kind:editable?'fill':'click',value});
      if (editable) actions.push({...base,kind:'click',value,label:'Open '+base.label});
    }
  }
  // Offer scroll operations for actual visible scroll containers, including dialogs.
  for (const e of document.querySelectorAll('body *')) {
    if (!visible(e) || !/auto|scroll/.test(getComputedStyle(e).overflowY) || e.scrollHeight<=e.clientHeight+2) continue;
    const r=viewportRect(e), x=r.x+r.w/2, y=r.y+r.h/2;
    if (r.w<40 || r.h<40 || !e.contains(document.elementFromPoint(x,y))) continue;
    const label=name(e).slice(0,80) || e.closest('[role="dialog"]')?.innerText.slice(0,60) || 'Piximi panel';
    const base={node:identity(e),role:'region',rect:r,value:String(Math.round(e.scrollTop))};
    if (e.scrollTop+e.clientHeight<e.scrollHeight-2)
      actions.push({...base,kind:'scroll',label:'Scroll down: '+label,delta:Math.min(440,e.clientHeight*0.7)});
    if (e.scrollTop>0) actions.push({...base,kind:'scroll',label:'Scroll up: '+label,delta:-Math.min(440,e.clientHeight*0.7)});
  }
  const words=[], walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  const range=document.createRange(); let node,length=0;
  while ((node=walker.nextNode()) && length<6000) {
    const value=node.textContent.trim(), parent=node.parentElement;
    if (!value || !parent || parent.closest('script,style,noscript,template') || !visible(parent)) continue;
    range.selectNodeContents(node); const r=range.getBoundingClientRect();
    if (r.width>0 && r.height>0 && r.bottom>0 && r.top<innerHeight && r.right>0 && r.left<innerWidth) {
      words.push(value); length+=value.length;
    }
  }
  const text=words.join('\n').slice(0,6000), height=document.documentElement.scrollHeight;
  const page_key=cache.pageKey(), guards={};
  for (const a of actions) if (!(a.node in guards)) guards[a.node]=cache.guard(cache.nodes.get(a.node));
  // Compare meaning and identity. Geometry is always resolved and hit-tested just before input.
  const semantics=actions.map(({rect,...action})=>action);
  const marker=[performance.timeOrigin,location.href,scrollX,scrollY,innerWidth,innerHeight,
    document.title,text,semantics,page_key[6]];
  const omitted_actions=Math.max(0,actions.length-250);
  actions.splice(250);
  actions.forEach((a,i)=>a.id='e'+(i+1));

  actions.push({id:'wait',kind:'wait',label:'Wait for the page to update'});
  const bodyText=document.body.innerText;
  const dialog=[...document.querySelectorAll('[role="dialog"]')].filter(visible).at(-1);
  const dialogText=dialog?.innerText || '';
  const progress=[...document.querySelectorAll('[role="progressbar"]')].filter(visible);
  const busy=/deserializing|Setting up training|Epoch \d+ of \d+/i.test(bodyText) || progress.length>0;
  const epochs=document.querySelector('input#epochs')?.value ?? null;
  const project=[...document.querySelectorAll('input')].find(e=>safe(e) && /example project/i.test(e.value))?.value || '';
  const metrics={};
  const evaluation=/Evaluation Result/.test(dialogText) && /Evaluation metrics/.test(dialogText);
  if (evaluation) {
    const lines=dialogText.split('\n').map(s=>s.trim()).filter(Boolean);
    for (const key of ['Accuracy','Cross entropy','Precision','Recall','F1-score']) {
      const i=lines.findIndex(line=>line.replace(/:$/, '')===key);
      if (i>=0 && lines[i+1]==='N/A') metrics[key]='N/A';
      else if (i>=0 && lines[i+1] && Number.isFinite(Number(lines[i+1]))) metrics[key]=Number(lines[i+1]);
    }
  }
  // Nivo renders one circle per epoch/series with a 2px border. Legend circles have no such border.
  const plotTitle=[...document.querySelectorAll('p')].find(e=>e.textContent==='Training History - Accuracy per Epoch');
  const points=plotTitle?.parentElement?.querySelectorAll('svg circle[stroke-width="2"]');
  const completed_epochs=points?.length ? points.length/2 : null;
  const piximi={editing_epochs:document.activeElement?.id==='epochs',url:location.href,project,epochs,completed_epochs,evaluation,metrics,busy,
    dialog:dialogText.slice(0,12000),status:busy ? bodyText.slice(0,200) : 'idle'};
  return {url:location.href,title:document.title,w:innerWidth,h:innerHeight,text,
    piximi,scroll:{y:scrollY,height},actions,marker,page_key,guards,omitted_actions};
})()
