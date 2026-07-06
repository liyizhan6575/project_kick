// Chapter 4 · "Work with us" — broadcast penalty scene: the goal end of a FULL pitch, painted on the ground.
// Rendered through the page's 3D flip camera proj([x,y,z]); world = pitch metres (x 0..105, y -34..34, z up). No keeper, no ball, no net.
window.PENALTY = (function(){
  var GX=105, GY=3.66, GZ=2.44, HW=0.07;   // right goal line · half goal-width (7.32m) · crossbar height · half a ~14cm pitch line

  function pscale(proj, p, sz){ var a=proj([p[0],p[1],p[2]]), b=proj([p[0],p[1],p[2]+sz]); return Math.hypot(b[0]-a[0],b[1]-a[1]); }  // screen px of a world height sz at p

  function draw(ctx, proj, alpha, t, dpr){
    if(alpha<=0.01) return;
    ctx.save(); ctx.lineCap='round'; ctx.lineJoin='round'; ctx.globalAlpha=alpha;
    var DN=3.0;   // near-clip plane (camera-space depth) — kept well in front so the line-width quad doesn't balloon near the lens
    function dval(p){ return proj([p[0],p[1],0])[2]; }   // camera-space depth of a ground point
    // a pitch line is a filled quad with a real-world width → it tapers in perspective like a printed marking;
    // near-clip first so any part behind the camera doesn't smear (depth is monotonic along a straight ground segment)
    function gl(p1, p2){
      var d1=dval(p1), d2=dval(p2); if(d1<=DN && d2<=DN) return;
      if(d1<=DN || d2<=DN){ var a=(d1<=DN)?p1:p2, b=(d1<=DN)?p2:p1;
        for(var k=0;k<14;k++){ var m=[(a[0]+b[0])/2,(a[1]+b[1])/2]; if(dval(m)<=DN) a=m; else b=m; }
        if(d1<=DN) p1=b; else p2=b; }
      var dx=p2[0]-p1[0], dy=p2[1]-p1[1], L=Math.hypot(dx,dy); if(L<1e-6) return;
      var px=-dy/L*HW, py=dx/L*HW;
      var A=proj([p1[0]+px,p1[1]+py,0]), B=proj([p2[0]+px,p2[1]+py,0]), C=proj([p2[0]-px,p2[1]-py,0]), D=proj([p1[0]-px,p1[1]-py,0]);
      ctx.beginPath(); ctx.moveTo(A[0],A[1]); ctx.lineTo(B[0],B[1]); ctx.lineTo(C[0],C[1]); ctx.lineTo(D[0],D[1]); ctx.closePath(); ctx.fill();
    }
    ctx.fillStyle='rgba(150,162,178,0.5)';
    // pitch boundary at this end — the box sits inside a real pitch
    gl([105,-34],[105,34]);                                       // goal line / byline (full 68m, out to both corners)
    gl([105,-34],[60,-34]); gl([105,34],[60,34]);                 // touchlines (sidelines) running back up the pitch
    gl([88.5,-20.16],[88.5,20.16]); gl([88.5,-20.16],[105,-20.16]); gl([88.5,20.16],[105,20.16]);   // penalty box (front + sides)
    gl([99.5,-9.16],[99.5,9.16]); gl([99.5,-9.16],[105,-9.16]); gl([99.5,9.16],[105,9.16]);          // 6-yard box
    var pa=[]; for(var aa=127;aa<=233;aa+=5){ var r=aa*Math.PI/180; pa.push([94+9.15*Math.cos(r), 9.15*Math.sin(r)]); }   // penalty arc (the D)
    for(var i=0;i<pa.length-1;i++) gl(pa[i],pa[i+1]);
    // penalty spot — a filled ground circle, so it projects to a perspective ellipse (printed on the turf)
    ctx.fillStyle='rgba(150,162,178,0.62)'; ctx.beginPath();
    for(var s=0;s<=24;s++){ var sa=s/24*6.2832, q=proj([94+0.17*Math.cos(sa),0.17*Math.sin(sa),0]); (s===0)?ctx.moveTo(q[0],q[1]):ctx.lineTo(q[0],q[1]); }
    ctx.closePath(); ctx.fill();
    // --- goal frame (two posts + crossbar), no net ---
    var pw=Math.max(1.7*dpr, pscale(proj,[GX,0,1.2],0.13));
    var L0=proj([GX,-GY,0]), L1=proj([GX,-GY,GZ]), R0=proj([GX,GY,0]), R1=proj([GX,GY,GZ]);
    ctx.strokeStyle='#eef2f7'; ctx.lineWidth=pw;
    ctx.beginPath(); ctx.moveTo(L0[0],L0[1]); ctx.lineTo(L1[0],L1[1]); ctx.lineTo(R1[0],R1[1]); ctx.lineTo(R0[0],R0[1]); ctx.stroke();
    ctx.restore();
  }

  return {draw:draw};
})();
