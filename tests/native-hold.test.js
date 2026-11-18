// Execute patched native handlers from a temporary user-provided fixture, not a copied implementation.
const assert = require('node:assert/strict'), fs = require('node:fs'), vm = require('node:vm'), path = require('node:path');
const methods = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
for (const index of [0,1]) {
  function scenario(hold, repeatAction=0) {
    let now=10000,next=1;const timers=new Map(),seeks=[];let forwards=0;
    const p=()=>({Application:{KeyAction:{Down:0,Up:1}}});p.q={accessibility:{screenReader:{enabled:true}}};
    const c={Date:{now:()=>now},Buffer,console:{log(){}},require(){throw Error('not used');},
      setTimeout(fn,delay){const id=next++;timers.set(id,{fn,at:now+delay});return id;},clearTimeout(id){timers.delete(id);},
      a:{Application:{KeyAction:{Down:0,Up:1}}},p,m:{q:{accessibility:{screenReader:{enabled:true}}}},
      G:{K:{Config:{supportsScreenReaderDirectionalLongPress:()=>false}}},A:{y:{player:{paused:false,trickplayGear:0}}},ee:{Right:1,Left:0},r:{Right:1,Left:0}};
    vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(__dirname,'../atvpatch/payloads/player-ui.js'),'utf8'),c);
    const handler=vm.runInContext('('+methods[index]+')',c);
    const widget={config:{supportsScreenReaderDirectionalLongPress:false},state:{speed:1,hasThumbnails:false},trickplayGear:0,isDragging:false,
      trickplayPrewarm(){},animatePlus10Icon(){},cancel(){},fastForward(){forwards++;},rewind(){throw Error('wrong direction');},
      callbacks:{seek(delta){seeks.push(delta);}},playbackSession:{seek(delta){seeks.push(delta);},trickplayFastForward(){forwards++;}}};
    const advance=ms=>{now+=ms;for(const[id,t]of[...timers])if(t.at<=now){timers.delete(id);t.fn();}};
    handler.call(widget,1,0);
    if(hold){for(let i=0;i<30;i++){advance(100);handler.call(widget,1,repeatAction);}}
    else advance(200);
    handler.call(widget,1,1);
    if(hold){assert.equal(forwards,1,'reader mode must still enter native trickplay');assert.deepEqual(seeks,[],'long release must not become a short skip');}
    else{assert.equal(forwards,0);assert.deepEqual(seeks,[10],'short press remains ten seconds');}
  }
  scenario(false);scenario(true);scenario(true,2);
}
console.log('Actual patched native handlers passed: reader=true, native longpress support=false, short and repeated held keys');
