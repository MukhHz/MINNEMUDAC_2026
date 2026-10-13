// Q1 slides: estimated need vs. food shelf activity (MinneMUDAC 2026)
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("C:/Users/eirfa/.claude/skills/synced/3b1e3b06-7398-41e9-8d20-1a8ba1d90228_01ccd755-25f6-4c85-8be6-07fa5869c312/pptx/scripts/apply_theme.js");

const OUT = process.argv[2];
const NOTES = require("./notes.json");
const HERE = __dirname;

const THEME = {
  name: "Q1 Need vs Activity",
  headFontFace: "Arial",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2430", lt1: "FFFFFF", dk2: "3A4656", lt2: "F2F3F5",
    accent1: "2A78D6", accent2: "EB6834", accent3: "1BAF7A", accent4: "6250D6", accent5: "A3A29C", accent6: "0F8F63",
    hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HEX = { ink: "1B2430", muted: "5F6670", grid: "E3E5E8", higher: "2A78D6", lower: "EB6834", grey: "C4C7CC", tint: "F2F3F5" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";          // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Q1: Estimated need vs. food shelf activity";
pres.author = "MinneMUDAC 2026 team";
const C = pres.SchemeColor;

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "Q1 Dark Title",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: 0.8, y: 1.55, w: 11.5, h: 0.5, fontSize: 16, bold: true, color: "9FC2EE", fontFace: THEME.bodyFontFace, align: "left" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.1, w: 11.7, h: 2.0, fontSize: 44, bold: true, color: C.background1, valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.35, w: 11.0, h: 1.6, fontSize: 20, color: "C9D1DB", valign: "top", align: "left" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "Q1 Content",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.4, w: 12.1, h: 0.85, fontSize: 32, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Q1 · Need vs. food shelf activity", options: { x: 0.6, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: "8A9099", margin: 0 } } },
  ],
  slideNumber: { x: 12.3, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: "8A9099", align: "right" },
});

pres.addSection({ title: "Q1: Need vs. activity" });
const S = (master) => pres.addSlide({ masterName: master, sectionTitle: "Q1: Need vs. activity" });

const txt = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, fontFace: THEME.bodyFontFace, color: C.text1, ...o });
const chartBase = () => ({
  catAxisLabelColor: HEX.muted, valAxisLabelColor: HEX.muted, catAxisLabelFontSize: 13, valAxisLabelFontSize: 12,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt",
  valGridLine: { color: HEX.grid, size: 0.75 }, catGridLine: { style: "none" },
  catAxisLineShow: false, valAxisLineShow: false,
});
// stat card: big number + short label, on a light tint
function stat(slide, x, y, w, h, big, label, color, name, size = 40) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: C.background2 }, line: { type: "none" }, rectRadius: 0.12, objectName: name + " card" });
  txt(slide, big, { x: x + 0.3, y: y + 0.2, w: w - 0.6, h: h * 0.5, fontSize: size, bold: true, color, fontFace: THEME.headFontFace, valign: "bottom", objectName: name + " number" });
  txt(slide, label, { x: x + 0.3, y: y + 0.2 + h * 0.5, w: w - 0.6, h: h * 0.5 - 0.35, fontSize: 15, color: HEX.muted, valign: "top", objectName: name + " label" });
}
function liveTag(slide, x = 0.8, y = 1.7) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 1.65, h: 0.48, fill: { color: C.text1 }, line: { type: "none" }, rectRadius: 0.24, objectName: "live map tag" });
  txt(slide, "LIVE MAP", { x, y, w: 1.65, h: 0.48, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle", charSpacing: 2, objectName: "live map tag text" });
}

// ---------------------------------------------------------------- 1. title
{
  const s = S("Q1 Dark Title");
  s.addText("QUESTION 1", { placeholder: "kicker" });
  s.addText("Does estimated need match food shelf activity?", { placeholder: "title" });
  s.addText("Feeding America's Map the Meal Gap vs. The Food Group's food shelf reports · 87 counties · 2022–2024", { placeholder: "body" });
  s.addNotes(NOTES[0]);
}

// ---------------------------------------------------------------- 2. same story? partly
{
  const s = S("Q1 Content");
  s.addText("Same story? Only partly", { placeholder: "title" });
  s.addChart(pres.charts.LINE, [
    { name: "Need (food-insecure people)", labels: ["2022", "2023", "2024"], values: [100, 114.1, 125.0] },
    { name: "Pounds", labels: ["2022", "2023", "2024"], values: [100, 118.0, 131.1] },
    { name: "Visits", labels: ["2022", "2023", "2024"], values: [100, 126.4, 145.8] },
    { name: "Individuals", labels: ["2022", "2023", "2024"], values: [100, 135.5, 159.9] },
  ], {
    x: 0.6, y: 1.5, w: 6.6, h: 5.2, ...chartBase(),
    chartColors: ["1B2430", "1BAF7A", "2A78D6", "6250D6"], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 8,
    valAxisMinVal: 90, valAxisMaxVal: 170, valAxisMajorUnit: 20,
    showLegend: true, legendPos: "b", legendFontSize: 12, legendColor: HEX.muted,
    showTitle: true, title: "Statewide totals, 2022 = 100", titleFontSize: 14, titleColor: HEX.muted, titleFontFace: "+mn-lt",
    showValue: false, objectName: "index chart",
  });
  const rows = [
    ["✓", "County size", "ρ ≈ 0.9, but population alone does as well", C.accent3],
    ["✓", "Direction over time", "Need +25%, visits +46%", C.accent3],
    ["✗", "Per resident", "Higher need rate ≠ more visits (ρ ≈ 0)", C.accent2],
  ];
  rows.forEach(([mark, head, sub, col], i) => {
    const y = 1.75 + i * 1.6;
    s.addShape(pres.shapes.OVAL, { x: 7.75, y, w: 0.8, h: 0.8, fill: { color: col }, line: { type: "none" }, objectName: `verdict ${i + 1} mark` });
    txt(s, mark, { x: 7.75, y, w: 0.8, h: 0.8, fontSize: 28, bold: true, color: C.background1, align: "center", valign: "middle", objectName: `verdict ${i + 1} symbol` });
    txt(s, head, { x: 8.8, y: y - 0.05, w: 4.0, h: 0.5, fontSize: 22, bold: true, fontFace: THEME.headFontFace, objectName: `verdict ${i + 1} head` });
    txt(s, sub, { x: 8.8, y: y + 0.45, w: 4.0, h: 0.6, fontSize: 15, color: HEX.muted, objectName: `verdict ${i + 1} sub` });
  });
  s.addNotes(NOTES[1]);
}

// ---------------------------------------------------------------- 3. which metric
{
  const s = S("Q1 Content");
  s.addText("Pounds tracks need best, by a small margin", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [
    { name: "Totals", labels: ["Visits", "Pounds", "Individuals"], values: [0.89, 0.92, 0.90] },
    { name: "Per resident", labels: ["Visits", "Pounds", "Individuals"], values: [0.06, 0.10, 0.05] },
  ], {
    x: 0.6, y: 1.5, w: 7.6, h: 5.2, barDir: "col", barGrouping: "clustered", barGapWidthPct: 60, ...chartBase(),
    chartColors: ["1B2430", "A3A29C"], valAxisMinVal: 0, valAxisMaxVal: 1, valAxisMajorUnit: 0.25, valAxisLabelFormatCode: "0.00",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 14, dataLabelColor: HEX.ink, dataLabelFormatCode: "0.00",
    showLegend: true, legendPos: "b", legendFontSize: 13, legendColor: HEX.muted,
    showTitle: true, title: "Correlation with need (Spearman, average 2022–2024)", titleFontSize: 14, titleColor: HEX.muted, titleFontFace: "+mn-lt",
    objectName: "metric chart",
  });
  stat(s, 8.75, 1.75, 3.95, 2.25, "+0.02", "Pounds' lead on totals: consistent every year, but small", C.text1, "pounds lead");
  stat(s, 8.75, 4.3, 3.95, 2.25, "0.9 → 0.1", "Totals vs. per resident: the real gap", C.accent2, "level gap");
  s.addNotes(NOTES[2]);
}

// ---------------------------------------------------------------- 4. shortlist
{
  const s = S("Q1 Content");
  s.addText("12 counties break the pattern", { placeholder: "title" });
  const lower = [["Nicollet", 0.29], ["Pope", 0.39], ["Lac qui Parle", 0.41], ["Norman", 0.42], ["Roseau", 0.46]];
  const higher = [["Olmsted", 2.04], ["Pipestone", 2.11], ["Mahnomen", 2.46], ["Renville", 2.78], ["Rice", 3.22], ["Washington", 3.29], ["Steele", 4.13]];
  const all = [...lower, ...higher];
  const labels = all.map(([n, t]) => `${n}  ${t.toFixed(2)}×`);
  s.addChart(pres.charts.BAR, [
    { name: "Lower than expected", labels, values: all.map(([n, t]) => (t < 1 ? Math.log2(t) : 0)) },
    { name: "Higher than expected", labels, values: all.map(([n, t]) => (t > 1 ? Math.log2(t) : 0)) },
  ], {
    x: 0.6, y: 1.45, w: 7.9, h: 5.35, barDir: "bar", barGrouping: "clustered", barOverlapPct: 100, barGapWidthPct: 45, ...chartBase(),
    chartColors: ["EB6834", "2A78D6"], catAxisLabelPos: "low", catAxisLabelFontSize: 13, catAxisLabelColor: HEX.ink,
    valAxisMinVal: -2.25, valAxisMaxVal: 2.25, valAxisMajorUnit: 1, valAxisHidden: true, valGridLine: { style: "none" },
    showLegend: false, showValue: false, objectName: "shortlist chart",
  });
  txt(s, "← less than expected", { x: 1.9, y: 6.55, w: 3.0, h: 0.3, fontSize: 12, color: HEX.lower, bold: true, objectName: "axis hint lower" });
  txt(s, "more than expected →", { x: 5.5, y: 6.55, w: 2.9, h: 0.3, fontSize: 12, color: HEX.higher, bold: true, align: "right", objectName: "axis hint higher" });
  liveTag(s, 11.05, 0.58);
  stat(s, 8.9, 1.6, 3.8, 2.15, "≥2× or ≤½", "of what similar-need counties record", C.text1, "rule");
  stat(s, 8.9, 4.0, 3.8, 2.15, "2+ metrics", "in 2+ of 3 years, checked two ways, fully reported", C.text1, "checks");
  s.addNotes(NOTES[3]);
}

// ---------------------------------------------------------------- 5. what explains it
{
  const s = S("Q1 Content");
  s.addText("Access explains the gaps. Hardship doesn't", { placeholder: "title" });
  const f = [
    ["Nearest food shelf in another county", -0.33, true], ["Residents >10 miles away", -0.27, true], ["Food shelves per resident", 0.25, true],
    ["Poverty rate", -0.16, false], ["No-vehicle households", -0.09, false], ["SNAP participation", -0.06, false], ["Rural share", 0.06, false],
  ].reverse();
  const labels = f.map(r => r[0]);
  s.addChart(pres.charts.BAR, [
    { name: "Significant", labels, values: f.map(r => (r[2] ? r[1] : 0)) },
    { name: "Not significant", labels, values: f.map(r => (r[2] ? 0 : r[1])) },
  ], {
    x: 0.6, y: 1.45, w: 8.0, h: 5.35, barDir: "bar", barGrouping: "clustered", barOverlapPct: 100, barGapWidthPct: 45, ...chartBase(),
    chartColors: ["1B2430", "C4C7CC"], catAxisLabelPos: "low", catAxisLabelFontSize: 13, catAxisLabelColor: HEX.ink,
    valAxisMinVal: -0.4, valAxisMaxVal: 0.4, valAxisMajorUnit: 0.2, valAxisLabelFormatCode: "+0.0;-0.0;0",
    showValue: true, dataLabelFormatCode: "+0.00;-0.00;;", dataLabelFontSize: 12, dataLabelColor: HEX.ink, dataLabelPosition: "outEnd",
    showLegend: true, legendPos: "b", legendFontSize: 12, legendColor: HEX.muted,
    showTitle: true, title: "Correlation with the mismatch, 86 counties", titleFontSize: 14, titleColor: HEX.muted, titleFontFace: "+mn-lt",
    objectName: "factor chart",
  });
  stat(s, 9.0, 1.6, 3.7, 2.15, "ρ = −0.33", "nearest food shelf across the line · p = 0.002", C.text1, "strongest factor");
  stat(s, 9.0, 4.0, 3.7, 2.15, "None", "of the hardship measures (poverty, no car, SNAP) predicted the gaps", C.accent2, "hardship");
  s.addNotes(NOTES[4]);
}

// ---------------------------------------------------------------- 6. counted where the food shelf is (live map)
{
  const s = S("Q1 Content");
  s.addText("Activity is counted where the food shelf is", { placeholder: "title" });
  s.addImage({ path: path.join(HERE, "map_nicollet.png"), x: 0.6, y: 1.5, w: 6.75, h: 6.75 * 650 / 842, objectName: "Nicollet map", altText: "Map zoomed on Nicollet with an arrow to Blue Earth (49%)" });
  liveTag(s);
  stat(s, 7.85, 1.5, 4.85, 2.55, "49%", "of Nicollet residents are closer to a Blue Earth food shelf", C.text1, "nicollet share");
  txt(s, [
    { text: "Nicollet ", options: { color: HEX.ink } }, { text: "0.29×", options: { color: HEX.lower, bold: true } },
    { text: "   →   Blue Earth ", options: { color: HEX.ink } }, { text: "1.89×", options: { color: HEX.higher, bold: true } },
  ], { x: 8.15, y: 4.25, w: 4.5, h: 0.5, fontSize: 18, objectName: "nicollet comparison" });
  stat(s, 7.85, 4.95, 4.85, 1.85, "6 of 9", "Wilkin helpline callers referred to a food shelf, though Wilkin has none", C.text1, "wilkin");
  s.addNotes(NOTES[5]);
}

// ---------------------------------------------------------------- 7. distance & mobile pantries (live map)
{
  const s = S("Q1 Content");
  s.addText("Distance matters; mobile pantries may help", { placeholder: "title" });
  s.addImage({ path: path.join(HERE, "map_distance.png"), x: 0.6, y: 1.45, w: 5.4, h: 5.4 * 785 / 790, objectName: "distance map", altText: "Map of neighborhoods colored by distance to the nearest food shelf" });
  liveTag(s);
  stat(s, 6.5, 1.5, 3.0, 2.5, "25% vs 9%", "residents >10 mi away: lower counties vs. the rest", C.accent2, "distance", 32);
  stat(s, 9.7, 1.5, 3.0, 2.5, "0 of 10", "lower counties with a mobile pantry", C.accent2, "mobile", 32);
  stat(s, 6.5, 4.3, 3.0, 2.5, "2.4×", "Cook: remote, but 64% of visits from mobile pantries", C.accent1, "cook", 32);
  stat(s, 9.7, 4.3, 3.0, 2.5, "1.23×", "far-away counties with a mobile pantry (0.80× without)", C.text1, "far counties", 32);
  txt(s, "Mobile pantry results are suggestive (p ≈ 0.05–0.10).", { x: 6.5, y: 6.9, w: 6.2, h: 0.3, fontSize: 11, color: HEX.muted, italic: true, objectName: "mobile caveat" });
  s.addNotes(NOTES[6]);
}

// ---------------------------------------------------------------- 8. network & busy hubs
{
  const s = S("Q1 Content");
  s.addText("The supply network and site size matter too", { placeholder: "title" });
  s.addChart(pres.charts.BAR, [
    { name: "Median county, activity vs. expected", labels: ["North Country", "Second Harvest Heartland", "Channel One", "Second Harvest Northland"], values: [0.82, 0.91, 1.12, 1.30] },
  ], {
    x: 0.6, y: 1.45, w: 7.0, h: 5.35, barDir: "col", barGapWidthPct: 55, ...chartBase(),
    chartColors: ["EB6834", "EB6834", "2A78D6", "2A78D6"], invertedColors: ["EB6834", "EB6834", "2A78D6", "2A78D6"],
    valAxisMinVal: 0, valAxisMaxVal: 1.5, valAxisMajorUnit: 0.5, valAxisLabelFormatCode: "0.0\"×\"",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00\"×\"", dataLabelFontSize: 14, dataLabelColor: HEX.ink,
    showLegend: false, showTitle: true, title: "Median county by main food bank (p = 0.02)", titleFontSize: 14, titleColor: HEX.muted, titleFontFace: "+mn-lt",
    catAxisLabelFontSize: 12, objectName: "food bank chart",
  });
  stat(s, 8.1, 1.6, 4.6, 2.15, "0.22 → 0.34", "share of the gaps explained once the food bank is added", C.text1, "r squared");
  stat(s, 8.1, 4.0, 4.6, 2.15, "~1,750", "visits per site per month in Washington, the busiest in MN", C.accent1, "busy hubs");
  s.addNotes(NOTES[7]);
}

// ---------------------------------------------------------------- 9. takeaway
{
  const s = S("Q1 Dark Title");
  s.addText("TAKEAWAY", { placeholder: "kicker" });
  s.addText("Where food shelves are matters as much as how much need there is", { placeholder: "title" });
  const recs = [["1", "Collect client ZIP codes", "to see cross-county use directly"], ["2", "Send mobile pantries", "to Lac qui Parle, Norman, Roseau"], ["3", "Compare food banks", "supply and how visits are recorded"]];
  recs.forEach(([n, head, sub], i) => {
    const x = 0.8 + i * 4.1;
    s.addShape(pres.shapes.OVAL, { x, y: 4.6, w: 0.75, h: 0.75, fill: { color: C.accent1 }, line: { type: "none" }, objectName: `rec ${n} circle` });
    txt(s, n, { x, y: 4.6, w: 0.75, h: 0.75, fontSize: 24, bold: true, color: C.background1, align: "center", valign: "middle", objectName: `rec ${n} number` });
    txt(s, head, { x: x + 0.95, y: 4.55, w: 3.05, h: 0.45, fontSize: 18, valign: "top", bold: true, color: C.background1, fontFace: THEME.headFontFace, objectName: `rec ${n} head` });
    txt(s, sub, { x: x + 0.95, y: 5.02, w: 3.05, h: 0.7, fontSize: 15, color: "C9D1DB", valign: "top", objectName: `rec ${n} sub` });
  });
  s.addNotes(NOTES[8]);
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
