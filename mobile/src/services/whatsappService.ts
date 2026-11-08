import * as Linking from 'expo-linking';
import { ContactItem } from '../types';

export class WhatsAppService {
  /**
   * Send WhatsApp text message to contact or number
   */
  public static async sendMessage(
    target: ContactItem | string,
    messageText: string = 'Salam Akmal Sir is on bike ride.'
  ): Promise<{ success: boolean; message: string }> {
    try {
      let rawNumber = typeof target === 'string' ? target : target.primaryNumber;
      let cleanNumber = rawNumber.replace(/[^0-9]/g, '');

      // Normalize Pakistan numbers: e.g. 03001234567 -> 923001234567
      if (cleanNumber.startsWith('03')) {
        cleanNumber = '92' + cleanNumber.substring(1);
      }

      const encodedMsg = encodeURIComponent(messageText);
      const appUrl = `whatsapp://send?phone=${cleanNumber}&text=${encodedMsg}`;
      const webUrl = `https://api.whatsapp.com/send?phone=${cleanNumber}&text=${encodedMsg}`;

      const canOpen = await Linking.canOpenURL(appUrl);
      if (canOpen) {
        await Linking.openURL(appUrl);
      } else {
        await Linking.openURL(webUrl);
      }

      const targetName = typeof target === 'string' ? cleanNumber : target.name;
      return {
        success: true,
        message: `Opening WhatsApp chat with ${targetName}`,
      };
    } catch (e: any) {
      console.warn('WhatsApp message error:', e);
      return { success: false, message: e.message || 'Could not open WhatsApp' };
    }
  }

  /**
   * Open WhatsApp call or contact chat
   */
  public static async makeCall(target: ContactItem | string): Promise<{ success: boolean; message: string }> {
    try {
      let rawNumber = typeof target === 'string' ? target : target.primaryNumber;
      let cleanNumber = rawNumber.replace(/[^0-9]/g, '');
      if (cleanNumber.startsWith('03')) {
        cleanNumber = '92' + cleanNumber.substring(1);
      }

      // WhatsApp deep link to user chat (where user can 1-tap call)
      const callUrl = `whatsapp://send?phone=${cleanNumber}&text=${encodeURIComponent('Calling you via JARVIS...')}`;
      const canOpen = await Linking.canOpenURL(callUrl);
      if (canOpen) {
        await Linking.openURL(callUrl);
      } else {
        await Linking.openURL(`https://api.whatsapp.com/send?phone=${cleanNumber}`);
      }

      const targetName = typeof target === 'string' ? cleanNumber : target.name;
      return {
        success: true,
        message: `Opening WhatsApp call for ${targetName}`,
      };
    } catch (e: any) {
      console.warn('WhatsApp call error:', e);
      return { success: false, message: e.message || 'WhatsApp call failed' };
    }
  }
}

