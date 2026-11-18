"""14.3.1 player transform. Anchors are checked before use."""
from pathlib import Path
from ...core import PatchError

PAYLOADS = Path(__file__).resolve().parents[2] / "payloads"

def patch_player(player_page):
    replacements = {
        b'this.store=e,this.pageType="type/playerPage"': b'this.store=e,this.pageType="type/playerPage",localHudObservePage(this)',
        b'visibility:e=>{this.isUnifiedPlayerVisible=e,': b'visibility:e=>{this.isUnifiedPlayerVisible=e,localHudSend(this),',
        b'keyHandlingSeekOrTrickplay(e,t){var i,s,n,o,r,l,d,c;': b'keyHandlingSeekOrTrickplay(e,t){localHudTraceHold(this,t,a.Application.KeyAction.Down,a.Application.KeyAction.Up,p.q.accessibility.screenReader.enabled,G.K.Config.supportsScreenReaderDirectionalLongPress());if(localHudDirectionalRepeat(this,e,t,a.Application.KeyAction.Down,a.Application.KeyAction.Up))return!0;var i,s,n,o,r,l,d,c;',
        b'keyHandlingSeekOrTrickplay(e,t){var i,a,s,n,o,l,d,c;': b'keyHandlingSeekOrTrickplay(e,t){localHudTraceHold(this,t,p().Application.KeyAction.Down,p().Application.KeyAction.Up,m.q.accessibility.screenReader.enabled,this.config.supportsScreenReaderDirectionalLongPress);if(localHudDirectionalRepeat(this,e,t,p().Application.KeyAction.Down,p().Application.KeyAction.Up))return!0;var i,a,s,n,o,l,d,c;',
    }
    for before, after in replacements.items():
        if player_page.count(before) != 1:
            raise PatchError('Player UI anchor mismatch')
        player_page = player_page.replace(before, after)
    # Keep native one-second hold/release behavior even when this platform reports accessibility enabled.
    # Do not alter screen-reader state, focus navigation, or global platform settings.
    for before, after in {
        b'if(!p.q.accessibility.screenReader.enabled||G.K.Config.supportsScreenReaderDirectionalLongPress())if(e===ee.Right)': b'if(!0)if(e===ee.Right)',
        b'return!m.q.accessibility.screenReader.enabled||this.config.supportsScreenReaderDirectionalLongPress?e===r.Right': b'return!0?e===r.Right',
    }.items():
        if player_page.count(before) != 1:
            raise PatchError('Native longpress capability gate mismatch')
        player_page = player_page.replace(before, after)
    player_page = b'"use strict";' + (PAYLOADS / 'player-ui.js').read_bytes() + b'\n' + player_page
    return player_page
