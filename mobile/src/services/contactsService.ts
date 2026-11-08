import * as Contacts from 'expo-contacts';
import { ContactItem } from '../types';

export class ContactsService {
  private static cachedContacts: ContactItem[] = [];

  /**
   * Request contacts permission and fetch phone contacts
   */
  public static async loadContacts(): Promise<ContactItem[]> {
    try {
      const { status } = await Contacts.requestPermissionsAsync();
      if (status !== 'granted') {
        console.warn('Contacts permission not granted');
        return this.getDefaultContacts();
      }

      const { data } = await Contacts.getContactsAsync({
        fields: [Contacts.Fields.Name, Contacts.Fields.PhoneNumbers],
      });

      if (!data || data.length === 0) {
        return this.getDefaultContacts();
      }

      const list: ContactItem[] = [];
      for (const c of data) {
        if (c.name && c.phoneNumbers && c.phoneNumbers.length > 0) {
          const numbers = c.phoneNumbers
            .filter(p => !!p.number)
            .map(p => ({
              number: (p.number || '').replace(/\s+/g, ''),
              label: p.label || 'Mobile',
            }));

          if (numbers.length > 0) {
            list.push({
              id: c.id,
              name: c.name,
              phoneNumbers: numbers,
              primaryNumber: numbers[0].number,
            });
          }
        }
      }

      this.cachedContacts = list;
      return list;
    } catch (e) {
      console.warn('Error loading contacts:', e);
      return this.getDefaultContacts();
    }
  }

  /**
   * Default sample contacts for testing or instant fallback
   */
  public static getDefaultContacts(): ContactItem[] {
    const list: ContactItem[] = [
      {
        id: 'sample_c1',
        name: 'Ali Raza',
        phoneNumbers: [{ number: '+923001234567', label: 'Mobile' }],
        primaryNumber: '+923001234567',
      },
      {
        id: 'sample_c2',
        name: 'Bhai Jaan',
        phoneNumbers: [{ number: '+923017654321', label: 'Mobile' }],
        primaryNumber: '+923017654321',
      },
      {
        id: 'sample_c3',
        name: 'Sadaqat Ali',
        phoneNumbers: [{ number: '+923021122334', label: 'Mobile' }],
        primaryNumber: '+923021122334',
      },
      {
        id: 'sample_c4',
        name: 'Hamza Developer',
        phoneNumbers: [{ number: '+923039988776', label: 'Mobile' }],
        primaryNumber: '+923039988776',
      },
      {
        id: 'sample_c5',
        name: 'Papa',
        phoneNumbers: [{ number: '+923005544332', label: 'Mobile' }],
        primaryNumber: '+923005544332',
      },
    ];
    this.cachedContacts = list;
    return list;
  }

  /**
   * Search contact by spoken voice query (e.g. "ali", "bhai", "sadaqat")
   */
  public static findContact(query: string): ContactItem | null {
    if (!query || !query.trim()) return null;
    const q = query.trim().toLowerCase();

    if (this.cachedContacts.length === 0) {
      this.cachedContacts = this.getDefaultContacts();
    }

    // 1. Exact or starts-with match
    const exact = this.cachedContacts.find(c => c.name.toLowerCase() === q);
    if (exact) return exact;

    const startsWith = this.cachedContacts.find(c => c.name.toLowerCase().startsWith(q));
    if (startsWith) return startsWith;

    // 2. Partial substring match
    const contains = this.cachedContacts.find(c => c.name.toLowerCase().includes(q));
    if (contains) return contains;

    // 3. Multi-word match (e.g. query "ali" matches "Ali Raza")
    const wordMatch = this.cachedContacts.find(c => {
      const parts = c.name.toLowerCase().split(/\s+/);
      return parts.some(p => p.includes(q) || q.includes(p));
    });
    if (wordMatch) return wordMatch;

    return null;
  }
}
