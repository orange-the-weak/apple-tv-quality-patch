// Version-pinned player support. This file contains original patch code only.
function localQualityHighest(levels) {
  return levels.filter(level => !level.iframes && !level.iframesOnly && !level.iframe).reduce((best, level) => {
    if (!best) return level;
    const pixels = (level.width || 0) * (level.height || 0);
    const bestPixels = (best.width || 0) * (best.height || 0);
    return pixels > bestPixels || (pixels === bestPixels && (level.bitrate || level.bandwidth || 0) > (best.bitrate || best.bandwidth || 0)) ? level : best;
  }, null);
}
function localQualityInstall(player, levels) {
  if (player._localForceTimer) clearTimeout(player._localForceTimer);
  player._localQualitySelection = { hls: player.hls, item: player.configuredItem, target: localQualityHighest(levels), lastAttempt: 0, attempted: false };
  // Yield until the manifest handler finishes, rather than buffering low quality for four seconds.
  player._localForceTimer = setTimeout(() => localQualityTick(player, true), 0);
}
function localQualityTick(player, initial) {
  const selection = player._localQualitySelection;
  if (!selection || !selection.target || player.hls !== selection.hls || player.configuredItem !== selection.item) return;
  const hls = player.hls, target = selection.target, query = hls.activeRootPlaylistQuery, api = hls.ol;
  if (!query || !query.rootPlaylistEntity || !api || typeof api.setManualMode !== "function" || typeof api.setEnabledMediaOptionByType !== "function") return;
  // Never fight the player's iframe/trickplay selection, paused seeking, or item transitions.
  if (hls.iframeMode || (typeof hls.desiredRate === "number" && hls.desiredRate !== 0 && hls.desiredRate !== 1)) return;
  if (!initial && (hls.desiredRate !== 1 || player.mediaElement && player.mediaElement.seeking)) return;
  const enabled = query.enabledVariantMediaOption;
  if (enabled && enabled.mediaOptionId === target.mediaOptionId) {
    if (!query.rootPlaylistEntity.manualMode) api.setManualMode(target.itemId, true);
    return;
  }
  const now = Date.now();
  if (selection.attempted && now - selection.lastAttempt < 5000) return;
  selection.lastAttempt = now; selection.attempted = true;
  try {
    api.setManualMode(target.itemId, true);
    // Preserve the working seamless path; forced immediate purges can create PTS gaps on this platform.
    api.setEnabledMediaOptionByType(target.itemId, 0, target);
    console.log("[LocalQualityRestore] " + JSON.stringify({ targetBitrate: target.bitrate || target.bandwidth, selectedBitrate: enabled && (enabled.bitrate || enabled.bandwidth), initial: !!initial }));
  } catch (error) {
    api.setManualMode(target.itemId, false);
    console.log("[LocalQualityRestore] failed");
  }
}
