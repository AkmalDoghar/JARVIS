import { Track } from '../types';
import { SafeNative } from './safeNativeModules';

export class AudioService {
  private static sound: any = null;
  private static playlist: Track[] = [];
  private static currentIndex: number = -1;
  private static isPlaying: boolean = false;
  private static currentPosition: number = 0;
  private static virtualTimer: any = null;
  private static onStatusChangeListeners: Array<
    (status: { isPlaying: boolean; track: Track | null; position: number; duration: number }) => void
  > = [];

  /**
   * Request media permissions and scan device for audio files
   */
  public static async scanDeviceSongs(): Promise<Track[]> {
    try {
      const MediaLibrary = SafeNative.MediaLibrary;
      if (MediaLibrary && typeof MediaLibrary.requestPermissionsAsync === 'function') {
        const { status } = await MediaLibrary.requestPermissionsAsync();
        if (status === 'granted') {
          const media = await MediaLibrary.getAssetsAsync({
            mediaType: 'audio',
            first: 100,
            sortBy: 'modificationTime',
          });

          if (media && media.assets && media.assets.length > 0) {
            const tracks: Track[] = media.assets.map((asset: any, index: number) => {
              const cleanName = (asset.filename || `Track_${index}`).replace(/\.[^/.]+$/, '');
              return {
                id: asset.id || `track_${index}`,
                title: cleanName,
                artist: 'Local Phone Audio',
                uri: asset.uri,
                duration: asset.duration || 180,
                filename: asset.filename || `${cleanName}.mp3`,
                isFavorite: index < 5,
              };
            });

            this.playlist = tracks;
            if (this.currentIndex === -1 && tracks.length > 0) {
              this.currentIndex = 0;
            }
            return tracks;
          }
        }
      }
      return this.getDefaultSamplePlaylist();
    } catch (e) {
      console.warn('[AudioService] Failed to scan device audio:', e);
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

  public static subscribeStatus(
    cb: (status: { isPlaying: boolean; track: Track | null; position: number; duration: number }) => void
  ): () => void {
    this.onStatusChangeListeners.push(cb);
    return () => {
      this.onStatusChangeListeners = this.onStatusChangeListeners.filter((l) => l !== cb);
    };
  }

  private static notifyStatus(pos?: number, dur?: number) {
    const cur = this.getCurrentTrack();
    const curPos = typeof pos === 'number' ? pos : this.currentPosition;
    const curDur = typeof dur === 'number' ? dur : cur ? cur.duration : 180;
    this.onStatusChangeListeners.forEach((cb) => {
      cb({
        isPlaying: this.isPlaying,
        track: cur,
        position: curPos,
        duration: curDur,
      });
    });
  }

  private static startVirtualTimer() {
    this.stopVirtualTimer();
    this.virtualTimer = setInterval(() => {
      if (this.isPlaying) {
        const cur = this.getCurrentTrack();
        const max = cur ? cur.duration : 180;
        this.currentPosition += 1;
        if (this.currentPosition >= max) {
          this.next();
        } else {
          this.notifyStatus();
        }
      }
    }, 1000);
  }

  private static stopVirtualTimer() {
    if (this.virtualTimer) {
      clearInterval(this.virtualTimer);
      this.virtualTimer = null;
    }
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

      this.currentPosition = 0;
      this.isPlaying = true;

      const Audio = SafeNative.Audio;
      if (Audio) {
        try {
          await Audio.setAudioModeAsync({
            allowsRecordingIOS: false,
            staysActiveInBackground: true,
            playsInSilentModeIOS: true,
            shouldDuckAndroid: true,
            playThroughEarpieceAndroid: false,
          });

          if (this.sound) {
            await this.sound.unloadAsync().catch(() => {});
            this.sound = null;
          }

          const { sound } = await Audio.Sound.createAsync(
            { uri: track.uri },
            { shouldPlay: true },
            (status: any) => {
              if (status.isLoaded) {
                this.isPlaying = status.isPlaying;
                this.currentPosition = status.positionMillis / 1000;
                if (status.didJustFinish) {
                  AudioService.next();
                } else {
                  this.notifyStatus(this.currentPosition, (status.durationMillis || 0) / 1000);
                }
              }
            }
          );
          this.sound = sound;
        } catch (audioErr) {
          console.warn('[AudioService] Native Audio error, falling back to simulated playback:', audioErr);
          this.startVirtualTimer();
        }
      } else {
        this.startVirtualTimer();
      }

      this.notifyStatus(0, track.duration);
      return true;
    } catch (e) {
      console.warn('[AudioService] Failed to play track:', e);
      this.isPlaying = true;
      this.startVirtualTimer();
      this.notifyStatus(0, 180);
      return true;
    }
  }

  /**
   * Play favorite songs specifically
   */
  public static async playFavorites(): Promise<boolean> {
    if (this.playlist.length === 0) {
      await this.scanDeviceSongs();
    }
    const favIdx = this.playlist.findIndex((t) => t.isFavorite);
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
      this.isPlaying = false;
      this.stopVirtualTimer();
      if (this.sound) {
        await this.sound.pauseAsync().catch(() => {});
      }
      this.notifyStatus();
      return true;
    } catch (e) {
      return false;
    }
  }

  /**
   * Resume playback
   */
  public static async resume(): Promise<boolean> {
    try {
      this.isPlaying = true;
      if (this.sound) {
        await this.sound.playAsync().catch(() => {});
      } else {
        this.startVirtualTimer();
      }
      this.notifyStatus();
      return true;
    } catch (e) {
      return await this.playTrack();
    }
  }

  /**
   * Stop playback completely
   */
  public static async stop(): Promise<boolean> {
    try {
      this.isPlaying = false;
      this.currentPosition = 0;
      this.stopVirtualTimer();
      if (this.sound) {
        await this.sound.stopAsync().catch(() => {});
      }
      this.notifyStatus(0);
      return true;
    } catch (e) {
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
      nextIdx = 0;
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
      this.currentPosition += seconds;
      if (this.sound) {
        const status = await this.sound.getStatusAsync();
        if (status.isLoaded) {
          const newPos = Math.min(status.positionMillis + seconds * 1000, status.durationMillis || 0);
          await this.sound.setPositionAsync(newPos);
          this.currentPosition = newPos / 1000;
        }
      }
      this.notifyStatus();
      return true;
    } catch (e) {
      this.notifyStatus();
      return true;
    }
  }

  /**
   * Seek backward by seconds (default -15 seconds)
   */
  public static async seekBackward(seconds: number = 15): Promise<boolean> {
    try {
      this.currentPosition = Math.max(0, this.currentPosition - seconds);
      if (this.sound) {
        const status = await this.sound.getStatusAsync();
        if (status.isLoaded) {
          const newPos = Math.max(status.positionMillis - seconds * 1000, 0);
          await this.sound.setPositionAsync(newPos);
          this.currentPosition = newPos / 1000;
        }
      }
      this.notifyStatus();
      return true;
    } catch (e) {
      this.notifyStatus();
      return true;
    }
  }
}
