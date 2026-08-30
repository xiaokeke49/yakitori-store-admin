const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const root = process.cwd();
const outRoot = path.join(root, '03_VI视觉系统', '05_最终空间融合版_V3', '04_工厂生产文件');
const logoRoot = path.join(root, '03_VI视觉系统', '01_Logo文件_待放入');
const photoPath = path.join(root, '02_空间效果图', '01_最终效果图_待放入', '最终版', '01_左前外部视角_v1.png');

const C = {
  night: '#102A43', black: '#181614', walnut: '#5A3822', amber: '#D28A32',
  paper: '#E8D8BC', green: '#344536', taupe: '#8A7764', red: '#9E2F25', cream: '#F3EEE5'
};

const logoSources = {
  standard: fs.readFileSync(path.join(logoRoot, '03_V2_标准组合_矢量.svg'), 'utf8'),
  round: fs.readFileSync(path.join(logoRoot, '01_V2_圆章Logo_矢量.svg'), 'utf8'),
  vertical: fs.readFileSync(path.join(logoRoot, '04_V2_竖排反白标志_矢量.svg'), 'utf8'),
};

function extractSvg(source) {
  const vb = (source.match(/viewBox="([^"]+)"/) || [null, '0 0 100 100'])[1];
  const inner = (source.match(/<svg[^>]*>([\s\S]*)<\/svg>/i) || [null, ''])[1]
    .replace(/<title>[\s\S]*?<\/title>/gi, '').replace(/<desc>[\s\S]*?<\/desc>/gi, '');
  return {vb, inner};
}
const logos = Object.fromEntries(Object.entries(logoSources).map(([k,v]) => [k, extractSvg(v)]));

function nestedLogo(kind, x, y, w, h, extra='') {
  const l = logos[kind];
  return `<svg x="${x}" y="${y}" width="${w}" height="${h}" viewBox="${l.vb}" preserveAspectRatio="xMidYMid meet" ${extra}>${l.inner}</svg>`;
}
function text(x,y,value,size=10,fill=C.black,weight=400,anchor='start',spacing=0) {
  return `<text x="${x}" y="${y}" font-family="Microsoft YaHei,Source Han Sans SC,Arial,sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" letter-spacing="${spacing}">${value}</text>`;
}
function waves(x,y,w,color=C.walnut,opacity=1) {
  const unit=w/3;
  return `<g transform="translate(${x} ${y})" fill="none" stroke="${color}" stroke-width="1.2" opacity="${opacity}">
    <path d="M0 0 C${unit*.25} -8 ${unit*.75} 8 ${unit} 0 S${unit*1.75} -8 ${unit*2} 0 S${unit*2.75} 8 ${unit*3} 0"/>
    <path d="M0 10 C${unit*.25} 2 ${unit*.75} 18 ${unit} 10 S${unit*1.75} 2 ${unit*2} 10 S${unit*2.75} 18 ${unit*3} 10" opacity=".55"/>
  </g>`;
}
function seal(x,y,s) { return `<g transform="translate(${x} ${y})"><rect width="${s}" height="${s}" rx="${s*.08}" fill="${C.red}"/>${text(s/2,s*.68,'游',s*.55,C.paper,700,'middle')}</g>`; }
function doc(w,h,body,bg=C.cream) {
  return `<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${w}mm" height="${h}mm" viewBox="0 0 ${w} ${h}"><rect width="${w}" height="${h}" fill="${bg}"/>${body}</svg>`;
}
function bleedMarks(w,h) {
  return `<g stroke="#00AEEF" stroke-width=".25" fill="none" opacity=".75"><rect x="3" y="3" width="${w-6}" height="${h-6}" stroke-dasharray="2 1"/></g>`;
}
function ensureDir(dir){ fs.mkdirSync(dir,{recursive:true}); }

const assets=[];
function add(category, slug, label, w, h, body, opts={}) {
  const dir=path.join(outRoot,category); ensureDir(dir);
  const svg=doc(w,h,body,opts.bg || C.cream);
  const svgPath=path.join(dir,`${slug}.svg`); fs.writeFileSync(svgPath,svg,'utf8');
  assets.push({category,slug,label,w,h,svgPath,dpi:opts.dpi || (Math.max(w,h)>700?100:(Math.max(w,h)>350?150:300))});
}

// 01 Brand marks — rebuilt from approved vector sources, not raster crops.
add('01_品牌标志','01_标准组合_生产版','标准组合',300,122,
  nestedLogo('standard',12,10,276,102),'');
add('01_品牌标志','02_圆章Logo_生产版','圆章Logo',200,200,
  nestedLogo('round',10,10,180,180));
add('01_品牌标志','03_竖排标志_生产版','竖排标志',100,300,
  `<rect width="100" height="300" fill="${C.black}"/>${nestedLogo('vertical',10,12,80,276)}`,{bg:C.black});

// 02 Spatial signage.
add('02_空间标识','01_户外圆形发光灯箱_直径600mm','户外圆形发光灯箱',600,600,
  `<circle cx="300" cy="300" r="285" fill="${C.paper}" stroke="${C.black}" stroke-width="12"/>
   ${nestedLogo('round',65,65,470,470)}<circle cx="300" cy="300" r="294" fill="none" stroke="${C.amber}" stroke-width="4"/>`,{dpi:150});
add('02_空间标识','02_户外竖式灯笼_300x900mm','户外竖式灯笼',300,900,
  `<rect x="16" y="16" width="268" height="868" rx="132" fill="${C.paper}" stroke="${C.black}" stroke-width="5"/>
   <g stroke="${C.taupe}" stroke-width="1" opacity=".38">${Array.from({length:17},(_,i)=>`<path d="M28 ${65+i*46} H272"/>`).join('')}</g>
   ${nestedLogo('round',48,150,204,204)}${text(150,440,'游味烧鸟',28,C.black,700,'middle',3)}
   ${text(150,500,'炭火 · 清酒 · 冷饮',14,C.walnut,500,'middle',2)}${waves(75,590,150,C.walnut,.8)}${seal(132,690,36)}`,{dpi:150});
add('02_空间标识','03_门帘暖帘_1800x900mm','门帘暖帘',1800,900,
  `<rect width="1800" height="900" fill="${C.paper}"/>
   <g stroke="${C.walnut}" stroke-width="3" opacity=".28"><path d="M600 0V900M1200 0V900"/></g>
   ${nestedLogo('standard',360,160,1080,440)}${waves(600,700,600,C.walnut,.75)}${seal(1480,690,72)}`,{dpi:100});
add('02_空间标识','04_室内导视牌_400x600mm','室内导视牌',400,600,
  `<rect width="400" height="600" fill="${C.walnut}"/><rect x="18" y="18" width="364" height="564" fill="none" stroke="${C.amber}" stroke-width="2"/>
   <circle cx="200" cy="130" r="92" fill="${C.paper}"/>${nestedLogo('round',122,52,156,156)}${text(200,285,'烧鸟',42,C.paper,700,'middle',5)}${text(200,355,'茶酒',42,C.paper,700,'middle',5)}${text(200,425,'冷饮',42,C.paper,700,'middle',5)}${waves(100,505,200,C.paper,.7)}`,{dpi:150});

// 03 Menu and tabletop.
add('03_菜单桌面','01_菜单封面_A4_含3mm出血','菜单封面 A4',216,303,
  `${bleedMarks(216,303)}<rect x="3" y="3" width="210" height="297" fill="${C.black}"/>
   <rect x="18" y="48" width="180" height="105" rx="3" fill="${C.paper}"/>${nestedLogo('standard',26,61,164,78)}${waves(43,205,130,C.paper,.55)}${text(108,255,'后湖湖畔 · 炭火烧鸟',8,C.paper,500,'middle',2)}${seal(96,270,24)}`,{bg:C.black});
add('03_菜单桌面','02_菜单内页_A4_含3mm出血','菜单内页 A4',216,303,
  `${bleedMarks(216,303)}${nestedLogo('round',80,15,56,56)}${text(24,90,'烧鸟',13,C.black,700)}${text(192,90,'YAKITORI',6,C.taupe,500,'end',1.5)}
   ${[0,1,2,3,4,5].map((i)=>`${text(28,118+i*25,['鸡腿葱串','鸡皮','鸡软骨','提灯','时蔬','主厨推荐'][i],7,C.black,500)}${text(188,118+i*25,['18','16','16','22','12','时价'][i],7,C.walnut,500,'end')}<path d="M28 ${124+i*25}H188" stroke="${C.taupe}" stroke-width=".35" opacity=".45"/>`).join('')}
   ${text(24,240,'清酒 · 茶酒 · 冷饮',9,C.black,700)}${waves(24,268,80,C.walnut,.6)}${seal(176,260,18)}`);
add('03_菜单桌面','03_预订卡名片_90x54mm_含3mm出血','预订卡 / 名片',96,60,
  `${bleedMarks(96,60)}<rect x="3" y="3" width="90" height="54" fill="${C.black}"/><circle cx="30" cy="30" r="22" fill="${C.paper}"/>${nestedLogo('round',10,10,40,40)}${text(58,18,'游味烧鸟',6,C.paper,700)}${text(58,27,'YOU WEI YAKITORI',3.2,C.paper,400,'start',.8)}${text(58,39,'后湖湖畔 · 炭火烧鸟',3.2,C.taupe)}${seal(76,41,9)}`,{bg:C.black});
add('03_菜单桌面','04_筷套_190x35mm_含3mm出血','筷套',196,41,
  `${bleedMarks(196,41)}<rect x="3" y="3" width="190" height="35" fill="${C.paper}"/>${nestedLogo('standard',12,7,86,27)}${waves(112,16,58,C.walnut,.65)}${seal(177,13,13)}`);
add('03_菜单桌面','05_杯垫_直径90mm','杯垫',90,90,
  `<circle cx="45" cy="45" r="44" fill="#C9A978" stroke="${C.walnut}" stroke-width="1.5"/>${nestedLogo('round',8,8,74,74)}`);

// 04 Uniform print panels.
add('04_员工服装','01_T恤背部印花_280x320mm','T恤背部印花',280,320,
  `<rect width="280" height="320" fill="${C.black}"/><circle cx="140" cy="130" r="98" fill="${C.paper}"/>${nestedLogo('round',52,42,176,176)}${text(140,260,'后湖有风 · 炭火有味',10,C.paper,500,'middle',2)}${seal(128,275,24)}`,{bg:C.black});
add('04_员工服装','02_围裙胸前印花_220x280mm','围裙胸前印花',220,280,
  `<rect width="220" height="280" fill="${C.black}"/><circle cx="110" cy="95" r="72" fill="${C.paper}"/>${nestedLogo('round',49,34,122,122)}${text(110,205,'游味烧鸟',17,C.paper,700,'middle',3)}${waves(60,235,100,C.paper,.65)}`,{bg:C.black});

// 05 Packaging and labels.
add('05_包装标签','01_外卖纸袋正面_300x380mm','外卖纸袋正面',300,380,
  `<rect width="300" height="380" fill="#B89462"/>${nestedLogo('round',60,58,180,180)}${text(150,278,'后湖有风，炭火有味',11,C.black,600,'middle',2)}${waves(75,315,150,C.walnut,.8)}${seal(250,318,24)}`);
add('05_包装标签','02_外卖盒顶面_260x180mm','外卖盒顶面',260,180,
  `<rect width="260" height="180" fill="#B89462"/><rect x="8" y="8" width="244" height="164" fill="none" stroke="${C.walnut}" stroke-width="1"/>${nestedLogo('round',73,18,114,114)}${waves(80,145,100,C.walnut,.75)}${seal(220,138,20)}`);
add('05_包装标签','03_酒瓶标签_80x120mm_含3mm出血','酒瓶标签',86,126,
  `${bleedMarks(86,126)}<rect x="3" y="3" width="80" height="120" fill="${C.paper}"/>${nestedLogo('round',16,12,54,54)}${text(43,82,'游味烧鸟',8,C.black,700,'middle',2)}${text(43,94,'清酒',6,C.walnut,500,'middle',2)}${waves(18,107,50,C.walnut,.65)}${seal(66,104,10)}`);
add('05_包装标签','04_封口贴_直径50mm','封口贴',50,50,
  `<circle cx="25" cy="25" r="24" fill="${C.paper}" stroke="${C.red}" stroke-width="1"/>${nestedLogo('round',4,4,42,42)}`);

// 06 Digital poster using the original high-resolution space image, not the VI-board thumbnail.
const photoData = fs.readFileSync(photoPath).toString('base64');
add('06_社交传播','01_社交媒体夜景海报_1080x1350px','社交媒体夜景海报',108,135,
  `<defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${C.night}" stop-opacity=".05"/><stop offset="1" stop-color="${C.black}" stop-opacity=".96"/></linearGradient></defs>
   <image x="0" y="0" width="108" height="135" preserveAspectRatio="xMidYMid slice" href="data:image/png;base64,${photoData}"/>
   <rect width="108" height="135" fill="url(#fade)"/><rect x="7" y="79" width="94" height="40" rx="2" fill="${C.paper}" opacity=".94"/>${nestedLogo('standard',11,82,86,34)}${text(54,128,'后湖有风，炭火有味，在人间烟火里，游味一晚。',3.2,C.paper,500,'middle',.25)}`,
  {dpi:254});

// 07 Brand icon sheet.
add('07_图标系统','01_品牌图标组合_300x80mm','品牌图标组合',300,80,
  `<g fill="none" stroke="${C.walnut}" stroke-width="1.4">
    <circle cx="35" cy="32" r="22"/><path d="M20 29c8-8 15 8 23 0s15 8 22 0M20 38c8-8 15 8 23 0s15 8 22 0"/>
    <circle cx="92" cy="32" r="22"/><path d="M92 47c-15-12 2-21-2-35 17 13 20 25 2 35z"/>
    <circle cx="149" cy="32" r="22"/><path d="M141 44h16l-2-28h-12zM140 24h18"/>
    <circle cx="206" cy="32" r="22"/><path d="M206 47c-14-8-14-24 0-32 14 8 14 24 0 32zM206 15v32"/>
    <circle cx="263" cy="32" r="22"/><circle cx="263" cy="25" r="6"/><circle cx="249" cy="30" r="5"/><circle cx="277" cy="30" r="5"/><path d="M246 47c4-12 30-12 34 0"/>
   </g>${['临湖','炭火','茶酒','自然','相聚'].map((v,i)=>text(35+i*57,72,v,5,C.black,500,'middle')).join('')}`);

// 08 Material specification board.
add('08_材质规范','01_材质选型板_A3横版','材质选型板',420,297,
  `${text(24,32,'游味烧鸟 · V3 材质选型板',17,C.black,700)}${text(24,48,'FINAL MATERIAL SPECIFICATION',6,C.taupe,400,'start',2)}
   ${[
    ['深胡桃木',C.walnut,'木作/菜单'],['炭化木/黑金属',C.black,'板前/标识'],['暖灰肌理墙',C.taupe,'墙面/背景'],
    ['米白灯笼纸',C.paper,'灯具/留白'],['苔植深绿',C.green,'植物/户外'],['湿润深色石材','#292724','道路/地面']
   ].map((a,i)=>{const x=24+(i%3)*132,y=72+Math.floor(i/3)*95;return `<rect x="${x}" y="${y}" width="112" height="58" rx="3" fill="${a[1]}"/>${text(x,y+73,a[0],7,C.black,700)}${text(x,y+84,a[2],5,C.taupe)}`}).join('')}
   ${text(24,277,'生产前需进行实物打样；木材、纸张、油墨与灯箱透光效果以现场样板确认为准。',6,C.walnut,500)}`);

async function renderAll(){
  const manifest=[];
  for(const a of assets){
    const dpi=a.dpi;
    let pxW=Math.round(a.w/25.4*dpi), pxH=Math.round(a.h/25.4*dpi);
    const maxEdge=8000; const scale=Math.min(1,maxEdge/Math.max(pxW,pxH)); pxW=Math.max(1,Math.round(pxW*scale)); pxH=Math.max(1,Math.round(pxH*scale));
    const pngPath=a.svgPath.replace(/\.svg$/i,'_高清.png');
    await sharp(a.svgPath,{density:Math.max(144,dpi)}).resize(pxW,pxH,{fit:'fill'}).png({compressionLevel:9}).withMetadata({density:dpi}).toFile(pngPath);
    manifest.push({...a,svgPath:path.relative(root,a.svgPath),pngPath:path.relative(root,pngPath),pxW,pxH});
  }
  fs.writeFileSync(path.join(outRoot,'production_manifest.json'),JSON.stringify(manifest,null,2),'utf8');
  console.log(JSON.stringify({outRoot,count:manifest.length},null,2));
}
renderAll().catch(e=>{console.error(e);process.exit(1)});
