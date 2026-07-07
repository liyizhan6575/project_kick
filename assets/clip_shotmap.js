// Chapter-2 · page 3 — SHOT MAP, tilted onto the broadcast pitch (a JS port of Tier-5 panel_shotmap).
// Every shot of both teams is a disc lying FLAT on the grass (drawn through the flip camera P([x,y]) so it
// foreshortens in perspective, like the lane-dom dots). Tier-5 marker semantics are reproduced:
//   • SIZE   ∝ xG via r = (3 + 9√xG) · SCALE metres (demo.html parity) — the biggest chance is still a modest disc.
//   • ON-TARGET  → filled team-colour disc (no outline).
//   • OFF-TARGET → hollow team-colour ring.
//   • GOAL       → a bright gold filled disc inside a concentric ring on a soft gold glow (rings + circles only).
//   • COLOUR by team — HOME kit gold, AWAY cool-white — matching the broadcast clip's kits.
// There is no real shot dataset in the repo (the clip is one goal), so the scatter is a curated, plausible set
// consistent with the clip's 2–0 home win (home attacks the x=0 goal, per the clip's home_atk_dir=-1).
// Reveal: a short staggered pop-in (dots fade + scale up with a slight overshoot), then a hold — Tier-5's INTRO.
window.CLIPSHOTMAP = (function(){
  function ss(s){s=s<0?0:s>1?1:s;return s*s*(3-2*s);}
  function cl(v,a,b){return v<a?a:v>b?b:v;}

  // synthetic shots — pitch metres, x∈[0,105] y∈[-34,34] centre origin (same frame as VIZ_CLIPS / lane dom).
  // HOME (gold) attacks the LEFT goal (x=0): a rich cluster + 2 goals → the 2–0 story.  AWAY (white) attacks the
  // RIGHT goal (x=105): sparse, biased toward the far side so it stays clear of the bottom-right caption card.
  var SHOTS=[
    // --- HOME (gold) ---
    {x:6,  y:2,   xg:0.09, s:'h', o:'goal'},   // Duarte's poacher's finish (matches the replay's xg 0.09)
    {x:9,  y:-4,  xg:0.44, s:'h', o:'goal'},   // a clear chance, buried
    {x:11, y:6,   xg:0.22, s:'h', o:'on'},
    {x:14, y:-9,  xg:0.13, s:'h', o:'on'},
    {x:17, y:1,   xg:0.08, s:'h', o:'on'},
    {x:22, y:9,   xg:0.05, s:'h', o:'on'},
    {x:19, y:-14, xg:0.06, s:'h', o:'off'},
    {x:26, y:12,  xg:0.03, s:'h', o:'off'},
    {x:31, y:-6,  xg:0.04, s:'h', o:'off'},
    {x:24, y:-2,  xg:0.07, s:'h', o:'off'},
    // --- AWAY (white) — sparse, no goals, held toward the far half ---
    {x:94, y:11,  xg:0.10, s:'a', o:'on'},
    {x:89, y:-2,  xg:0.06, s:'a', o:'on'},
    {x:82, y:16,  xg:0.04, s:'a', o:'off'},
    {x:78, y:7,   xg:0.03, s:'a', o:'off'},
    {x:91, y:21,  xg:0.05, s:'a', o:'off'}
  ];
  var COL={h:'#fbbf24', a:'#e7ebf2'};   // home kit gold · away cool-white
  var GOLD='#fbbf24';
  var SCALE=0.21, GOAL_R=1.5;           // xG→metre-radius scale · fixed goal-marker radius (metres) — all markers 30% smaller
  var N=SHOTS.length;
  var ORDER=SHOTS.map(function(_,i){return i;}).sort(function(a,b){return SHOTS[a].xg-SHOTS[b].xg;});  // small last → on top
  function radiusM(xg){ return (3.0+9.0*Math.sqrt(cl(xg,0,1)))*SCALE; }

  // ground-plane affine at (wx,wy): LOCAL metres → screen so markers lie FLAT on the grass (same as clip_lanedom)
  function gaff(P, wx, wy){ var e=3.0, p0=P([wx,wy]), px=P([wx+e,wy]), py=P([wx,wy-e]);
    return [(px[0]-p0[0])/e,(px[1]-p0[1])/e,(py[0]-p0[0])/e,(py[1]-p0[1])/e, p0[0], p0[1]]; }

  // project a metre polyline and stroke it (pitch lines)
  function poly(ctx, P, pts, close){ ctx.beginPath();
    for(var i=0;i<pts.length;i++){ var q=P(pts[i]); i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]); }
    if(close)ctx.closePath(); ctx.stroke(); }
  // project a metre arc (cx,cy,r, angle a0→a1) as a stroked polyline
  function arc(ctx, P, cx, cy, r, a0, a1){ var n=Math.max(6,Math.round(Math.abs(a1-a0)/0.16)), pts=[];
    for(var i=0;i<=n;i++){ var a=a0+(a1-a0)*i/n; pts.push([cx+r*Math.cos(a), cy+r*Math.sin(a)]); }
    poly(ctx, P, pts, false); }

  // faint pitch skeleton (box · halfway · centre circle · both penalty areas + 6-yard boxes + spots + D-arcs · goals)
  function pitch(ctx, P, alpha, dpr){
    ctx.lineCap='round'; ctx.lineJoin='round';
    ctx.strokeStyle='rgba(214,219,208,'+(alpha*0.42).toFixed(3)+')'; ctx.lineWidth=1.2*dpr;   // #d6dbd0 — same tone/brightness as the persistent outer frame
    poly(ctx, P, [[0,-34],[105,-34],[105,34],[0,34]], true);            // outer box
    ctx.strokeStyle='rgba(214,219,208,'+(alpha*0.42).toFixed(3)+')'; ctx.lineWidth=1.0*dpr;   // inner lines aligned to the outer frame's brightness (were a dim 0.34)
    poly(ctx, P, [[52.5,-34],[52.5,34]], false);                        // halfway line
    arc(ctx, P, 52.5, 0, 9.15, 0, 6.2832);                              // centre circle
    // left end (home attacks here)
    poly(ctx, P, [[0,-20.16],[16.5,-20.16],[16.5,20.16],[0,20.16]], false);   // penalty area
    poly(ctx, P, [[0,-9.16],[5.5,-9.16],[5.5,9.16],[0,9.16]], false);         // 6-yard box
    arc(ctx, P, 11, 0, 9.15, -0.93, 0.93);                                    // D (part outside the box)
    // right end (away attacks here)
    poly(ctx, P, [[105,-20.16],[88.5,-20.16],[88.5,20.16],[105,20.16]], false);
    poly(ctx, P, [[105,-9.16],[99.5,-9.16],[99.5,9.16],[105,9.16]], false);
    arc(ctx, P, 94, 0, 9.15, Math.PI-0.93, Math.PI+0.93);
    // penalty + centre spots
    ctx.fillStyle='rgba(214,219,208,'+(alpha*0.42).toFixed(3)+')';
    [[11,0],[94,0],[52.5,0]].forEach(function(sp){ var q=P(sp); ctx.beginPath(); ctx.arc(q[0],q[1],1.6*dpr,0,6.2832); ctx.fill(); });
    // goal frames
    ctx.strokeStyle='rgba(214,219,208,'+(alpha*0.42).toFixed(3)+')'; ctx.lineWidth=1.8*dpr;
    poly(ctx, P, [[0,-3.66],[-1.8,-3.66],[-1.8,3.66],[0,3.66]], false);
    poly(ctx, P, [[105,-3.66],[106.8,-3.66],[106.8,3.66],[105,3.66]], false);
  }

  // rank → pop-in scale (staggered wave with a slight overshoot bounce), Tier-5 INTRO semantics
  var INTRO=2.0, PER=0.15;
  function appear(rank, growT){ var start=(rank/Math.max(1,N-1))*(1-PER)*INTRO, a=ss(cl((growT-start)/(PER*INTRO),0,1));
    return a*(1.0+0.22*(1-a)); }

  // alpha = overall page visibility (fades in as the pitch blacks out) · growT = seconds since the grow began
  function draw(ctx, P, alpha, growT, opt){
    if(alpha<=0.01) return;
    opt=opt||{}; var dpr=opt.dpr||1;
    ctx.save();
    // solid black fill of the PITCH ONLY (exact touchlines) — same as lane dom: hides the faded grass without
    // covering the surrounding lit stands/seats
    var fill=[[0,-34],[105,-34],[105,34],[0,34]]; ctx.globalAlpha=alpha; ctx.fillStyle='#0a0a0a';
    ctx.beginPath(); for(var fi=0;fi<4;fi++){var fq=P(fill[fi]); fi?ctx.lineTo(fq[0],fq[1]):ctx.moveTo(fq[0],fq[1]);} ctx.closePath(); ctx.fill();

    pitch(ctx, P, alpha, dpr);

    // shots — two passes so the goal balls always sit on TOP of the discs/rings
    for(var pass=0; pass<2; pass++){
      for(var oi=0; oi<ORDER.length; oi++){
        var i=ORDER[oi], sh=SHOTS[i], isGoal=(sh.o==='goal');
        if((pass===0)===isGoal) continue;                        // pass 0 = non-goals · pass 1 = goals
        var scv=appear(oi, growT); if(scv<=0.01) continue;
        var col=COL[sh.s];
        if(isGoal){
          var c=P([sh.x,sh.y]), af0=gaff(P,sh.x,sh.y), spm=Math.hypot(af0[0],af0[1]);   // screen px per metre here
          var gr=GOAL_R*spm*scv;
          ctx.save(); ctx.globalCompositeOperation='lighter';    // soft gold glow behind the ball
          var gd=ctx.createRadialGradient(c[0],c[1],0,c[0],c[1],gr*2.6);
          gd.addColorStop(0,'rgba(251,191,36,'+(0.55*alpha).toFixed(3)+')'); gd.addColorStop(0.5,'rgba(251,191,36,'+(0.20*alpha).toFixed(3)+')'); gd.addColorStop(1,'rgba(251,191,36,0)');
          ctx.fillStyle=gd; ctx.beginPath(); ctx.arc(c[0],c[1],gr*2.6,0,6.2832); ctx.fill(); ctx.restore();
          var af=gaff(P,sh.x,sh.y), grr=GOAL_R*scv; ctx.save(); ctx.transform(af[0],af[1],af[2],af[3],af[4],af[5]);
          ctx.globalAlpha=0.98*alpha; ctx.fillStyle=GOLD; ctx.beginPath(); ctx.arc(0,0,grr*0.72,0,6.2832); ctx.fill();          // GOAL = filled gold core...
          ctx.globalAlpha=alpha; ctx.strokeStyle='#fff3d6'; ctx.lineWidth=grr*0.17; ctx.beginPath(); ctx.arc(0,0,grr*1.02,0,6.2832); ctx.stroke();   // ...inside a bright concentric ring (ring + circle only, no ball icon)
          ctx.restore();
        } else {
          var r=radiusM(sh.xg)*scv, af2=gaff(P,sh.x,sh.y);
          ctx.save(); ctx.transform(af2[0],af2[1],af2[2],af2[3],af2[4],af2[5]);
          if(sh.o==='on'){ ctx.globalAlpha=0.95*alpha; ctx.fillStyle=col; ctx.beginPath(); ctx.arc(0,0,r,0,6.2832); ctx.fill(); }
          else           { ctx.globalAlpha=0.9*alpha;  ctx.strokeStyle=col; ctx.lineWidth=Math.max(0.32,r*0.26); ctx.beginPath(); ctx.arc(0,0,r*0.96,0,6.2832); ctx.stroke(); }
          ctx.restore();
        }
      }
    }
    ctx.globalAlpha=1; ctx.restore();
  }

  return { draw:draw, get shots(){return SHOTS;} };
})();
