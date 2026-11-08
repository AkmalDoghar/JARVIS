import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { LogEntry } from '../types';

interface Props {
  logs: LogEntry[];
}

export const TerminalLog: React.FC<Props> = ({ logs }) => {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>HUD TELEMETRY LOG</Text>
        <Text style={styles.state}>ACTIVE</Text>
      </View>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {logs.length === 0 ? (
          <Text style={styles.emptyText}>Standing by for voice commands, Akmal Sir...</Text>
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
    flex: 1,
    minHeight: 110,
    maxHeight: 140,
    backgroundColor: 'rgba(5, 10, 20, 0.95)',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(0, 240, 255, 0.2)',
    padding: 10,
    marginHorizontal: 16,
    marginVertical: 6,
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
  title: {
    color: '#64748b',
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.5,
  },
  state: {
    color: '#00f0ff',
    fontSize: 9,
    fontFamily: 'monospace',
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    gap: 4,
  },
  emptyText: {
    color: '#475569',
    fontSize: 11,
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
    fontSize: 10,
    fontFamily: 'monospace',
  },
  sender: {
    fontSize: 10,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  senderJarvis: {
    color: '#00f0ff',
  },
  senderUser: {
    color: '#ffb703',
  },
  logText: {
    color: '#e2e8f0',
    fontSize: 11,
    flex: 1,
  },
});

