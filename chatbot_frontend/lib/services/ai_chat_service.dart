// lib/services/ai_chat_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class AiChatService {
  final String _backendBaseUrl = 'https://ai-agent-service-twzrbfjcqq-uc.a.run.app';

  AiChatService();

  Future<Map<String, dynamic>> sendMessage(String message) async {
    try {
      print('🔄 Sending message to backend: $message');
      
      final response = await http.post(
        Uri.parse('$_backendBaseUrl/chat/send'),
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
          'Accept': 'application/json',
          'X-API-Key': '9eZmwfCYkxK7RE074GSuDyl_HwZzhJcsRHYAJUqbzCU',
        },
        body: jsonEncode({'message': message}),
      ).timeout(const Duration(seconds: 45));

      print('📡 Response status: ${response.statusCode}');
      
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        
        // Enhanced logging for image debugging
        final responseParts = data['response']['parts'] as List<dynamic>? ?? [];
        for (var part in responseParts) {
          if (part['type'] == 'image') {
            print('🖼️ Image in response: ${part['uri']}');
            print('📝 Alt text: ${part['alt']}');
          }
        }
        
        return data['response'];
      } else {
        print('❌ Failed to send message: ${response.statusCode} - ${response.body}');
        throw Exception('Failed to get response from AI: Status ${response.statusCode}');
      }
    } catch (e) {
      print('💥 Error sending message to AI: $e');
      rethrow;
    }
  }

  Future<Map<String, dynamic>> sendMessageWithTTS({
    required String message,
    bool includeAudio = true,
    String voiceName = 'en-US-Chirp3-HD-Leda',
    String languageCode = 'en-US',
    String? customTTSMessage,
  }) async {
    try {
      print('🔄 Sending message with TTS: $message');
      
      final requestBody = {
        'message': message,
        'include_audio': includeAudio,
        'voice_name': voiceName,
        'language_code': languageCode,
      };

      if (customTTSMessage != null) {
        requestBody['tts_message'] = customTTSMessage;
      }

      final response = await http.post(
        Uri.parse('$_backendBaseUrl/chat/send-with-tts'),
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
          'Accept': 'application/json',
          'X-API-Key': '9eZmwfCYkxK7RE074GSuDyl_HwZzhJcsRHYAJUqbzCU',
        },
        body: jsonEncode(requestBody),
      ).timeout(const Duration(seconds: 60));

      print('📡 TTS Response status: ${response.statusCode}');
      
      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        
        // Enhanced logging for TTS and image debugging
        print('🔊 Audio generated: ${data['audio_generated']}');
        if (data['audio_data'] != null) {
          print('🔊 Audio data length: ${data['audio_data'].toString().length}');
        }
        
        // Log image information
        final responseParts = data['response']?['parts'] as List<dynamic>? ?? [];
        for (var part in responseParts) {
          if (part['type'] == 'image') {
            print('🖼️ Image in TTS response: ${part['uri']}');
            print('📝 Alt text: ${part['alt']}');
          }
        }
        
        return data;
      } else {
        print('❌ Failed to send message with TTS: ${response.statusCode} - ${response.body}');
        throw Exception('Failed to get TTS response: Status ${response.statusCode}');
      }
    } catch (e) {
      print('💥 Error sending message with TTS: $e');
      rethrow;
    }
  }

  Future<String> resetChatSession() async {
    try {
      print('🔄 Resetting chat session...');
      
      final response = await http.post(
        Uri.parse('$_backendBaseUrl/chat/reset'),
        headers: {
          'Accept': 'application/json',
          'X-API-Key': '9eZmwfCYkxK7RE074GSuDyl_HwZzhJcsRHYAJUqbzCU',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final message = data['message'] ?? 'Chat session reset';
        print('✅ Chat reset: $message');
        return message;
      } else {
        print('❌ Failed to reset chat: ${response.statusCode} - ${response.body}');
        throw Exception('Failed to reset chat session: ${response.body}');
      }
    } catch (e) {
      print('💥 Error resetting chat: $e');
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getHealthStatus() async {
    try {
      print('🔄 Checking service health...');
      
      final response = await http.get(
        Uri.parse('$_backendBaseUrl/health'),
        headers: {
          'Accept': 'application/json',
          'X-API-Key': '9eZmwfCYkxK7RE074GSuDyl_HwZzhJcsRHYAJUqbzCU',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        print('✅ Service health: ${data['status']}');
        return data;
      } else {
        throw Exception('Health check failed: ${response.statusCode}');
      }
    } catch (e) {
      print('💥 Error checking health: $e');
      rethrow;
    }
  }

  Future<bool> testConnection() async {
    try {
      print('🔄 Testing backend connection...');
      
      final response = await http.get(
        Uri.parse('$_backendBaseUrl/debug/startup-check'),
        headers: {
          'Accept': 'application/json',
          'X-API-Key': '9eZmwfCYkxK7RE074GSuDyl_HwZzhJcsRHYAJUqbzCU',
        },
      ).timeout(const Duration(seconds: 5));

      final isConnected = response.statusCode == 200;
      print('🌐 Backend connection: ${isConnected ? 'OK' : 'FAILED'}');
      return isConnected;
    } catch (e) {
      print('💥 Connection test failed: $e');
      return false;
    }
  }
}