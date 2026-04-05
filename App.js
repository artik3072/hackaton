import { StatusBar } from 'expo-status-bar';
import { StyleSheet, Text, View, TextInput, ScrollView, Image, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useState } from 'react';

// ⚙️ НАСТРОЙКА ПОДКЛЮЧЕНИЯ К БЭКЕНДУ
// ВАЖНО: НИКОГДА не используйте 0.0.0.0 в мобильном приложении!

// ДЛЯ ANDROID ЭМУЛЯТОРА (используйте 10.0.2.2)
// const API_BASE_URL = 'http://10.0.2.2:8000';

// ДЛЯ ФИЗИЧЕСКОГО УСТРОЙСТВА (раскомментируйте и укажите IP вашего компьютера)
const API_BASE_URL = 'http://192.168.0.10:8000';  // Замените на ваш реальный IP

// ДЛЯ iOS СИМУЛЯТОРА (раскомментируйте)
// const API_BASE_URL = 'http://localhost:8000';

export default function App() {
  const [inputText, setInputText] = useState('');
  const [output, setOutput] = useState('');
  const [loading, setLoading] = useState(false);

  // Отправка запроса к AI агенту
  const sendRequest = async () => {
    if (!inputText.trim()) {
      Alert.alert('Ошибка', 'Пожалуйста, введите ваш запрос');
      return;
    }

    setLoading(true);
    setOutput('⏳ Агент думает...');

    try {
      console.log(`Отправка запроса на: ${API_BASE_URL}/chat`);
      
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [
            {
              role: 'user',
              content: inputText
            }
          ],
          model: 'GigaChat:latest',
          temperature: 0.7,
          max_tokens: 3000,
          stream: false
        }),
      });

      const data = await response.json();

      if (data.success) {
        setOutput(data.answer);
      } else {
        setOutput(`❌ Ошибка: ${data.error || 'Не удалось получить ответ'}`);
      }
    } catch (error) {
      console.error('API Error:', error);
      setOutput(
        `❌ Не удалось подключиться к серверу\n\n` +
        `Проверьте:\n` +
        `1. Запущен ли бэкенд (python main.py)\n` +
        `2. Доступен ли адрес: ${API_BASE_URL}\n` +
        `3. Ошибка: ${error.message}\n\n` +
        `💡 Совет: Для Android эмулятора используйте 10.0.2.2\n` +
        `💡 Для физического устройства используйте IP вашего компьютера`
      );
    } finally {
      setLoading(false);
    }
  };

  // Очистка памяти агента
  const clearMemory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/memory`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        Alert.alert('✅ Успех', 'Память агента очищена');
        setOutput('🧠 Память агента очищена');
      } else {
        Alert.alert('Ошибка', 'Не удалось очистить память');
      }
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось соединиться с сервером');
    }
  };

  // Проверка статуса сервера
  const checkServer = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/`);
      const data = await response.json();
      Alert.alert(
        '✅ Сервер работает',
        `🤖 ${data["🤖"]}\n📊 Память: ${data["📊"].memory} сообщений`
      );
      setOutput(`✅ Сервер подключен!\n\n🤖 ${data["🤖"]}\n📊 В памяти ${data["📊"].memory} сообщений`);
    } catch (error) {
      Alert.alert('❌ Сервер недоступен', `Не удается подключиться к ${API_BASE_URL}`);
      setOutput(`❌ Сервер недоступен\n\nПроверьте подключение к ${API_BASE_URL}`);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Image source={require('./assets/logo.png')} style={styles.logo} />
        <Text style={styles.title}>Твой агент для всего!</Text>
      </View>

      {/* Input */}
      <View style={styles.inputWrapper}>
        <TextInput
          style={styles.input}
          placeholder="Введите запрос..."
          placeholderTextColor="#aaa"
          value={inputText}
          onChangeText={setInputText}
          multiline
        />

        {/* Send Button */}
        <TouchableOpacity style={styles.iconBox} onPress={sendRequest} disabled={loading}>
          <Text style={styles.buttonText}>{loading ? '⏳' : '✉️'}</Text>
        </TouchableOpacity>
      </View>

      {/* Кнопки управления */}
      <View style={styles.buttonRow}>
        <TouchableOpacity style={styles.button} onPress={checkServer}>
          <Text style={styles.buttonText}>🔌 Проверить</Text>
        </TouchableOpacity>
      </View>

      {/* Output */}
      <View style={styles.outputWrapper}>
        <ScrollView style={styles.outputScroll}>
          {loading && <ActivityIndicator size="large" color="#7c5cff" style={{ margin: 20 }} />}
          <Text style={styles.outputText}>{output || 'Ответ на ваш запрос появится здесь...'}</Text>
        </ScrollView>
      </View>

      <StatusBar style="light" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111111',
    padding: 20,
    paddingTop: 60,
  },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 25,
  },

  logo: {
    width: 50,
    height: 50,
    borderRadius: 25,
    marginRight: 10,
  },

  title: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '500',
  },

  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#3a3a3a',
    borderRadius: 12,
    paddingHorizontal: 10,
    marginBottom: 15,
  },

  input: {
    flex: 1,
    color: '#fff',
    paddingVertical: 12,
    maxHeight: 100,
  },

  iconBox: {
    backgroundColor: '#7c5cff',
    padding: 10,
    borderRadius: 8,
  },

  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
    marginBottom: 20,
  },

  button: {
    flex: 1,
    backgroundColor: '#3a3a3a',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 10,
    alignItems: 'center',
  },

  clearButton: {
    backgroundColor: '#dc2626',
  },

  buttonText: {
    color: '#ddd',
    fontSize: 14,
  },

  outputWrapper: {
    flex: 1,
    backgroundColor: '#a56ff5a1',
    borderRadius: 15,
    padding: 15,
  },

  outputScroll: {
    flex: 1,
  },

  outputText: {
    color: '#e0e0e0',
    fontSize: 14,
    lineHeight: 20,
  },
});