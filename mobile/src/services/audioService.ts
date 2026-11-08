import { Audio, AVPlaybackStatus } from 'expo-av';
import * as MediaLibrary from 'expo-media-library';
import { Track } from '../types';

export class AudioService {
  private static sound: Audio.Sound | null = null;
  private static playlist: Track[] = [];
  private static currentIndex: number = -1;
  private static isPlaying: boolean = false;
  private static onStatusChangeListeners: Array<(status: { isPlaying: boolean; track: Track | null; position: number; duration: number }) => void> = [];

  /**
   * Request media permissions and scan device for audio files
   */
  public static async scanDeviceSongs(): Promise<Track[]> {
    try {
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        console.warn('MediaLibrary permission not granted');
        return this.getDefaultSamplePlaylist();
      }

      const media = await MediaLibrary.getAssetsAsync({
        mediaType: 'audio',
        first: 100,
        sortBy: 'modificationTime',
      });

      if (!media || !media.assets || media.assets.length === 0) {
        return this.getDefaultSamplePlaylist();
      }

      const tracks: Track[] = media.assets.map((asset, index) => {
        const cleanName = asset.filename.replace(/\.[^/.]+$/, '');
        return {
          id: asset.id || `track_${index}`,
          title: cleanName,
          artist: 'Local Phone Audio',
          uri: asset.uri,
          duration: asset.duration || 0,
          filename: asset.filename,
          isFavorite: index < 5, // first 5 marked as favorites by default
        };
      });

      this.playlist = tracks;
      if (this.currentIndex === -1 && tracks.length > 0) {
        this.currentIndex = 0;
      }

      return tracks;
    } catch (e) {
      console.warn('Failed to scan device audio:', e);
      return this.getDefaultSamplePlaylist();
    }
  }

  /**
   * Fallback curated sample tracks if device storage is empty or in simulator
   */
  public static getDefaultSamplePlaylist(): Track[] {
    const samples: Track[] = [
      {
        id: 'sample_1',
        title: 'Akmal Sir Favorite - Ride Beats 01',
        artist: 'JARVIS Synthesizer',
        uri: 'https://cdn.freesound.org/previews/573/573381_5674468-lq.mp3',
        duration: 180,
        filename: 'ride_beats_01.mp3',
        isFavorite: true,
      },
      {
        id: 'sample_2',
        title: 'Highway Speed Cyberdrive',
        artist: 'JARVIS Synthesizer',
        uri: 'https://cdn.freesound.org/previews/567/567634_5674468-lq.mp3',
        duration: 210,
        filename: 'highway_cyberdrive.mp3',
        isFavorite: true,
      },
      {
        id: 'sample_3',
        title: 'Arc Reactor Resonance',
        artist: 'JARVIS Synthesizer',
        uri: 'https://cdn.freesound.org/previews/573/573381_5674468-lq.mp3',
        duration: 160,
        filename: 'arc_reactor.mp3',
        isFavorite: true,
      },
    ];
    this.playlist = samples;
    this.currentIndex = 0;
    return samples;
  }

  public static getPlaylist(): Track[] {
    return this.playlist;
  }

  public static getCurrentTrack(): Track | null {
    if (this.currentIndex >= 0 && this.currentIndex < this.playlist.length) {
      return this.playlist[this.currentIndex];
    }
    return null;
  }

  public static getIsPlaying(): boolean {
    return this.isPlaying;
  }

  public static subscribeStatus(cb: (status: { isPlaying: boolean; track: Track | null; position: number; duration: number }) => void): () => void {
    this.onStatusChangeListeners.push(cb);
    return () => {
      this.onStatusChangeListeners = this.onStatusChangeListeners.filter(l => l !== cb);
    };
  }

  private static notifyStatus(position: number = 0, duration: number = 0) {
    const cur = this.getCurrentTrack();
    this.onStatusChangeListeners.forEach(cb => {
      cb({
        isPlaying: this.isPlaying,
        track: cur,
        position,
        duration: duration || (cur ? cur.duration : 0),
      });
    });
  }

  /**
   * Play current or specific track index
   */
  public static async playTrack(index?: number): Promise<boolean> {
    try {
      if (this.playlist.length === 0) {
        await this.scanDeviceSongs();
      }

      if (this.playlist.length === 0) {
        return false;
      }

      if (typeof index === 'number' && index >= 0 && index < this.playlist.length) {
        this.currentIndex = index;
      } else if (this.currentIndex < 0) {
        this.currentIndex = 0;
      }

      const track = this.playlist[this.currentIndex];
      if (!track) return false;

      // Configure background audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        staysActiveInBackground: true,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });

      if (this.sound) {
        await this.sound.unloadAsync();
        this.sound = null;
      }

      const { sound } = await Audio.Sound.createAsync(
        { uri: track.uri },
        { shouldPlay: true },
        this.onPlaybackStatusUpdate
      );

      this.sound = sound;
      this.isPlaying = true;
      this.notifyStatus(0, track.duration);
      return true;
    } catch (e) {
      console.warn('Failed to play track:', e);
      return false;
    }
  }

  /**
   * Play favorite songs specifically
   */
  public static async playFavorites(): Promise<boolean> {
    if (this.playlist.length === 0) {
      await this.scanDeviceSongs();
    }
    const favIdx = this.playlist.findIndex(t => t.isFavorite);
    if (favIdx >= 0) {
      return await this.playTrack(favIdx);
    }
    return await this.playTrack(0);
  }

  /**
   * Pause playback
   */
  public static async pause(): Promise<boolean> {
    try {
      if (this.sound) {
        await this.sound.pauseAsync();
        this.isPlaying = false;
        this.notifyStatus();
        return true;
      }
      return false;
    } catch (e) {
      console.warn('Failed to pause:', e);
      return false;
    }
  }

  /**
   * Resume playback
   */
  public static async resume(): Promise<boolean> {
    try {
      if (this.sound) {
        await this.sound.playAsync();
        this.isPlaying = true;
        this.notifyStatus();
        return true;
      } else {
        return await this.playTrack();
      }
    } catch (e) {
      console.warn('Failed to resume:', e);
      return false;
    }
  }

  /**
   * Stop playback completely
   */
  public static async stop(): Promise<boolean> {
    try {
      if (this.sound) {
        await this.sound.stopAsync();
        this.isPlaying = false;
        this.notifyStatus(0);
        return true;
      }
      return false;
    } catch (e) {
      console.warn('Failed to stop:', e);
      return false;
    }
  }

  /**
   * Next track in playlist
   */
  public static async next(): Promise<boolean> {
    if (this.playlist.length === 0) return false;
    let nextIdx = this.currentIndex + 1;
    if (nextIdx >= this.playlist.length) {
      nextIdx = 0; // loop back
    }
    return await this.playTrack(nextIdx);
  }

  /**
   * Previous track in playlist
   */
  public static async previous(): Promise<boolean> {
    if (this.playlist.length === 0) return false;
    let prevIdx = this.currentIndex - 1;
    if (prevIdx < 0) {
      prevIdx = this.playlist.length - 1;
    }
    return await this.playTrack(prevIdx);
  }

  /**
   * Seek forward by seconds (default +15 seconds)
   */
  public static async seekForward(seconds: number = 15): Promise<boolean> {
    try {
      if (!this.sound) return false;
      const status = await this.sound.getStatusAsync();
      if (status.isLoaded) {
        const newPos = Math.min(status.positionMillis + seconds * 1000, status.durationMillis || 0);
        await this.sound.setPositionAsync(newPos);
        this.notifyStatus(newPos / 1000, (status.durationMillis || 0) / 1000);
        return true;
      }
      return false;
    } catch (e) {
      console.warn('Failed to seek forward:', e);
      return false;
    }
  }

  /**
   * Seek backward by seconds (default -15 seconds)
   */
  public static async seekBackward(seconds: number = 15): Promise<boolean> {
    try {
      if (!this.sound) return false;
      const status = await this.sound.getStatusAsync();
      if (status.isLoaded) {
        const newPos = Math.max(status.positionMillis - seconds * 1000, 0);
        await this.sound.setPositionAsync(newPos);
        this.notifyStatus(newPos / 1000, (status.durationMillis || 0) / 1000);
        return true;
      }
      return false;
    } catch (e) {
      console.warn('Failed to seek backward:', e);
      return false;
    }
  }

  private static onPlaybackStatusUpdate = (status: AVPlaybackStatus) => {
    if (status.isLoaded) {
      this.isPlaying = status.isPlaying;
      if (status.didJustFinish) {
        // Auto play next song
        AudioService.next();
      } else {
        AudioService.notifyStatus(status.positionMillis / 1000, (status.durationMillis || 0) / 1000);
      }
    } else {
      if (status.error) {
        console.warn(`Playback error: ${status.error}`);
      }
    }
  };
}
