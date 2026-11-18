const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
function sandbox(file) {
  let now = 10000, next = 1;
  const timers = new Map(), intervals = new Map(), posts = [];
  const context = { Buffer, console: {log() {}}, Date: {now: () => now},
    setTimeout: (fn, delay) => { const id = next++; timers.set(id, {fn, at: now + delay}); return id; },
    clearTimeout: id => timers.delete(id), setInterval: fn => {const id=next++;intervals.set(id,fn);return id;}, clearInterval: id => intervals.delete(id),
    require: () => ({request: () => ({on() {}, setTimeout() {}, end: body => posts.push(JSON.parse(body)), destroy() {}})}) };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../atvpatch/payloads',file),'utf8'),context);
  return {context,timers,posts,intervals,advance(ms) {now += ms; for(const [id,t] of [...timers])if(t.at<=now){timers.delete(id);t.fn();}}};
}
{
  const s=sandbox('player-ui.js'), c=s.context, widget={};
  assert.equal(c.localHudDirectionalRepeat(widget,'right',0,0,1),false);
  let held=0;widget.longpressTimeout=c.setTimeout(()=>{held++;widget.longpressTimeout=undefined;},1000);
  for(let i=0;i<12;i++){s.advance(100);assert.equal(c.localHudDirectionalRepeat(widget,'right',0,0,1),true);}
  assert.equal(held,1,'repeat DOWN must not starve the original hold timeout');
  assert.equal(c.localHudDirectionalRepeat(widget,'right',1,0,1),false);
  assert.equal(c.localHudDirectionalRepeat(widget,'right',0,0,1),false,'next gesture starts normally');
  widget.longpressTimeout=c.setTimeout(()=>{throw Error('old direction');},1000);
  assert.equal(c.localHudDirectionalRepeat(widget,'left',0,0,1),false);
  assert.equal(widget.longpressTimeout,undefined,'direction change cancels previous hold');
  s.advance(2000);assert.equal(c.localHudDirectionalRepeat(widget,'left',0,0,1),false,'a missing UP cannot permanently suppress later gestures');
}
{
  const s=sandbox('player-ui.js'), c=s.context;
  const page=()=>({handlers:{},disposed:false,top:true,isUnifiedPlayerVisible:false,on(name,fn){this.handlers[name]=fn;},isPageTopmost(){return this.top;}});
  const a=page();c.localHudObservePage(a);a.handlers.pageDidAppear();
  assert.equal(s.posts.at(-1).playbackPage,true);
  a.isUnifiedPlayerVisible=true;c.localHudSend(a);assert.equal(s.posts.at(-1).controlsVisible,true);
  a.handlers.pageWillDisappear();assert.equal(s.posts.at(-1).playbackPage,false);
  const b=page();c.localHudObservePage(b);b.handlers.pageDidAppear();
  const n=s.posts.length;c.localHudSend(a);a.handlers.dispose();assert.equal(s.posts.length,n,'old pages cannot hide a new owner');
  b.top=false;c.localHudSend(b);assert.equal(s.posts.at(-1).controlsVisible,false);
  b.handlers.dispose();assert.equal(s.intervals.size,0,'page disposal removes heartbeat');
}
{
  const s=sandbox('quality.js'), c=s.context, calls=[];
  const low={itemId:'item',mediaOptionId:'low',width:1084,height:542,bitrate:2000000};
  const high={itemId:'item',mediaOptionId:'high',width:3840,height:1920,bitrate:25000000};
  const iframe={itemId:'item',mediaOptionId:'iframe',width:7680,height:4320,bitrate:50000000,iframes:true};
  const query={enabledVariantMediaOption:low,rootPlaylistEntity:{manualMode:false}};
  const hls={activeRootPlaylistQuery:query,desiredRate:1,iframeMode:false,ol:{
    setManualMode(id,enabled){query.rootPlaylistEntity.manualMode=enabled;},
    setEnabledMediaOptionByType(id,type,target,immediate,options){calls.push({target,immediate,options});query.enabledVariantMediaOption=target;}
  }};
  const player={hls,configuredItem:{},mediaElement:{seeking:false}};
  c.localQualityInstall(player,[low,high,iframe]);s.advance(0);
  assert.equal(calls.length,1,'select after the manifest turn, not after 4 seconds');
  assert.equal(calls[0].target,high);assert.equal(calls[0].immediate,undefined);assert.equal(calls[0].options,undefined,'do not purge healthy buffers during a variant switch');
  s.advance(6000);query.enabledVariantMediaOption=low;hls.iframeMode=true;c.localQualityTick(player,false);assert.equal(calls.length,1);
  hls.iframeMode=false;hls.desiredRate=4;c.localQualityTick(player,false);assert.equal(calls.length,1);
  hls.desiredRate=1;c.localQualityTick(player,false);assert.equal(calls.length,2,'restore highest after exiting trickplay');
  c.localQualityTick(player,false);assert.equal(calls.length,2,'no redundant buffer switches');
  query.enabledVariantMediaOption=low;player.mediaElement.seeking=true;s.advance(6000);c.localQualityTick(player,false);assert.equal(calls.length,2);
  player.mediaElement.seeking=false;player.configuredItem={};c.localQualityTick(player,false);assert.equal(calls.length,2,'old timers cannot target a different item');
}
console.log('Payload tests passed: held-key repeats, UI ownership/lifecycle, early quality selection and post-trickplay restoration');
