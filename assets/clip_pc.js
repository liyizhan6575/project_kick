// Pitch Control (Bornn–Fernández) — JS port of the user's pitch_control.ipynb model.
// Per-player influence = a velocity-oriented 2D Gaussian; team pitch control = sigmoid(Σ home − Σ away).
// Input positions are pitch METRES (x[0,105], y[-34,34]) — the same frame as the pitch + Sony TRACK.
window.CLIPPC = (function(){
  var GW=44, GH=30;                       // surface grid (≈2.4 m cells) — coarse enough to stay cheap at 12.5fps
  var PC_GAIN=4.2, PC_ALPHA=0.85;         // colour intensity: stretch the narrow PC range (~±0.23) into a long bright ramp (was faint/"candle"-like)
  var MAXSPD2=169.0;                      // (13 m/s)^2

  // one player's influence at grid point (gx,gy): exp(-½ (p-μ)ᵀ Σ⁻¹ (p-μ)), Σ=R·S·S·Rᵀ
  function infl(px,py,vx,vy, dball, gx,gy){
    var Ri=Math.min(3/180*dball*dball+4, 10), srat=(vx*vx+vy*vy)/MAXSPD2;
    var th=Math.atan2(vy,vx+1e-7), c=Math.cos(th), s=Math.sin(th);
    var s0=(1+srat)*Ri*0.5, s1=(1-srat)*Ri*0.5; if(s1<0.4)s1=0.4;   // guard tiny perpendicular axis
    var mx=px+0.5*vx, my=py+0.5*vy, dx=gx-mx, dy=gy-my;
    var rx=c*dx+s*dy, ry=-s*dx+c*dy;       // rotate into the player frame (Rᵀ)
    return Math.exp(-0.5*((rx*rx)/(s0*s0)+(ry*ry)/(s1*s1)));
  }

  // home/away: [[x,y,vx,vy],...] (metres) ; ball:[bx,by]. Returns Float32Array(GW*GH) of PC∈[0,1].
  function compute(home, away, ball){
    var pc=new Float32Array(GW*GH), i, n;
    // pre-distance each player to the ball (the influence radius only depends on it)
    for(i=0;i<home.length;i++){ var hx=home[i][0]-ball[0], hy=home[i][1]-ball[1]; home[i][4]=Math.sqrt(hx*hx+hy*hy); }
    for(i=0;i<away.length;i++){ var ax=away[i][0]-ball[0], ay=away[i][1]-ball[1]; away[i][4]=Math.sqrt(ax*ax+ay*ay); }
    for(var gy=0;gy<GH;gy++){ var wy=-34+(gy+0.5)/GH*68;
      for(var gx=0;gx<GW;gx++){ var wx=(gx+0.5)/GW*105, hi=0, ai=0;
        for(i=0,n=home.length;i<n;i++){ var p=home[i]; hi+=infl(p[0],p[1],p[2],p[3],p[4],wx,wy); }
        for(i=0,n=away.length;i<n;i++){ var q=away[i]; ai+=infl(q[0],q[1],q[2],q[3],q[4],wx,wy); }
        pc[gy*GW+gx]=1/(1+Math.exp(-(hi-ai)));
      } }
    return pc;
  }

  // build [[x,y,vx,vy,distball],...] for a team by differencing frame A→B at the tracking fps
  function vels(A, B, fps){
    var out=new Array(A.length);
    for(var i=0;i<A.length;i++){ var a=A[i], b=B[i]||a; out[i]=[a[0],a[1],(b[0]-a[0])*fps,(b[1]-a[1])*fps,0]; }
    return out;
  }

  // CONTOUR-style surface (not a mosaic): rasterize the PC grid to a small offscreen, then bilinear-upscale it onto the
  // pitch plane — gold = home control, blue = away, transparent where contested so the grass shows. The chapter-3 board
  // is ~top-down, so a single affine maps the pitch rectangle to screen; drawImage's smoothing gives the smooth contour.
  var _oc=null,_octx=null,_oimg=null;
  function draw(ctx, proj, pc, alpha){
    if(alpha<=0.01||!pc) return;
    if(!_oc){ _oc=document.createElement('canvas'); _oc.width=GW; _oc.height=GH; _octx=_oc.getContext('2d'); _oimg=_octx.createImageData(GW,GH); }
    var d=_oimg.data;
    for(var i=0;i<GW*GH;i++){ var dv=pc[i]-0.5, j=i*4, a;
      if(dv>0){ d[j]=251; d[j+1]=191; d[j+2]=36; }              // gold = home control
      else    { d[j]=228; d[j+1]=234; d[j+2]=244; }             // cool white = away control (matches the white away team)
      a=Math.abs(dv)*PC_GAIN; d[j+3]=Math.round((a>1?1:a)*PC_ALPHA*alpha*255);   // stretched: contested → transparent, dominant → bright
    }
    _octx.putImageData(_oimg,0,0);
    var O=proj([0,-34]), U=proj([105,-34]), V=proj([0,34]);     // pitch-rectangle corners (top-down board ≈ affine)
    ctx.save(); ctx.imageSmoothingEnabled=true; ctx.imageSmoothingQuality='high';
    ctx.transform((U[0]-O[0])/GW,(U[1]-O[1])/GW,(V[0]-O[0])/GH,(V[1]-O[1])/GH,O[0],O[1]);   // composes with the active page-shift translate
    ctx.drawImage(_oc,0,0); ctx.restore();
  }

  return {compute:compute, vels:vels, draw:draw, GW:GW, GH:GH};
})();

// One-time smoothed copy of the Sony tracking for the CHAPTER-3 board (chapter 1 keeps its raw CV jitter on purpose).
// A short centred moving-average per player/ball coordinate within each segment removes the per-frame shake.
(function(){
  var TR=window.TRACK; if(!TR) return; var R=2;
  function sm(a){ var n=a.length, o=new Array(n); for(var f=0;f<n;f++){ var lo=f-R<0?0:f-R, hi=f+R>n-1?n-1:f+R, s=0, c=0; for(var g=lo;g<=hi;g++){s+=a[g];c++;} o[f]=s/c; } return o; }
  function smCol(F,k,pi,ci){ var a=[]; for(var f=0;f<F.length;f++) a.push(F[f][k][pi][ci]); return sm(a); }
  window.TRACK_SMOOTH={ fps:TR.fps, segments:TR.segments.map(function(sg){
    var F=sg.frames, n=F.length, H=F[0].h.length, AW=F[0].a.length, hx=[],hy=[],ax=[],ay=[], pi, f;
    for(pi=0;pi<H;pi++){ hx.push(smCol(F,'h',pi,0)); hy.push(smCol(F,'h',pi,1)); }
    for(pi=0;pi<AW;pi++){ ax.push(smCol(F,'a',pi,0)); ay.push(smCol(F,'a',pi,1)); }
    var bx=[],by=[]; for(f=0;f<n;f++){ bx.push(F[f].b[0]); by.push(F[f].b[1]); } var sbx=sm(bx), sby=sm(by);
    var out=[]; for(f=0;f<n;f++){ var h=[],aa=[]; for(pi=0;pi<H;pi++)h.push([hx[pi][f],hy[pi][f]]); for(pi=0;pi<AW;pi++)aa.push([ax[pi][f],ay[pi][f]]); out.push({h:h,a:aa,b:[sbx[f],sby[f]]}); }
    return {frames:out};
  }) };
})();
