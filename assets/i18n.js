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
      scroll: "请向下滑",
      ch1_eyebrow: "01 · 计算机视觉",
      ch1_head: "直接从视频中提取数据",
      ch1_body: "关键点检测、球员分类与追踪——均为自主研发、自主训练的原创模型——将转播画面转化为空间数据，无需接入第三方数据源。底层训练数据集同样遵循最高标准：逐帧严谨标注。",
      ch1_dot1: "关键点检测", ch1_dot2: "轨迹估计", ch1_dot3: "目标追踪",
      ch2_eyebrow: "02 · 可视化",
      ch2_head: "任意数据流，直接生成转播画面。",
      ch2_body: "无论是事件数据还是追踪数据——Sony Hawk-Eye、Stats Perform、StatsBomb，或你已经使用的任何标准——我们都能将其转化为清晰、干净、可直接上屏的转播图形。",
      ch2_dot1: "进球回放", ch2_dot2: "进攻通道", ch2_dot3: "射门分布",
      ch3_eyebrow: "03 · 研究",
      ch3_head: "这不只是工程项目。",
      ch3_body_1: "球场控制、预期进球、预期威胁——我们立足足球科学的前沿成果，并在此基础上构建自研模型，为每一个问题选择最合适的方法持续打磨。我们在 ",
      ch3_body_2: " 开源该领域领先的指标，也欢迎每一位有志学者与实践者加入这项研究。",
      ch3_dot1: "球场控制", ch3_dot2: "xG 模型", ch3_dot3: "xT 模型",
      ch4_head: '无论你是谁，都有<span class="g">参与其中的方式</span>。',
      ch4_c1_t: "数据提供商", ch4_c1_b: "用计算机视觉，让你的数据更进一步。更清晰的关键点识别，遮挡中依然稳定的球员追踪，以及镜头之外每名球员的轨迹补全。",
      ch4_c2_t: "转播方", ch4_c2_b: "任意数据格式输入，成品级转播输出。实时 AI 解说、球员聚焦、战术拆解与场上动态图形——随比赛同步生成。",
      ch4_c3_t: "俱乐部", ch4_c3_b: "一套内置我们模型的标注软件。教练可以绘制战术、生成转播级画面，并制作真正让球员记得住的录像分析课。",
      ch4_c4_t: "个人创作者", ch4_c4_b: "足球不只属于“专业人士”。热爱这项运动，也擅长某件事——音乐、艺术、历史、代码，什么都可以！来一起做点没人做过的东西。带上热爱，剩下的交给我们。",
      ch4_cta: "联系我们 / 预约演示",
      ch4_partners: "合作伙伴",
      partner_baidu_cloud: "百度智能云", partner_baidu_app: "百度App", partner_bilibili: "哔哩哔哩",
      ch1_note: '每一个可见标志点，都<b>锁定在像素坐标上</b>——99.7% 召回率，亚像素级精度。实测，不是估算。'
    },
    // Deutsch — translated + native-reviewed. Any missing key falls back to English.
    de: {
      doc_title: "KICK · Wissenschaft trifft Fußball",
      nav_cv: "Computer Vision", nav_viz: "Visualisierung", nav_research: "Forschung", nav_work: "Mitmachen",
      hero_slogan: '<span class="g">Wissenschaft</span> trifft Fußball.',
      scroll: "Nach unten scrollen",
      ch1_eyebrow: "01 · Computer Vision",
      ch1_head: "Wir lesen das Spiel direkt aus dem Video",
      ch1_body: "Keypoint-Erkennung, Spielerklassifizierung und Tracking – eigene Modelle, intern entwickelt und trainiert – machen aus Broadcast-Video räumliche Daten, ganz ohne Drittanbieter-Feed. Der Datensatz darunter genügt demselben Anspruch: akribisch annotiert, Bild für Bild.",
      ch1_dot1: "Keypoint-Erkennung", ch1_dot2: "Trace-Schätzung", ch1_dot3: "Objektverfolgung",
      ch2_eyebrow: "02 · Visualisierung",
      ch2_head: "Aus jedem Feed wird Broadcast.",
      ch2_body: "Event-Daten oder vollständiges Tracking – Sony Hawk-Eye, Stats Perform, StatsBomb oder welchen Standard auch immer Sie schon nutzen – wir nehmen alles davon und machen daraus saubere, sendefertige Grafiken.",
      ch2_dot1: "Torwiederholung", ch2_dot2: "Zonendominanz", ch2_dot3: "Schusskarte",
      ch3_eyebrow: "03 · Forschung",
      ch3_head: "Mehr als ein Engineering-Projekt.",
      ch3_body_1: "Pitch Control, Expected Goals, Expected Threat – wir bauen auf dem Besten der Fußballwissenschaft auf und entwickeln es mit eigenen Value-Modellen weiter, für jedes Problem mit der passenden Methode verfeinert. Wir stellen die führenden Metriken des Fachs auf ",
      ch3_body_2: " als Open Source bereit und laden alle angehenden Forschenden und Praktiker ein, an der Forschung mitzuwirken.",
      ch3_dot1: "Pitch Control", ch3_dot2: "xG-Modell", ch3_dot3: "xT-Modell",
      ch4_head: 'Egal, wer Sie sind – es gibt <span class="g">einen Weg hinein.</span>',
      ch4_c1_t: "Datenanbieter", ch4_c1_b: "Computer Vision, die Ihre Zahlen aufwertet. Schärfere Keypoints, Spieler auch bei Verdeckung durchgängig verfolgt und Traces für alle außerhalb des Bildes.",
      ch4_c2_t: "Broadcaster", ch4_c2_b: "Jedes Datenformat rein, fertige Sendung raus. Live-KI-Kommentar, Spieler-Spotlights, Taktik-Analysen und Grafiken direkt auf dem Spielfeld – live, während das Spiel läuft.",
      ch4_c3_t: "Vereine", ch4_c3_b: "Annotationssoftware mit unseren Modellen an Bord. Trainer skizzieren Taktik, erzeugen Grafiken in Broadcast-Qualität und gestalten Videoanalysen, die hängen bleiben.",
      ch4_c4_t: "Einzelpersonen", ch4_c4_b: "Fußball ist nicht nur etwas für die Branche. Sie lieben das Spiel und sind in irgendetwas brillant – Musik, Kunst, Geschichte, Code, was auch immer? Kommen Sie und schaffen Sie etwas, das es so noch nie gab. Bringen Sie die Leidenschaft mit – den Rest finden wir.",
      ch4_cta: "Kontakt aufnehmen / Demo anfragen",
      ch4_partners: "Partnerschaften",
      partner_baidu_cloud: "Baidu AI Cloud", partner_baidu_app: "Baidu App", partner_bilibili: "Bilibili",
      ch1_note: 'Jede sichtbare Landmarke, <b>auf den Pixel genau</b> – 99,7 % Recall, Subpixel-Präzision. Gemessen, nicht geschätzt.'
    },
    // Español — translated + native-reviewed. Any missing key falls back to English.
    es: {
      doc_title: "KICK · Unimos ciencia y fútbol",
      nav_cv: "Visión por computadora", nav_viz: "Visualización", nav_research: "Investigación", nav_work: "Trabaja con nosotros",
      hero_slogan: 'Unimos <span class="g">ciencia</span> y fútbol.',
      scroll: "Desplázate hacia abajo",
      ch1_eyebrow: "01 · Visión por computadora",
      ch1_head: "Leemos el juego directamente del video",
      ch1_body: "Detección de puntos clave, clasificación y seguimiento de jugadores —modelos originales, construidos y entrenados internamente— convierten el video de transmisión en datos espaciales, sin necesidad de señales de terceros. El conjunto de datos que los sustenta cumple el mismo estándar: anotado con rigor, cuadro por cuadro.",
      ch1_dot1: "Detección de puntos clave", ch1_dot2: "Estimación de trayectorias", ch1_dot3: "Seguimiento de objetos",
      ch2_eyebrow: "02 · Visualización",
      ch2_head: "Convertimos cualquier señal en transmisión.",
      ch2_body: "Datos de eventos o seguimiento completo —Sony Hawk-Eye, Stats Perform, StatsBomb o el estándar que ya utilices— tomamos cualquiera de ellos y lo convertimos en gráficos limpios, listos para transmisión.",
      ch2_dot1: "Repetición de gol", ch2_dot2: "Dominio de carriles", ch2_dot3: "Mapa de tiros",
      ch3_eyebrow: "03 · Investigación",
      ch3_head: "Más que un proyecto de ingeniería.",
      ch3_body_1: "Control del terreno, goles esperados, amenaza esperada —partimos de lo mejor de la ciencia del fútbol y construimos sobre ella con nuestros propios modelos de valor, refinados con el método adecuado para cada problema. Publicamos en código abierto las métricas de referencia del sector en ",
      ch3_body_2: ", e invitamos a todos los académicos y profesionales en ciernes a sumarse a la investigación.",
      ch3_dot1: "Control del terreno", ch3_dot2: "Modelo xG", ch3_dot3: "Modelo xT",
      ch4_head: 'Seas quien seas, hay <span class="g">una puerta de entrada.</span>',
      ch4_c1_t: "Proveedores de datos", ch4_c1_b: "Visión por computadora que eleva tus cifras. Puntos clave más precisos, jugadores rastreados a pesar de las oclusiones y trayectorias para todos los que quedan fuera de cámara.",
      ch4_c2_t: "Emisoras", ch4_c2_b: "Cualquier formato de datos a la entrada, una transmisión terminada a la salida. Narración en vivo con IA, jugadores destacados, análisis tácticos y gráficos sobre el terreno de juego, a medida que sucede el partido.",
      ch4_c3_t: "Clubes", ch4_c3_b: "Software de anotación con nuestros modelos integrados. Los entrenadores dibujan tácticas, generan gráficos con calidad de transmisión y crean sesiones de video que dejan huella.",
      ch4_c4_t: "Personas", ch4_c4_b: "El fútbol no es solo para la industria. ¿Amas el juego y destacas en algo —música, arte, historia, código, lo que sea? Ven a crear algo que nadie haya hecho antes. Tú pon la pasión; del resto nos encargamos nosotros.",
      ch4_cta: "Contáctanos / Solicita una demo",
      ch4_partners: "Alianzas",
      partner_baidu_cloud: "Baidu AI Cloud", partner_baidu_app: "Baidu App", partner_bilibili: "Bilibili",
      ch1_note: 'Cada punto de referencia visible, <b>fijado al píxel</b> — 99,7 % de exhaustividad, precisión subpíxel. Medido, no estimado.'
    }
  };
  var LANGS = { en: 1, zh: 1, de: 1, es: 1 }, HTMLLANG = { en: 'en', zh: 'zh-CN', de: 'de', es: 'es' };

  function qsa(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function apply(lang){
    var d = DICT[lang] || {}, e = DICT.en;
    function val(k){ return (d[k] != null) ? d[k] : e[k]; }
    qsa('[data-i18n]').forEach(function(el){ var v = val(el.getAttribute('data-i18n')); if(v != null) el.textContent = v; });
    qsa('[data-i18n-html]').forEach(function(el){ var v = val(el.getAttribute('data-i18n-html')); if(v != null) el.innerHTML = v; });
    qsa('[data-i18n-title]').forEach(function(el){ var v = val(el.getAttribute('data-i18n-title')); if(v != null) el.title = v; });
    qsa('[data-i18n-aria]').forEach(function(el){ var v = val(el.getAttribute('data-i18n-aria')); if(v != null) el.setAttribute('aria-label', v); });
    var dt = val('doc_title'); if(dt) document.title = dt;
    document.documentElement.lang = HTMLLANG[lang] || 'en';
    document.documentElement.setAttribute('data-lang', lang);
    qsa('[data-lang-btn]').forEach(function(b){ b.classList.toggle('on', b.getAttribute('data-lang-btn') === lang); });
  }
  function set(lang){ if(!LANGS[lang]) lang = 'en'; try{ localStorage.setItem('kick_lang', lang); }catch(e){} apply(lang); }
  function init(){
    var url = null; try{ url = new URLSearchParams(location.search).get('lang'); }catch(e){}
    var saved = null; try{ saved = localStorage.getItem('kick_lang'); }catch(e){}
    var forced = LANGS[url] ? url : null;
    var nav2 = (navigator.language || navigator.userLanguage || '').toLowerCase().slice(0, 2);
    var lang = forced || (LANGS[saved] ? saved : null) || (LANGS[nav2] ? nav2 : 'en');
    qsa('[data-lang-btn]').forEach(function(b){ b.addEventListener('click', function(){ set(b.getAttribute('data-lang-btn')); }); });
    if(forced){ set(forced); } else { apply(lang); }   // ?lang=en|zh|de|es deep-links (and persists); otherwise saved pref / browser language
  }
  if(document.readyState !== 'loading') init(); else document.addEventListener('DOMContentLoaded', init);
  return { set: set, apply: apply, get dict(){ return DICT; } };
})();
