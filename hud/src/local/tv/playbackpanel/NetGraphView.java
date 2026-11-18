package local.tv.playbackpanel;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.os.SystemClock;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.Locale;

/** A bounded, time-based history. All mutation and drawing happens on the UI thread. */
public final class NetGraphView extends TextView {
 private final ArrayList<Double> rates=new ArrayList<>();
 private final ArrayList<Long> times=new ArrayList<>();
 private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
 private volatile String summary="0 samples";
 public NetGraphView(Context context){super(context);}
 public void addRate(double rate){
  if(!Double.isFinite(rate)||rate<0)return;
  long now=SystemClock.elapsedRealtime();rates.add(rate);times.add(now);
  while(times.size()>90||(!times.isEmpty()&&now-times.get(0)>120000)){times.remove(0);rates.remove(0);}
  double peak=0;for(double v:rates)peak=Math.max(peak,v);
  summary=String.format(Locale.ROOT,"%d samples, peak=%.2f Mbps",rates.size(),peak);invalidate();
 }
 public String stats(){return summary;}
 @Override protected void onDraw(Canvas canvas){
  super.onDraw(canvas);
  float left=getPaddingLeft(),right=getWidth()-getPaddingRight();
  float top=getHeight()-99,bottom=getHeight()-26;
  if(right<=left||bottom<=top)return;
  double peak=0;for(double r:rates)peak=Math.max(peak,r);
  double ceiling=Math.max(10,Math.ceil(peak/10)*10);
  paint.setTypeface(getTypeface());paint.setTextSize(16);paint.setColor(0xffaab7c7);
  canvas.drawText(getContext().getString(R.string.graph_caption,ceiling),left,top-7,paint);
  paint.setColor(0x35ffffff);paint.setStrokeWidth(1);
  for(int i=0;i<=2;i++){float y=top+(bottom-top)*i/2;canvas.drawLine(left,y,right,y,paint);}
  if(rates.size()<2)return;
  long now=SystemClock.elapsedRealtime();Path line=new Path();float firstX=0,lastX=0;
  for(int i=0;i<rates.size();i++){
   float x=right-(right-left)*Math.min(120000,now-times.get(i))/120000f;
   float y=bottom-(float)(rates.get(i)/ceiling)*(bottom-top);
   if(i==0){line.moveTo(x,y);firstX=x;}else line.lineTo(x,y);lastX=x;
  }
  Path fill=new Path(line);fill.lineTo(lastX,bottom);fill.lineTo(firstX,bottom);fill.close();
  paint.setStyle(Paint.Style.FILL);paint.setColor(0x284cc9f0);canvas.drawPath(fill,paint);
  paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(2.5f);paint.setColor(0xff64d8f5);canvas.drawPath(line,paint);paint.setStyle(Paint.Style.FILL);
 }
}
