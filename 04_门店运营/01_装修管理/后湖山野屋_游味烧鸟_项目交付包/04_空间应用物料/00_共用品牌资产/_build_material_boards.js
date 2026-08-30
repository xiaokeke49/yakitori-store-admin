const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

const root = path.resolve(__dirname, "..");
const dataUri = (name) => `data:image/png;base64,${fs.readFileSync(path.join(__dirname, name)).toString("base64")}`;
const logo = dataUri("V2_标准组合_透明底.png");
const round = dataUri("V2_圆章Logo_透明底.png");
const reverse = dataUri("V2_竖排标志_反白透明底.png");

const C = {
  paper: "#F5F0E8", ink: "#222220", lake: "#48616B", warm: "#CDC3BA",
  moss: "#606042", wood: "#5D442F", orange: "#DD8245", tea: "#D7CABC", city: "#97826E",
};

function shell(title, en, drawing, notes, material) {
  const noteSvg = notes.map((t, i) => `<text x="1120" y="${380 + i * 58}" class="body">${t}</text>`).join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000" viewBox="0 0 1600 1000">
    <style>
      .title{font-family:'Microsoft YaHei','Source Han Sans SC',sans-serif;font-size:46px;font-weight:700;fill:${C.ink}}
      .en{font-family:Montserrat,Arial,sans-serif;font-size:16px;letter-spacing:5px;fill:${C.city}}
      .body{font-family:'Microsoft YaHei','Source Han Sans SC',sans-serif;font-size:25px;fill:${C.ink}}
      .small{font-family:'Microsoft YaHei','Source Han Sans SC',sans-serif;font-size:20px;fill:${C.city}}
      .label{font-family:'Microsoft YaHei','Source Han Sans SC',sans-serif;font-size:22px;font-weight:700;fill:${C.paper}}
    </style>
    <rect width="1600" height="1000" fill="${C.paper}"/>
    <rect x="0" y="0" width="24" height="1000" fill="${C.orange}"/>
    <text x="80" y="100" class="title">${title}</text>
    <text x="82" y="142" class="en">${en}</text>
    <line x1="80" y1="182" x2="1520" y2="182" stroke="${C.warm}" stroke-width="2"/>
    <rect x="80" y="230" width="970" height="650" rx="18" fill="#E7DED0" stroke="#CABCA8"/>
    ${drawing}
    <rect x="1090" y="230" width="430" height="650" rx="18" fill="#EEE7DC"/>
    <rect x="1090" y="230" width="430" height="82" rx="18" fill="${C.lake}"/>
    <rect x="1090" y="290" width="430" height="22" fill="${C.lake}"/>
    <text x="1120" y="282" class="label">制作要点</text>
    ${noteSvg}
    <line x1="1120" y1="710" x2="1490" y2="710" stroke="${C.warm}"/>
    <text x="1120" y="758" class="small">材质：${material}</text>
    <circle cx="1130" cy="822" r="18" fill="${C.ink}"/><circle cx="1180" cy="822" r="18" fill="${C.lake}"/><circle cx="1230" cy="822" r="18" fill="${C.wood}"/><circle cx="1280" cy="822" r="18" fill="${C.orange}"/>
    <text x="80" y="945" class="small">游味烧鸟 VI · 当前采用 V2 · 生产前须按现场尺寸及供应商工艺深化</text>
  </svg>`;
}

const boards = [
  {
    folder: "01_门头与木质Logo标牌", title: "门头与木质 Logo 标牌", en: "FACADE SIGNAGE",
    notes: ["炭化木横向纹理", "米白立体字", "暖阳橙红印", "2700K 均匀背光"], material: "炭化木 / 黑化钢 / 暖白发光字",
    drawing: `<rect x="145" y="340" width="840" height="360" rx="8" fill="${C.wood}"/><g opacity=".23" stroke="#C49A73"><line x1="180" y1="350" x2="180" y2="690"/><line x1="250" y1="350" x2="250" y2="690"/><line x1="340" y1="350" x2="340" y2="690"/><line x1="460" y1="350" x2="460" y2="690"/><line x1="610" y1="350" x2="610" y2="690"/><line x1="770" y1="350" x2="770" y2="690"/><line x1="900" y1="350" x2="900" y2="690"/></g><rect x="190" y="390" width="750" height="260" rx="4" fill="#1D1A17"/><image href="${reverse}" x="440" y="395" width="250" height="230" preserveAspectRatio="xMidYMid meet"/><path d="M145 715 H985" stroke="${C.orange}" stroke-width="10" opacity=".7"/>`
  },
  {
    folder: "02_中部沙发区圆形品牌标志", title: "中部沙发区圆形品牌标志", en: "LOUNGE BRAND MEDALLION",
    notes: ["直径 600–700 mm", "与沙发中轴对齐", "保留底部湖纹", "红印只出现一次"], material: "深色木板 / 米白浅浮雕 / 暖光",
    drawing: `<rect x="170" y="285" width="790" height="535" fill="#3B2A20"/><g stroke="#7A543D" stroke-width="13"><line x1="200" y1="285" x2="200" y2="820"/><line x1="255" y1="285" x2="255" y2="820"/><line x1="310" y1="285" x2="310" y2="820"/><line x1="365" y1="285" x2="365" y2="820"/><line x1="420" y1="285" x2="420" y2="820"/><line x1="475" y1="285" x2="475" y2="820"/><line x1="530" y1="285" x2="530" y2="820"/><line x1="585" y1="285" x2="585" y2="820"/><line x1="640" y1="285" x2="640" y2="820"/><line x1="695" y1="285" x2="695" y2="820"/><line x1="750" y1="285" x2="750" y2="820"/><line x1="805" y1="285" x2="805" y2="820"/><line x1="860" y1="285" x2="860" y2="820"/><line x1="915" y1="285" x2="915" y2="820"/></g><circle cx="565" cy="550" r="220" fill="${C.paper}" opacity=".97"/><image href="${round}" x="345" y="330" width="440" height="440" preserveAspectRatio="xMidYMid meet"/>`
  },
  {
    folder: "03_展示冰箱木质品牌底座", title: "展示冰箱木质品牌底座", en: "REFRIGERATED DISPLAY BASE",
    notes: ["约 2000 mm 长", "可拆检修面板", "不遮挡散热口", "后方不新增操作台"], material: "耐候原木 / 黑化金属 / 低反玻璃",
    drawing: `<rect x="145" y="310" width="840" height="360" rx="26" fill="#2C2927"/><rect x="180" y="345" width="770" height="270" rx="14" fill="#7E8D8B" opacity=".72"/><g fill="${C.orange}" opacity=".9"><ellipse cx="260" cy="430" rx="42" ry="14"/><ellipse cx="365" cy="430" rx="42" ry="14"/><ellipse cx="470" cy="430" rx="42" ry="14"/><ellipse cx="575" cy="430" rx="42" ry="14"/><ellipse cx="680" cy="430" rx="42" ry="14"/><ellipse cx="785" cy="430" rx="42" ry="14"/><ellipse cx="890" cy="430" rx="42" ry="14"/></g><rect x="145" y="650" width="840" height="170" rx="4" fill="${C.wood}"/><image href="${logo}" x="400" y="664" width="330" height="135" preserveAspectRatio="xMidYMid meet"/><g stroke="#2A201B" stroke-width="4"><line x1="185" y1="690" x2="310" y2="690"/><line x1="185" y1="712" x2="310" y2="712"/><line x1="185" y1="734" x2="310" y2="734"/></g>`
  },
  {
    folder: "04_菜单与菜单封套", title: "菜单与菜单封套", en: "MENU SYSTEM",
    notes: ["成品 180×260 mm", "封套可替换内页", "推荐菜仅一枚橙点", "正文保持高对比"], material: "布纹封套 / 茶白纸 / 暖铜螺钉",
    drawing: `<g transform="translate(185 285) rotate(-4 230 280)"><rect width="460" height="560" rx="14" fill="${C.ink}"/><image href="${reverse}" x="115" y="75" width="230" height="330" preserveAspectRatio="xMidYMid meet"/><text x="230" y="485" text-anchor="middle" class="small" fill="${C.tea}">游于后湖，味在人间</text></g><g transform="translate(610 300) rotate(3 180 270)"><rect width="360" height="540" fill="${C.tea}"/><text x="40" y="80" class="title" font-size="34">炭火烧鸟</text><path d="M305 45 l12 12 -12 12 -12-12z" fill="${C.orange}"/><g class="body" font-size="20"><text x="42" y="160">鸡腿葱串</text><text x="300" y="160">18</text><text x="42" y="220">鸡皮</text><text x="300" y="220">16</text><text x="42" y="280">提灯</text><text x="300" y="280">22</text><text x="42" y="340">香菇</text><text x="300" y="340">12</text></g><path d="M40 445 C115 405 190 410 265 448 C300 466 330 466 350 458" fill="none" stroke="${C.lake}" stroke-width="5" opacity=".5"/></g>`
  },
  {
    folder: "05_桌面小灯", title: "桌面小灯", en: "TABLE LAMP",
    notes: ["2200K–2400K", "CRI ≥ 90", "三档调光", "续航不少于 8 小时"], material: "炭黑金属 / 亚麻 / 防滑底座",
    drawing: `<ellipse cx="555" cy="800" rx="250" ry="35" fill="#000" opacity=".12"/><rect x="420" y="700" width="270" height="70" rx="16" fill="${C.ink}"/><rect x="455" y="365" width="200" height="330" rx="95" fill="${C.tea}" stroke="${C.ink}" stroke-width="18"/><path d="M470 385 H640 V680 H470 Z" fill="#F6DBA4" opacity=".68"/><g stroke="${C.ink}" stroke-width="16"><line x1="455" y1="370" x2="455" y2="700"/><line x1="655" y1="370" x2="655" y2="700"/><line x1="455" y1="370" x2="655" y2="370"/></g><path d="M505 708 C540 690 575 690 610 708" fill="none" stroke="${C.orange}" stroke-width="5"/><text x="555" y="745" text-anchor="middle" class="small" fill="${C.tea}">游味</text>`
  },
  {
    folder: "06_桌牌与今日炭火推荐牌", title: "桌牌与“今日炭火推荐”牌", en: "TABLE CARD",
    notes: ["A6 竖式", "正反双面", "内容每日可更新", "暖铜或原木底座"], material: "暖肌纸 / 暖铜 / 原木",
    drawing: `<g transform="translate(190 305)"><rect x="20" y="15" width="350" height="500" rx="12" fill="#000" opacity=".13"/><rect width="350" height="500" rx="12" fill="${C.tea}"/><image href="${round}" x="65" y="45" width="220" height="220" preserveAspectRatio="xMidYMid meet"/><text x="175" y="330" text-anchor="middle" class="body">游味烧鸟</text><text x="175" y="382" text-anchor="middle" class="small">今晚风刚好</text></g><g transform="translate(610 305)"><rect width="350" height="500" rx="12" fill="${C.ink}"/><text x="175" y="100" text-anchor="middle" class="title" fill="${C.tea}" font-size="34">今日炭火推荐</text><line x1="60" y1="145" x2="290" y2="145" stroke="${C.orange}"/><g class="body" fill="${C.tea}" font-size="22"><text x="65" y="220">01  鸡腿葱串</text><text x="65" y="280">02  提灯</text><text x="65" y="340">03  香菇</text></g><path d="M60 420 C120 388 180 390 240 421 C270 437 295 438 315 430" fill="none" stroke="${C.lake}" stroke-width="5"/></g><rect x="140" y="810" width="870" height="42" rx="12" fill="${C.city}"/>`
  },
  {
    folder: "07_木质烧鸟签筒", title: "木质烧鸟签筒", en: "SKEWER HOLDER",
    notes: ["直径 90–110 mm", "可抽洗不锈钢内胆", "哑光耐油木蜡油", "小面积刻辅助口号"], material: "原木 / 炭化木 / 不锈钢内胆",
    drawing: `<g stroke="${C.wood}" stroke-width="7"><line x1="420" y1="330" x2="350" y2="725"/><line x1="490" y1="300" x2="455" y2="725"/><line x1="560" y1="340" x2="550" y2="725"/><line x1="630" y1="295" x2="655" y2="725"/><line x1="700" y1="325" x2="760" y2="725"/></g><g fill="${C.orange}"><circle cx="420" cy="330" r="16"/><circle cx="490" cy="300" r="16"/><circle cx="560" cy="340" r="16"/><circle cx="630" cy="295" r="16"/><circle cx="700" cy="325" r="16"/></g><ellipse cx="555" cy="675" rx="190" ry="52" fill="#8B6848"/><path d="M365 675 H745 L710 830 H400 Z" fill="${C.wood}"/><ellipse cx="555" cy="830" rx="155" ry="36" fill="#3B2A20"/><text x="555" y="760" text-anchor="middle" class="body" fill="${C.tea}">一串炭火 · 一晚湖风</text>`
  },
  {
    folder: "08_杯具杯套与外带包装", title: "杯具、杯套与外带包装", en: "TAKEAWAY PACKAGING",
    notes: ["食品级水性油墨", "冷/热/油品分装", "圆章＋湖纹系统", "暖阳橙作封签"], material: "牛皮纸 / 茶白纸 / 炭黑纸板",
    drawing: `<g transform="translate(140 390)"><path d="M40 40 H300 L275 390 H65 Z" fill="${C.tea}"/><path d="M65 185 H275 V300 H65 Z" fill="${C.lake}"/><image href="${round}" x="110" y="165" width="120" height="120" preserveAspectRatio="xMidYMid meet"/></g><g transform="translate(480 310)"><path d="M55 90 H390 L430 480 H15 Z" fill="#BA8D59"/><path d="M130 100 C130 -25 315 -25 315 100" fill="none" stroke="${C.ink}" stroke-width="16"/><image href="${logo}" x="85" y="190" width="280" height="150" preserveAspectRatio="xMidYMid meet"/><text x="220" y="415" text-anchor="middle" class="small">慢下来，吃一串烧鸟</text></g><g transform="translate(850 460)"><rect width="160" height="270" rx="28" fill="${C.ink}"/><rect width="160" height="65" rx="28" fill="${C.orange}"/><circle cx="80" cy="65" r="48" fill="${C.orange}"/><image href="${round}" x="42" y="27" width="76" height="76" preserveAspectRatio="xMidYMid meet"/></g>`
  },
  {
    folder: "09_员工围裙与工作服", title: "员工围裙与工作服", en: "STAFF UNIFORM",
    notes: ["厨师炭火黑", "服务围裙木原褐", "茶白刺绣", "不做角色化日式装扮"], material: "耐油棉混纺 / 防泼水帆布 / 哑黑五金",
    drawing: `<g transform="translate(180 290)"><path d="M150 0 L285 55 L250 170 L210 135 V540 H-20 V135 L-60 170 L-95 55 L40 0 Q95 55 150 0 Z" fill="${C.ink}"/><circle cx="95" cy="150" r="62" fill="${C.tea}"/><image href="${round}" x="42" y="97" width="106" height="106" preserveAspectRatio="xMidYMid meet"/><text x="95" y="510" text-anchor="middle" class="small" fill="${C.tea}">YOU WEI</text></g><g transform="translate(565 340)"><path d="M80 0 H250 L300 500 H30 Z" fill="${C.wood}"/><path d="M100 0 C100 -100 230 -100 230 0" fill="none" stroke="${C.wood}" stroke-width="25"/><rect x="92" y="150" width="145" height="105" rx="8" fill="#755139"/><circle cx="165" cy="108" r="63" fill="${C.tea}"/><image href="${round}" x="110" y="53" width="110" height="110" preserveAspectRatio="xMidYMid meet"/></g>`
  },
  {
    folder: "10_户外引导灯牌", title: "户外引导灯牌", en: "OUTDOOR WAYFINDING LIGHTBOX",
    notes: ["450×800 mm", "IP54 及以上", "2400K–2700K", "防倾倒隐藏走线"], material: "炭黑金属 / 亚麻透光面 / 防水底座",
    drawing: `<ellipse cx="555" cy="840" rx="270" ry="35" fill="#000" opacity=".13"/><path d="M320 300 H790 L850 810 H260 Z" fill="${C.ink}"/><rect x="330" y="335" width="450" height="410" rx="18" fill="#F2D6A0"/><image href="${round}" x="435" y="360" width="240" height="240" preserveAspectRatio="xMidYMid meet"/><text x="555" y="650" text-anchor="middle" class="body">湖边入口  →</text><text x="555" y="700" text-anchor="middle" class="small">OPEN · 18:00</text><path d="M280 810 H830" stroke="${C.orange}" stroke-width="12"/>`
  },
];

(async () => {
  const rendered = [];
  for (const board of boards) {
    const svg = shell(board.title, board.en, board.drawing, board.notes, board.material);
    const out = path.join(root, board.folder, "效果示意_V2.png");
    await sharp(Buffer.from(svg)).png().toFile(out);
    rendered.push(out);
  }
  const thumbs = await Promise.all(rendered.map((file) => sharp(file).resize(700, 438).png().toBuffer()));
  const composites = thumbs.map((input, i) => ({
    input,
    left: 40 + (i % 2) * 730,
    top: 120 + Math.floor(i / 2) * 468,
  }));
  const overviewTitle = Buffer.from(`<svg width="1500" height="120" xmlns="http://www.w3.org/2000/svg"><rect width="1500" height="120" fill="#F5F0E8"/><text x="40" y="70" font-family="Microsoft YaHei,sans-serif" font-size="40" font-weight="700" fill="#222220">游味烧鸟 · 空间应用物料总览 V2</text><text x="1120" y="70" font-family="Montserrat,Arial,sans-serif" font-size="16" letter-spacing="4" fill="#97826E">MATERIAL SYSTEM</text></svg>`);
  await sharp({ create: { width: 1500, height: 2480, channels: 4, background: "#D7CABC" } })
    .composite([{ input: overviewTitle, left: 0, top: 0 }, ...composites])
    .png()
    .toFile(path.join(root, "00_物料效果总览_V2.png"));
  console.log(`Built ${boards.length} material boards`);
})();
