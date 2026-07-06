// Broadcast ENVIRONMENT — faithful port of the Tier-5 stadium bowl + floodlit green pitch.
// World metres x[0,105] y[-34,34] z up; drawn through proj([x,y,z]) (camera matches Tier-5 at camT=1).
// Seats are cached once in world space and re-projected only when the camera (camT) or width changes.
window.CLIPENV = (function(){
  function cl(v,a,b){return v<a?a:v>b?b:v;}
  function lp(a,b,t){return a+(b-a)*t;}
  function lerpRGB(a,b,t){return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t];}
  function rgb(c){return 'rgb('+Math.round(c[0]*255)+','+Math.round(c[1]*255)+','+Math.round(c[2]*255)+')';}
  function hex01(h){h=(h||'#888888').replace('#','');return [parseInt(h.slice(0,2),16)/255,parseInt(h.slice(2,4),16)/255,parseInt(h.slice(4,6),16)/255];}
  function lum01(c){return 0.299*c[0]+0.587*c[1]+0.114*c[2];}
  function smoother(p){p=cl(p,0,1);return p*p*p*(p*(p*6-15)+10);}   // smootherstep
  function hash01(i){return (((i*1103515245+12345)%1000)+1000)%1000/1000;}   // deterministic per-seat dither

  // ---------- bowl geometry (world metres) ----------
  var XL=-7, XR=112, YN=41, YB=-41, R=22, BASE=3, DEPTH=34, HH=23, ROWS=18;
  var GRASS_A=[0x2b/255,0x44/255,0x2b/255], GRASS_B=[0x20/255,0x33/255,0x20/255];
  var SEAT_FRONT=[0.82,0.90,1.00], SEAT_BACK=[0.36,0.44,0.62], LED=[0.45,0.85,1.0];
  var SEAT_K=210;   // seat-dot radius constant (px·metre) — tuned to the reference

  var Pp=[], Nn=[], kinds=[];
  function straight(x0,y0,x1,y1,nx,ny){ var L=Math.hypot(x1-x0,y1-y0), k=Math.max(2,Math.floor(L/1.7));
    for(var i=0;i<k;i++){var t=(i+0.5)/k; Pp.push([lp(x0,x1,t),lp(y0,y1,t)]); Nn.push([nx,ny]); kinds.push('s');} }
  function arc(cx,cy,a0,a1){ var L=R*Math.abs(a1-a0), k=Math.max(3,Math.floor(L/1.7));
    for(var i=0;i<k;i++){var th=a0+(a1-a0)*(i+0.5)/k; Pp.push([cx+R*Math.cos(th),cy+R*Math.sin(th)]); Nn.push([Math.cos(th),Math.sin(th)]); kinds.push('c');} }
  straight(XL,YB+R,XL,YN-R,-1,0); arc(XL+R,YN-R,Math.PI,Math.PI/2);
  straight(XL+R,YN,XR-R,YN,0,1);  arc(XR-R,YN-R,Math.PI/2,0);
  straight(XR,YN-R,XR,YB+R,1,0);  arc(XR-R,YB+R,0,-Math.PI/2);
  straight(XR-R,YB,XL+R,YB,0,-1); arc(XL+R,YB+R,-Math.PI/2,-Math.PI);
  var NP=Pp.length;

  // seats: [wx,wy,wz, baseRGB]
  var SEATS=[];
  for(var ri=0;ri<ROWS;ri++){ var v=(ri+0.5)/ROWS, col=lerpRGB(SEAT_FRONT,SEAT_BACK,cl(v,0,1));
    for(var si=0;si<NP;si++){ if(kinds[si]!=='s')continue;
      SEATS.push([Pp[si][0]+Nn[si][0]*DEPTH*v, Pp[si][1]+Nn[si][1]*DEPTH*v, 6+HH*v, col]); } }
  (function(){ var arcs=[[XL+R,YN-R,Math.PI,Math.PI/2],[XR-R,YN-R,Math.PI/2,0],[XR-R,YB+R,0,-Math.PI/2],[XL+R,YB+R,-Math.PI/2,-Math.PI]];
    for(var a=0;a<arcs.length;a++){ var C=arcs[a], dir=Math.sign(C[3]-C[2]), NW=Math.max(2,Math.round(R*Math.abs(C[3]-C[2])/10)), bnd=[],k;
      for(k=0;k<=NW;k++) bnd.push(C[2]+(C[3]-C[2])*k/NW);
      for(var ri2=0;ri2<ROWS;ri2++){ var v2=(ri2+0.5)/ROWS, col2=lerpRGB(SEAT_FRONT,SEAT_BACK,cl(v2,0,1)), Rr=22+DEPTH*v2, ga=dir*1.6/Rr;
        for(var kk=0;kk<NW;kk++){ var s0=bnd[kk]+(kk>0?ga:0), s1=bnd[kk+1]-(kk+1<NW?ga:0), n=Math.max(1,Math.round(Math.abs(s1-s0)*Rr/1.7));
          for(var sj=0;sj<n;sj++){ var th=s0+(s1-s0)*(sj+0.5)/n; SEATS.push([C[0]+Rr*Math.cos(th),C[1]+Rr*Math.sin(th),6+HH*v2,col2]); } } } } })();
  var FRONTW=[]; for(var fi=0;fi<NP;fi++) FRONTW.push([Pp[fi][0]+Nn[fi][0]*DEPTH*0.48, Pp[fi][1]+Nn[fi][1]*DEPTH*0.48]);
  var SEAT_XLO=1e9, SEAT_XHI=-1e9;   // wx range of the seat field (± edge) — the celebration sweep front travels across this
  for(var _sx=0;_sx<SEATS.length;_sx++){ var _wx=SEATS[_sx][0]; if(_wx<SEAT_XLO)SEAT_XLO=_wx; if(_wx>SEAT_XHI)SEAT_XHI=_wx; }
  SEAT_XLO-=14; SEAT_XHI+=14;

  function nfa(wy){ var b=cl((wy+77)/14,0,1); return wy<-39 ? b*0.72 : b; }   // near-side dissolve: south stand wraps the bowl, rendered slightly dimmer (×0.72) than far/sides but clearly present; back rows nearest the lens (wy<-77) still fade out

  // seat-projection cache (re-project only when camera/width changes)
  var _cache={key:'',pts:null};
  function projectSeats(proj,key){
    if(_cache.key===key) return _cache.pts;
    var pts=new Array(SEATS.length);
    for(var s=0;s<SEATS.length;s++){ var st=SEATS[s], p=proj([st[0],st[1],st[2]]); pts[s]=[p[0],p[1],p[2]||80,nfa(st[1]),st[3],st[0],s]; }   // +wx, +idx for the sweep
    _cache={key:key,pts:pts}; return pts;
  }
  // bowl geometry (facade wall + roof neon) cached by the SAME key as the seats → frozen at the broadcast
  // projection during the 2→3 flip (key is camT-based; camT=1 throughout chapters 2+3), so the whole bowl stays
  // STILL and just fades instead of swinging round with the pitch. The green pitch stays live (it must track the flip).
  var _bowl={key:'',facade:null,roof:null};
  function projectBowl(proj, key){
    if(_bowl.key===key) return _bowl;
    var facade=new Array(NP), roof=new Array(NP);
    for(var i=0;i<NP;i++){ facade[i]=[proj([Pp[i][0],Pp[i][1],0]), proj([Pp[i][0],Pp[i][1],BASE])]; var w=FRONTW[i]; roof[i]=proj([w[0],w[1],32]); }
    _bowl={key:key,facade:facade,roof:roof}; return _bowl;
  }

  function drawBowl(ctx, proj, projB, A, key, sweep){
    if(A<=0.01) return;
    var ckT=parseFloat(key), bp=(ckT>=0.999)?projB:proj;   // ckT = camT; frozen state (camT≈1, chapters 2+3) → FIXED broadcast camera so a mid-flip cache can't distort the bowl; the 1→2 reveal (camT<1) still transitions with the live camera
    var BC=projectBowl(bp,key);
    // facade wall (Pp z=0 -> z=BASE) — frozen via the bowl cache
    ctx.fillStyle='#0a0c14';
    for(var i=0;i<NP;i++){ var j=(i+1)%NP, fa=nfa((Pp[i][1]+Pp[j][1])/2); if(fa<=0.01)continue;
      var b0=BC.facade[i][0], b1=BC.facade[j][0], t0=BC.facade[i][1], t1=BC.facade[j][1];
      ctx.globalAlpha=A*0.92*fa; ctx.beginPath(); ctx.moveTo(b0[0],b0[1]); ctx.lineTo(b1[0],b1[1]); ctx.lineTo(t1[0],t1[1]); ctx.lineTo(t0[0],t0[1]); ctx.closePath(); ctx.fill(); }
    // seats — ONLY the far (north) stand's back rows are clipped under its roof line (they must not poke above the cyan roof).
    // The side (east/west) + near (south) stands are drawn UNCLIPPED, so nothing on those stands is ever cut.
    var pts=projectSeats(bp,key), front=0, sgn=1;
    if(sweep){ var pe=smoother(sweep.cprog), R=SEAT_XHI-SEAT_XLO, OV=R*0.42; front = sweep.dir<0 ? (SEAT_XHI+OV)-(R+2*OV)*pe : (SEAT_XLO-OV)+(R+2*OV)*pe; sgn = sweep.dir<0?1:-1; }   // front travels OFF one edge → OFF the other (overshoot) so the wave ENTERS and fully EXITS instead of parking lit at the far edge
    function paintSeat(q){ if(q[3]<=0.02)return;
      var col=q[4], rad=cl(SEAT_K/q[2],0.45,2.8), al=A*0.6*q[3];
      if(sweep){ var behind=(q[5]-front)*sgn, sw=cl(behind/14+1,0,1)*Math.exp(-Math.max(behind,0)/22), it=sw*sweep.amp*(0.5+0.5*hash01(q[6]));
        if(it>0.01){ col=lerpRGB(col,sweep.hot,it); rad*=(1+0.8*it); al=cl(al*(1+0.9*it),0,1); } }
      ctx.globalAlpha=al; ctx.fillStyle=rgb(col); ctx.beginPath(); ctx.arc(q[0],q[1],rad,0,6.2832); ctx.fill(); }
    ctx.save(); ctx.beginPath(); for(var rc=0;rc<NP;rc++){ var rp=BC.roof[rc]; rc?ctx.lineTo(rp[0],rp[1]):ctx.moveTo(rp[0],rp[1]); } ctx.closePath(); ctx.clip();
    for(var s=0;s<pts.length;s++){ if(SEATS[s][1]>30) paintSeat(pts[s]); }     // far/north back rows: under the roof ring
    ctx.restore();
    for(var s2=0;s2<pts.length;s2++){ if(SEATS[s2][1]<=30) paintSeat(pts[s2]); }  // side + near stands: unclipped (never cut)
    // ROOF OCCLUSION — the cyan line is a roof: mask everything ABOVE its upper arc (far + side) to page-black, so no seat back rows (or background dots) show through. We can't see past the roof.
    var arc=[], k0=-1;
    for(var ka=0;ka<NP;ka++){ if(FRONTW[ka][1]>=-25 && FRONTW[(ka+NP-1)%NP][1]<-25){ k0=ka; break; } }   // first roof point just past the (roofless) south gap
    if(k0>=0){ for(var km=0;km<NP;km++){ var ki=(k0+km)%NP; if(FRONTW[ki][1]>=-25) arc.push(BC.roof[ki]); else break; } }
    if(arc.length>1){ if(arc[0][0]>arc[arc.length-1][0]) arc.reverse();   // order the arc left→right
      ctx.globalAlpha=A; ctx.fillStyle='#0a0a0a';
      ctx.beginPath(); ctx.moveTo(arc[0][0],arc[0][1]); for(var ka2=1;ka2<arc.length;ka2++) ctx.lineTo(arc[ka2][0],arc[ka2][1]);
      ctx.lineTo(ctx.canvas.width,0); ctx.lineTo(0,0); ctx.closePath(); ctx.fill(); ctx.globalAlpha=1; }
    // roof neon (front_w @ z32) — frozen via the bowl cache (stays still through the flip) + near-side dissolve
    ctx.globalCompositeOperation='lighter'; var _led=(LED[0]*255|0)+','+(LED[1]*255|0)+','+(LED[2]*255|0);
    for(var pass=0;pass<2;pass++){ ctx.lineWidth=pass?2.6:5.5; var ba=pass?0.5:0.14;
      for(var n2=0;n2<NP;n2++){ var w0=FRONTW[n2], w1=FRONTW[(n2+1)%NP], fa3=nfa((w0[1]+w1[1])/2); if(fa3<=0.02) continue;
        var sSf=((w0[1]+w1[1])/2 < -25) ? (ckT<0.999 ? (1-smoother(cl((A-0.5)/0.42,0,1))) : 0) : 1;   // south (near) roof: full cyan OVAL only during the 1→2 reveal (camT<1); always OFF once camT=1 (chapter 2 + the 2→3 flip) so it never flashes back as the stadium fades out
        if(sSf<=0.02) continue;
        var p0=BC.roof[n2], p1=BC.roof[(n2+1)%NP];
        ctx.strokeStyle='rgba('+_led+','+(A*ba*fa3*sSf).toFixed(3)+')'; ctx.beginPath(); ctx.moveTo(p0[0],p0[1]); ctx.lineTo(p1[0],p1[1]); ctx.stroke(); } }
    ctx.globalCompositeOperation='source-over'; ctx.globalAlpha=1;
  }

  // ---------- on-grass images (team flags + KICK logo) ----------
  var _ICO={}; ['home','away'].forEach(function(k){var im=new Image(); im.src='assets/_icon_'+k+'.png'; _ICO[k]=im;});
  var _LOGO=new Image(); _LOGO.src='assets/logo_wordmark.png';
  var FLAG_DIM=0.13, SCORE_DIM=0.15;   // resting alpha (Tier-5 source values); brightens during the celebration
  // ground affine: local metre frame (lx,ly) -> screen, lying flat on the pitch at (wx,wy). e=0.6 m is load-bearing.
  function gaff(proj, wx, wy, scale, cx, cy){
    var e=0.6, p0=proj([wx,wy,0]), px=proj([wx+e,wy,0]), py=proj([wx,wy+e,0]);
    var A00=(px[0]-p0[0])/e*scale, A10=(px[1]-p0[1])/e*scale, A01=(py[0]-p0[0])/e*scale, A11=(py[1]-p0[1])/e*scale;
    return [A00,A10,A01,A11, p0[0]-(A00*cx+A01*cy), p0[1]-(A10*cx+A11*cy)];   // canvas transform args a,b,c,d,e,f
  }

  // ---------- green pitch ----------
  var TH=Math.acos(5.5/9.15);
  function poly(ctx,proj,pts,close){ ctx.beginPath(); for(var i=0;i<pts.length;i++){var p=proj([pts[i][0],pts[i][1],0]); i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]);} if(close)ctx.closePath(); ctx.stroke(); }
  function circ(cx,cy,r,a0,a1,n){ var a=[]; for(var i=0;i<=n;i++){var th=a0+(a1-a0)*i/n; a.push([cx+r*Math.cos(th),cy+r*Math.sin(th)]);} return a; }
  var LINES=[
    [[0,-34],[105,-34],[105,34],[0,34],[0,-34]], [[52.5,-34],[52.5,34]],
    [[0,-20.16],[16.5,-20.16],[16.5,20.16],[0,20.16]], [[105,-20.16],[88.5,-20.16],[88.5,20.16],[105,20.16]],
    [[0,-9.16],[5.5,-9.16],[5.5,9.16],[0,9.16]], [[105,-9.16],[99.5,-9.16],[99.5,9.16],[105,9.16]],
    circ(52.5,0,9.15,0,6.2832,48), circ(11,0,9.15,-TH,TH,26), circ(94,0,9.15,Math.PI-TH,Math.PI+TH,26)
  ];
  function drawStripes(ctx, proj, A){
    for(var i=0;i<14;i++){ var x0=105*i/14, x1=105*(i+1)/14, c0=proj([x0,-34,0]),c1=proj([x1,-34,0]),c2=proj([x1,34,0]),c3=proj([x0,34,0]);
      ctx.globalAlpha=A; ctx.fillStyle=rgb(i%2?GRASS_A:GRASS_B); ctx.beginPath(); ctx.moveTo(c0[0],c0[1]); ctx.lineTo(c1[0],c1[1]); ctx.lineTo(c2[0],c2[1]); ctx.lineTo(c3[0],c3[1]); ctx.closePath(); ctx.fill(); }
  }
  function drawLines(ctx, proj, A){
    ctx.globalAlpha=A*0.62; ctx.strokeStyle='#d6dbd0'; ctx.lineWidth=1.4; ctx.lineCap='round'; ctx.lineJoin='round';
    for(var L=0;L<LINES.length;L++) poly(ctx,proj,LINES[L], L===0);
    ctx.fillStyle='#d6dbd0';
    [[52.5,0],[11,0],[94,0]].forEach(function(m){var p=proj([m[0],m[1],0]); ctx.beginPath(); ctx.arc(p[0],p[1],2,0,6.2832); ctx.fill();});
  }
  function drawFurniture(ctx, proj, A){
    ctx.globalAlpha=A*0.7; ctx.strokeStyle='#cccccc'; ctx.lineWidth=2;
    [0,105].forEach(function(x0){ var f=[[x0,-3.66,0],[x0,-3.66,2.44],[x0,3.66,2.44],[x0,3.66,0]]; ctx.beginPath();
      for(var i=0;i<f.length;i++){var p=proj(f[i]); i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]);} ctx.stroke(); });
    [[0,-34],[0,34],[105,-34],[105,34]].forEach(function(cn){ var cx=cn[0],cy=cn[1],dd=cx<52.5?1:-1;
      ctx.globalAlpha=A*0.75; ctx.strokeStyle='#d0d0d0'; ctx.lineWidth=1.3; var b=proj([cx,cy,0]),tp=proj([cx,cy,1.5]); ctx.beginPath(); ctx.moveTo(b[0],b[1]); ctx.lineTo(tp[0],tp[1]); ctx.stroke();
      ctx.globalAlpha=A*0.85; ctx.fillStyle='#e0b23a'; var q0=proj([cx,cy,1.5]),q1=proj([cx+dd*1.4,cy,1.34]),q2=proj([cx,cy,1.12]); ctx.beginPath(); ctx.moveTo(q0[0],q0[1]); ctx.lineTo(q1[0],q1[1]); ctx.lineTo(q2[0],q2[1]); ctx.closePath(); ctx.fill(); });
    ctx.globalAlpha=1;
  }

  // ---------- on-grass flags / score / logo ----------
  function drawFlags(ctx, proj, A, clip, alpha){
    if(!clip) return; var ha=clip.score.home_atk_dir, hwx=(ha===0.0)?72.0:33.0, spec=[['home',hwx],['away',105-hwx]];
    for(var f=0;f<2;f++){ var side=spec[f][0], wx=spec[f][1], icon=_ICO[side], af=gaff(proj,wx,0,1.0,0,0);
      if(icon&&icon.complete&&icon.naturalWidth){ ctx.save(); ctx.transform(af[0],af[1],af[2],af[3],af[4],af[5]); ctx.beginPath(); ctx.arc(0,0,7,0,6.2832); ctx.clip(); ctx.globalAlpha=A*alpha; ctx.drawImage(icon,-7,-7,14,14); ctx.restore(); }
      ctx.globalAlpha=A*alpha;
      [[7.15,'#f4f4f4',2.2],[7.6,'#787d87',1.6]].forEach(function(rg){ ctx.lineWidth=rg[2]; ctx.strokeStyle=rg[1]; ctx.beginPath();
        for(var i=0;i<=48;i++){var th=i/48*6.2832, p=proj([wx+rg[0]*Math.cos(th),rg[0]*Math.sin(th),0]); i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1]);} ctx.stroke(); }); }
    ctx.globalAlpha=1;
  }
  function drawLogo(ctx, proj, A){
    if(!_LOGO.complete||!_LOGO.naturalWidth) return; var mw=15, mh=mw*_LOGO.naturalHeight/_LOGO.naturalWidth, af=gaff(proj,52.5,0,1.0,0,0);
    ctx.save(); ctx.transform(af[0],af[1],af[2],af[3],af[4],af[5]); ctx.globalAlpha=A*0.11; ctx.drawImage(_LOGO,-mw/2,-mh/2,mw,mh); ctx.restore(); ctx.globalAlpha=1;
  }
  function drawScore(ctx, proj, A, clip, phase, alpha){
    if(!clip) return; var s=clip.score, ord=(s.home_atk_dir===0.0), post=(phase==='goal'||phase==='celeb'||phase==='checker'||phase==='hold');
    var sh=post?s.home_post:s.home_pre, sa=post?s.away_post:s.away_pre, txt=ord?(sa+' - '+sh):(sh+' - '+sa), af=gaff(proj,52.5,-19.0,1.0,0,0);
    ctx.save(); ctx.transform(af[0],af[1],af[2],af[3],af[4],af[5]); ctx.globalAlpha=A*alpha; ctx.fillStyle='#ffffff';
    ctx.font='800 10px "PingFang SC",sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(txt,0,0); ctx.restore(); ctx.globalAlpha=1;
  }

  function draw(ctx, proj, projB, detail, key, t, st){
    var A=detail; if(A<=0.01) return;
    var sweep=null;
    if(st && st.clip && st.phase==='celeb'){   // goal celebration: crowd-wave sweep in the scoring team's attack direction
      var c=st.clip, scorer=hex01(c.teams[c.goal_side].kit), L=lum01(scorer);
      var hot = L>=0.82 ? [scorer[0]*0.58,scorer[1]*0.58,scorer[2]*0.58]
                        : [scorer[0]+(1-scorer[0])*0.28,scorer[1]+(1-scorer[1])*0.28,scorer[2]+(1-scorer[2])*0.28];
      var cprog=cl(st.pt*1.1,0,1), amp=smoother(cl(st.pt/0.05,0,1))*(1-smoother(cl((st.pt-0.86)/0.14,0,1)));   // 1.1 (was 1.375) → crowd wave travels 25% slower
      sweep={cprog:cprog, amp:amp, hot:hot, dir:(c.mouth[0]>=0.5?-1:1)};   // attack toward x=105 → sweep right→left
    }
    drawBowl(ctx, proj, projB, A, key, sweep);   // stadium + celebration crowd sweep
    drawStripes(ctx, proj, A);            // green pitch
    drawLines(ctx, proj, A);
    drawFurniture(ctx, proj, A);          // goal frames + corner pennants
  }
  return {draw:draw};
})();
