"""14.3.1 worker transform. Anchors are checked before use."""
from pathlib import Path
from ...core import PatchError

PAYLOADS = Path(__file__).resolve().parents[2] / "payloads"

def patch_worker(original_worker, *, reclaim_video, video_buffer_mib):
    loop = b'for(let e=0;e<t.levels.length;++e){const i=t.levels[e];'
    old_force = b'this._envForcePlaybackLevel&&this._envForcePlaybackLevel===e&&this.setForcedLevel(i)'
    if not original_worker.count(loop) == 1:
        raise PatchError('Patch anchor mismatch: original_worker.count(loop) == 1')
    if not original_worker.count(old_force) == 1:
        raise PatchError('Patch anchor mismatch: original_worker.count(old_force) == 1')
    selection = b'const localHighest=t.levels.reduce((best,level,index)=>{const prev=t.levels[best];const pixels=(level.width||0)*(level.height||0),oldPixels=(prev.width||0)*(prev.height||0);return pixels>oldPixels||(pixels===oldPixels&&(level.bitrate||level.bandwidth||0)>(prev.bitrate||prev.bandwidth||0))?index:best},0);console.log("[LocalQualityTest] variants="+t.levels.length+" selected="+localHighest);t.levels.forEach((level,index)=>console.log("[LocalQualityLevel] "+JSON.stringify({index:index,width:level.width,height:level.height,bitrate:level.bitrate,bandwidth:level.bandwidth,frameRate:level.frameRate,codec:level.videoCodec,range:level.videoRange})));'
    telemetry = b'if(this._localQualityTimer)clearInterval(this._localQualityTimer);const localHlsInstance=this.hls;this._localQualityTimer=setInterval(()=>{if(this.hls!==localHlsInstance){clearInterval(this._localQualityTimer);return}try{const d=this.state.debug||{},body=JSON.stringify({time:Date.now(),bufferSeconds:(()=>{const m=this.hls.bc;if(!m)return;const b=m.getCombinedBufferInfo(m.currentTime,.5);return b?Math.max(0,b.len):void 0;})(),videoBufferSeconds:this.hls.bc?this.hls.bc.getCurrentWaterLevelByType(0,.5):void 0,audioBufferSeconds:this.hls.bc?this.hls.bc.getCurrentWaterLevelByType(1,.5):void 0,buffering:this.state.buffering,width:this.state.width,height:this.state.height,bitrate:d.bitrateAverage,peak:d.bitratePeak,frameRate:d.frameRate,codec:this.state.videoCodec,range:this.state.videoRange,level:d.level});const req=require("http").request({hostname:"127.0.0.1",port:18767,path:"/format",method:"POST",headers:{"Content-Type":"application/json","Content-Length":Buffer.byteLength(body)}},res=>res.resume());req.on("error",()=>{});req.setTimeout(700,()=>req.destroy());req.end(body)}catch(err){}},3000);'
    supported_force = b'localQualityInstall(this,t.levels);'
    marker = b'const d=this.state.debug||{},body='
    trace = b'const d=this.state.debug||{};this._localTraceCount=(this._localTraceCount||0)+1;if(this._localTraceCount%5===0){const q=this.hls.activeRootPlaylistQuery;console.log("[LocalRuntime] "+JSON.stringify({bitrate:d.bitrateAverage,position:this.hls.realCurrentTime,bufferAheadSeconds:(()=>{const m=this.hls.bc;if(!m)return;const b=m.getCombinedBufferInfo(m.currentTime,.5);return b?Math.max(0,b.len):void 0;})(),bufferTotalSeconds:this.hls.bufferedDuration,videoBufferSeconds:this.hls.bc?this.hls.bc.getCurrentWaterLevelByType(0,.5):void 0,audioBufferSeconds:this.hls.bc?this.hls.bc.getCurrentWaterLevelByType(1,.5):void 0,buffering:this.state.buffering,manual:q&&q.rootPlaylistEntity&&q.rootPlaylistEntity.manualMode}));}const body='
    reclaim = b'try{const me=this.mediaElement,q=this.hls.activeRootPlaylistQuery,now=Date.now();if(me&&me.mediaSource&&!me.seeking&&q&&q.rootPlaylistEntity.manualMode&&d.bitrateAverage>=20000000&&now-(this._localLastTrim||0)>6000){const pos=me.currentTime;for(const sb of me.mediaSource.sourceBuffers){if(sb.mimeType&&sb.mimeType.indexOf("video/")===0&&!sb.updating&&sb.buffered.length&&pos-sb.buffered.start(0)>18){sb.remove(0,pos-12);this._localLastTrim=now;console.log("[LocalBufferTrim] keepBehindSeconds=12");break;}}}}catch(err){console.log("[LocalBufferTrim] skipped");}'
    if reclaim_video:
        trace = trace.replace(b'const d=this.state.debug||{};', b'const d=this.state.debug||{};' + reclaim)
    if not telemetry.count(marker) == 1:
        raise PatchError('Patch anchor mismatch: telemetry.count(marker) == 1')
    telemetry = telemetry.replace(marker, trace)
    telemetry = telemetry.replace(b'const d=this.state.debug||{};',b'localQualityTick(this,false);const d=this.state.debug||{};',1)
    telemetry = telemetry.replace(b'time:Date.now(),bufferSeconds:',b'time:Date.now(),position:this.hls.realCurrentTime,desiredRate:this.hls.desiredRate,iframeMode:this.hls.iframeMode,selectedBitrate:this.hls.activeRootPlaylistQuery&&this.hls.activeRootPlaylistQuery.enabledVariantMediaOption&&this.hls.activeRootPlaylistQuery.enabledVariantMediaOption.bitrate,targetBitrate:this._localQualitySelection&&this._localQualitySelection.target&&this._localQualitySelection.target.bitrate,bufferSeconds:')
    telemetry = telemetry.replace(b'body=JSON.stringify({',b'body=JSON.stringify(Object.assign({')
    telemetry = telemetry.replace(b'level:d.level});',b'level:d.level},localBufferMetrics(this)));')
    selection += supported_force + telemetry
    patched_worker = original_worker.replace(loop, selection + loop)
    patched_worker = b'\"use strict\";' + (PAYLOADS / 'quality.js').read_bytes() + b'\n' + (PAYLOADS / 'buffer-metrics.js').read_bytes() + b'\n' + patched_worker
    rate_anchor = b'async configureHls(e){var t,i,n,a,l,u,d;'
    if not patched_worker.count(rate_anchor) == 1:
        raise PatchError('Patch anchor mismatch: patched_worker.count(rate_anchor) == 1')
    patched_worker = patched_worker.replace(rate_anchor, rate_anchor + b'this._envPeakBitRate=100000000;this._envAverageBitRate=100000000;this._envAbrBandWidthFactor=1;this._envAbrBandWidthUpFactor=1;console.log("[LocalQualityPolicy] adaptive-high peak=100000000 average=100000000 abr=1 manual=delayed");')
    allocation_anchor = b'this.lunaSourceBuffer=new s.Media.SourceBuffer(t,this.maxBufferSize)'
    if not patched_worker.count(allocation_anchor) == 1:
        raise PatchError('Patch anchor mismatch: patched_worker.count(allocation_anchor) == 1')
    buffer_override = (b'this.maxBufferSize=(r.type==="video"?Math.max(this.maxBufferSize,' + str(video_buffer_mib*1024*1024).encode() + b'):this.maxBufferSize),') if video_buffer_mib else b''
    patched_worker = patched_worker.replace(allocation_anchor, b'this.lunaSourceBuffer=(' + buffer_override + b'console.log("[LocalBufferAlloc] type="+r.type+" bytes="+this.maxBufferSize),new s.Media.SourceBuffer(t,this.maxBufferSize))')
    return patched_worker
