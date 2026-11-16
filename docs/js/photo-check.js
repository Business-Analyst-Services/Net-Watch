/* Net Watch · Check a photo. Runs the baseline model in the browser: the photo never leaves the device.
   Features match model/baseline.py: HSV histogram (8x4x4), sharpness, contrast, edges, brightness, centre region. */
(function(){
function feats(src){
  const W=160,H=120,c=document.createElement('canvas');c.width=W;c.height=H;
  const x=c.getContext('2d',{willReadFrequently:true});x.imageSmoothingEnabled=true;x.imageSmoothingQuality='high';
  x.drawImage(src,0,0,W,H);const d=x.getImageData(0,0,W,H).data;
  const hist=new Float64Array(128),g=new Float64Array(W*H);
  for(let i=0,p=0;i<d.length;i+=4,p++){
    const r=d[i],gg=d[i+1],b=d[i+2],mx=Math.max(r,gg,b),mn=Math.min(r,gg,b),df=mx-mn;
    let h=0;if(df){if(mx===r)h=((gg-b)/df)%6;else if(mx===gg)h=(b-r)/df+2;else h=(r-gg)/df+4;h/=6;if(h<0)h+=1}
    const H8=Math.floor(h*255)/255,S=mx?Math.floor(df*255/mx)/255:0,V=mx/255;
    const bi=Math.min(7,Math.floor(H8*8)),bj=Math.min(3,Math.floor(S*4)),bk=Math.min(3,Math.floor(V*4));
    hist[bi*16+bj*4+bk]++;
    g[p]=Math.floor((r*299+gg*587+b*114)/1000);
  }
  const N=W*H;for(let i=0;i<128;i++)hist[i]/=N;
  const mean=a=>a.reduce((s,v)=>s+v,0)/a.length,std=(a,m)=>Math.sqrt(a.reduce((s,v)=>s+(v-m)*(v-m),0)/a.length);
  const lap=[];for(let yy=1;yy<H-1;yy++)for(let xx=1;xx<W-1;xx++){const k=yy*W+xx;lap.push(g[k]*4-g[k-W]-g[k+W]-g[k-1]-g[k+1])}
  const lm=mean(lap),lv=lap.reduce((s,v)=>s+(v-lm)*(v-lm),0)/lap.length;
  let gx=0,gy=0;for(let yy=0;yy<H;yy++)for(let xx=0;xx<W-1;xx++)gx+=Math.abs(g[yy*W+xx+1]-g[yy*W+xx]);gx/=H*(W-1);
  for(let yy=0;yy<H-1;yy++)for(let xx=0;xx<W;xx++)gy+=Math.abs(g[(yy+1)*W+xx]-g[yy*W+xx]);gy/=(H-1)*W;
  const ga=Array.from(g),gm=mean(ga),cen=[];for(let yy=30;yy<110;yy++)for(let xx=40;xx<120;xx++)cen.push(g[yy*W+xx]);const cm=mean(cen);
  return [...hist,Math.log1p(lv),std(ga,gm)/64,(gx+gy)/32,gm/255,std(cen,cm)/64,cm/255];
}
function predict(f){const M=window.MODELW;const z=M.coef.map((w,k)=>w.reduce((s,wi,i)=>s+wi*(f[i]-M.mean[i])/M.scale[i],M.intercept[k]));
  const mx=Math.max(...z),e=z.map(v=>Math.exp(v-mx)),t=e.reduce((a,b)=>a+b,0);
  const probs=Object.fromEntries(M.classes.map((c,i)=>[c,e[i]/t]));const top=M.classes[z.indexOf(mx)];
  return {top,conf:probs[top],probs,review:probs[top]<M.abstain}}
window.PhotoCheck={feats,predict,check:img=>predict(feats(img))};
})();
