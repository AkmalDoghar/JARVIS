import * as Linking from 'expo-linking';
import { Platform } from 'react-native';
import { SafeNative } from './safeNativeModules';

export class AppLauncherService {
  /**
   * Open phone photo gallery safely
   */
  public static async openGallery(): Promise<{ success: boolean; message: string }> {
    try {
      if (Platform.OS === 'android') {
        const IntentLauncher = SafeNative.IntentLauncher;
        if (IntentLauncher && typeof IntentLauncher.startActivityAsync === 'function') {
          await IntentLauncher.startActivityAsync('android.intent.action.VIEW', {
            data: 'content://media/internal/images/media',
            type: 'image/*',
          });
          return { success: true, message: 'Opening phone gallery' };
        }
      }
      await Linking.openURL('content://media/internal/images/media').catch(() => {});
      return { success: true, message: 'Opening photos' };
    } catch (e: any) {
      return { success: false, message: 'Gallery app could not be opened' };
    }
  }

  /**
   * Open phone camera safely
   */
  public static async openCamera(): Promise<{ success: boolean; message: string }> {
    try {
      if (Platform.OS === 'android') {
        const IntentLauncher = SafeNative.IntentLauncher;
        if (IntentLauncher && typeof IntentLauncher.startActivityAsync === 'function') {
          await IntentLauncher.startActivityAsync('android.media.action.STILL_IMAGE_CAMERA');
          return { success: true, message: 'Opening camera' };
        }
      }
      await Linking.openURL('camera://').catch(() => {});
      return { success: true, message: 'Opening camera' };
    } catch (e: any) {
      return { success: false, message: 'Camera could not be opened' };
    }
  }

  /**
   * Open Maps / Navigation
   */
  public static async openMaps(query: string = 'nearest petrol pump'): Promise<{ success: boolean; message: string }> {
    try {
      const url = `geo:0,0?q=${encodeURIComponent(query)}`;
      const can = await Linking.canOpenURL(url);
      if (can) {
        await Linking.openURL(url);
        return { success: true, message: 'Opening navigation maps' };
      } else {
        await Linking.openURL(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`);
        return { success: true, message: 'Opening Google Maps web' };
      }
    } catch (e: any) {
      return { success: false, message: 'Maps could not be opened' };
    }
  }

  /**
   * Open generic URL or app scheme
   */
  public static async openUrl(url: string): Promise<{ success: boolean; message: string }> {
    try {
      await Linking.openURL(url);
      return { success: true, message: `Opened ${url}` };
    } catch (e: any) {
      return { success: false, message: `Could not open ${url}` };
    }
  }
}
