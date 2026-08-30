const sharp = require("sharp");
const path = require("path");

const src = "C:/Users/admin/AppData/Local/Temp/codex-clipboard-f8961c41-5730-4ef3-8c9c-4350e16afb76.png";
const out = path.resolve(__dirname, "../02_可用标志");

async function extractStamp() {
  const { data, info } = await sharp(src)
    .extract({ left: 170, top: 128, width: 30, height: 38 })
    .resize({ width: 120, kernel: "lanczos3" })
    .ensureAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });

  for (let i = 0; i < data.length; i += 4) {
    const r = data[i];
    const g = data[i + 1];
    const b = data[i + 2];
    data[i + 3] = r > 70 && r > g * 1.25 && r > b * 1.25
      ? Math.min(255, (r - g) * 5)
      : 0;
  }

  await sharp(data, { raw: info }).png().toFile(path.join(out, "05_红印章_透明底.png"));
}

async function buildLockups() {
  const wordmark = await sharp(path.join(out, "03_中文标准字_透明底.png"))
    .resize({ width: 1260 })
    .png()
    .toBuffer();
  const seal = await sharp(path.join(out, "05_红印章_透明底.png"))
    .resize({ width: 66 })
    .png()
    .toBuffer();
  const typography = Buffer.from(`
    <svg width="1600" height="650" xmlns="http://www.w3.org/2000/svg">
      <text x="800" y="470" text-anchor="middle" fill="#181512"
        font-family="Montserrat, Arial, sans-serif" font-size="44" letter-spacing="12">YOU WEI YAKITORI</text>
      <line x1="470" y1="505" x2="1130" y2="505" stroke="#A06B58" stroke-width="2"/>
      <text x="800" y="565" text-anchor="middle" fill="#181512"
        font-family="Source Han Serif SC, Microsoft YaHei, serif" font-size="38" letter-spacing="8">后湖湖畔 · 炭火烧鸟</text>
    </svg>`);
  const layers = [
    { input: wordmark, left: 170, top: 35 },
    { input: seal, left: 1390, top: 285 },
    { input: typography, left: 0, top: 0 },
  ];

  await sharp({ create: { width: 1600, height: 650, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } } })
    .composite(layers)
    .png()
    .toFile(path.join(out, "08_标准组合_清稿版_透明底.png"));
  await sharp({ create: { width: 1600, height: 650, channels: 4, background: "#F5F0E8" } })
    .composite(layers)
    .png()
    .toFile(path.join(out, "09_标准组合_清稿版_浅底预览.png"));
}

(async () => {
  await extractStamp();
  await buildLockups();
})();
