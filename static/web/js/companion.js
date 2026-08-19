const RECAPS = {
  quick: `<p class="recap-label">30-second recap</p>
<ul>
<li>The narrator walks St. Petersburg at night, almost without friends.</li>
<li>He meets Nastenka on the embankment and stays with her.</li>
<li>She is waiting for another man — a lodger who promised to return.</li>
<li>They begin a careful friendship in the white nights.</li>
<li>He is already more attached than he admits.</li>
</ul>
<p class="recap-label">Key characters</p>
<p>Narrator — lonely dreamer. Nastenka — the young woman he meets. The lodger — the man she waits for.</p>`,
  standard: `<p class="recap-label">2-minute recap</p>
<p>A nameless young man has lived in Petersburg for years and still feels unknown there. He walks at night, talking more easily to houses than to people. On one of those walks he finds Nastenka by the water, frightened and alone, and he stays.</p>
<p>She tells him, without much ceremony, that her heart is already promised. A lodger once lived in her grandmother’s house. He was kind to her, then left, and said he would come back. She is waiting on the bridge of those nights for that return.</p>
<p>What you should hold: the city, the chance meeting, her waiting, and the narrator’s growing wish to be needed. The story, at this point, is still an open night — not a conclusion.</p>
<p class="recap-label">Where you are</p>
<p>Night 2. They have begun to trust each other. The lodger has not appeared. Nothing later has happened yet, as far as PageBack is concerned.</p>`,
  detailed: `<p class="recap-label">5-minute recap</p>
<p><strong>Night 1.</strong> The narrator describes his solitude and the strange tenderness he feels for the streets. He meets Nastenka. She is restless, almost theatrical in her honesty, and already bound to someone who is not there.</p>
<p><strong>Night 2.</strong> They meet again. The friendship quickens. She tells more of the lodger, the cramped household with her grandmother, and the promise that keeps her looking down the canal. The narrator listens, and something in him rearranges around her voice.</p>
<p><strong>Characters so far.</strong> The narrator wants company and is ashamed of how much. Nastenka wants the man who said he would return. The lodger is only a figure in her telling — important, but not yet on the page with them.</p>
<p><strong>Atmosphere.</strong> Pale nights, a city that never quite goes dark, talk that feels safer because morning is far away.</p>
<p><strong>Current place.</strong> You have read through Night 2. PageBack will not speak of what follows.</p>`,
};

const WHO = {
  narrator: `<strong>The Narrator</strong><br>A dreamy young man who walks Petersburg after dark. By Night 2 you know he is lonely, quick to attach, and already treating Nastenka as the first real conversation of his summer.`,
  nastenka: `<strong>Nastenka</strong><br>A young woman he meets on the embankment. She lives with her grandmother and is waiting for a lodger who promised to come back. She is frank, restless, and kinder than the situation is.`,
  lodger: `<strong>The Lodger</strong><br>You have not met him. You only have Nastenka’s account: he lived in their house, was kind to her, left, and said he would return. Whether he will is beyond Night 2, so PageBack will not guess.`,
};

const ASKS = {
  trust: `Based only on Nights 1–2: she is frightened and alone when they meet, and he does not take advantage of that. She talks because he stays, listens, and offers company without claiming her. Trust here is still new, and still mixed with her waiting for someone else.`,
  waiting: `She is waiting for the lodger who once lived with her grandmother — a man who was kind to her and promised to return. That is all the first two nights establish. PageBack will not say whether he keeps the promise.`,
  ending: `That is beyond your current reading point, so I will not spoil it. What you know is only this: she is waiting, and the narrator is already attached.`,
};

function setModes(board, active) {
  board.querySelectorAll(".mode").forEach((btn) => {
    const on = btn.dataset.mode === active;
    btn.classList.toggle("is-on", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  });
  const copy = board.querySelector("[data-recap-copy]");
  if (copy) copy.innerHTML = RECAPS[active] || RECAPS.quick;
}

function bindRecaps() {
  document.querySelectorAll("[data-recap-board]").forEach((board) => {
    setModes(board, "quick");
    board.querySelectorAll(".mode").forEach((btn) => {
      btn.addEventListener("click", () => setModes(board, btn.dataset.mode));
    });
  });
}

function bindWho() {
  const panel = document.querySelector("[data-who-panel]");
  if (!panel) return;
  document.querySelectorAll("[data-who]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-who]").forEach((el) => el.classList.remove("is-on"));
      btn.classList.add("is-on");
      panel.innerHTML = WHO[btn.dataset.who] || "";
    });
  });
}

function bindAsk() {
  const panel = document.querySelector("[data-ask-panel]");
  if (!panel) return;
  document.querySelectorAll("[data-ask]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-ask]").forEach((el) => el.classList.remove("is-on"));
      btn.classList.add("is-on");
      panel.textContent = ASKS[btn.dataset.ask] || "";
    });
  });
}

bindRecaps();
bindWho();
bindAsk();
