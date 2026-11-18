package local.tv.playbackpanel;

import android.content.Context;
import android.os.SystemClock;
import org.json.JSONObject;
import java.io.*;
import java.util.*;

/** Bounded local diagnostics; never persist raw logcat, URLs or account data. */
final class DiagnosticLog {
 private static final long LIMIT=1024*1024, AGE=7L*24*60*60*1000;
 private final File dir;
 private volatile boolean running=true;
 private volatile Process reader;
 private long lastPrune=0,lastRx=-1,lastTime=0;
 private int audioWarnings=0;
 private volatile String error="";
 DiagnosticLog(Context context){
  dir=new File(context.getFilesDir(),"playback-diagnostics");dir.mkdirs();prune();
  new Thread(()->{
   while(running){try{
    if(context.checkSelfPermission("android.permission.READ_LOGS")!=0){Thread.sleep(5000);continue;}
    Process p=new ProcessBuilder("/system/bin/logcat","-v","epoch","-T","1","-s","Luna:I","*:S").redirectErrorStream(true).start();reader=p;
    try(BufferedReader in=new BufferedReader(new InputStreamReader(p.getInputStream(),"UTF-8"))){String line;while(running&&(line=in.readLine())!=null)capture(line);}
    p.destroy();reader=null;
   }catch(Exception e){error=e.getClass().getSimpleName();}
   if(running)try{Thread.sleep(5000);}catch(InterruptedException ignored){}
   }
  },"bounded-playback-log").start();
 }
 private synchronized void capture(String line){try{
  if(line.contains("Slow audio write")||line.contains("AudioTrack appear")){audioWarnings++;return;}
  int pos=line.indexOf("[LocalRuntime] ");
  if(pos>=0){JSONObject src=new JSONObject(line.substring(pos+15));write("runtime",numbers(src,new String[]{"bitrate","position","bufferAheadSeconds","bufferTotalSeconds","videoBufferSeconds","audioBufferSeconds","buffering","manual","selectedBitrate","targetBitrate"}));return;}
  pos=line.indexOf("[LocalQualityRestore] ");
  if(pos>=0){String value=line.substring(pos+22).trim();
   if(value.equals("failed"))write("quality",new JSONObject().put("failed",true));
   else write("quality",numbers(new JSONObject(value),new String[]{"targetBitrate","selectedBitrate","initial"}));return;}
  pos=line.indexOf("[LocalParallel] ");
  if(pos>=0){String event=line.substring(pos+16).trim();if(event.matches("(?:start seq=\\d+|ready seq=\\d+|hit ready=(?:true|false)|fallback|schedule-skipped)"))write("parallel",new JSONObject().put("event",event));}
 }catch(Exception e){error=e.getClass().getSimpleName();}}
 private JSONObject numbers(JSONObject src,String[] keys)throws Exception{
  JSONObject result=new JSONObject();for(String key:keys){Object v=src.opt(key);if(v instanceof Number||v instanceof Boolean)result.put(key,v);}return result;
 }
 synchronized void sample(JSONObject src){try{
  JSONObject row=numbers(src,new String[]{"bufferLowSeconds","bufferHighSeconds","bufferMaxSeconds","streamStopped","mediaPaused","videoBytes","audioBytes","videoPeakBytes","audioPeakBytes","videoQuotaSeen","audioQuotaSeen","videoSegments","audioSegments","videoConfiguredBytes","audioConfiguredBytes","videoBehindSeconds","audioBehindSeconds","prefetchPending","prefetchReady","time","position","desiredRate","iframeMode","selectedBitrate","targetBitrate","bufferSeconds","videoBufferSeconds","audioBufferSeconds","buffering","width","height","bitrate","peak","frameRate","level"});
  for(String key:new String[]{"codec","range"}){String v=src.optString(key);if(v.matches("[A-Za-z0-9_.-]{1,40}"))row.put(key,v);}
  long now=SystemClock.elapsedRealtime(),rx=android.net.TrafficStats.getTotalRxBytes();
  if(lastRx>=0&&rx>=lastRx&&now>lastTime)row.put("tvRxMbps",(rx-lastRx)*.008/(now-lastTime));
  lastRx=rx;lastTime=now;row.put("audioWarnings",audioWarnings);audioWarnings=0;write("sample",row);
 }catch(Exception e){error=e.getClass().getSimpleName();}}
 private File segment(int i){return new File(dir,"playback-"+i+".jsonl");}
 private synchronized void prune(){long now=System.currentTimeMillis();for(int i=0;i<8;i++){File f=segment(i);if(f.exists()&&now-f.lastModified()>AGE)f.delete();}lastPrune=now;}
 private synchronized void write(String type,JSONObject data)throws Exception{
  long now=System.currentTimeMillis();if(now-lastPrune>60000)prune();
  byte[] bytes=new JSONObject().put("recordedAt",now).put("type",type).put("data",data).toString().concat("\n").getBytes("UTF-8");
  if(bytes.length>4096)return;
  if(segment(0).length()+bytes.length>LIMIT){segment(7).delete();for(int i=6;i>=0;i--)if(segment(i).exists()&&!segment(i).renameTo(segment(i+1)))throw new IOException("rotate");}
  try(FileOutputStream out=new FileOutputStream(segment(0),true)){out.write(bytes);}
 }
 synchronized void dump(PrintWriter out,String[] args){
  prune();long total=0;for(int i=0;i<8;i++)total+=segment(i).length();
  out.println("diagnosticLog bytes="+total+" cap=8388608 segments=8 maxAgeDays=7 reader="+(reader!=null)+" error="+error);
  if(args.length==2&&args[0].equals("logs"))try{int index=Integer.parseInt(args[1]);if(index<0||index>7)return;File f=segment(index);if(!f.exists())return;
   out.println("BEGIN_PLAYBACK_JSONL");try(BufferedReader in=new BufferedReader(new InputStreamReader(new FileInputStream(f),"UTF-8"))){String line;while((line=in.readLine())!=null)out.println(line);}out.println("END_PLAYBACK_JSONL");
  }catch(Exception ignored){}
 }
 void close(){running=false;Process p=reader;if(p!=null)p.destroy();}
}
