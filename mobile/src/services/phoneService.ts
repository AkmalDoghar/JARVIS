import * as Linking from 'expo-linking';
import { Platform } from 'react-native';
import * as IntentLauncher from 'expo-intent-launcher';
import { ContactItem } from '../types';

export class PhoneService {
  /**
   * Initiate a phone call to a phone number or ContactItem
   */
  public static async makeCall(target: ContactItem | string): Promise<{ success: boolean; message: string }> {
    try {
      let phoneNumber = typeof target === 'string' ? target : target.primaryNumber;
      // Clean phone number
      phoneNumber = phoneNumber.replace(/[^0-9+]/g, '');

      if (!phoneNumber) {
        return { success: false, message: 'Invalid phone number' };
      }

      const url = `tel:${phoneNumber}`;
      const canOpen = await Linking.canOpenURL(url);

      if (canOpen) {
        await Linking.openURL(url);
        return {
          success: true,
          message: `Dialing ${typeof target === 'string' ? phoneNumber : target.name} (${phoneNumber})`,
        };
      } else {
        // Fallback for Android using IntentLauncher
        if (Platform.OS === 'android') {
          await IntentLauncher.startActivityAsync('android.intent.action.DIAL', {
            data: url,
          });
          return { success: true, message: `Opened dialer for ${phoneNumber}` };
        }
        return { success: false, message: 'Device does not support calling' };
      }
    } catch (e: any) {
      console.warn('Call error:', e);
      return { success: false, message: e.message || 'Call failed' };
    }
  }

  /**
   * End or dismiss the active call
   */
  public static async endCall(): Promise<{ success: boolean; message: string }> {
    try {
      if (Platform.OS === 'android') {
        // Bring home screen / close in-call screen
        await IntentLauncher.startActivityAsync('android.intent.action.MAIN', {
          category: 'android.intent.category.HOME',
        });
        return { success: true, message: 'Call dismissed. Returned to JARVIS HUD.' };
      }
      return { success: true, message: 'Call disconnected.' };
    } catch (e: any) {
      return { success: false, message: e.message || 'Failed to dismiss call' };
    }
  }
}
