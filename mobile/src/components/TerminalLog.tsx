import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { LogEntry } from '../types';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface Props {
  logs: LogEntry[];
}

export const TerminalLog: React.FC<Props> = ({ logs }) => {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View style={styles.headerTitleGroup}>
          <MaterialCommunityIcons name="console-line" size={14} color="#00f0ff" />
          <Text style={styles.title}>HUD TELEMETRY FEED</Text>
        </View>
        <View style={styles.liveIndicator}>
          <View style={styles.liveDot} />
          <Text style={styles.liveText}>LIVE</Text>
        </View>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {logs.length === 0 ? (
          <Text style={styles.emptyText}>[SYS]: Standing by for voice commands, Akmal Sir...</Text>
        ) : (
          logs.map((log) => {
            const isJarvis = log.sender === 'JARVIS';
            const isUser = log.sender === 'AKMAL_SIR';
            return (
              <View key={log.id} style={styles.logRow}>
                <Text style={styles.timestamp}>[{log.timestamp}]</Text>
                <Text
                  style={[
                    styles.sender,
                    isJarvis && styles.senderJarvis,
                    isUser && styles.senderUser,
                  ]}
                >
                  {isJarvis ? 'JARVIS:' : isUser ? 'AKMAL SIR:' : 'SYS:'}
                </Text>
                <Text style={styles.logText}>{log.text}</Text>
              </View>
            );
          })
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'rgba(2, 6, 23, 0.95)',
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: 'rgba(0, 240, 255, 0.22)',
    padding: 12,
    marginHorizontal: 16,
    marginVertical: 6,
    minHeight: 110,
    maxHeight: 130,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.08)',
    paddingBottom: 4,
  },
  headerTitleGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  title: {
    color: '#00f0ff',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.5,
    fontFamily: 'monospace',
  },
  liveIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#00ffaa',
  },
  liveText: {
    color: '#00ffaa',
    fontSize: 8,
    fontFamily: 'monospace',
    fontWeight: '800',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    gap: 4,
  },
  emptyText: {
    color: '#475569',
    fontSize: 10,
    fontFamily: 'monospace',
    fontStyle: 'italic',
  },
  logRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 4,
    flexWrap: 'wrap',
  },
  timestamp: {
    color: '#475569',
    fontSize: 9,
    fontFamily: 'monospace',
  },
  sender: {
    fontSize: 9,
    fontWeight: '800',
    fontFamily: 'monospace',
  },
  senderJarvis: {
    color: '#00f0ff',
  },
  senderUser: {
    color: '#f59e0b',
  },
  logText: {
    color: '#cbd5e1',
    fontSize: 10,
    flex: 1,
    fontFamily: 'monospace',
  },
});
