// Read-only buffer diagnostics. Values describe occupied bytes, observed peaks, and watermarks.
function localBufferMetrics(player) {
  const result = {};
  try {
    const hls=player.hls, media=hls && hls.bc;
    if(!media) return result;
    const monitor=media.bufferMonitorInfo || {}, tracks=media.sourceBufferEntities || [];
    result.bufferLowSeconds=monitor.lowWaterLevelSeconds;
    result.bufferHighSeconds=monitor.highWaterLevelSeconds;
    result.bufferMaxSeconds=monitor.maxBufferSeconds;
    result.streamStopped=!!media.stopStreaming;
    result.mediaPaused=!!media.paused;
    for(let index=0;index<2;index++) {
      const track=tracks[index]; if(!track) continue;
      const prefix=index===0?'video':'audio';
      result[prefix+'Bytes']=track.totalBytes;
      result[prefix+'PeakBytes']=track.maxTotalBytes;
      result[prefix+'QuotaSeen']=!!track.gotQuotaExceeded;
      result[prefix+'Segments']=(track.bufferedSegments || []).length;
    }
    const source=player.mediaElement && player.mediaElement.mediaSource;
    if(source) for(const buffer of source.sourceBuffers) {
      const prefix=buffer.mimeType && buffer.mimeType.indexOf('video/')===0?'video':buffer.mimeType && buffer.mimeType.indexOf('audio/')===0?'audio':null;
      if(!prefix) continue;
      result[prefix+'ConfiguredBytes']=buffer.maxBufferSize;
      if(buffer.buffered.length) result[prefix+'BehindSeconds']=Math.max(0,player.mediaElement.currentTime-buffer.buffered.start(0));
    }
    const ahead=hls.$u && hls.$u._localAhead;
    result.prefetchPending=!!ahead;
    result.prefetchReady=!!(ahead && ahead.ready);
  } catch(error) {}
  return result;
}
