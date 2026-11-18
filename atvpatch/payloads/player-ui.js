// Original UI bridge code: no vendor player implementation is distributed here.
let localHudOwner = null;
function localHudPost(state) {
  try {
    const body = JSON.stringify(Object.assign({ time: Date.now() }, state));
    const request = require("http").request({ hostname: "127.0.0.1", port: 18767, path: "/ui", method: "POST", headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) } }, response => response.resume());
    request.on("error", () => {});
    request.setTimeout(700, () => request.destroy());
    request.end(body);
  } catch (error) {}
}
function localHudSend(page) {
  if (localHudOwner !== page) return;
  const active = !page.disposed && page.isPageTopmost();
  localHudPost({ playbackPage: !!active, controlsVisible: !!(active && page.isUnifiedPlayerVisible) });
}
function localHudObservePage(page) {
  const appear = () => { localHudOwner = page; localHudSend(page); };
  const leave = () => {
    if (localHudOwner === page) { localHudOwner = null; localHudPost({ playbackPage: false, controlsVisible: false }); }
  };
  page.on("pageDidAppear", appear);
  page.on("pageWillDisappear", leave);
  const heartbeat = setInterval(() => localHudSend(page), 1000);
  page.on("dispose", () => { clearInterval(heartbeat); leave(); });
}
function localHudDirectionalRepeat(widget, direction, action, down, up) {
  if (action === down) {
    const now = Date.now(), same = widget._localHeldDirection === direction;
    if (same && now - widget._localHeldDownAt < 1500) { widget._localHeldDownAt = now; return true; }
    if (widget._localHeldDirection !== undefined) {
      clearTimeout(widget.longpressTimeout);
      widget.longpressTimeout = undefined;
    }
    widget._localHeldDirection = direction; widget._localHeldDownAt = now;
  } else if (action === up && widget._localHeldDirection === direction) {
    widget._localHeldDirection = undefined;
  }
  return false;
}

function localHudTraceHold(widget, action, down, up, reader, nativeLongAllowed) {
  widget._localHoldTraceCount = (widget._localHoldTraceCount || 0) + 1;
  if (widget._localHoldTraceCount <= 40) console.log("[LocalHoldInput] " + JSON.stringify({ time: Date.now(), phase: action === down ? 0 : action === up ? 1 : 2, reader: !!reader, nativeLongAllowed: !!nativeLongAllowed }));
}
