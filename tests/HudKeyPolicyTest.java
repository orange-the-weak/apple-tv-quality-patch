import local.tv.playbackpanel.HudKeyPolicy;
public final class HudKeyPolicyTest {
 public static void main(String[] args){
  for(int key:new int[]{19,20,21,22,23,4,198,234})
   for(int action=0;action<2;action++)for(int repeat=0;repeat<2;repeat++)
    for(boolean foreground:new boolean[]{false,true})for(boolean page:new boolean[]{false,true})for(boolean fresh:new boolean[]{false,true}){
     boolean expected=key==19&&action==0&&repeat==0&&foreground&&page&&fresh;
     if(HudKeyPolicy.shouldRequestUp(key,action,repeat,foreground,page,fresh)!=expected)throw new AssertionError("UP route gate");
    }
  for(boolean foreground:new boolean[]{false,true})for(boolean page:new boolean[]{false,true})
   for(boolean controls:new boolean[]{false,true})for(boolean fresh:new boolean[]{false,true})
    if(HudKeyPolicy.followControls(foreground,page,controls,fresh)!=(foreground&&page&&controls&&fresh))throw new AssertionError("control visibility");
  if(!HudKeyPolicy.isInfoKey(0,543)||!HudKeyPolicy.isInfoKey(234,0)||!HudKeyPolicy.isInfoKey(198,0))throw new AssertionError("123 binding");
  for(int key:new int[]{19,20,21,22,23})if(HudKeyPolicy.isInfoKey(key,0))throw new AssertionError("directional key consumed");
  HudKeyPolicy.UpRequest request=new HudKeyPolicy.UpRequest();
  long oldSession=request.session();
  request.request(100,oldSession);
  if(request.consume(200,false))throw new AssertionError("wait for native controls");
  request.invalidate(); // page leave, followed immediately by another page appearing
  if(request.consume(300,true))throw new AssertionError("old request crossed playback pages");
  request.request(400,oldSession); // queued key callback from the old page
  if(request.consume(500,true))throw new AssertionError("queued old key crossed session");
  request.request(600,request.session());
  if(!request.consume(700,true)||request.consume(701,true))throw new AssertionError("new page request must fire once");
  request.request(800,request.session());request.cancel();
  if(request.consume(900,true))throw new AssertionError("manual toggle or hide must cancel pending UP");
  request.request(1000,request.session());
  if(request.consume(3000,true)||request.consume(3001,true))throw new AssertionError("expired request must stay cancelled");
  request.request(4000,request.session());
  if(request.consume(3999,true))throw new AssertionError("invalid clock age");
  request.request(5000,request.session());
  if(request.consume(5100,false)||!request.consume(5200,true))throw new AssertionError("same-page delayed controls must still show HUD");
  System.out.println("HUD keys and control-follow policy passed");
 }
}
