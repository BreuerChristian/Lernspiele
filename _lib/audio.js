/*
 * Lernspiele Audio-Helper
 *
 * Geteilter Web-Audio-Layer fuer alle Lernspiele. Standardisiert das
 * Sound-Vokabular: correct/wrong/tap erzeugen ueberall den gleichen Klang,
 * sodass Kinder die Rueckmeldung wiedererkennen.
 *
 * Verwendung:
 *   <script src="../_lib/audio.js"></script>
 *   <script>
 *     // Beim ersten User-Tap einmal anstossen (iOS-Anforderung):
 *     document.addEventListener('pointerdown', Lernspiele.Audio.ensure, { once: true });
 *
 *     Lernspiele.Audio.correct();   // richtige Antwort
 *     Lernspiele.Audio.wrong();     // falsche Antwort
 *     Lernspiele.Audio.tap();       // generischer Tap-Feedback-Ton
 *     Lernspiele.Audio.tone(660, 0.12);  // freier Ton fuer Spielmechanik
 *     Lernspiele.Audio.sequence([
 *       { freq: 440, dur: 0.10 },
 *       { freq: 660, dur: 0.14, delay: 0.10 },
 *       { freq: 880, dur: 0.20, delay: 0.10 }
 *     ]);
 *   </script>
 *
 * Sound-Vokabular (verbindlich):
 *   correct  : 660 -> 880 Hz aufsteigend, 2 Toene, sine, vol 0.07
 *   wrong    : 220 -> 180 Hz absteigend, 2 Toene, triangle, vol 0.05
 *   tap      : 440 Hz, 60 ms, sine, vol 0.04
 *
 * Eigene Toene fuer Spielmechanik (zaehlen, stapeln, fliegen) sind erlaubt
 * und sollten ueber tone() / sequence() laufen.
 */

(function (global) {
  'use strict';

  let audioCtx = null;

  function ensureAudio() {
    if (audioCtx) {
      if (audioCtx.state === 'suspended') {
        try { audioCtx.resume(); } catch (e) { /* ignore */ }
      }
      return audioCtx;
    }
    try {
      const Ctor = global.AudioContext || global.webkitAudioContext;
      if (!Ctor) return null;
      audioCtx = new Ctor();
    } catch (e) {
      audioCtx = null;
    }
    return audioCtx;
  }

  function tone(freq, dur, vol, type) {
    if (dur === undefined) dur = 0.12;
    if (vol === undefined) vol = 0.06;
    if (!type) type = 'sine';
    const ctx = ensureAudio();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    osc.connect(gain);
    gain.connect(ctx.destination);
    const t = ctx.currentTime;
    gain.gain.setValueAtTime(vol, t);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.start(t);
    osc.stop(t + dur);
  }

  function sequence(steps) {
    if (!Array.isArray(steps)) return;
    let acc = 0;
    for (let i = 0; i < steps.length; i++) {
      const s = steps[i];
      acc += (s.delay || 0);
      const freq = s.freq;
      const dur = s.dur;
      const vol = s.vol;
      const type = s.type;
      setTimeout(function () { tone(freq, dur, vol, type); }, acc * 1000);
    }
  }

  function correct() {
    sequence([
      { freq: 660, dur: 0.14, vol: 0.07 },
      { freq: 880, dur: 0.22, vol: 0.07, delay: 0.11 }
    ]);
  }

  function wrong() {
    sequence([
      { freq: 220, dur: 0.18, vol: 0.05, type: 'triangle' },
      { freq: 180, dur: 0.20, vol: 0.05, type: 'triangle', delay: 0.10 }
    ]);
  }

  function tap() {
    tone(440, 0.06, 0.04, 'sine');
  }

  global.Lernspiele = global.Lernspiele || {};
  global.Lernspiele.Audio = {
    ensure: ensureAudio,
    tone: tone,
    sequence: sequence,
    correct: correct,
    wrong: wrong,
    tap: tap
  };
})(window);
