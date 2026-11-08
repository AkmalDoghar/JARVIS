import { ParsedCommand } from '../types';
import { SafeNative } from './safeNativeModules';

export class VoiceEngine {
  private static isSpeaking: boolean = false;

  /**
   * Speak out text with a JARVIS-style calm, futuristic tone
   */
  public static async speak(text: string, onDone?: () => void): Promise<void> {
    try {
      this.isSpeaking = true;
      const Speech = SafeNative.Speech;
      if (Speech && typeof Speech.speak === 'function') {
        Speech.stop();
        Speech.speak(text, {
          language: 'en-GB', // JARVIS British accent default
          pitch: 0.95,
          rate: 0.98,
          onDone: () => {
            this.isSpeaking = false;
            if (onDone) onDone();
          },
          onError: () => {
            this.isSpeaking = false;
            if (onDone) onDone();
          },
        });
      } else {
        // Fallback: wait 1.5s then trigger onDone
        setTimeout(() => {
          this.isSpeaking = false;
          if (onDone) onDone();
        }, 1200);
      }
    } catch (e) {
      console.warn('[VoiceEngine] Speech synthesis error:', e);
      this.isSpeaking = false;
      if (onDone) onDone();
    }
  }

  public static stopSpeaking(): void {
    try {
      const Speech = SafeNative.Speech;
      if (Speech && typeof Speech.stop === 'function') {
        Speech.stop();
      }
      this.isSpeaking = false;
    } catch (e) {
      // ignore
    }
  }

  /**
   * Parse voice input (Roman Urdu, Urdu-English, English) into structured commands.
   * Completely handles Akmal Sir's bike voice commands offline without latency!
   */
  public static parseCommand(raw: string): ParsedCommand {
    const text = (raw || '').trim().toLowerCase();

    // 1. MUSIC: Fast-forward / Rewind
    if (
      text.includes('forword') ||
      text.includes('forward') ||
      text.includes('aage kro') ||
      text.includes('agay karo') ||
      text.includes('skip 10')
    ) {
      return { type: 'SEEK_FORWARD', rawText: raw };
    }
    if (
      text.includes('backward') ||
      text.includes('rewind') ||
      text.includes('peeche') ||
      text.includes('pichay kro gana')
    ) {
      return { type: 'SEEK_BACKWARD', rawText: raw };
    }

    // 2. MUSIC: Next Track
    if (
      text.includes('next') ||
      text.includes('agla') ||
      text.includes('next song') ||
      text.includes('change song') ||
      text.includes('agla gana')
    ) {
      return { type: 'NEXT_TRACK', rawText: raw };
    }

    // 3. MUSIC: Previous Track
    if (
      text.includes('previous') ||
      text.includes('pichay') ||
      text.includes('pichla') ||
      text.includes('back song') ||
      text.includes('prev')
    ) {
      return { type: 'PREV_TRACK', rawText: raw };
    }

    // 4. MUSIC: Stop / Pause
    if (
      text.includes('stop') ||
      text.includes('pause') ||
      text.includes('roko') ||
      text.includes('band kro gana') ||
      text.includes('music band') ||
      text.includes('gana roko')
    ) {
      return { type: 'PAUSE_MUSIC', rawText: raw };
    }

    // 5. MUSIC: Play / Resume / Favorites
    if (
      text.includes('favourit') ||
      text.includes('favorite') ||
      text.includes('favourite') ||
      text.includes('pasandeeda') ||
      text.includes('play music') ||
      text.includes('play song') ||
      text.includes('play') ||
      text.includes('chalao') ||
      text.includes('gana lagao') ||
      text.includes('resume')
    ) {
      return { type: 'PLAY_MUSIC', rawText: raw };
    }

    // 6. CALL: End / Disconnect Call
    if (
      text.includes('call band') ||
      text.includes('call kato') ||
      text.includes('call kaat') ||
      text.includes('call cut') ||
      text.includes('end call') ||
      text.includes('disconnect') ||
      text.includes('hang up')
    ) {
      return { type: 'END_CALL', rawText: raw };
    }

    // 7. WHATSAPP: Call or Message
    if (text.includes('whatsapp') || text.includes('whatsap')) {
      const isCall =
        text.includes('call') ||
        text.includes('milao') ||
        text.includes('ring');

      let target = '';
      const nameMatch = text.match(
        /(?:whatsapp\s+(?:per|pe)?\s*([a-zA-Z0-9\s]+?)\s*(?:ko|call|message|msg))/i
      );
      if (nameMatch && nameMatch[1]) {
        target = nameMatch[1].replace(/call|message|msg|ko/g, '').trim();
      } else {
        const clean = text.replace(/whatsapp|whatsap|call|message|msg|per|pe|ko/gi, '').trim();
        target = clean;
      }

      if (isCall) {
        return { type: 'WHATSAPP_CALL', target: target || undefined, rawText: raw };
      } else {
        return { type: 'WHATSAPP_MESSAGE', target: target || undefined, rawText: raw };
      }
    }

    // 8. PHONE CALL: "Ali ko call milao", "call Bhai", "phone lagao Imran"
    if (
      text.includes('call') ||
      text.includes('phone') ||
      text.includes('milao') ||
      text.includes('mila do') ||
      text.includes('dial')
    ) {
      let target = text
        .replace(/(?:ko\s*)?(?:call\s*milao|call\s*kro|call\s*karo|phone\s*karo|phone\s*milao|call|phone|dial|mila\s*do)/gi, '')
        .replace(/^(?:jarvis|hey jarvis|mr jarvis)\s*/gi, '')
        .replace(/\b(?:ko|pe|per)\b/gi, '')
        .trim();

      return {
        type: 'CALL_CONTACT',
        target: target || undefined,
        rawText: raw,
      };
    }

    // 9. APPS: Gallery, Camera, Maps
    if (text.includes('gallery') || text.includes('tasweer') || text.includes('photos')) {
      return { type: 'OPEN_GALLERY', rawText: raw };
    }
    if (text.includes('camera') || text.includes('photo khincho')) {
      return { type: 'OPEN_CAMERA', rawText: raw };
    }
    if (text.includes('maps') || text.includes('location') || text.includes('rasta') || text.includes('navigation')) {
      return { type: 'OPEN_MAPS', rawText: raw };
    }

    // 10. TELEMETRY & STATUS
    if (text.includes('battery') || text.includes('charging')) {
      return { type: 'BATTERY_STATUS', rawText: raw };
    }
    if (text.includes('time') || text.includes('waqt') || text.includes('kitne baje')) {
      return { type: 'TIME_CHECK', rawText: raw };
    }
    if (text.includes('status') || text.includes('report') || text.includes('kya haal')) {
      return { type: 'JARVIS_STATUS', rawText: raw };
    }

    return { type: 'UNKNOWN', rawText: raw };
  }
}
