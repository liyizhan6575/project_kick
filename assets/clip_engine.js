// Native broadcast-clip engine.
// Loads the per-clip position JSONs (kick_goalclip_v1) exported from Tier-5, and drives a play
// timeline: lead-in -> build-up keyframes (paced by each frame's `dur`) -> shot flight -> goal ->
// celebration (goals) OR dead-ball hold -> checker (set-pieces). Cycles through all clips forever.
window.CLIPENGINE = (function(){
  var clips=[], ready=false;
  function cl(v,a,b){return v<a?a:v>b?b:v;}
  function ss(s){s=s<0?0:s>1?1:s; return s*s*(3-2*s);}   // smoothstep — EXACTLY Tier-5 goal_sequence.ss; eases each segment so players + ball settle into every keyframe (kills the linear robot-snap)

  // appended-phase durations (seconds), after the build-up keyframes
  var SPD=0.48, SHOTCAP=1.2, LEAD=0.3, FLASH=0.35, CELEB=6.3, CHK_LEAD=1.5, CHK=2.4;   // SPD = build-up tempo (0.48 = 20% slower than 0.40) ; SHOTCAP keeps the final assist at build-up pace
  var PASS_VMAX=30, SHOT_VEL=46, CHK_MIN=0.9;   // m/s ; CHK_MIN = min seconds each checker is held in the set-piece spotlight so it reads (no flicker) ; SHOTCAP trims only the run onto the shot (no pre-shot pause, build-up keeps its natural pace) ; CELEB = celebration window (sweep + fireworks pace)
  function dwell(c,f){
    var base=(f===c.nf-1 ? Math.min(c.frames[f].dur, SHOTCAP) : c.frames[f].dur) * SPD;
    if(c.set_piece){   // CHECKER MODE: corner is WHIPPED in (seg1, fast, no cap), then each box touch is HELD ≥ CHK_MIN so the checker reads (no flicker)
      if(f>=2 && base<CHK_MIN) base=CHK_MIN;
      return base;
    }
    var a=c.frames[f-1].ball, b=c.frames[f].ball;   // open-play: cap pass velocity so long balls don't blur past the shot
    if(a&&b){ var vmin=Math.hypot(b[0]-a[0],b[1]-a[1])/PASS_VMAX; if(vmin>base) base=vmin; }
    return base;
  }

  function measure(c){
    var bu=0; for(var f=1; f<c.nf; f++) bu+=dwell(c,f);   // segment (f-1 -> f) at real Opta timing; only the pre-shot approach is trimmed
    c._bu=bu; c._lead=c.set_piece?0.12:LEAD;   // set-piece: almost no pre-roll — the ball whips off the corner immediately (no static hold on the touchline)
    var mouthM=[c.mouth[0]*105,(c.mouth[1]-0.5)*68], lb=c.frames[c.nf-1].ball||mouthM, _sd=Math.hypot(mouthM[0]-lb[0],mouthM[1]-lb[1]);
    c._shotT=_sd<3?0.06:Math.max(0.35,Math.min(1.2,_sd/SHOT_VEL));   // shot flight time; if the ball already reached the goal during build-up (Last Row goals) the shot beat is vestigial → near-zero so the celebration starts right away (no dead hang)
    if(c.set_piece && !c.is_goal){ c._tail=CHK_LEAD+CHK; }              // non-goal set-piece: checker hold only
    else                         { c._tail=c._shotT+FLASH+CELEB; }      // GOAL (open-play OR corner): header/shot flies in → ball fades → celebration
    c._total=c._lead+bu+c._tail;
  }

  function init(arr){ clips=(arr||[]).filter(Boolean); clips.forEach(measure); ready=clips.length>0; return clips; }

  // tail phase resolver: tt = seconds into the tail (after build-up); returns {phase, pt} (pt in 0..1)
  function tailPhase(c, tt){
    if(c.set_piece && !c.is_goal){   // non-goal set-piece: dead-ball checker hold
      if(tt < CHK_LEAD)        return {phase:'chk_lead', pt: tt/CHK_LEAD};
      tt -= CHK_LEAD;
      return {phase:'checker',  pt: cl(tt/CHK,0,1)};
    }
    if(tt < c._shotT)          return {phase:'shot',  pt: tt/c._shotT};
    tt -= c._shotT;
    if(tt < FLASH)             return {phase:'goal',  pt: tt/FLASH};
    tt -= FLASH;
    return {phase:'celeb', pt: cl(tt/CELEB,0,1)};
  }

  // playback state at global time gt (seconds), cycling all clips
  function state(gt){
    if(!ready) return null;
    var cyc=0, i; for(i=0;i<clips.length;i++) cyc+=clips[i]._total;
    var lt=((gt%cyc)+cyc)%cyc, idx=0;
    while(idx<clips.length-1 && lt>=clips[idx]._total){ lt-=clips[idx]._total; idx++; }
    var c=clips[idx], t=lt-c._lead, kf=0, ff=0, ph={phase:'build', pt:0};
    if(t<=0){ kf=0; ff=0; }
    else if(t < c._bu){
      var acc=0; kf=c.nf-1; ff=1;
      for(var f=1; f<c.nf; f++){ var seg=dwell(c,f); if(acc+seg>=t){ kf=f-1; ff=ss((t-acc)/seg); break; } acc+=seg; }   // smoothstep per segment — Tier-5's t=ss(k/nfr)
    } else { kf=c.nf-1; ff=1; ph=tailPhase(c, t-c._bu); }
    if(ph.phase==='build') ph={phase:'build', pt:0};
    return {clip:c, idx:idx, kf:kf, ff:ff, phase:ph.phase, pt:ph.pt, localT:lt, total:c._total};
  }

  return {init:init, state:state, get ready(){return ready;}, get clips(){return clips;}};
})();
