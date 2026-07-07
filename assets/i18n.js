// assets/i18n.js — DOM internationalisation (English / 简体中文).
// Scope: DOM copy only. Canvas/broadcast text stays English by design — Teko & Chakra Petch have no CJK glyphs,
// and xG/xT/"Pitch Control" etc. are broadcast/analytics terms kept in English.
// Wiring: elements carry data-i18n (textContent), data-i18n-html (innerHTML, for spans/bold), data-i18n-title
// (title attr, the dot tooltips), or data-i18n-aria (aria-label). The GitHub link lives in a STABLE <a id="ch3link">
// between two text spans (ch3_body_1 / ch3_body_2) so it is never recreated (the engine caches that element).
window.I18N = (function(){
  var DICT = {
    en: {
      doc_title: "KICK · Bridging Science and Football",
      nav_cv: "Computer Vision", nav_viz: "Visualization", nav_research: "Research", nav_work: "Work with us",
      hero_slogan: 'Bridging <span class="g">Science</span> and Football.',
      scroll: "Scroll down",
      ch1_eyebrow: "01 · Computer Vision",
      ch1_head: "We read the game straight from video",
      ch1_body: "Keypoint detection, player classification and tracking — original models, built and trained in-house — turn broadcast video into spatial data, no third-party feed required. The dataset underneath is held to the same standard: rigorously annotated, frame by frame.",
      ch1_dot1: "Keypoint Detection", ch1_dot2: "Trace Estimation", ch1_dot3: "Object Tracking",
      ch2_eyebrow: "02 · Visualization",
      ch2_head: "We turn any feed into broadcast.",
      ch2_body: "Event data or full tracking — Sony Hawk-Eye, Stats Perform, StatsBomb, or whatever standard you already run — we take any of it and turn it into clean, broadcast-ready graphics.",
      ch2_dot1: "Goal Replay", ch2_dot2: "Lane Dominance", ch2_dot3: "Shot Map",
      ch3_eyebrow: "03 · Research",
      ch3_head: "More than an engineering project.",
      ch3_body_1: "Pitch control, expected goals, expected threat — we stand on the best of football science and build on it with our own value models, refined with the right method for each problem. We open-source the field's leading metrics on ",
      ch3_body_2: ", and welcome every aspiring scholar and practitioner to join the research.",
      ch3_dot1: "Pitch Control", ch3_dot2: "xG Model", ch3_dot3: "xT Model",
      ch4_head: 'Whoever you are, there\'s <span class="g">a way in.</span>',
      ch4_c1_t: "Data providers", ch4_c1_b: "Computer vision that lifts your numbers. Sharper keypoints, players tracked through occlusion, and traces for everyone off camera.",
      ch4_c2_t: "Broadcasters", ch4_c2_b: "Any data format in, a finished broadcast out. Live AI commentary, player spotlights, tactical breakdowns and on-pitch graphics — as the match happens.",
      ch4_c3_t: "Clubs", ch4_c3_b: "Annotation software with our models inside. Coaches draw tactics, generate broadcast-grade visuals, and build film sessions that stick.",
      ch4_c4_t: "Individuals", ch4_c4_b: "Football isn't just for the industry. Love the game and brilliant at something — music, art, history, code, anything? Come make something nobody's made. Bring the passion; we'll find the rest.",
      ch4_cta: "Get in touch / Request a demo",
      ch4_partners: "Partnerships",
      partner_baidu_cloud: "Baidu AI Cloud", partner_baidu_app: "Baidu App", partner_bilibili: "Bilibili",
      ch1_note: 'Every visible landmark, <b>pinned to the pixel</b> — 99.7% recall, sub-pixel precision. Measured, not estimated.'
    },
    // 简体中文 — translated + native-reviewed. Any missing key falls back to English.
    zh: {
      doc_title: "KICK · 连接科学与足球的桥梁",
      nav_cv: "计算机视觉", nav_viz: "可视化", nav_research: "研究", nav_work: "合作",
      hero_slogan: '连接<span class="g">科学</span>与足球的桥梁',
      scroll: "向下滚动",
      ch1_eyebrow: "01 · 计算机视觉",
      ch1_head: "直接从视频中提取数据",
      ch1_body: "关键点检测、球员分类与追踪——均为我们自主研发、自主训练的原创模型——将转播画面转化为空间数据，无需任何第三方数据源。底层训练数据集也恪守同样的标准：逐帧标注，一丝不苟。",
      ch1_dot1: "关键点检测", ch1_dot2: "轨迹估计", ch1_dot3: "目标追踪",
      ch2_eyebrow: "02 · 可视化",
      ch2_head: "任意数据，直出转播画面。",
      ch2_body: "无论是事件数据还是完整追踪数据——Sony Hawk-Eye、Stats Perform、StatsBomb，或是你正在使用的任何标准——我们都能把它变成干净利落、可直接转播的图形。",
      ch2_dot1: "进球回放", ch2_dot2: "通道掌控", ch2_dot3: "射门分布图",
      ch3_eyebrow: "03 · 研究",
      ch3_head: "不止是一项工程。",
      ch3_body_1: "球场控制、预期进球、预期威胁——我们立足足球科学的顶尖成果，再以自研的价值模型在此基础上拓展，针对每一个问题选用最合适的方法悉心打磨。我们在 ",
      ch3_body_2: " 上开源该领域领先的指标，也欢迎每一位有志的学者与从业者加入这项研究。",
      ch3_dot1: "球场控制", ch3_dot2: "xG 模型", ch3_dot3: "xT 模型",
      ch4_head: '无论你是谁，都有<span class="g">属于你的入口</span>。',
      ch4_c1_t: "数据提供方", ch4_c1_b: "用计算机视觉，提升你的数据。更精准的关键点、遮挡之下依然不丢的球员追踪，以及镜头之外每个人的轨迹补全。",
      ch4_c2_t: "转播方", ch4_c2_b: "任意数据格式输入，成品转播输出。实时 AI 解说、球员聚焦、战术拆解与场上图形——随比赛同步呈现。",
      ch4_c3_t: "俱乐部", ch4_c3_b: "一套内置我们模型的标注软件。教练可以绘制战术、生成转播级画面，制作出让球员真正记得住的录像分析课。",
      ch4_c4_t: "个人", ch4_c4_b: "足球不只属于这个行业。你热爱这项运动，又在某件事上格外擅长——音乐、艺术、历史、代码，无论什么？那就来创造一件前所未有的东西。带上热爱，其余的交给我们。",
      ch4_cta: "联系我们 / 预约演示",
      ch4_partners: "合作伙伴",
      partner_baidu_cloud: "百度智能云", partner_baidu_app: "百度App", partner_bilibili: "哔哩哔哩",
      ch1_note: '每一个可见的关键点，<b>精确到像素</b>——99.7% 召回率，亚像素级精度。实测所得，而非估算。'
    }
  };

  function qsa(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function apply(lang){
    var d = DICT[lang] || {}, e = DICT.en;
    function val(k){ return (d[k] != null) ? d[k] : e[k]; }
    qsa('[data-i18n]').forEach(function(el){ var v = val(el.getAttribute('data-i18n')); if(v != null) el.textContent = v; });
    qsa('[data-i18n-html]').forEach(function(el){ var v = val(el.getAttribute('data-i18n-html')); if(v != null) el.innerHTML = v; });
    qsa('[data-i18n-title]').forEach(function(el){ var v = val(el.getAttribute('data-i18n-title')); if(v != null) el.title = v; });
    qsa('[data-i18n-aria]').forEach(function(el){ var v = val(el.getAttribute('data-i18n-aria')); if(v != null) el.setAttribute('aria-label', v); });
    var dt = val('doc_title'); if(dt) document.title = dt;
    document.documentElement.lang = (lang === 'zh') ? 'zh-CN' : 'en';
    document.documentElement.setAttribute('data-lang', lang);
    qsa('[data-lang-btn]').forEach(function(b){ b.classList.toggle('on', b.getAttribute('data-lang-btn') === lang); });
  }
  function set(lang){ lang = (lang === 'zh') ? 'zh' : 'en'; try{ localStorage.setItem('kick_lang', lang); }catch(e){} apply(lang); }
  function init(){
    var url = null; try{ url = new URLSearchParams(location.search).get('lang'); }catch(e){}
    var saved = null; try{ saved = localStorage.getItem('kick_lang'); }catch(e){}
    var forced = (url === 'zh' || url === 'en') ? url : null;
    var lang = forced || saved || (((navigator.language || navigator.userLanguage || '').toLowerCase().indexOf('zh') === 0) ? 'zh' : 'en');
    qsa('[data-lang-btn]').forEach(function(b){ b.addEventListener('click', function(){ set(b.getAttribute('data-lang-btn')); }); });
    if(forced){ set(forced); } else { apply(lang); }   // ?lang=zh|en deep-links (and persists); otherwise saved pref / browser language
  }
  if(document.readyState !== 'loading') init(); else document.addEventListener('DOMContentLoaded', init);
  return { set: set, apply: apply, get dict(){ return DICT; } };
})();
