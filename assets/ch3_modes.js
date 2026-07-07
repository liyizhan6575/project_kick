// Chapter-3 display modes 1 (xG) + 2 (xT). Mode 0 (pitch control) lives in _stage.html.
// Both render on the vertical Research board through the page's flip camera P([metreX,metreY]).
window.CH3 = (function(){
  function cl(v,a,b){return v<a?a:v>b?b:v;}
  function ss(s){s=s<0?0:s>1?1:s;return s*s*(3-2*s);}
  function lp(a,b,t){return a+(b-a)*t;}
  function sbm(x,y){return [x/120*105,(y/80-0.5)*68];}   // StatsBomb (120×80) → pitch metres (105 × ±34)

  // ===== MODE 1 · xG — NARRATED: spot → distance → angle sweep → flash GK+defenders → feature readout → flip xG → ball =====
  var SHOT=sbm(101,58), GC=sbm(120,40), PT=sbm(120,44), PB=sbm(120,36), XG=0.05;   // box corner, just outside the area — LEFT side
  var DIST_M=Math.hypot(GC[0]-SHOT[0],GC[1]-SHOT[1]);
  var ANG_DEG=(function(){ var vt=[PT[0]-SHOT[0],PT[1]-SHOT[1]], vb=[PB[0]-SHOT[0],PB[1]-SHOT[1]];
    return Math.acos(cl((vt[0]*vb[0]+vt[1]*vb[1])/(Math.hypot(vt[0],vt[1])*Math.hypot(vb[0],vb[1])),-1,1))*180/Math.PI; })();
  // categorical + boolean features the model consumes (spatial ones — location/distance/angle/keeper/defenders — are shown on the pitch)
  var PARAMS=[
    ['BODY','Right Foot'],          // shot_body_part
    ['TECHNIQUE','Normal'],         // shot_technique
    ['SHOT TYPE','Open Play'],      // shot_type
    ['PLAY PATTERN','Regular Play'],// play_pattern
    ['ASSISTED','No'],              // shot_assisted
    ['THROUGH BALL','No'],          // through_ball
    ['LOFTED PASS','No']            // lofted_pass
  ];
  // keeper + nearest defenders (gk_x/y, def1/def2 ... in the model) — flashed in as positioned checkers with their coords
  var DEFLINE=[
    {p:sbm(117,42), gk:true, c:'#46b89c', lbl:'GK 117,42'},
    {p:sbm(113,53),          c:'#6e86a6', lbl:'113,53'},
    {p:sbm(109,45),          c:'#6e86a6', lbl:'109,45'},
    {p:sbm(106,36),          c:'#6e86a6', lbl:'106,36'}
  ];

  function drawXG(ctx, P, alpha, t, W, H, dpr, sc){
    if(alpha<=0.01) return;
    var fscale=(sc&&H>W)?cl(1.7*sc/(11*dpr),0.7,1):1;   // portrait: shrink labels to track the smaller pitch; landscape stays 1:1
    var uf=Math.abs(P([105,0])[1]-P([0,0])[1])*0.0145;   // ONE base font tied to the board's ON-SCREEN length → distance/angle/defender/verdict + feature readout track the actual pitch size in EVERY window (full / half / portrait), never oversized
    var at=t%14.0;
    var pSpot=ss(cl(at/0.8,0,1));
    var distLen=ss(cl((at-1.0)/1.2,0,1)), distA=alpha*(1-ss(cl((at-2.6)/0.5,0,1)));   // distance draws in, holds, fades before the sweep
    var lineIn=ss(cl((at-3.3)/0.5,0,1)), sweep=ss(cl((at-3.9)/1.2,0,1));               // right-post line fades in, then the wedge sweeps
    var angA=alpha*(1-ss(cl((at-5.4)/0.5,0,1)));                                        // angle fades out once the sweep is read, before the defenders
    var pFade=ss(cl((at-10.8)/0.6,0,1));                                                // defenders + feature text HOLD long enough to read, then fade
    var pPar=cl((at-6.4)/2.0,0,1), parA=alpha*(1-pFade);                                // typed 6.4-8.4, then held readable until 10.8
    var pBall=ss(cl((at-11.6)/0.5,0,1));
    var s=P(SHOT), gc=P(GC), pt=P(PT), pb=P(PB);
    var perpx=gc[1]-s[1], perpy=s[0]-gc[0], perpl=Math.hypot(perpx,perpy)||1; perpx/=perpl; perpy/=perpl;   // unit perpendicular, LEFT of the shot→goal axis
    ctx.save(); ctx.lineCap='round'; ctx.textBaseline='alphabetic';

    // --- distance: dashed line shot→goal; number sits OFF the line (perpendicular offset) ---
    if(distLen>0.001&&distA>0.01){ ctx.globalAlpha=distA; ctx.setLineDash([5*dpr,4*dpr]); ctx.strokeStyle='rgba(230,234,244,0.78)'; ctx.lineWidth=1.4*dpr;
      ctx.beginPath(); ctx.moveTo(s[0],s[1]); ctx.lineTo(lp(s[0],gc[0],distLen),lp(s[1],gc[1],distLen)); ctx.stroke(); ctx.setLineDash([]);
      if(distLen>0.55){ ctx.globalAlpha=distA*ss(cl((distLen-0.55)/0.4,0,1)); ctx.fillStyle='#e6eaf4'; ctx.font='600 '+uf+'px ui-monospace,monospace'; ctx.textAlign='center';
        ctx.fillText(DIST_M.toFixed(1)+' m', lp(s[0],gc[0],-0.22), lp(s[1],gc[1],-0.22)); } }   // label sits just BEYOND the shot (away from the goal), in open grass clear of the box / 6-yard / arc lines

    // --- angle: line to the RIGHT post fades in, THEN the wedge sweeps across; label nudged LEFT clear of the fan ---
    if(lineIn>0.001&&angA>0.01){
      ctx.globalAlpha=angA*lineIn*0.85; ctx.strokeStyle='#fbbf24'; ctx.lineWidth=1.7*dpr;
      ctx.beginPath(); ctx.moveTo(s[0],s[1]); ctx.lineTo(pb[0],pb[1]); ctx.stroke();
      if(sweep>0.001){ var swp=[lp(pb[0],pt[0],sweep),lp(pb[1],pt[1],sweep)];
        ctx.globalAlpha=angA*0.15; ctx.fillStyle='#fbbf24'; ctx.beginPath(); ctx.moveTo(s[0],s[1]); ctx.lineTo(pb[0],pb[1]); ctx.lineTo(swp[0],swp[1]); ctx.closePath(); ctx.fill();
        ctx.globalAlpha=angA*0.9; ctx.strokeStyle='#fbbf24'; ctx.lineWidth=1.7*dpr; ctx.beginPath(); ctx.moveTo(s[0],s[1]); ctx.lineTo(swp[0],swp[1]); ctx.stroke(); }
      if(sweep>0.5){ ctx.globalAlpha=angA*ss(cl((sweep-0.5)/0.4,0,1)); ctx.fillStyle='#fbbf24'; ctx.font='600 '+uf+'px ui-monospace,monospace'; ctx.textAlign='center';
        ctx.fillText(ANG_DEG.toFixed(0)+'°', lp(s[0],gc[0],0.24)+perpx*16*dpr, lp(s[1],gc[1],0.24)+perpy*16*dpr); } }

    // --- after the sweep: FLASH IN the keeper + nearest defenders, each tagged with its location at the top-right ---
    for(var di=0; di<DEFLINE.length; di++){
      var d=DEFLINE[di], st=5.7+di*0.16, app=ss(cl((at-st)/0.4,0,1)); if(app<=0.001) continue;
      var dp=P(d.p), a=alpha*app*(1-pFade), fr=cl((at-st)/0.55,0,1);
      if(fr>0&&fr<1){ ctx.globalAlpha=a*(1-fr)*0.8; ctx.strokeStyle=d.c; ctx.lineWidth=1.4*dpr; ctx.beginPath(); ctx.arc(dp[0],dp[1],(4+11*fr)*dpr,0,6.283); ctx.stroke(); }   // expanding flash ring
      ctx.globalAlpha=a; ctx.fillStyle=d.c; ctx.beginPath(); ctx.arc(dp[0],dp[1],(d.gk?5.2:4.6)*dpr,0,6.283); ctx.fill();
      ctx.strokeStyle='rgba(255,255,255,0.55)'; ctx.lineWidth=1.1*dpr; ctx.stroke();
      ctx.globalAlpha=a*0.92; ctx.fillStyle='#b4bac3'; ctx.font='600 '+(uf*0.76)+'px ui-monospace,monospace'; ctx.textAlign='left'; ctx.fillText(d.lbl, dp[0]+7*dpr, d.gk?dp[1]+13*dpr:dp[1]-6*dpr);   // GK sits near the top goal line → drop its label BELOW the dot so it clears the edge
    }

    // --- feature readout (top-half RIGHT, clear of pitch lines): YELLOW titles fade in together, THEN light-grey values type in one by one ---
    if(at>6.4&&parA>0.01){
      var maxT=0,maxV=0; PARAMS.forEach(function(p){ maxT=Math.max(maxT,p[0].length); maxV=Math.max(maxV,p[1].length); });
      var col=maxT+2, ncell=col+maxV;
      var x0=P([73.25,0])[0], availW=P([73.25,-34])[0]-x0-6*dpr;   // pitch centre line → right sideline
      ctx.font='600 10px ui-monospace,monospace'; var u=ctx.measureText('0').width/10;
      var fs=Math.min(availW/(ncell*u), uf);                      // sized to BOTH the pitch width and the shared viewport base → scales with the screen, matches the on-pitch labels
      ctx.font='600 '+fs+'px ui-monospace,monospace'; var chW=ctx.measureText('0').width, lh=fs*1.42;
      var lx=x0, ly=P([73.25,0])[1]-3*lh;   // LEFT EDGE on the pitch's centre line; block vertically centred there
      var titleA=ss(cl((at-6.4)/0.6,0,1));                        // 1) ALL feature titles fade in together
      var totV=0; PARAMS.forEach(function(p){totV+=p[1].length;});
      var valShown=Math.floor(cl((at-7.1)/2.4,0,1)*totV), vcum=0;  // 2) THEN each value writes in, one entry after another
      ctx.textAlign='left';
      for(var li=0;li<PARAMS.length;li++){ var ti=PARAMS[li][0], va=PARAMS[li][1], ty=ly+li*lh, vv=cl(valShown-vcum,0,va.length);
        ctx.globalAlpha=parA*titleA; ctx.fillStyle='#fbbf24'; ctx.fillText(ti, lx, ty);
        if(vv>0){ ctx.globalAlpha=parA; ctx.fillStyle='#c8ccd2'; ctx.fillText(va.slice(0,vv), lx+col*chW, ty); }
        if(titleA>0.99&&valShown>=vcum&&valShown<vcum+va.length){ ctx.globalAlpha=parA; ctx.fillStyle='#c8ccd2'; ctx.fillText('▋', lx+col*chW+vv*chW, ty); }   // caret on the row currently typing
        vcum+=va.length; } }

    // --- shot spot (the marker that becomes the ball) ---
    ctx.globalAlpha=alpha*pSpot*(1-pBall);
    ctx.fillStyle='#fbbf24'; ctx.beginPath(); ctx.arc(s[0],s[1],4.6*dpr,0,6.283); ctx.fill();
    ctx.strokeStyle='#0a0a0c'; ctx.lineWidth=1.2*dpr; ctx.stroke();

    // --- ball flies to the goalmouth (fast) and fades out as it crosses the goal line ---
    if(pBall>0){ var bp=[lp(s[0],gc[0],pBall),lp(s[1],gc[1],pBall)]; ctx.globalAlpha=alpha*(1-ss(cl((pBall-0.82)/0.18,0,1)));
      ctx.fillStyle='#ffffff'; ctx.beginPath(); ctx.arc(bp[0],bp[1],3.6*dpr,0,6.283); ctx.fill();
      ctx.lineWidth=0.8*dpr; ctx.strokeStyle='rgba(30,30,30,0.6)'; ctx.stroke(); }

    // --- verdict: one line, right on top of the pitch — number's right edge aligned to the pitch's RIGHT sideline, label LEFT of it ---
    { var ny=P([105,0])[1]-13*dpr, nvUp=ss(cl((at-8.5)/0.4,0,1)), nvDown=ss(cl((at-12.1)/0.35,0,1)), val=(XG*nvUp*(1-nvDown)).toFixed(2), xR=P([105,-34])[0], gap=10*dpr;   // label ALWAYS on top; number 0.00 → flips to 0.05 once all metrics are shown → back to 0.00 after the goal fades
      ctx.globalAlpha=alpha; ctx.textAlign='right';
      ctx.font='800 '+(Math.max(uf*1.4, H*0.015*fscale))+'px ui-monospace,monospace'; ctx.fillStyle='#fbbf24'; ctx.fillText(val, xR, ny);   // value = max(board-relative, viewport-relative): board-rel wins full-screen, viewport-rel wins half-screen → readable in both, identical to xT
      var vw=ctx.measureText(val).width;
      ctx.font='600 '+(Math.max(uf, 11*dpr*fscale))+'px ui-monospace,monospace'; ctx.fillStyle='#9aa0a8'; ctx.fillText('EXPECTED GOAL', xR-vw-gap, ny); }   // label: same max() so both readouts track full & half screen identically
    ctx.restore();
  }

  function tag(ctx, p, txt, col, a, dpr, fscale){ fscale=fscale||1;
    ctx.globalAlpha=a; ctx.font='600 '+(11*dpr*fscale)+'px ui-monospace,monospace'; ctx.textBaseline='middle';
    ctx.fillStyle='rgba(10,10,12,0.72)'; var w=ctx.measureText(txt).width+8*dpr*fscale;
    ctx.fillRect(p[0]+8*dpr*fscale, p[1]-8*dpr*fscale, w, 16*dpr*fscale);
    ctx.fillStyle=col; ctx.fillText(txt, p[0]+12*dpr*fscale, p[1]);
  }

  // ===== MODE 2 · xT — chain over our model's PER-ACTION threat surfaces (NOT a single xT grid) =====
  // Each action type has its OWN 16×12 surface V_T(loc)=P(score next k), generated from threat_model/value_gbm.pkl.
  // col = x (0 own goal → 15 attacking goal), row = y (0 → 11 touchline).
  var GRID_TACKLE=[
    [0.0005,0.0004,0.0005,0.0007,0.0007,0.0007,0.0007,0.0008,0.0014,0.0020,0.0025,0.0027,0.0034,0.0041,0.0029,0.0026],
    [0.0004,0.0004,0.0007,0.0007,0.0007,0.0008,0.0008,0.0008,0.0015,0.0015,0.0020,0.0022,0.0022,0.0020,0.0021,0.0021],
    [0.0005,0.0004,0.0007,0.0007,0.0008,0.0008,0.0009,0.0009,0.0019,0.0018,0.0022,0.0030,0.0021,0.0020,0.0026,0.0029],
    [0.0005,0.0007,0.0009,0.0008,0.0009,0.0008,0.0008,0.0010,0.0019,0.0019,0.0028,0.0026,0.0025,0.0027,0.0035,0.0041],
    [0.0006,0.0008,0.0010,0.0010,0.0011,0.0011,0.0009,0.0015,0.0020,0.0020,0.0024,0.0032,0.0031,0.0071,0.0122,0.0112],
    [0.0006,0.0008,0.0011,0.0010,0.0011,0.0011,0.0010,0.0016,0.0026,0.0023,0.0024,0.0036,0.0037,0.0104,0.0112,0.0172],
    [0.0005,0.0007,0.0010,0.0008,0.0009,0.0010,0.0009,0.0016,0.0024,0.0021,0.0023,0.0035,0.0036,0.0102,0.0128,0.0142],
    [0.0004,0.0007,0.0010,0.0008,0.0009,0.0009,0.0009,0.0014,0.0019,0.0020,0.0022,0.0029,0.0030,0.0075,0.0107,0.0086],
    [0.0004,0.0006,0.0009,0.0008,0.0009,0.0009,0.0009,0.0013,0.0018,0.0018,0.0020,0.0021,0.0023,0.0026,0.0031,0.0024],
    [0.0004,0.0005,0.0009,0.0008,0.0009,0.0009,0.0009,0.0011,0.0016,0.0016,0.0019,0.0020,0.0019,0.0018,0.0019,0.0015],
    [0.0004,0.0004,0.0008,0.0007,0.0008,0.0007,0.0007,0.0009,0.0012,0.0017,0.0020,0.0024,0.0018,0.0019,0.0016,0.0013],
    [0.0005,0.0005,0.0006,0.0008,0.0008,0.0008,0.0008,0.0010,0.0013,0.0012,0.0019,0.0021,0.0016,0.0021,0.0016,0.0016]
  ];
  var GRID_CARRY=[
    [0.0009,0.0006,0.0009,0.0013,0.0013,0.0014,0.0016,0.0016,0.0025,0.0039,0.0040,0.0045,0.0071,0.0102,0.0084,0.0077],
    [0.0006,0.0006,0.0010,0.0012,0.0013,0.0016,0.0015,0.0016,0.0025,0.0024,0.0028,0.0041,0.0049,0.0053,0.0067,0.0071],
    [0.0007,0.0007,0.0011,0.0012,0.0015,0.0016,0.0019,0.0018,0.0029,0.0029,0.0036,0.0046,0.0054,0.0054,0.0075,0.0082],
    [0.0008,0.0011,0.0017,0.0017,0.0020,0.0017,0.0018,0.0020,0.0028,0.0033,0.0035,0.0045,0.0062,0.0085,0.0113,0.0127],
    [0.0011,0.0013,0.0019,0.0019,0.0023,0.0024,0.0020,0.0023,0.0033,0.0032,0.0029,0.0047,0.0065,0.0202,0.0422,0.0310],
    [0.0011,0.0013,0.0020,0.0020,0.0024,0.0025,0.0021,0.0027,0.0044,0.0038,0.0038,0.0064,0.0106,0.0205,0.0960,0.1945],
    [0.0008,0.0012,0.0017,0.0018,0.0021,0.0022,0.0021,0.0027,0.0043,0.0038,0.0038,0.0064,0.0106,0.0203,0.1100,0.1355],
    [0.0008,0.0012,0.0017,0.0017,0.0020,0.0022,0.0021,0.0024,0.0036,0.0037,0.0038,0.0059,0.0073,0.0130,0.0293,0.0203],
    [0.0008,0.0010,0.0017,0.0017,0.0020,0.0020,0.0021,0.0023,0.0034,0.0034,0.0036,0.0043,0.0060,0.0079,0.0097,0.0067],
    [0.0007,0.0008,0.0018,0.0017,0.0020,0.0019,0.0020,0.0019,0.0027,0.0028,0.0035,0.0043,0.0050,0.0067,0.0064,0.0049],
    [0.0008,0.0009,0.0019,0.0018,0.0024,0.0020,0.0018,0.0019,0.0026,0.0027,0.0030,0.0044,0.0045,0.0062,0.0053,0.0044],
    [0.0009,0.0008,0.0012,0.0016,0.0017,0.0016,0.0017,0.0016,0.0024,0.0024,0.0026,0.0031,0.0037,0.0061,0.0052,0.0051]
  ];
  var GRID_PASS=[
    [0.0007,0.0005,0.0007,0.0010,0.0010,0.0011,0.0012,0.0012,0.0018,0.0028,0.0029,0.0028,0.0039,0.0049,0.0035,0.0032],
    [0.0004,0.0005,0.0008,0.0009,0.0010,0.0012,0.0011,0.0012,0.0018,0.0018,0.0020,0.0024,0.0025,0.0024,0.0027,0.0029],
    [0.0006,0.0005,0.0009,0.0010,0.0011,0.0012,0.0014,0.0014,0.0022,0.0024,0.0025,0.0025,0.0029,0.0030,0.0041,0.0039],
    [0.0010,0.0008,0.0013,0.0012,0.0014,0.0012,0.0013,0.0014,0.0022,0.0025,0.0024,0.0027,0.0034,0.0051,0.0048,0.0047],
    [0.0013,0.0010,0.0014,0.0014,0.0016,0.0017,0.0015,0.0017,0.0025,0.0024,0.0021,0.0026,0.0036,0.0048,0.0124,0.0096],
    [0.0014,0.0010,0.0015,0.0015,0.0017,0.0018,0.0015,0.0019,0.0030,0.0029,0.0027,0.0038,0.0043,0.0074,0.0110,0.0221],
    [0.0007,0.0009,0.0013,0.0013,0.0015,0.0016,0.0016,0.0019,0.0031,0.0029,0.0028,0.0038,0.0043,0.0075,0.0128,0.0163],
    [0.0006,0.0009,0.0013,0.0013,0.0015,0.0016,0.0015,0.0018,0.0026,0.0028,0.0027,0.0034,0.0042,0.0051,0.0102,0.0074],
    [0.0006,0.0008,0.0013,0.0013,0.0015,0.0015,0.0016,0.0017,0.0025,0.0027,0.0025,0.0027,0.0033,0.0047,0.0046,0.0033],
    [0.0006,0.0006,0.0013,0.0012,0.0013,0.0014,0.0015,0.0015,0.0022,0.0023,0.0024,0.0024,0.0025,0.0032,0.0033,0.0027],
    [0.0006,0.0006,0.0011,0.0011,0.0013,0.0012,0.0012,0.0013,0.0017,0.0019,0.0020,0.0022,0.0022,0.0026,0.0023,0.0019],
    [0.0007,0.0006,0.0009,0.0012,0.0011,0.0012,0.0013,0.0012,0.0018,0.0018,0.0018,0.0019,0.0020,0.0027,0.0021,0.0021]
  ];
  var GRIDS={TACKLE:GRID_TACKLE, CARRY:GRID_CARRY, PASS:GRID_PASS}, GRIDMAX={};
  (function(){ for(var k in GRIDS){ var mx=0; GRIDS[k].forEach(function(row){ row.forEach(function(v){ if(v>mx) mx=v; }); }); GRIDMAX[k]=mx; } })();
  var XT=[
    {a:sbm(46,40), b:sbm(46,40),  kind:'TACKLE'},   // ball won centrally — chain start
    {a:sbm(46,40), b:sbm(60,42),  kind:'CARRY'},    // carry forward through the centre
    {a:sbm(60,42), b:sbm(76,14),  kind:'PASS'},     // pass out to the RIGHT wing (switch the play)
    {a:sbm(76,14), b:sbm(98,10),  kind:'CARRY'},    // carry up the right wing, into the attacking third
    {a:sbm(98,10), b:sbm(110,44), kind:'PASS'}      // cross from the right wing into the box (high xT)
  ];
  // active threat surface — YELLOW→WHITE heatmap (each grid normalised by its own max), crossfading between two action types
  function drawGrid(ctx, P, a, dpr, kA, kB, cf){
    var GA=GRIDS[kA], GB=GRIDS[kB], mA=GRIDMAX[kA], mB=GRIDMAX[kB], gap=0.6*dpr;
    for(var r=0;r<12;r++) for(var c=0;c<16;c++){
      var ti=Math.pow(cl(lp(GA[r][c]/mA, GB[r][c]/mB, cf),0,1),0.6);
      var p0=P([c/16*105, r/12*68-34]), p1=P([(c+1)/16*105, (r+1)/12*68-34]);
      var rx=Math.min(p0[0],p1[0]), ry=Math.min(p0[1],p1[1]), rw=Math.abs(p1[0]-p0[0]), rh=Math.abs(p1[1]-p0[1]);
      ctx.globalAlpha=a*(0.07+ti*0.5);
      ctx.fillStyle='rgb(255,'+Math.round(lp(191,255,ti))+','+Math.round(lp(36,255,ti))+')';   // gold → white
      ctx.fillRect(rx+gap, ry+gap, rw-2*gap, rh-2*gap);
    }
  }
  // grid-cell helpers for the start→end highlight
  function cellOf(pos){ return {c:cl(Math.floor(pos[0]/105*16),0,15), r:cl(Math.floor((pos[1]+34)/68*12),0,11)}; }
  function cellRect(P, cell){ var p0=P([cell.c/16*105, cell.r/12*68-34]), p1=P([(cell.c+1)/16*105, (cell.r+1)/12*68-34]);
    return [Math.min(p0[0],p1[0]), Math.min(p0[1],p1[1]), Math.abs(p1[0]-p0[0]), Math.abs(p1[1]-p0[1])]; }
  function drawXT(ctx, P, alpha, t, W, H, dpr, sc){
    if(alpha<=0.01) return;
    var fscale=(sc&&H>W)?cl(1.7*sc/(11*dpr),0.7,1):1;   // portrait: shrink labels to track the smaller pitch; landscape stays 1:1
    var uf=Math.abs(P([105,0])[1]-P([0,0])[1])*0.0145;   // board-relative base (as in drawXG) — combined via max() below so the readout matches xG's sizing in BOTH full & half screen
    var n=XT.length, per=2.6, total=n*per+2.6, at=t%total, i, ev, st, p, A, B;   // slower per-event so the value + map read
    var ci=Math.min(Math.floor(at/per),n-1), pcur=ss(cl((at-ci*per)/per,0,1)), aev=XT[ci];
    ctx.save(); ctx.textBaseline='alphabetic';
    // active threat surface — crossfades to each event's OWN action-type grid
    var gridA=alpha;   // the coloured grid is the PERMANENT xT-mode background — only fades on mode switch (via alpha)
    if(gridA>0.01){ var cf=ss(cl((at-ci*per)/0.45,0,1)), kPrev=XT[(ci-1+n)%n].kind;
      drawGrid(ctx, P, gridA, dpr, kPrev, aev.kind, cf);
      // cell trail: each action's end cell lights up; the previous one dims (rolling bright head + dim trail, not a reset)
      ctx.strokeStyle='#ffffff'; ctx.lineWidth=1.5*dpr; var ramp=cl(pcur*1.6,0,1);
      for(var ei=0;ei<=ci;ei++){ var f=(ei===ci)?lp(0.28,1.0,ramp):(ei===ci-1)?lp(1.0,0.28,ramp):0.28;
        var er=cellRect(P,cellOf(XT[ei].b)); ctx.globalAlpha=gridA*f; ctx.strokeRect(er[0],er[1],er[2],er[3]); } }
    // PASS 1 — every chain line, BEHIND the dots
    for(i=0;i<n;i++){ ev=XT[i]; st=i*per; p=ss(cl((at-st)/per,0,1)); if(p<=0||ev.a===ev.b) continue;
      A=P(ev.a); B=P(ev.b);
      ctx.strokeStyle='#ffffff'; ctx.globalAlpha=alpha*(0.4+0.5*p); ctx.lineWidth=2*dpr; ctx.lineCap='round';   // unified: every trace WHITE (no per-event hue)
      if(ev.kind==='CARRY') ctx.setLineDash([5*dpr,4*dpr]);
      ctx.beginPath(); ctx.moveTo(A[0],A[1]); ctx.lineTo(lp(A[0],B[0],p),lp(A[1],B[1],p)); ctx.stroke(); ctx.setLineDash([]); }
    // PASS 2 — every dot + kind label, ON TOP of all the lines
    for(i=0;i<n;i++){ ev=XT[i]; st=i*per; p=ss(cl((at-st)/per,0,1)); if(p<=0) continue;
      A=P(ev.a); B=P(ev.b); var hp=[lp(A[0],B[0],p),lp(A[1],B[1],p)];
      ctx.globalAlpha=alpha; ctx.fillStyle='#fbbf24'; ctx.beginPath(); ctx.arc(hp[0],hp[1],4*dpr,0,6.283); ctx.fill();   // unified: every dot YELLOW
      ctx.strokeStyle='rgba(8,8,10,0.65)'; ctx.lineWidth=1*dpr; ctx.stroke();
      var la=alpha*ss(cl((at-st-per*0.7)/0.4,0,1));
      if(la>0.01) tag(ctx, B, ev.kind, '#f2f4f7', la, dpr, fscale); }   // unified: tags black & white (near-white text on the dark chip)
    // header above the pitch — TOP-LEFT: which map · TOP-RIGHT: expected threat for this event
    if(gridA>0.01){ var ny=P([105,0])[1]-13*dpr, xL=P([105,34])[0], xR=P([105,-34])[0]; ctx.textBaseline='alphabetic'; ctx.globalAlpha=alpha;
      // TOP-LEFT — active surface label: persistent (no fade); only the type word swaps per event
      ctx.textAlign='left'; ctx.font='700 '+(11*dpr*fscale)+'px ui-monospace,monospace'; ctx.fillStyle='#d6dae0'; ctx.fillText(aev.kind, xL, ny);   // neutral (no per-event hue) — avoids the red/blue height illusion
      ctx.font='600 '+(11*dpr*fscale)+'px ui-monospace,monospace'; ctx.fillStyle='#8a909a'; ctx.fillText(' SURFACE', xL+ctx.measureText(aev.kind).width, ny);
      // TOP-RIGHT — "EXPECTED THREAT" persistent; only the NUMBER animates (counts from the previous event's value)
      var pi=(ci-1+n)%n, bC2=cellOf(aev.b), pC2=cellOf(XT[pi].b),
          curV=GRIDS[aev.kind][bC2.r][bC2.c], prevV=GRIDS[XT[pi].kind][pC2.r][pC2.c],
          vtxt=lp(prevV, curV, ss(cl((at-ci*per)/0.4,0,1))).toFixed(3);
      ctx.textAlign='right'; ctx.font='800 '+(Math.max(uf*1.4, H*0.015*fscale))+'px ui-monospace,monospace'; ctx.fillStyle='#fbbf24'; ctx.fillText(vtxt, xR, ny);   // value = max(board-relative, viewport-relative): board-rel wins full-screen, viewport-rel wins half-screen → readable in both, identical to xG
      var vw=ctx.measureText(vtxt).width;
      ctx.font='600 '+(Math.max(uf, 11*dpr*fscale))+'px ui-monospace,monospace'; ctx.fillStyle='#9aa0a8'; ctx.fillText('EXPECTED THREAT', xR-vw-10*dpr, ny); }   // label: same max() so both readouts track full & half screen identically
    ctx.restore();
  }

  return {drawXG:drawXG, drawXT:drawXT};
})();
