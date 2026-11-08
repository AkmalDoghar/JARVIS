import * as Linking from 'expo-linking';
import { Platform } from 'react-native';
import * as IntentLauncher from 'expo-intent-launcher';

export class AppLauncherService {
  /**
   * Open phone photo gallery
   */
  public static async openGallery(): Promise<{ success: boolean; message: string }> {
    try {
      if (Platform.OS === 'android') {
        await IntentLauncher.startActivityAsync('android.intent.action.VIEW', {
          data: 'content://media/internal/images/media',
          type: 'image/*',
        });
        return { success: true, message: 'Opening phone gallery' };
      } else {
        await Linking.openURL('photos-redirect://');
        return { success: true, message: 'Opening photos' };
      }
    } catch (e: any) {
      // Fallback intent for android
      try {
        await IntentLauncher.startActivityAsync('android.intent.action.MAIN', {
          category: 'android.intent.category.APP_GALLERY',
        });
        return { success: true, message: 'Opening gallery' };
      } catch (err: any) {
        return { success: false, message: 'Gallery app could not be opened' };
      }
    }
  }

  /**
   * Open phone camera
   */
  public static async openCamera(): Promise<{ success: boolean; message: string }> {
    try {
      if (Platform.OS === 'android') {
        await IntentLauncher.startActivityAsync('android.media.action.STILL_IMAGE_CAMERA');
        return { success: true, message: 'Opening camera' };
      } else {
        await Linking.openURL('camera://');
        return { success: true, message: 'Opening camera' };
      }
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
