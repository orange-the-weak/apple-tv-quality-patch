"""14.3.1 hls transform. Anchors are checked before use."""
from pathlib import Path
from ...core import PatchError

PAYLOADS = Path(__file__).resolve().parents[2] / "payloads"

def patch_hls(hls_original, *, prefetch):
    abort_anchor = b'if(0===p||!Tf(m))return i;'
    if not hls_original.count(abort_anchor) == 1:
        raise PatchError('Patch anchor mismatch: hls_original.count(abort_anchor) == 1')
    hls_patched = hls_original.replace(abort_anchor, b'if(0===p||!Tf(m)||s.rootPlaylistEntity&&s.rootPlaylistEntity.manualMode)return i;')
    # Pause should fill toward the normal high watermark, not stop at the low playback threshold.
    pause_anchor = b'function Gg(e,t,i,r){let s=t;return r.stopStreaming?s=i:r.paused&&(s=e),s}'
    if hls_patched.count(pause_anchor) != 1:
        raise PatchError('Paused buffer watermark anchor mismatch')
    hls_patched = hls_patched.replace(pause_anchor,b'function Gg(e,t,i,r){return r.stopStreaming?i:t}')
    if prefetch:
        parallel_anchor = b'Ga(e,t,i,r){var s,l,'
        parallel_methods = b'localLoadWithPrefetch(e,frag,options){const result=this.Ga(e,!1,frag,options);try{this.localSchedulePrefetch(e,frag);}catch(err){console.log("[LocalParallel] schedule-skipped");}return result;}localSchedulePrefetch(e,current){if(current.mediaOptionType!==fs.Variant||current.iframe||current.part||this.$a[fs.Variant]||!e.rootPlaylistQuery.rootPlaylistEntity.manualMode)return;const details=this.getQueryForOption(current).mediaOptionDetails;if(!details||details.liveOrEvent)return;const list=details.fragments||[],index=list.findIndex(f=>f.mediaSeqNum===current.mediaSeqNum&&f.discoSeqNum===current.discoSeqNum),next=index>=0?list[index+1]:null;if(!next||next.part||next.duration>8||next.byteRangeOffset&&next.byteRangeOffset.end-next.byteRangeOffset.start>33554432)return;const id=Nh(next);if(this._localAhead&&this._localAhead.id===id)return;if(this._localAhead)this._localAhead.cache.unsubscribe();const record={id:id,ready:!1,cache:null},prefetchContext=Object.assign({},e,{_localPrefetchOnly:!0});record.cache=new vg(id,()=>this.Ga(prefetchContext,!0,next,void 0).pipe(Cn(()=>{record.ready=!0;console.log("[LocalParallel] ready seq="+next.mediaSeqNum);})),!0);this._localAhead=record;console.log("[LocalParallel] start seq="+next.mediaSeqNum);}Ga(e,t,i,r){if(!t&&this._localAhead&&this._localAhead.id===Nh(i)){const saved=this._localAhead;this._localAhead=null;console.log("[LocalParallel] hit ready="+saved.ready);return saved.cache.result$.pipe(an(()=>saved.cache.unsubscribe()),pr(()=>{console.log("[LocalParallel] fallback");return this.Ga(e,!1,i,r);}));}var s,l,'
        if not hls_patched.count(parallel_anchor) == 1:
            raise PatchError('Patch anchor mismatch: hls_patched.count(parallel_anchor) == 1')
        hls_patched = hls_patched.replace(parallel_anchor, parallel_methods)
        load_anchor = b'p=this.Ga(e,!1,u,r).pipe(On('
        if not hls_patched.count(load_anchor) == 1:
            raise PatchError('Patch anchor mismatch: hls_patched.count(load_anchor) == 1')
        hls_patched = hls_patched.replace(load_anchor, b'p=this.localLoadWithPrefetch(e,u,r).pipe(On(')
        clear_anchor = b'clear(e,t=!0,i=!0){this.$a.forEach('
        if not hls_patched.count(clear_anchor) == 1:
            raise PatchError('Patch anchor mismatch: hls_patched.count(clear_anchor) == 1')
        hls_patched = hls_patched.replace(clear_anchor, b'clear(e,t=!0,i=!0){if(this._localAhead){this._localAhead.cache.unsubscribe();this._localAhead=null;}this.$a.forEach(')
        prefetch_state_anchor = b'A="mediaSink"in e,w=new Oi('
        if not hls_patched.count(prefetch_state_anchor) == 1:
            raise PatchError('Patch anchor mismatch: hls_patched.count(prefetch_state_anchor) == 1')
        hls_patched = hls_patched.replace(prefetch_state_anchor, b'A="mediaSink"in e&&!e._localPrefetchOnly,w=new Oi(')
    return hls_patched
