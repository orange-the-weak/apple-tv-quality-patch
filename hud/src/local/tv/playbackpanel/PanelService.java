package local.tv.playbackpanel;

import android.accessibilityservice.AccessibilityService;
import android.view.accessibility.AccessibilityEvent;
import android.view.*;
import android.widget.TextView;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.regex.*;

public class PanelService extends AccessibilityService {
 private final Handler ui=new Handler();
 private final ScheduledExecutorService worker=Executors.newSingleThreadScheduledExecutor();
 private WindowManager wm; private NetGraphView view; private ScheduledFuture<?> job;
 private volatile java.lang.Process process; private volatile boolean visible=false;
 private long lastPress=0, baseRx=-1, prevRx=-1, prevTime=0; private volatile int generation=0;
 private String video="", source="", audio="";
 private String t(int id,Object... args){return getString(id,args);}
 private volatile long lastTextReceived=0;
 private int ticks=0; private String networkSource="", lastText="", lastError="";
 private java.net.ServerSocket formatServer; private volatile org.json.JSONObject playerFormat; private volatile long formatReceived;
 private DiagnosticLog diagnosticLog;
 private volatile boolean playbackPage=false,controlsVisible=false;
 private volatile long uiReceived=0;
 private final HudKeyPolicy.UpRequest pendingUp=new HudKeyPolicy.UpRequest();
 private static final int HUD_NONE=0,HUD_MANUAL=1,HUD_CONTROLS=2;
 private volatile int hudMode=HUD_NONE;
 private final Runnable uiWatchdog=new Runnable(){public void run(){
  if(!freshUi())pendingUp.invalidate();
  if(hudMode==HUD_CONTROLS&&!canFollowControls())hide();
  ui.postDelayed(this,1000);
 }};
 private String bitrateLine="",bufferLine="";
 @Override protected void onServiceConnected(){wm=getSystemService(WindowManager.class);video=t(R.string.waiting_decoder);source=t(R.string.player);audio=t(R.string.format_unavailable); if(diagnosticLog!=null)diagnosticLog.close();diagnosticLog=new DiagnosticLog(this);if(formatServer==null||formatServer.isClosed())startFormatServer();ui.removeCallbacks(uiWatchdog);ui.post(uiWatchdog);android.util.Log.i("PlaybackPanel","Ready; DPAD_UP passthrough");}
 private void startFormatServer(){new Thread(()->{
  try{formatServer=new java.net.ServerSocket();formatServer.setReuseAddress(true);formatServer.bind(new java.net.InetSocketAddress("127.0.0.1",18767));
   while(!formatServer.isClosed()){try(java.net.Socket socket=formatServer.accept()){
    socket.setSoTimeout(700);BufferedReader in=new BufferedReader(new InputStreamReader(socket.getInputStream(),"UTF-8"));
    String first=in.readLine(),line;int length=0,headers=0;
    while((line=in.readLine())!=null&&!line.isEmpty()){if((headers+=line.length())>4096)throw new IOException("headers");if(line.toLowerCase(Locale.ROOT).startsWith("content-length:"))length=Integer.parseInt(line.substring(15).trim());}
    boolean formatRequest="POST /format HTTP/1.1".equals(first),uiRequest="POST /ui HTTP/1.1".equals(first);
    if((!formatRequest&&!uiRequest)||length<=0||length>2048)throw new IOException("request");
    char[] chars=new char[length];int read=0,n;while(read<length&&(n=in.read(chars,read,length-read))>0)read+=n;
    if(read!=length)throw new IOException("body");org.json.JSONObject data=new org.json.JSONObject(new String(chars));
    if(formatRequest&&data.optDouble("bitrate",-1)>0&&data.optInt("width")>0&&data.optInt("height")>0){playerFormat=data;formatReceived=SystemClock.elapsedRealtime();if(diagnosticLog!=null)diagnosticLog.sample(data);}
    if(uiRequest&&data.has("playbackPage")&&data.has("controlsVisible")){
     final boolean nextPage=data.optBoolean("playbackPage"),nextControls=data.optBoolean("controlsVisible");
     final long received=SystemClock.elapsedRealtime();
     // Apply each snapshot in order on the UI thread. A leave must not be
     // overwritten by a later heartbeat before its cancellation is handled.
     ui.post(()->{
      if(!nextPage)pendingUp.invalidate();
      playbackPage=nextPage;controlsVisible=nextControls;uiReceived=received;
      if(hudMode==HUD_CONTROLS&&!canFollowControls())hide();
      if(pendingUp.consume(SystemClock.elapsedRealtime(),canFollowControls()))showFollowingControls();
     });
    }
    socket.getOutputStream().write("HTTP/1.1 204 No Content\r\nConnection: close\r\nContent-Length: 0\r\n\r\n".getBytes("US-ASCII"));
   }catch(Exception ignored){}}
  }catch(Exception e){android.util.Log.w("PlaybackPanel","Local format receiver unavailable");}
 },"local-player-format").start();}
 private volatile String foregroundPackage="";
 private boolean freshUi(){return uiReceived>0&&SystemClock.elapsedRealtime()-uiReceived<2500;}
 private boolean appleForeground(){return "com.apple.atve.androidtv.appletv".equals(foregroundPackage);}
 private boolean canFollowControls(){return HudKeyPolicy.followControls(appleForeground(),playbackPage,controlsVisible,freshUi());}
 private void requestHud(){requestHud(pendingUp.session());}
 private void requestHud(long session){
  if(session!=pendingUp.session()||hudMode==HUD_MANUAL||!HudKeyPolicy.shouldRequestUp(19,0,0,appleForeground(),playbackPage,freshUi()))return;
  long now=SystemClock.elapsedRealtime();pendingUp.request(now,session);
  if(pendingUp.consume(now,canFollowControls()))showFollowingControls();
 }
 private void showFollowingControls(){if(hudMode==HUD_MANUAL)return;hudMode=HUD_CONTROLS;if(!visible)toggle();}
 private void toggleManual(){pendingUp.cancel();if(visible){hide();return;}hudMode=HUD_MANUAL;toggle();}
 @Override protected boolean onKeyEvent(KeyEvent e){
  if(HudKeyPolicy.isInfoKey(e.getKeyCode(),e.getScanCode())){
   if(e.getAction()==KeyEvent.ACTION_DOWN&&e.getRepeatCount()==0&&SystemClock.elapsedRealtime()-lastPress>350){lastPress=SystemClock.elapsedRealtime();ui.post(this::toggleManual);}
   return true;
  }
  if(HudKeyPolicy.shouldRequestUp(e.getKeyCode(),e.getAction(),e.getRepeatCount(),appleForeground(),playbackPage,freshUi())){
   final long session=pendingUp.session();ui.post(()->requestHud(session));
  }
  // UP and all directional repeats reach the player unchanged.
  return false;
 }
 private void toggle(){if(visible){hide();return;} visible=true; int token=++generation;
  baseRx=prevRx=-1; prevTime=0;ticks=0; video=t(R.string.waiting_decoder);audio=t(R.string.format_unavailable);
  view=new NetGraphView(this);view.setTextSize(13);view.setTextColor(Color.WHITE);view.setTypeface(Typeface.create("sans-serif",Typeface.NORMAL));view.setPadding(22,16,22,122);view.setMinWidth(460);
  GradientDrawable bg=new GradientDrawable();bg.setColor(0xb810141b);bg.setCornerRadius(16);view.setBackground(bg);view.setText(t(R.string.loading));
  WindowManager.LayoutParams p=new WindowManager.LayoutParams(-2,-2,WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE|WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE,android.graphics.PixelFormat.TRANSLUCENT);p.gravity=Gravity.TOP|Gravity.RIGHT;p.x=0;p.y=0;
  try{wm.addView(view,p);}catch(Exception e){visible=false;view=null;return;}
  job=worker.scheduleWithFixedDelay(()->sample(token),0,2,TimeUnit.SECONDS);
 }
 private void hide(){pendingUp.cancel();hudMode=HUD_NONE;visible=false;++generation;if(job!=null){job.cancel(true);job=null;}java.lang.Process p=process;if(p!=null)p.destroyForcibly();if(view!=null){try{wm.removeView(view);}catch(Exception ignored){}view=null;}}
 private String dump(String service)throws Exception{
  if(Thread.currentThread().isInterrupted())throw new InterruptedException();
  java.util.List<String> command=new java.util.ArrayList<>(java.util.Arrays.asList("/system/bin/dumpsys","-t","2"));command.addAll(java.util.Arrays.asList(service.split(" ")));
  java.lang.Process p=new ProcessBuilder(command).redirectErrorStream(true).start();process=p;
  ByteArrayOutputStream out=new ByteArrayOutputStream();try(InputStream in=p.getInputStream()){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1){if(out.size()+n>2097152)throw new IOException("output limit");out.write(b,0,n);}}
  if(!p.waitFor(1,TimeUnit.SECONDS))p.destroyForcibly();process=null;return out.toString("UTF-8");
 }
 private static String value(String s,String pattern){Matcher m=Pattern.compile(pattern).matcher(s);return m.find()?m.group(1):"";}
 private void metadata()throws Exception{
  bitrateLine="";bufferLine="";
  String sessions=dump("media_session");String pkg="";
  for(String chunk:sessions.split("package=")){if(chunk.contains("state=PlaybackState {state=3,")){pkg=value(chunk,"^([a-zA-Z0-9_.]+)");if(!pkg.isEmpty())break;}}
  if(pkg.isEmpty())for(String chunk:sessions.split("package=")){if(chunk.startsWith("com.apple.atve.androidtv.appletv")&&chunk.contains("state=PlaybackState {state=2,")){pkg="com.apple.atve.androidtv.appletv";break;}}
  if(pkg.isEmpty()){source=t(R.string.no_session);video=t(R.string.no_player_data);audio=t(R.string.format_unavailable);return;}
  int uid;try{android.content.pm.ApplicationInfo info=getPackageManager().getApplicationInfo(pkg,0);uid=info.uid;source=getPackageManager().getApplicationLabel(info).toString();}catch(Exception e){return;}
  video=t(R.string.video_unknown);
  org.json.JSONObject format=playerFormat;
  if(pkg.equals("com.apple.atve.androidtv.appletv")&&format!=null&&SystemClock.elapsedRealtime()-formatReceived<12000){
   String codec=format.optString("codec"),range=format.optString("range");String kind=codec.startsWith("dvh")?"Dolby Vision":codec.startsWith("hvc")||codec.startsWith("hev")?"HEVC":codec.startsWith("avc")?"H.264":codec;
   if(!kind.equals("Dolby Vision")&&!range.isEmpty())kind+=" · "+range;
   double fps=format.optDouble("frameRate",0);video=t(R.string.video,format.optInt("width")+" × "+format.optInt("height")+" · "+kind+(fps>0?String.format(Locale.ROOT," · %.2f fps",fps):""));
   bitrateLine=t(R.string.bitrate,format.optDouble("bitrate")/1000000.0);
  }
  if(bitrateLine.isEmpty())video=liveVideo(pkg,uid);
  if(pkg.equals("com.apple.atve.androidtv.appletv")&&format!=null&&SystemClock.elapsedRealtime()-formatReceived<12000&&format.has("bufferSeconds")){
   double seconds=format.optDouble("bufferSeconds",Double.NaN);
   if(Double.isFinite(seconds)&&seconds>=0)bufferLine=t(R.string.buffer,seconds,format.optBoolean("buffering")?t(R.string.buffering):"");
   double vb=format.optDouble("videoBufferSeconds",Double.NaN),ab=format.optDouble("audioBufferSeconds",Double.NaN);
   if(Double.isFinite(vb)&&vb>=0&&Double.isFinite(ab)&&ab>=0)bufferLine=t(R.string.buffer_tracks,vb,ab,format.optBoolean("buffering")?t(R.string.waiting):"");
  }
  String flinger=dump("media.audio_flinger");audio=t(R.string.format_unavailable);
  for(String part:flinger.split("(?m)(?=^Output thread)")){
   if(!part.startsWith("Output thread")||!part.contains("Standby: no")||!Pattern.compile("(?m)^\\s*\\d+ Tracks of which [1-9]\\d* are active").matcher(part).find())continue;
   String fmt=value(part,"HAL format:.*?\\((AUDIO_FORMAT_[A-Z0-9_]+)\\)").replace("AUDIO_FORMAT_",""),rate=value(part,"Sample rate: (\\d+)");
   if(fmt.isEmpty())continue;fmt=fmt.equals("E_AC3")?"DD+":fmt.equals("E_AC3_JOC")?t(R.string.atmos_joc):fmt.equals("AC3")?"Dolby Digital":fmt;
   audio=fmt+(rate.isEmpty()?"":" · "+(Integer.parseInt(rate)/1000)+" kHz");if(part.contains("(DIRECT)"))break;
  }
 }
 private String liveVideo(String pkg,int uid)throws Exception{
  String surfaces=dump("SurfaceFlinger"),size="";
  for(String block:surfaces.split("(?m)(?=^\\+ )")){
   String header=block.split("\\n",2)[0];
   if(!header.startsWith("+ BufferStateLayer (SurfaceView["+pkg+"/")||!header.contains("uid="+uid)||!block.contains("isProtected=1"))continue;
   if(!Pattern.compile("Region VisibleRegion \\(this=[^\\n]*count=[1-9]").matcher(block).find())continue;
   Matcher m=Pattern.compile("activeBuffer=\\[\\s*(\\d+)x\\s*(\\d+):").matcher(block);
   if(m.find()&&Integer.parseInt(m.group(1))>0&&Integer.parseInt(m.group(2))>0){size=m.group(1)+" × "+m.group(2);break;}
  }
  String processes=dump("activity processes"),pid=value(processes,"ProcessRecord\\{[^\\n]*? (\\d+):"+Pattern.quote(pkg)+"/");
  String codec="";
  if(!pid.isEmpty()){
   String resources=dump("media.resource_manager").split("  Events logs",2)[0];
   for(String block:resources.split("(?m)(?=^    Pid: )")){
    if(!block.startsWith("    Pid: "+pid+"\n"))continue;
    if(block.contains("Name: OMX.dolby.vision"))codec="Dolby Vision";
    else if(block.contains("DECODER.HEVC")||block.contains("hevc.decoder"))codec="HEVC";
    else if(block.contains("DECODER.AVC")||block.contains("avc.decoder"))codec="H.264";
   }
  }
  if(size.isEmpty()&&codec.isEmpty())return t(R.string.video_unknown);
  if(size.isEmpty())return t(R.string.decoder,codec);
  return t(R.string.frame,size,codec.isEmpty()?t(R.string.codec_unknown):" · "+codec);
 }
 private long rx(){
  try{java.lang.reflect.Method m=android.net.TrafficStats.class.getDeclaredMethod("getRxBytes",String.class);
   for(String iface:new String[]{"wlan0","eth0"}){long v=((Long)m.invoke(null,iface)).longValue();if(v>0){networkSource=iface.equals("wlan0")?"Wi-Fi":t(R.string.ethernet);return v;}}
  }catch(Exception ignored){}
  long total=android.net.TrafficStats.getTotalRxBytes();networkSource=t(R.string.system_total);return total;
 }
 @Override protected void dump(FileDescriptor fd,PrintWriter out,String[] args){if(java.util.Arrays.asList(args).contains("show"))ui.post(this::requestHud);if(java.util.Arrays.asList(args).contains("manual"))ui.post(this::toggleManual);if(java.util.Arrays.asList(args).contains("hide"))ui.post(()->hide());if(diagnosticLog!=null)diagnosticLog.dump(out,args);if(java.util.Arrays.asList(args).contains("metrics")){out.println("metricsAgeMs="+(formatReceived==0?-1:SystemClock.elapsedRealtime()-formatReceived));if(playerFormat!=null)out.println("metrics="+playerFormat.toString());}out.println("trigger=DPAD_UP+123 mode="+hudMode+" playbackPage="+playbackPage+" controlsVisible="+controlsVisible+" uiFresh="+freshUi()+" foreground="+foregroundPackage+" telemetryAgeMs="+(formatReceived==0?-1:SystemClock.elapsedRealtime()-formatReceived));out.println("visible="+visible);out.println("error="+lastError);out.println("network="+networkSource+" rx="+rx());out.println("displaySnapshotAgeMs="+(lastTextReceived==0?-1:SystemClock.elapsedRealtime()-lastTextReceived));if(visible&&lastTextReceived>0&&SystemClock.elapsedRealtime()-lastTextReceived<6000)out.println(lastText);else out.println("displaySnapshot=hidden-or-stale");NetGraphView graph=view;if(graph!=null)out.println("graph="+graph.stats());}
 private void sample(int token){if(!visible||generation!=token)return;try{
  if(ticks++%2==0){try{metadata();lastError="";}catch(Exception e){lastError=e.toString();}}long now=SystemClock.elapsedRealtime(),bytes=rx();String net=t(R.string.network_loading);double measuredRate=Double.NaN;
  if(bytes>=0){if(baseRx<0||bytes<prevRx){baseRx=bytes;prevRx=bytes;prevTime=now;}double mbps=prevTime<now?(bytes-prevRx)*8.0/(now-prevTime)/1000.0:0;measuredRate=mbps;net=t(R.string.download,mbps/8,mbps,(bytes-baseRx)/1000000.0);prevRx=bytes;prevTime=now;}
  final String text=t(R.string.heading,source)+"\n"+video+(bitrateLine.isEmpty()?"":"\n"+bitrateLine)+(bufferLine.isEmpty()?"":"\n"+bufferLine)+"\n"+t(R.string.audio_output,audio)+"\n"+net;
  lastText=text;lastTextReceived=SystemClock.elapsedRealtime();final double rate=measuredRate;ui.post(()->{if(visible&&generation==token&&view!=null){view.setText(text);if(Double.isFinite(rate))view.addRate(rate);}});
 }catch(Exception e){lastError=e.toString();ui.post(()->{if(visible&&generation==token&&view!=null)view.setText(t(R.string.stats_unavailable));});}}
 @Override public void onAccessibilityEvent(AccessibilityEvent e){
  if(e.getEventType()==AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED&&e.getPackageName()!=null){
   String pkg=e.getPackageName().toString();
   if(!pkg.equals(getPackageName())){foregroundPackage=pkg;if(!pkg.equals("com.apple.atve.androidtv.appletv")){pendingUp.invalidate();if(hudMode==HUD_CONTROLS)hide();}}
  }
 }
 @Override public void onInterrupt(){}
 @Override public void onDestroy(){if(diagnosticLog!=null)diagnosticLog.close();hide();worker.shutdownNow();try{if(formatServer!=null)formatServer.close();}catch(Exception ignored){}ui.removeCallbacksAndMessages(null);super.onDestroy();}
}
