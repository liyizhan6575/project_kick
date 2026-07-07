// Chapter-2 · page 2 — LANE DOMINANCE, tilted onto the broadcast pitch (a JS port of Tier-5 panel_lanedom).
// The pitch splits into 5 lateral lanes (right-wing → left-wing). Each lane carries a THREAT SHARE (xT-like,
// computed here from the clip's own ball path); the dominant lane is the team's main avenue of attack.
// Three layers, cascading through the lanes, drawn through the page's flip camera P([metreX,metreY]) so they
// lie tilted on the 3D pitch (not top-down):
//   • BAND  — a full-length lane band, kit-tinted by share (dominant brightest), WIPES in toward the goal.
//   • %     — a big number per lane on the defensive end, COUNTS UP 0→share.
//   • ARROW — a halftone dot-chevron (>>>) per lane pointing at the goal; #chevrons ∝ amplified share.
window.CLIPLANEDOM = (function(){
  var LANES=['rwing','rhalf','center','lhalf','lwing'];
  var EDGES=[0.0,0.204,0.365,0.635,0.796,1.0];                 // Tier-2 deck.lane5 edges (display y)
  var EN={rwing:'RIGHT WING',rhalf:'RIGHT HALF',center:'CENTRE',lhalf:'LEFT HALF',lwing:'LEFT WING'};
  function ss(s){s=s<0?0:s>1?1:s;return s*s*(3-2*s);}
  function cl(v,a,b){return v<a?a:v>b?b:v;}

  var _share=null, _goalx=105, _ax=1, _dom='center', _maxs=1, _mins=0;
  // per-lane threat share from the clip's ball path (advancement-weighted → xT-like), consolidated to the
  // team's attacking direction. Recomputed if the clip changes.
  function compute(clip){
    if(!clip||!clip.frames) return null;
    var F=clip.frames, gx=(clip.mouth&&clip.mouth[0]<0.5)?0:105;
    var thr={}; LANES.forEach(function(k){thr[k]=0;});
    for(var i=0;i<F.length;i++){ var b=F[i].ball; if(!b) continue;
      var adv=Math.max(0,(105-Math.abs(b[0]-gx))/105), d=(b[1]+34)/68, li=4;
      for(var e=0;e<5;e++){ if(d>=EDGES[e]&&d<EDGES[e+1]){li=e;break;} }
      thr[LANES[li]]+=adv*adv; }
    var tot=0; LANES.forEach(function(k){tot+=thr[k];}); tot=tot||1;
    // a single goal clip's ball path is far too peaky to read as a team's lane usage (one lane ~60%). Keep the
    // SHAPE (which lane leads) but pull every share hard toward balanced so all five read as realistic, similar values.
    var U=1/LANES.length, FLAT=0.20; _share={}; LANES.forEach(function(k){ _share[k]=U+((thr[k]/tot)-U)*FLAT; });
    _goalx=gx; _ax=(gx===0)?-1:1;
    _dom=LANES[0]; LANES.forEach(function(k){ if(_share[k]>_share[_dom]) _dom=k; });
    var v=LANES.map(function(k){return _share[k];}); _maxs=Math.max.apply(null,v); _mins=Math.min.apply(null,v);
    return _share;
  }

  function laneY(i){ return ((EDGES[i]+EDGES[i+1])/2-0.5)*68; }   // lane centre, metres
  function bandAlpha(sh){ return 0.06+0.5*Math.pow(sh/(_maxs||1),2.0); }   // kit-tint wash; dominant brightest
  function amp(sh){ var r=_maxs-_mins; return r<=0?1:0.40+0.60*(sh-_mins)/r; }   // spread close shares so every lane reads
  function nTicks(sh){ return Math.max(1, Math.round(amp(sh)*3.2)); }           // chevrons per lane (tilted view: fewer than Tier-5's 6.7)

  // ground-plane affine at pitch point (wx,wy): maps LOCAL metres → screen so text/dots lie FLAT on the grass
  // (foreshortened in perspective), instead of standing up facing the camera. Same idea as clip_env's gaff.
  function gaff(P, wx, wy){ var e=3.0, p0=P([wx,wy]), px=P([wx+e,wy]), py=P([wx,wy-e]);   // local +y → world -y (toward camera) so ground text reads upright, not mirrored
    return [(px[0]-p0[0])/e,(px[1]-p0[1])/e,(py[0]-p0[0])/e,(py[1]-p0[1])/e, p0[0], p0[1]]; }

  // dot-chevron (>>>) pointing toward +x*ax — Tier-5 _dot_chevron: rows×width dot grid, middle row tips furthest
  function chevron(cx,cy,sp,ax,rows,width){
    var mid=(rows/2)|0, pts=[];
    for(var r=0;r<rows;r++) for(var c=0;c<width;c++)
      pts.push([cx+ax*(mid-Math.abs(r-mid)-c)*sp, cy+(r-mid)*sp]);
    return pts;
  }

  // growT = seconds since the lane-dom grow began. alpha = overall page visibility (fades in as the pitch blacks out).
  function draw(ctx, P, alpha, growT, opt){
    if(alpha<=0.01||!_share) return;
    opt=opt||{}; var dpr=opt.dpr||1, sc=opt.sc||3, W=opt.W||1200, H=opt.H||800;
    var ax=_ax, ARROWX0=(ax<0)?95.0:10.0, TDX=11.0;   // arrows RIGHT-aligned on the pitch (rightmost chevron near the defensive edge), digit to their left
    var FADE=0.7, STAG=0.22, START=0.15;                          // cascade timing (s)
    var FS=6.5;                                                   // ONE world font size for every lane (fits all lanes → uniform, no overlap)
    // lane render order: nearest touchline (rwing, biggest on screen) last so it sits on top
    var order=[4,3,2,1,0];                                        // lwing(far)→rwing(near): painter's order
    ctx.save(); ctx.textBaseline='alphabetic';
    // solid black fill of the PITCH ONLY (exact touchlines) so the faded grass doesn't let seats show through the
    // translucent bands — without covering the surrounding stands/seats
    var fill=[[0,-34],[105,-34],[105,34],[0,34]]; ctx.globalAlpha=alpha; ctx.fillStyle='#0a0a0a';
    ctx.beginPath(); for(var fi=0;fi<4;fi++){var fq=P(fill[fi]); fi?ctx.lineTo(fq[0],fq[1]):ctx.moveTo(fq[0],fq[1]);} ctx.closePath(); ctx.fill();

    // DIM pitch outline on the blacked-out pitch — the outer rectangle dims down from the light page-1 lines and
    // sits at the SAME dim brightness/tone as the inner lane dividers (aligned)
    var LINE_A=alpha*0.42;
    ctx.strokeStyle='rgba(214,219,208,'+LINE_A.toFixed(3)+')'; ctx.lineWidth=1.2*dpr;
    var box=[[0,-34],[105,-34],[105,34],[0,34]]; ctx.beginPath();
    for(var bi=0;bi<=4;bi++){var q=P(box[bi%4]);bi?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]);} ctx.stroke();
    // (no halfway/centre line on the lane-dominance page)
    // lane divider lines — SAME dim tone/brightness as the outer rectangle (aligned)
    for(var e=1;e<5;e++){ var yy=(EDGES[e]-0.5)*68, a0=P([0,yy]), a1=P([105,yy]);
      ctx.strokeStyle='rgba(214,219,208,'+LINE_A.toFixed(3)+')'; ctx.beginPath(); ctx.moveTo(a0[0],a0[1]); ctx.lineTo(a1[0],a1[1]); ctx.stroke(); }

    for(var oi=0;oi<order.length;oi++){ var i=order[oi], lane=LANES[i], sh=_share[lane];
      var rank=4-i;                                              // rwing(near) first in the cascade → top-of-screen? use display order
      var t0=START+ (i)*STAG;                                    // cascade far→near visually; timing by lane index
      var p=ss(cl((growT-t0)/FADE,0,1));
      var y0=(EDGES[i]-0.5)*68, y1=(EDGES[i+1]-0.5)*68;
      // BAND wipes toward the goal
      var xlo,xhi; if(ax<0){ xlo=105.0*(1-p); xhi=105.0; } else { xlo=0.0; xhi=105.0*p; }
      if(p>0.001){
        var c0=P([xlo,y0]),c1=P([xhi,y0]),c2=P([xhi,y1]),c3=P([xlo,y1]);
        ctx.globalAlpha=bandAlpha(sh)*p*alpha;
        ctx.fillStyle=(lane===_dom)?'#fbbf24':'#fbbf24';        // home kit gold (dominant same hue, brighter via alpha)
        ctx.beginPath();ctx.moveTo(c0[0],c0[1]);ctx.lineTo(c1[0],c1[1]);ctx.lineTo(c2[0],c2[1]);ctx.lineTo(c3[0],c3[1]);ctx.closePath();ctx.fill();
      }
      // ARROWS — dot-chevrons that LIE on the grass (drawn in a ground affine → dots foreshorten to ellipses),
      // driving toward the goal, revealed as the lane grows
      var n=nTicks(sh), cyw=laneY(i), offs=chevron(0,0,1.5,ax,5,3);
      for(var j=0;j<n;j++){
        var rp=ss(cl((p-(j/n)*0.75)/0.24,0,1)); if(rp<=0.02) continue;
        var bright=(n===1)?1:0.45+0.55*(j/(n-1));               // leading (goal-side) chevron brightest
        var af=gaff(P, ARROWX0+ax*j*TDX, cyw); ctx.save(); ctx.transform(af[0],af[1],af[2],af[3],af[4],af[5]);
        ctx.globalAlpha=alpha*rp*bright*0.92; ctx.fillStyle='#e8e8ea';   // uniform arrow colour across all lanes
        for(var k=0;k<offs.length;k++){ ctx.beginPath(); ctx.arc(offs[k][0],offs[k][1],0.5,0,6.283); ctx.fill(); }
        ctx.restore();
      }
      // % number (counts up) + lane tag, PAINTED FLAT on the grass (ground affine) at the defensive end.
      // Font size is in METRES → perspective sizes it (near lanes big, far lanes small); no overlap, no upright text.
      var lnx=(ax<0)?(ARROWX0-(n-1)*TDX-8):(ARROWX0+(n-1)*TDX+8), cyw2=(y0+y1)/2, pv=Math.round(sh*100*p);   // %-digit sits just to the LEFT of THIS lane's leftmost arrow (arrows are right-aligned, so lanes with more arrows push their digit further left)
      var af2=gaff(P, lnx, cyw2); ctx.save(); ctx.transform(af2[0],af2[1],af2[2],af2[3],af2[4],af2[5]);
      ctx.textAlign=(ax<0)?'right':'left'; ctx.textBaseline='middle';
      ctx.globalAlpha=alpha*cl(p*3,0,1); ctx.fillStyle='#f2f2f2';   // uniform %-number colour across all lanes (no special tint for the leading lane)
      ctx.font='700 '+FS.toFixed(2)+'px "Chakra Petch", ui-sans-serif, sans-serif';   // uniform world size + Chakra Petch Bold
      ctx.fillText(pv+'%', 0, 0);
      ctx.restore();
    }
    ctx.globalAlpha=1; ctx.restore();
  }

  return { compute:compute, draw:draw, get share(){return _share;}, get dom(){return _dom;} };
})();
