// Native broadcast-clip renderer. Draws one engine state (CLIPENGINE.state) onto the canvas through
// the page's flip camera P([metreX,metreY]) — so players ride the birdview->broadcast tilt continuously.
// Modules: players (beveled checker discs + jersey + position tag), ball (+shot flight). Chrome /
// celebration / fireworks / checker land on top of this in later passes.
window.CLIPRENDER = (function(){
  function hex(h){h=(h||'#888888').replace('#','');return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)];}
  function rgb(c){return 'rgb('+(c[0]|0)+','+(c[1]|0)+','+(c[2]|0)+')';}
  function shadeC(c,f){return [c[0]*f,c[1]*f,c[2]*f];}
  function lightenC(c,f){return [c[0]+(255-c[0])*f,c[1]+(255-c[1])*f,c[2]+(255-c[2])*f];}
  function lum(c){return (0.299*c[0]+0.587*c[1]+0.114*c[2])/255;}
  function cl(v,a,b){return v<a?a:v>b?b:v;}
  function lp(a,b,t){return a+(b-a)*t;}
  function ss(s){s=s<0?0:s>1?1:s;return s*s*(3-2*s);}

  // interpolate players by id between keyframes kf and kf+1 (id identity, not array index)
  function players(c, kf, ff){
    var A=c.frames[kf], B=c.frames[Math.min(kf+1,c.nf-1)], bm={}, out=[], i, p, b, x, y;
    for(i=0;i<B.h.length;i++) bm['h'+B.h[i].id]=B.h[i];
    for(i=0;i<B.a.length;i++) bm['a'+B.a[i].id]=B.a[i];
    function add(arr,side){ for(var k=0;k<arr.length;k++){ p=arr[k]; b=bm[side+p.id];
      x=p.xy[0]; y=p.xy[1]; if(b){ x=lp(p.xy[0],b.xy[0],ff); y=lp(p.xy[1],b.xy[1],ff); }
      out.push({id:p.id, side:side, pos:p.pos, j:p.j, gk:p.gk, x:x, y:y}); } }
    add(A.h,'h'); add(A.a,'a');
    return out;
  }

  // perspective-correct radius: project a 3m lateral offset at this depth
  function discR(P, x, y){ var a=P([x,y]), b=P([x+3,y]); return Math.max(2.3, Math.hypot(b[0]-a[0],b[1]-a[1])*0.42); }

  // ground affine at (wx,wy): maps a local pitch-metre frame (origin = the player) → screen, so anything drawn lies FLAT on the grass (same homography as the lines/flags). e=0.6 m is load-bearing.
  function gaff(P, wx, wy){ var e=0.6, p0=P([wx,wy]), px=P([wx+e,wy]), py=P([wx,wy+e]);
    return [(px[0]-p0[0])/e,(px[1]-p0[1])/e,(py[0]-p0[0])/e,(py[1]-p0[1])/e,p0[0],p0[1]]; }
  function drawDisc(ctx, P, pl, kits, carrier){
    var kit=hex(kits[pl.side==='h'?'home':'away']), L=lum(kit), af=gaff(P,pl.x,pl.y), R=1.15;   // R = checker radius in METRES; the affine foreshortens it onto the grass (perspective size for free)
    ctx.save(); ctx.transform(af[0],af[1],af[2],af[3],af[4],af[5]);
    ctx.fillStyle='rgba(0,0,0,0.34)'; ctx.beginPath(); ctx.arc(0,0,R*1.05,0,6.2832); ctx.fill();                 // dark outline ring
    ctx.fillStyle=rgb(shadeC(kit,0.5)); ctx.beginPath(); ctx.arc(0,0,R,0,6.2832); ctx.fill();                    // rim
    ctx.lineWidth=R*0.10; ctx.strokeStyle='#ffffff'; ctx.beginPath(); ctx.arc(0,0,R*0.99,0,6.2832); ctx.stroke(); // white edge
    ctx.fillStyle=rgb(kit); ctx.beginPath(); ctx.arc(0,0,R*0.84,0,6.2832); ctx.fill();                            // main kit
    ctx.fillStyle=rgb(lightenC(kit,0.34)); ctx.beginPath(); ctx.arc(0,0,R*0.6,0,6.2832); ctx.fill();              // centre highlight
    ctx.restore();
  }

  function ballMetre(c, st){
    var f=c.frames, mouthM=[c.mouth[0]*105, (c.mouth[1]-0.5)*68];
    if(st.phase==='build'){ var A=f[st.kf], B=f[Math.min(st.kf+1,c.nf-1)];
      if(!A.ball) return B.ball||null; if(!B.ball) return A.ball;
      return [lp(A.ball[0],B.ball[0],st.ff), lp(A.ball[1],B.ball[1],st.ff)]; }
    var src=f[c.nf-1].ball||mouthM;
    if(st.phase==='shot'){ return [lp(src[0],mouthM[0],st.pt), lp(src[1],mouthM[1],st.pt)]; }
    return mouthM;   // goal / celeb / checker holds: ball at goal mouth (or spot)
  }

  function drawBall(ctx, P, bm){
    if(!bm) return; var af=gaff(P,bm[0],bm[1]), R=0.55;   // ball radius in METRES — flat on the grass via the same ground affine as the checkers
    ctx.save(); ctx.transform(af[0],af[1],af[2],af[3],af[4],af[5]);
    ctx.fillStyle='#ffffff'; ctx.beginPath(); ctx.arc(0,0,R,0,6.2832); ctx.fill();
    ctx.lineWidth=R*0.16; ctx.strokeStyle='rgba(35,35,35,0.55)'; ctx.beginPath(); ctx.arc(0,0,R,0,6.2832); ctx.stroke();
    ctx.restore();
  }

  function draw(ctx, st, t, hp){
    if(!st) return; var c=st.clip, P=hp.P, A=cl(hp.alpha==null?1:hp.alpha,0,1);
    if(A<=0.01) return;
    ctx.save(); ctx.globalAlpha=A;
    var pls=players(c, st.kf, st.ff), carrier=c.frames[st.kf].carrier;
    if(c.set_piece){   // CHECKER MODE (set-piece): one-checker spotlight — only the on-ball players follow the ball (passer fades out, receiver fades in), every other player hidden
      var nxt=c.frames[Math.min(st.kf+1,c.nf-1)].carrier;
      for(var k=0;k<pls.length;k++){ var id=String(pls[k].id);
        pls[k]._sa=(id===String(carrier))?(String(carrier)===String(nxt)?1:1-st.ff):(id===String(nxt))?st.ff:0; }
      pls=pls.filter(function(p){return p._sa>0.01;});
    }
    // when the goal goes IN, ALL players fade out (over the flash + into the early celebration) so only the fireworks + crowd sweep remain
    var playerA=(st.phase==='goal')?(1-0.7*st.pt):(st.phase==='celeb')?Math.max(0,0.3-2.4*st.pt):(st.phase==='hold')?0:1;
    pls.sort(function(a,b){return b.y-a.y;});   // painter's order: far end (large y) drawn first
    var kits={home:c.teams.home.kit, away:c.teams.away.kit};
    if(playerA>0.01) for(var i=0;i<pls.length;i++){ ctx.globalAlpha=A*playerA*(pls[i]._sa==null?1:pls[i]._sa); drawDisc(ctx, P, pls[i], kits, carrier); }
    ctx.globalAlpha=A;
    var ballA=(st.phase==='goal')?(1-st.pt):(st.phase==='celeb'||st.phase==='hold')?0:1;   // ball fades out as the goal is scored — crosses the line and vanishes into the net (no ball left sitting on the line through the celebration)
    if(ballA>0.01){ ctx.globalAlpha=A*ballA; drawBall(ctx, P, ballMetre(c, st)); }
    ctx.restore();
  }

  // ===== broadcast chrome (screen space): pixel clock + team badge + scorer + REPLAY + score =====
  var _ICONS={}; ['home','away'].forEach(function(k){var im=new Image(); im.src='assets/_icon_'+k+'.png'; _ICONS[k]=im;});
  var CFONT={
    "0":["01110","10001","10011","10101","11001","10001","01110"],"1":["00100","01100","00100","00100","00100","00100","01110"],
    "2":["01110","10001","00001","00010","00100","01000","11111"],"3":["11111","00010","00100","00010","00001","10001","01110"],
    "4":["00010","00110","01010","10010","11111","00010","00010"],"5":["11111","10000","11110","00001","00001","10001","01110"],
    "6":["00110","01000","10000","11110","10001","10001","01110"],"7":["11111","00001","00010","00100","01000","01000","01000"],
    "8":["01110","10001","10001","01110","10001","10001","01110"],"9":["01110","10001","10001","01111","00001","00010","01100"],
    "H":["10001","10001","10001","11111","10001","10001","10001"],"T":["11111","00100","00100","00100","00100","00100","00100"],
    "F":["11111","10000","10000","11110","10000","10000","10000"],"E":["11111","10000","10000","11110","10000","10000","11111"],
    "P":["11110","10001","10001","11110","10000","10000","10000"],"K":["10001","10010","10100","11000","10100","10010","10001"]
  };
  var CROWS=9, CCOLS=23, COFF_A=0.10, CGLOW=0.32;   // narrower grid — minutes only ("22'" / "120'")
  function stateArr(s){
    var cells=[], x=0, i, r, c, pat;
    for(i=0;i<s.length;i++){ var ch=s[i];
      if(ch===' ') x+=3;
      else if(ch==="'"){ x+=2; cells.push([0,x]); cells.push([1,x]); x+=3; }
      else { pat=CFONT[ch]; if(pat){ for(r=0;r<7;r++)for(c=0;c<5;c++) if(pat[r][c]==='1') cells.push([r,x+c]); x+=6; } } }
    var width=x-1, coff=Math.floor((CCOLS-width)/2), roff=Math.floor((CROWS-7)/2), arr=[];
    for(r=0;r<CROWS;r++) arr.push(new Array(CCOLS).fill(0));
    for(i=0;i<cells.length;i++){ var rr=cells[i][0]+roff, cc=cells[i][1]+coff; if(rr>=0&&rr<CROWS&&cc>=0&&cc<CCOLS) arr[rr][cc]=1; }
    return arr;
  }
  function layout(s){ var L=[], x=0; for(var i=0;i<s.length;i++){ var ch=s[i]; if(ch===' '){x+=3;} else if(ch==="'"){ L.push({c:ch,x:x+2,d:false}); x+=5; } else { L.push({c:ch,x:x,d:true}); x+=6; } } return {L:L,w:x-1}; }   // per-char x-offsets — used to spin each digit independently (odometer count)
  function rrect(ctx,x,y,w,h,r){ ctx.beginPath(); ctx.moveTo(x+r,y); ctx.arcTo(x+w,y,x+w,y+h,r); ctx.arcTo(x+w,y+h,x,y+h,r); ctx.arcTo(x,y+h,x,y,r); ctx.arcTo(x,y,x+w,y,r); ctx.closePath(); }
  var _ckFlip={};   // per-clock flip state: {text, prev, flipT} — drives the split-flap on a value change
  function drawClock(ctx, cx, cy, clockH, text, a, t, id){
    var ds=clockH/CROWS, hw=(CCOLS-1)/2*ds, hh=(CROWS-1)/2*ds, pad=1.4*ds, ip=0.55*ds;
    id=id||'main'; var s=_ckFlip[id]||(_ckFlip[id]={text:text,prev:text,flipT:-99});
    if(text!==s.text){ s.prev=s.text; s.text=text; s.flipT=t; }                       // value changed → start a flip
    var nL=layout(s.text), oL=layout(s.prev), roff=Math.floor((CROWS-7)/2), DH=8*ds;
    var aligned=(s.flipT>-90&&nL.w===oL.w&&nL.L.length===oL.L.length), maxStep=1;
    if(aligned){ for(var li=0;li<nL.L.length;li++){ var nc=nL.L[li], oc=oL.L[li]; if(nc.x!==oc.x||nc.d!==oc.d){aligned=false;break;} if(nc.d&&nc.c!==oc.c) maxStep=Math.max(maxStep,(+nc.c-+oc.c+10)%10); } }
    var SPIN=cl(0.4+0.075*maxStep,0.45,1.3), fp=cl((t-s.flipT)/SPIN,0,1), rolling=(aligned&&fp<1), breath=0.72+0.28*(0.5+0.5*Math.sin(2*Math.PI*t/2.6));   // ODOMETER: each changed digit counts UP through EVERY intermediate value (2→9 shows 3,4,5,6,7,8); duration scales with the biggest jump
    ctx.globalAlpha=a;
    [[0.5*ds,'#5a616c',1.5],[1.15*ds,'#363b44',1.1]].forEach(function(rg){ ctx.lineWidth=rg[2]; ctx.strokeStyle=rg[1]; rrect(ctx,cx-hw-pad-rg[0],cy-hh-pad-rg[0],2*hw+2*pad+2*rg[0],2*hh+2*pad+2*rg[0],ds*2.6+rg[0]); ctx.stroke(); });
    rrect(ctx,cx-hw-pad,cy-hh-pad,2*hw+2*pad,2*hh+2*pad,ds*2.6); ctx.fillStyle='#23262d'; ctx.fill(); ctx.lineWidth=2; ctx.strokeStyle='#363b44'; ctx.stroke();
    rrect(ctx,cx-hw-pad+ip,cy-hh-pad+ip,2*hw+2*pad-2*ip,2*hh+2*pad-2*ip,ds*2.1); ctx.fillStyle='#0c0d10'; ctx.fill();
    var coff=Math.floor((CCOLS-nL.w)/2);
    function dot(px,py,al){ ctx.globalAlpha=al*CGLOW*breath; ctx.fillStyle='#fff'; ctx.beginPath(); ctx.arc(px,py,ds*0.5,0,6.2832); ctx.fill(); ctx.globalAlpha=al; ctx.beginPath(); ctx.arc(px,py,ds*0.3,0,6.2832); ctx.fill(); }
    function dGlyph(d,gx,voff){ var pat=CFONT[''+d]; if(!pat)return; for(var gr=0;gr<7;gr++)for(var gc=0;gc<5;gc++){ if(pat[gr][gc]==='1') dot(cx+((gx+gc)-(CCOLS-1)/2)*ds, cy-((CROWS-1)/2-(gr+roff))*ds+voff, a); } }
    for(var r=0;r<CROWS;r++)for(var c=0;c<CCOLS;c++){ ctx.globalAlpha=a*COFF_A; ctx.fillStyle='#fff'; ctx.beginPath(); ctx.arc(cx+(c-(CCOLS-1)/2)*ds, cy-((CROWS-1)/2-r)*ds, ds*0.3,0,6.2832); ctx.fill(); }   // dim background grid (static)
    ctx.save(); rrect(ctx,cx-hw-pad+ip,cy-hh-pad+ip,2*hw+2*pad-2*ip,2*hh+2*pad-2*ip,ds*2.1); ctx.clip();   // clip lit dots so spinning digits vanish at the bezel
    for(var li2=0;li2<nL.L.length;li2++){ var ch=nL.L[li2], gx=coff+ch.x, bx=cx+(gx-(CCOLS-1)/2)*ds;
      if(!ch.d){ dot(bx, cy-((CROWS-1)/2-roff)*ds, a); dot(bx, cy-((CROWS-1)/2-(roff+1))*ds, a); continue; }   // apostrophe — static
      if(rolling&&oL.L[li2].c!==ch.c){ var o=+oL.L[li2].c, n=+ch.c, steps=(n-o+10)%10, v=o+fp*steps, lo=Math.floor(v), fr=v-lo; dGlyph(lo%10,gx,-fr*DH); dGlyph((lo+1)%10,gx,(1-fr)*DH); }   // count UP through every value
      else dGlyph(+ch.c,gx,0);
    }
    ctx.restore();
    ctx.globalAlpha=1; return {hw:hw, pad:pad};
  }
  function chrome(ctx, st, t, hp){
    if(!st) return; var c=st.clip, detail=cl(hp.detail==null?1:hp.detail,0,1), A=ss(cl((detail-0.55)/0.32,0,1));
    if(A<=0.01) return;
    var W=hp.W, H=hp.H, clockH=Math.max(18,H*0.05), cyc=H*0.115, cxc=W*0.475;
    var ck=drawClock(ctx, cxc, cyc, clockH, c.clock.text||'', A, t);
    var clkL=cxc-ck.hw-ck.pad, clkR=cxc+ck.hw+ck.pad;
    // team badge (scoring side) left of the clock
    var bR=clockH*0.66, bx=clkL-bR-clockH*0.3, by=cyc, icon=_ICONS[c.teams[c.goal_side].icon];
    ctx.globalAlpha=A; ctx.fillStyle='#171717'; ctx.beginPath(); ctx.arc(bx,by,bR,0,6.2832); ctx.fill();
    if(icon&&icon.complete&&icon.naturalWidth){ ctx.save(); ctx.beginPath(); ctx.arc(bx,by,bR*0.9,0,6.2832); ctx.clip(); ctx.globalAlpha=A; ctx.drawImage(icon,bx-bR*0.9,by-bR*0.9,bR*1.8,bR*1.8); ctx.restore(); }
    ctx.globalAlpha=A; ctx.lineWidth=Math.max(1.4,bR*0.07); ctx.strokeStyle='#787d87'; ctx.beginPath(); ctx.arc(bx,by,bR*1.05,0,6.2832); ctx.stroke();
    // scorer text block right of the clock
    var tx=clkR+clockH*0.42; ctx.globalAlpha=A; ctx.textAlign='left'; ctx.textBaseline='alphabetic';
    ctx.fillStyle='#f2f2f2'; ctx.font='700 '+Math.round(clockH*0.46)+'px sans-serif'; ctx.fillText(c.scorer.name||'', tx, cyc-clockH*0.05);
    ctx.fillStyle='#b6bac2'; ctx.font='700 '+Math.round(clockH*0.3)+'px sans-serif'; ctx.fillText((c.scorer.descriptor||'').toUpperCase(), tx, cyc+clockH*0.32);
    ctx.fillStyle='#7e8693'; ctx.font='700 '+Math.round(clockH*0.27)+'px ui-monospace,monospace'; ctx.fillText('xG '+(c.scorer.xg||0).toFixed(2), tx, cyc+clockH*0.62);
    // REPLAY tab below the clock
    var rw=clockH*1.45, rh=clockH*0.46, ry=cyc+clockH*0.5+ck.pad+rh*0.95;
    ctx.globalAlpha=A; ctx.fillStyle='#2ee6f2'; rrect(ctx,cxc-rw,ry-rh/2,2*rw,rh,rh/2); ctx.fill();
    ctx.fillStyle='#06141a'; ctx.font='700 '+Math.round(rh*0.58)+'px ui-monospace,monospace'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText('REPLAY', cxc, ry+rh*0.04);
    ctx.globalAlpha=1;   // (score now lives on the grass — drawn by clip_env)
  }

  // circular team badge (dark disc · icon clipped · contour ring) — drawn next to the stand clock
  function standIcon(ctx, icon, x, y, R, a){
    ctx.globalAlpha=a; ctx.fillStyle='#15171c'; ctx.beginPath(); ctx.arc(x,y,R,0,6.2832); ctx.fill();
    if(icon&&icon.complete&&icon.naturalWidth){ ctx.save(); ctx.beginPath(); ctx.arc(x,y,R*0.88,0,6.2832); ctx.clip(); ctx.globalAlpha=a; ctx.drawImage(icon,x-R*0.88,y-R*0.88,R*1.76,R*1.76); ctx.restore(); }
    ctx.globalAlpha=a; ctx.lineWidth=Math.max(1,R*0.08); ctx.strokeStyle='#5a616c'; ctx.beginPath(); ctx.arc(x,y,R*1.05,0,6.2832); ctx.stroke();
    ctx.globalAlpha=1;
  }
  // pixel clock as a JUMBOTRON on the north (far) stand, flanked by the two team badges — projected + perspective-scaled
  function stadiumClock(ctx, st, t, hp){
    if(!st) return; var detail=cl(hp.detail==null?1:hp.detail,0,1); if(detail<=0.02) return;
    var P3=hp.proj, c0=P3([52.5,58,17]), c1=P3([52.5,58,18]);   // north-stand centre (world) + 1 m up
    var pxm=Math.hypot(c1[0]-c0[0],c1[1]-c0[1]), clockH=Math.max(12, pxm*9);   // ~9 m jumbotron
    var mins=(st.clip.clock&&st.clip.clock.minute!=null)?(st.clip.clock.minute+"'"):'';   // minutes only
    var ck=drawClock(ctx, c0[0], c0[1], clockH, mins, detail, t, 'jumbo');
    var R=clockH*0.66, gx=ck.hw+ck.pad+R+clockH*0.62;          // home shield (left) · away attack (right) — slightly farther from the clock
    standIcon(ctx, _ICONS.home, c0[0]-gx, c0[1]-R*0.1, R, detail);   // home shield sits ~5px low in its art — lift to match the away icon's centre
    standIcon(ctx, _ICONS.away, c0[0]+gx, c0[1], R, detail);
  }

  // ===== goal-post fireworks (3D, celeb only) — fib-sphere bursts in the scoring team's colour =====
  var FW_DIR=[], FW_SPD=[];
  (function(){ var n=46, gr=Math.PI*(1+Math.sqrt(5)); for(var i=0;i<n;i++){ var ii=i+0.5, ph=Math.acos(1-2*ii/n), tt=gr*ii;
    FW_DIR.push([Math.sin(ph)*Math.cos(tt), Math.sin(ph)*Math.sin(tt), Math.cos(ph)]); FW_SPD.push(0.75+0.25*i/(n-1)); } })();
  function fireworks(ctx, st, hp){
    if(!st || st.phase!=='celeb') return; var detail=cl(hp.detail==null?1:hp.detail,0,1); if(detail<=0.05) return;
    var c=st.clip, proj=hp.proj, tcel=st.pt*4.2;                 // seconds into the celebration
    var pgx = c.mouth[0]<0.5 ? 0 : 105;                          // the goal they scored at
    var sc=hex(c.teams[c.goal_side].kit).map(function(v){return v/255;});
    var col1=sc.map(function(v){return cl(v+0.30,0,1);}), col2=sc.map(function(v){return cl(v*0.3+0.7,0,1);});
    function fill(col,a){ ctx.fillStyle='rgba('+(col[0]*255|0)+','+(col[1]*255|0)+','+(col[2]*255|0)+','+a.toFixed(3)+')'; }
    var offs=[0.2,2.0], posts=[5.5,-5.5];   // only TWO firework rounds (each round = the twin goal-posts), same for open-play + set-piece goals
    ctx.globalCompositeOperation='lighter';
    for(var o=0;o<offs.length;o++) for(var pp=0;pp<2;pp++){
      var sy=posts[pp], tau=tcel-offs[o]; if(tau<0||tau>1.63) continue;
      if(tau<=0.40){ var rz=19*(1-Math.pow(1-tau/0.40,2));      // rise: white comet
        for(var k=0;k<5;k++){ var tz=rz-0.9*k; if(tz<0)break; var p=proj([pgx,sy,tz]); fill([1,1,1],detail*Math.max(0,1-k/5)*0.9);
          ctx.beginPath(); ctx.arc(p[0],p[1],2.0,0,6.2832); ctx.fill(); } }
      else{ var tb=(tau-0.40)/1.23;                              // burst: 46 fib-sphere sparks + gravity droop
        for(var q=0;q<46;q++){ var d=FW_DIR[q], spd=FW_SPD[q];
          var bx=pgx+d[0]*spd*tb*10.35, by=sy+d[1]*spd*tb*10.35, bz=19+d[2]*spd*tb*10.35-14*tb*tb; if(bz<0) continue;
          var p=proj([bx,by,bz]); fill((tb<0.12)?[1,1,1]:(q%2?col2:col1), detail*cl(Math.pow(1-tb,1.4),0,1));
          ctx.beginPath(); ctx.arc(p[0],p[1],2.3,0,6.2832); ctx.fill(); } }
    }
    ctx.globalCompositeOperation='source-over'; ctx.globalAlpha=1;
  }

  return {draw:draw, chrome:chrome, stadiumClock:stadiumClock, fireworks:fireworks};
})();
