const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, LevelFormat, PageBreak, Footer, PageNumber,
} = require("docx");

const S = __dirname;
const OUT = process.argv[2];
const lines17 = JSON.parse(fs.readFileSync(path.join(S, "lines17.json"), "utf8"));
const gm = JSON.parse(fs.readFileSync(path.join(S, "gm_pilot.json"), "utf8"));
const FONT = "Tahoma";
const byId = Object.fromEntries(lines17.map(l => [l.id, l.fa]));

// ---------- helpers ----------
const run = (text, o = {}) => new TextRun({ text, font: FONT, rightToLeft: o.ltr ? false : true, size: o.size || 22, bold: o.bold, italics: o.italics, color: o.color });
const p = (text, o = {}) => new Paragraph({
  bidirectional: !o.ltr, alignment: o.ltr ? AlignmentType.LEFT : (o.center ? AlignmentType.CENTER : AlignmentType.START),
  spacing: { after: o.after ?? 120, line: o.line || 320 },
  children: Array.isArray(text) ? text : [run(text, o)],
  heading: o.heading, numbering: o.bullet ? { reference: o.ltr ? "bullets-ltr" : "bullets", level: 0 } : undefined,
  border: o.rule ? { bottom: { style: BorderStyle.SINGLE, size: 6, color: "999999", space: 4 } } : undefined,
});
const h1 = (t, o = {}) => p(t, { ...o, heading: HeadingLevel.HEADING_1, size: 32, bold: true, after: 200 });
const h2 = (t, o = {}) => p(t, { ...o, heading: HeadingLevel.HEADING_2, size: 26, bold: true, after: 140 });
const bl = (t, o = {}) => p(t, { ...o, bullet: true, after: 80 });
const brk = () => new Paragraph({ children: [new PageBreak()] });

const W = 9360; // content width for A4 with 1" margins ~ 9026; use 9000
const TW = 9000;
const cell = (content, w, o = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  shading: o.head ? { type: ShadingType.CLEAR, fill: "E8E8E8", color: "auto" } : undefined,
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: (Array.isArray(content) ? content : [content]).map(c => typeof c === "string" ? p(c, { size: o.size || 22, bold: o.head || o.bold, after: 40, ltr: o.ltr }) : c),
});
// RTL table: first column is visually on the right
function table(cols, rows, widths, o = {}) {
  return new Table({
    width: { size: TW, type: WidthType.DXA }, columnWidths: widths, visuallyRightToLeft: !o.ltr,
    rows: [
      new TableRow({ tableHeader: true, children: cols.map((c, i) => cell(c, widths[i], { head: true, ltr: o.ltr })) }),
      ...rows.map(r => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], { size: i === (o.bigCol ?? -1) ? 26 : 22, ltr: (o.ltrCols || [0]).includes(i) && !(o.plainCols || []).includes(i) })) })),
    ],
  });
}
const footer = (label) => ({ default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [run(label + " — ", { size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "777777" })] })] }) });
function doc(label, children) {
  return new Document({
    creator: "Mere Voice", title: label,
    styles: { default: { document: { run: { font: FONT, size: 22 } } } },
    numbering: { config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.START, style: { paragraph: { indent: { right: 360, hanging: 240 } } } }] },
      { reference: "bullets-ltr", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 240 } } } }] },
    ] },
    sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1300, left: 1450, right: 1450 } } }, footers: footer(label), children }],
  });
}

// ---------- shared performer blocks ----------
const takeDirections = [
  h2("دو شیوه‌ی اجرا برای هر سطر"),
  p([run("اجرای A — «طبیعی»: ", { bold: true }), run("همان‌طور بخوانید که اگر این جمله را آرام برای کسی در همان اتاق می‌گفتید. بدون بازیگری و بدون اغراق.")]),
  p([run("اجرای B — «دور»: ", { bold: true }), run("یکنواخت‌تر و خنثی‌تر، کمی دور؛ مثل صدایی که گزارش می‌دهد و احساسش را نشان نمی‌دهد.")]),
  p("در هر دو اجرا صدا باید کامل و روشن باشد. آرام خواندن اشکالی ندارد، اما لطفاً پچ‌پچ یا نجوا نکنید، حتی اگر جمله شاعرانه است.", { italics: true }),
];

const setupBlock = [
  h2("پیش از ضبط (۵ دقیقه)"),
  bl("اتاقی ساکت با وسایل نرم (پرده، تخت، کمد لباس) انتخاب کنید. پنکه، کولر، یخچال و پنجره‌ی رو به خیابان را خاموش یا بسته کنید."),
  bl("گوشی را در حالت پرواز بگذارید تا زنگ و اعلان ضبط را خراب نکند."),
  bl("گوشی را روی سطحی ثابت بگذارید، حدود ۲۰ تا ۳۰ سانتی‌متر از دهان و کمی کنار آن (نه دقیقاً روبه‌رو، تا صدای «پ» و نفس به میکروفن نخورد)."),
  bl("در برنامه‌ی ضبط صدا بالاترین کیفیت را انتخاب کنید. آیفون: تنظیمات ← Voice Memos ← Audio Quality ← Lossless. اندروید: در تنظیمات برنامه‌ی ضبط، «کیفیت بالا» یا WAV."),
  bl("هیچ افکت، «بهبود صدا» یا حذف نویز را روشن نکنید."),
  bl("یک ضبط آزمایشی بگیرید: یک جمله با صدای معمولی بگویید و گوش دهید. صدا باید واضح باشد، نه خیلی آهسته و نه ترکیده. اگر خش دارد، کمی دورتر بروید."),
  bl("در ابتدای اولین فایل، ۱۰ ثانیه ساکت بمانید (فقط صدای اتاق). این به ما کمک می‌کند نویز اتاق را بشناسیم."),
  bl("تا پایان جلسه جای خود، فاصله از گوشی و وضعیت نشستن را ثابت نگه دارید."),
];

const readingRules = [
  h2("هنگام خواندن"),
  bl("هر سطر را کامل و یک‌جا بخوانید. نفس کشیدن وسط جمله طبیعی است و اشکالی ندارد."),
  bl("اگر وسط جمله اشتباه کردید، دو ثانیه مکث کنید و کل جمله را از اول بخوانید. لازم نیست چیزی را پاک کنید."),
  bl("هیچ کلمه‌ای را عوض نکنید. متن محاوره‌ای (مثل «می‌زنه» و «رو») را محاوره‌ای بخوانید و متن رسمی را رسمی."),
  bl("اگر تلفظ کلمه‌ای را مطمئن نیستید (مثلاً «اوپیوم» یا «آنتی بیوتیک»)، همان‌طور بخوانید که طبیعی می‌دانید و آن را در یادداشتی برای ما بنویسید."),
  bl("بین سطرها چند ثانیه مکث کنید. عجله لازم نیست."),
];

const namingBlock = (examples) => [
  h2("نام‌گذاری و ارسال فایل‌ها"),
  p([run("نام فایل‌ها: ", { bold: true }), run("در ابتدای نام هر فایل، نام کوچک خود را با حروف انگلیسی بنویسید؛ مثلاً Sara.")]),
  p("بهترین روش: برای هر اجرا یک فایل جدا، با نامی به این شکل («Sara» را با نام خودتان عوض کنید):"),
  ...examples.map(e => p(e, { ltr: true, size: 22, bold: true, after: 60 })),
  p("اگر جدا کردن فایل‌ها سخت است: همه را پشت سر هم در یک فایل ضبط کنید و پیش از هر سطر، کد آن را بلند بگویید (مثلاً «وُیس صفر صفر یک، اجرای آ») و دو ثانیه مکث کنید. ما خودمان فایل را تقسیم می‌کنیم."),
  p([run("مهم: ", { bold: true }), run("فایل‌ها را به‌صورت «فایل» (Document/File) بفرستید، نه پیام صوتی. پیام‌رسان‌ها پیام صوتی را فشرده می‌کنند و کیفیت از بین می‌رود. گوگل‌درایو، یا تلگرام با گزینه‌ی «ارسال به‌صورت فایل»، مناسب است.")]),
];

// ---------- 01 audition ----------
const auditionIds = ["VOICE-001", "VOICE-004", "VOICE-009"];
const auditionRows = [];
for (const t of ["A", "B"]) for (const id of auditionIds) auditionRows.push([`Sara_${id}_${t}`, t === "A" ? "طبیعی" : "دور", byId[id]]);
const audition = doc("تست صدا — «صدا»", [
  h1("تست صدا برای نقش «صدا»"),
  p("آنجا که خسارت محکم ایستاده", { size: 24, bold: true }),
  p("«صدا» شخصیتی دیده‌نشدنی در این نمایش است. در این مرحله چند صدای مختلف را امتحان می‌کنیم تا ببینیم کدام به این نقش جان می‌دهد. از شما خواهش می‌کنیم سه سطر را، هر کدام دو بار و با دو حال متفاوت، ضبط کنید. کل کار حدود ۱۵ دقیقه طول می‌کشد.", { after: 200 }),
  p("", { after: 120, rule: true }),
  ...setupBlock, ...takeDirections, ...readingRules,
  brk(),
  h2("سطرها (به ترتیب جدول بخوانید)"),
  p("ستون اول نام فایل است. «Sara» را با نام کوچک خودتان به حروف انگلیسی عوض کنید.", { size: 20, italics: true }),
  table(["نام فایل", "اجرا", "متن"], auditionRows, [2600, 1300, 5100], { bigCol: 2 }),
  p("", { after: 200 }),
  ...namingBlock(["Sara_VOICE-001_A", "Sara_VOICE-004_B"]),
  p("سپاس از وقت و صدای شما.", { bold: true, after: 0 }),
]);

// ---------- 02 full session ----------
const original = [
  "امروز صبح زود بیدار شدم، ولی تا ظهر هیچ کاری نکردم.",
  "می‌شه یه لحظه صبر کنی؟ الان میام.",
  "گفتم که نمی‌دونم کجا گذاشتمش، شاید تو کشوی میز باشه.",
  "هوا خیلی سرد شده، پنجره رو ببند لطفاً.",
  "دیروز تو خیابون یه نفر رو دیدم که شبیه برادرت بود.",
  "اگه فردا بارون بیاد، برنامه رو می‌ذاریم برای هفته‌ی بعد.",
  "چرا زودتر نگفتی؟ من که همه‌ش منتظر بودم.",
  "این چای یه کم تلخه، شکر داریم؟",
  "جلسه‌ی بعدی روز سه‌شنبه ساعت ده صبح برگزار خواهد شد.",
  "لطفاً پیش از مصرف، دستورالعمل را به دقت مطالعه کنید.",
  "این دارو را دور از دسترس کودکان و در دمای اتاق نگهداری کنید.",
  "در صورت بروز حساسیت، مصرف را قطع کنید و با پزشک مشورت نمایید.",
  "کتابخانه‌ی مرکزی شهر در سال هزار و سیصد و چهل تأسیس شد.",
  "قطار تهران به مشهد با بیست دقیقه تأخیر حرکت کرد.",
  "تو واقعاً فکر می‌کنی که او برمی‌گردد؟",
  "چه باران تندی! همه‌ی لباس‌هایم خیس شد.",
  "آیا کسی صدای در را شنید؟",
  "کی قرار است این همه کاغذ را مرتب کند؟",
  "نان، پنیر، سبزی و دو بطری آب معدنی بخرید.",
  "شماره‌ی اتاقش دویست و سی و هفت است، طبقه‌ی سوم.",
  "یک، دو، سه، چهار، پنج؛ دوباره از اول.",
  "ساعت دوازده و ربع شب بود که تلفن زنگ زد.",
  "نور زرد چراغ روی دیوار کهنه می‌لرزید.",
  "باد از لای پنجره می‌آمد و بوی خاک باران‌خورده را با خود می‌آورد.",
  "در سکوت اتاق فقط صدای تیک‌تاک ساعت شنیده می‌شد.",
  "او آهسته دستش را روی شانه‌ی مادرش گذاشت و چیزی نگفت.",
  "کوچه تاریک بود و هیچ‌کس از آن‌جا نمی‌گذشت.",
  "سال‌ها گذشت، اما آن روز هنوز در خاطرش مانده بود.",
  "دفترچه‌ی کوچک آبی‌رنگ پدربزرگم هنوز روی قفسه است.",
  "صدای آرام قدم‌های او در راهروی طولانی بیمارستان می‌پیچید.",
  "خانه‌ی قدیمی مادربزرگ پر از بوی نان تازه بود.",
  "کشتی در بندر لنگر انداخت و ملوان‌ها پیاده شدند.",
  "پیرمرد دیشب در خواب مرد.",
  "مهر اداره روی نامه خورده بود و ماه مهر هم تمام شده بود.",
  "گل‌های باغچه را صبح زود آب دادم.",
  "نه، خواهش می‌کنم، دیگر این را تکرار نکن.",
  "بالاخره تمام شد؛ حالا می‌توانیم نفس بکشیم.",
  "بعضی شب‌ها صدای قطار از دور می‌آید و بعد همه‌چیز دوباره ساکت می‌شود.",
];
const fullRows = [];
for (const l of lines17) for (const t of ["A", "B"]) fullRows.push([`Sara_${l.id}_${t}`, t === "A" ? "طبیعی" : "دور", l.fa]);
const numbered = (arr, start = 1) => arr.map((t, i) => p([run(`${(start + i).toLocaleString("fa-IR")}. `, { bold: true }), run(t, { size: 24 })], { after: 90 }));
const donors = gm.pilot.flatMap(x => x.donors.map(d => [`Sara_${d.id}`, d.text]));
const targets = gm.pilot.map(x => [`Sara_${x.target_id}`, x.target_text]);
const full = doc("جلسه‌ی ضبط کامل — «صدا»", [
  h1("جلسه‌ی ضبط کامل برای نقش «صدا»"),
  p("آنجا که خسارت محکم ایستاده", { size: 24, bold: true }),
  p("این جلسه چهار بخش دارد و با استراحت حدود یک تا یک‌ونیم ساعت طول می‌کشد. می‌توانید بخش‌ها را در روزهای مختلف ضبط کنید، به شرط آن‌که اتاق، فاصله و گوشی یکسان بمانند.", { after: 120 }),
  table(["بخش", "چه چیزی", "زمان تقریبی"], [
    ["۱", "هفده سطر «صدا»، هر کدام دو اجرا", "۲۰ دقیقه"],
    ["۲", "خواندن متن‌های متنوع (برای شناخت صدای شما)", "۱۵ دقیقه"],
    ["۳", "صحبت آزاد", "۵ دقیقه"],
    ["۴", "سطرهای «گور-ماشین» (آزمایش مونتاژ)", "۱۰ دقیقه"],
  ], [900, 5800, 2300]),
  p("", { after: 120 }),
  ...setupBlock, ...readingRules,
  brk(),
  h1("بخش ۱ — هفده سطر «صدا»"),
  ...takeDirections,
  table(["نام فایل", "اجرا", "متن"], fullRows, [2700, 1300, 5000], { bigCol: 2 }),
  brk(),
  h1("بخش ۲ — خواندن متن‌های متنوع"),
  p("این متن‌ها ربطی به نمایش ندارند. فقط برای این است که صدای شما را در حالت‌های مختلف بشناسیم: محاوره، رسمی، پرسش، عدد و توصیف. ساده و طبیعی بخوانید، هر جمله یک‌بار. همه را در یک فایل ضبط کنید با نام:"),
  p("Sara_READING", { ltr: true, bold: true }),
  p("اگر فایل طولانی شد، می‌توانید دو فایل بسازید: Sara_READING_1 و Sara_READING_2.", { size: 20, italics: true }),
  h2("الف) جمله‌های روزمره و رسمی"),
  ...numbered(original),
  h2("ب) سطرهایی از شعر ماشینی «گور-ماشین»"),
  p("این سطرها را یک ماشین از واژه‌های نوشته‌شده ساخته است و ممکن است عجیب به نظر برسند. ساده و روشن بخوانید، بدون تفسیر.", { italics: true }),
  ...numbered(gm.reading_lines, original.length + 1),
  brk(),
  h1("بخش ۳ — صحبت آزاد"),
  p("سه تا پنج دقیقه آزاد و بی‌متن صحبت کنید؛ مثلاً درباره‌ی راه همیشگی‌تان تا خانه، یک روز معمولی، یا اتاقی که در آن بزرگ شده‌اید. لازم نیست جالب یا منظم باشد؛ فقط طبیعی. نام فایل:"),
  p("Sara_FREE", { ltr: true, bold: true }),
  h1("بخش ۴ — سطرهای «گور-ماشین»"),
  p("در این بخش آزمایش می‌کنیم که آیا می‌شود از تکه‌های ضبط‌شده، جمله‌های تازه ساخت. هر سطر را یک‌بار و در حالت «طبیعی» بخوانید، هر کدام در فایلی جدا با نام ستون اول. اگر جدا کردن سخت است، همه را در یک فایل با گفتن کد پیش از هر سطر ضبط کنید."),
  h2("۴-الف) سطرهای اول"),
  table(["نام فایل", "متن"], donors, [2700, 6300], { bigCol: 1 }),
  p("", { after: 120 }),
  h2("۴-ب) سطرهای دوم"),
  table(["نام فایل", "متن"], targets, [2700, 6300], { bigCol: 1 }),
  p("", { after: 200 }),
  ...namingBlock(["Sara_VOICE-012_A", "Sara_READING", "Sara_GM-03b"]),
  p("سپاس از وقت و صدای شما.", { bold: true, after: 0 }),
]);

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  for (const [name, d] of [["01_Audition_Script_FA.docx", audition], ["02_Full_Session_Script_FA.docx", full]]) {
    fs.writeFileSync(path.join(OUT, name), await Packer.toBuffer(d));
    console.log("wrote", name);
  }
})();
