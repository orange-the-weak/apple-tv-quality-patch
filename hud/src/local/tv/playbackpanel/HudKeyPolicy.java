package local.tv.playbackpanel;

/** Key and route policy independent of Android. Directional keys are never consumed. */
public final class HudKeyPolicy {
 private HudKeyPolicy(){}
 public static boolean isInfoKey(int key,int scan){return scan==543||key==234||(key==198&&scan==0);}
 public static boolean shouldRequestUp(int key,int action,int repeat,boolean appleForeground,boolean playbackPage,boolean freshUi){
  return key==19&&action==0&&repeat==0&&appleForeground&&playbackPage&&freshUi;
 }
 public static boolean followControls(boolean appleForeground,boolean playbackPage,boolean controlsVisible,boolean freshUi){
  return appleForeground&&playbackPage&&controlsVisible&&freshUi;
 }

 /** Main-thread-only pending request, bound to a playback lifecycle generation. */
 public static final class UpRequest {
  private long session=0,requestedSession=-1,requestedAt=-1;
  public long session(){return session;}
  public void cancel(){requestedAt=-1;requestedSession=-1;}
  public void invalidate(){session++;cancel();}
  public void request(long now,long expectedSession){
   if(expectedSession!=session)return;
   requestedAt=now;requestedSession=session;
  }
  public boolean consume(long now,boolean canFollow){
   if(requestedAt<0)return false;
   long age=now-requestedAt;
   if(requestedSession!=session||age<0||age>=2000){cancel();return false;}
   if(!canFollow)return false;
   cancel();return true;
  }
 }
}
