// lib/screens/ai_chat_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:audioplayers/audioplayers.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/ai_chat_service.dart';

class AiChatScreen extends StatefulWidget {
  @override
  AiChatScreenState createState() => AiChatScreenState();
}

class AiChatScreenState extends State<AiChatScreen>
    with TickerProviderStateMixin {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final AiChatService _aiChatService = AiChatService();
  
  // Audio components
  late stt.SpeechToText _speech;
  late AudioPlayer _audioPlayer;
  
  // State variables
  List<ChatMessage> _messages = [];
  bool _isLoading = false;
  bool _isListening = false;
  bool _speechToTextEnabled = false;
  bool _textToSpeechEnabled = true;
  bool _isPlayingAudio = false;
  String _lastWords = '';
  double _confidence = 1.0;
  
  // Animation controllers
  late AnimationController _typingAnimationController;
  late AnimationController _pulseAnimationController;

  @override
  void initState() {
    super.initState();
    _initializeServices();
    _loadSettings();
    _setupAnimations();
  }

  void _setupAnimations() {
    _typingAnimationController = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 1500),
    )..repeat();
    
    _pulseAnimationController = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 1000),
    )..repeat(reverse: true);
  }

  void _initializeServices() async {
    _speech = stt.SpeechToText();
    _audioPlayer = AudioPlayer();
    
    // Initialize speech recognition
    bool available = await _speech.initialize(
      onStatus: (val) => _onSpeechStatus(val),
      onError: (val) => _onSpeechError(val),
    );
    
    if (available) {
      setState(() => _speechToTextEnabled = true);
      print('✅ Speech-to-Text initialized successfully');
    } else {
      print('❌ Speech-to-Text initialization failed');
    }
    
    // Set up audio player listeners
    _audioPlayer.onPlayerComplete.listen((event) {
      setState(() => _isPlayingAudio = false);
    });
  }

  void _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _textToSpeechEnabled = prefs.getBool('tts_enabled') ?? true;
    });
  }

  void _saveSettings() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('tts_enabled', _textToSpeechEnabled);
  }

  @override
  void dispose() {
    _typingAnimationController.dispose();
    _pulseAnimationController.dispose();
    _audioPlayer.dispose();
    _speech.cancel();
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onSpeechStatus(String status) {
    setState(() {
      _isListening = status == 'listening';
    });
  }

  void _onSpeechError(dynamic error) {
    print('❌ Speech error: $error');
    setState(() {
      _isListening = false;
    });
    _showSnackBar('Speech recognition error: ${error.toString()}');
  }

  void _toggleMicrophone() async {
    if (_isListening) {
      // Cancel recording
      await _cancelListening();
    } else {
      // Start recording
      await _startListening();
    }
  }

  Future<void> _startListening() async {
    if (!_speechToTextEnabled && !kIsWeb) {
      _showSnackBar('Speech-to-Text not available');
      return;
    }
    
    // Stop any playing audio first
    if (_isPlayingAudio) {
      _audioPlayer.stop();
      setState(() => _isPlayingAudio = false);
    }
    
    // Request microphone permission on mobile
    if (!kIsWeb) {
      var status = await Permission.microphone.request();
      if (!status.isGranted) {
        _showSnackBar('Microphone permission denied');
        return;
      }
    }

  try {
    await _speech.listen(
      onResult: (val) => setState(() {
        _lastWords = val.recognizedWords;
        _confidence = val.confidence;
        _textController.text = _lastWords;
      }),
      listenOptions: stt.SpeechListenOptions(
        partialResults: true,
        cancelOnError: true,
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 3),
        localeId: 'en_US',
        // You can also set listenMode / onDevice if you use them:
        // listenMode: stt.ListenMode.dictation,
        // onDevice: false,
      ),
    );
      
    } catch (e) {
      print('❌ Error starting speech recognition: $e');
      _showSnackBar('Failed to start voice recording');
      setState(() => _isListening = false);
    }
  }

  Future<void> _cancelListening() async {
    _speech.stop();
    setState(() {
      _isListening = false;
      _lastWords = '';
      _textController.text = ''; // Clear the text field when canceling
    });
    _showSnackBar('Recording cancelled');
  }

  Future<void> _finishListening() async {
    if (_isListening) {
      _speech.stop();
      setState(() => _isListening = false);
    }
  }

  void _sendMessage([String? overrideText]) async {
    // Finish listening if we're currently recording and send STT result
    if (_isListening) {
      await _finishListening();
      // Give a moment for the speech recognition to finalize
      await Future.delayed(Duration(milliseconds: 100));
    }
    
    final text = overrideText ?? _textController.text.trim();
    
    if (text.isEmpty || _isLoading) return;

    final userMessage = ChatMessage(
      text: text,
      isUser: true,
      timestamp: DateTime.now(),
    );

    setState(() {
      _messages.add(userMessage);
      _isLoading = true;
    });

    _textController.clear();
    _lastWords = '';
    _scrollToBottom();

    try {
      Map<String, dynamic> response;
      
      // Use TTS endpoint if TTS is enabled, otherwise use regular endpoint
      if (_textToSpeechEnabled) {
        response = await _aiChatService.sendMessageWithTTS(
          message: text,
          includeAudio: true,
        );
        
        // Handle the TTS response structure
        await _handleTTSResponse(response);
      } else {
        final regularResponse = await _aiChatService.sendMessage(text);
        response = {'response': regularResponse};
        await _handleRegularResponse(response);
      }
      
    } catch (e) {
      print('❌ Error sending message: $e');
      _addErrorMessage('Sorry, I encountered an error. Please try again.');
    } finally {
      setState(() => _isLoading = false);
      _scrollToBottom();
    }
  }

  Future<void> _handleTTSResponse(Map<String, dynamic> response) async {
    final aiResponse = response['response'];
    if (aiResponse != null) {
      final aiMessage = await _createMessageFromResponse(aiResponse, false);
      setState(() => _messages.add(aiMessage));
      
      // Auto-play audio if TTS is enabled and audio was generated
      if (_textToSpeechEnabled && response['audio_generated'] == true) {
        final audioData = response['audio_data'];
        if (audioData != null && audioData.isNotEmpty) {
          await _playTTSAudio(audioData);
        }
      }
    }
  }

  Future<void> _handleRegularResponse(Map<String, dynamic> response) async {
    final aiResponse = response['response'];
    if (aiResponse != null) {
      final aiMessage = await _createMessageFromResponse(aiResponse, false);
      setState(() => _messages.add(aiMessage));
    }
  }

  String _buildImageUrl(String imageFileName) {
    // If it's already a complete URL, return as-is
    if (imageFileName.startsWith('http')) {
      return imageFileName;
    }
    
    // Handle base64 images
    if (imageFileName.startsWith('data:image/')) {
      return imageFileName;
    }
    
    // Build Firebase Storage URL from filename
    String cleanFileName = imageFileName;
    
    // Remove leading slash if present
    if (cleanFileName.startsWith('/')) {
      cleanFileName = cleanFileName.substring(1);
    }
    
    // Build the correct Firebase Storage URL structure
    String encodedPath;
    
    // Check if it already has the correct path structure
    if (cleanFileName.startsWith('ai_images/manual001/')) {
      encodedPath = Uri.encodeComponent(cleanFileName);
    } else {
      // Add the correct path prefix
      String fullPath = 'ai_images/manual001/$cleanFileName';
      encodedPath = Uri.encodeComponent(fullPath);
    }
    
    // Use the correct Firebase Storage URL format
    return 'https://firebasestorage.googleapis.com/v0/b/ai-chatbot.firebasestorage.app/o/$encodedPath?alt=media';
  }

  Future<ChatMessage> _createMessageFromResponse(Map<String, dynamic> response, bool isUser) async {
    final parts = response['parts'] as List<dynamic>? ?? [];
    
    List<MessagePart> messageParts = [];
    String combinedText = '';
    
    for (var part in parts) {
      final partType = part['type'] as String?;
      
      if (partType == 'text') {
        final content = part['content'] as String? ?? '';
        combinedText += '$content ';
        messageParts.add(TextPart(content: content));
        
      } else if (partType == 'image') {
        final imageUri = part['uri'] as String?;
        final altText = part['alt'] as String? ?? 'Image';
        
        if (imageUri != null && imageUri.isNotEmpty) {
          print('🖼️ Processing image URI: $imageUri');

          // Use the URI directly if it's already a complete URL (signed URL from backend)
          String completeUrl;
          if (imageUri.startsWith('http')) {
            completeUrl = imageUri; // Use signed URL directly
            print('✅ Using signed URL from backend: ${completeUrl.length > 100 ? "${completeUrl.substring(0, 100)}..." : completeUrl}');
          } else {
            // Build proper image URL from filename (fallback)
            completeUrl = _buildImageUrl(imageUri);
            print('🔗 Built image URL from filename: $completeUrl');
          }
          
          messageParts.add(ImagePart(
            uri: completeUrl,
            altText: altText,
          ));
        }
      }
    }
    
    return ChatMessage(
      text: combinedText.trim(),
      isUser: isUser,
      timestamp: DateTime.now(),
      parts: messageParts,
    );
  }

  Future<void> _playTTSAudio(String audioData) async {
    if (!_textToSpeechEnabled) return;
    
    try {
      setState(() => _isPlayingAudio = true);
      
      // Handle base64 audio data
      if (audioData.startsWith('data:audio/')) {
        final base64Data = audioData.split(',').last;
        final bytes = base64Decode(base64Data);
        await _audioPlayer.play(BytesSource(bytes));
      } else {
        final bytes = base64Decode(audioData);
        await _audioPlayer.play(BytesSource(bytes));
      }
      
      print('🔊 Playing TTS audio (${audioData.length} characters)');
      
    } catch (e) {
      print('❌ Error playing TTS audio: $e');
      setState(() => _isPlayingAudio = false);
      _showSnackBar('Audio playback failed');
    }
  }

  void _addErrorMessage(String error) {
    final errorMessage = ChatMessage(
      text: error,
      isUser: false,
      timestamp: DateTime.now(),
      isError: true,
    );
    setState(() => _messages.add(errorMessage));
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _clearChat() {
    setState(() {
      _messages.clear();
    });
    _aiChatService.resetChatSession().catchError((e) {
      print('⚠️ Error resetting chat session: $e');
      return '';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('AskTheManual'),
        backgroundColor: Colors.grey[800],
        foregroundColor: Colors.white,
        elevation: 2,
        actions: [
          // Text-to-Speech Toggle (Auto-play)
          IconButton(
            icon: Icon(_textToSpeechEnabled ? Icons.volume_up : Icons.volume_off),
            onPressed: () {
              setState(() {
                _textToSpeechEnabled = !_textToSpeechEnabled;
              });
              _saveSettings();
              _showSnackBar(_textToSpeechEnabled 
                ? 'Auto-play audio enabled' 
                : 'Auto-play audio disabled');
            },
            tooltip: 'Toggle Auto-play Audio',
          ),
          // Clear Chat
          IconButton(
            icon: Icon(Icons.clear_all),
            onPressed: _clearChat,
            tooltip: 'Clear Chat',
          ),
        ],
      ),
      body: Column(
        children: [
          // Audio playing indicator
          if (_isPlayingAudio)
            Container(
              width: double.infinity,
              padding: EdgeInsets.symmetric(vertical: 8, horizontal: 16),
              color: Colors.blue[50],
              child: Row(
                children: [
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
                    ),
                  ),
                  SizedBox(width: 12),
                  Text(
                    'Playing audio response...',
                    style: TextStyle(
                      color: Colors.blue[700],
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  Spacer(),
                  TextButton(
                    onPressed: () {
                      _audioPlayer.stop();
                      setState(() => _isPlayingAudio = false);
                    },
                    child: Text('Stop', style: TextStyle(color: Colors.blue[700])),
                  ),
                ],
              ),
            ),
          
          // Voice recording indicator
          if (_isListening)
            Container(
              width: double.infinity,
              padding: EdgeInsets.symmetric(vertical: 12, horizontal: 16),
              color: Colors.red[50],
              child: Row(
                children: [
                  AnimatedBuilder(
                    animation: _pulseAnimationController,
                    builder: (context, child) {
                      return Container(
                        width: 16,
                        height: 16,
                        decoration: BoxDecoration(
                          color: Colors.red.withValues(alpha: 0.5 + 0.5 * _pulseAnimationController.value),
                          shape: BoxShape.circle,
                        ),
                      );
                    },
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Listening... (tap mic to cancel)',
                          style: TextStyle(
                            color: Colors.red[700],
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        if (_lastWords.isNotEmpty) ...[
                          SizedBox(height: 4),
                          Text(
                            _lastWords,
                            style: TextStyle(
                              color: Colors.red[600],
                              fontSize: 14,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  Text(
                    '${(_confidence * 100).toInt()}%',
                    style: TextStyle(
                      color: Colors.red[600],
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          
          // Chat messages
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: EdgeInsets.all(16),
              itemCount: _messages.length + (_isLoading ? 1 : 0),
              itemBuilder: (context, index) {
                if (index == _messages.length && _isLoading) {
                  return _buildTypingIndicator();
                }
                return _buildMessageBubble(_messages[index]);
              },
            ),
          ),
          
          // Input area
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey[50],
              border: Border(
                top: BorderSide(color: Colors.grey[300]!),
              ),
            ),
            child: _buildInputArea(),
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    return Row(
      children: [
        // Text input field with microphone button
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(25),
              border: Border.all(color: Colors.grey[300]!),
            ),
            child: Row(
              children: [
                // Microphone button (left side of text field)
                if (_speechToTextEnabled) ...[
                  SizedBox(width: 8),
                  Material(
                    color: Colors.transparent,
                    borderRadius: BorderRadius.circular(20),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(20),
                      onTap: _isLoading ? null : _toggleMicrophone,
                      child: SizedBox(
                        width: 36,
                        height: 36,
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            Icon(
                              Icons.mic,
                              color: _isListening ? Colors.red[600] : Colors.grey[600],
                              size: 20,
                            ),
                            if (_isListening)
                              Positioned(
                                top: 6,
                                right: 6,
                                child: Container(
                                  width: 14,
                                  height: 14,
                                  decoration: BoxDecoration(
                                    color: Colors.red,
                                    shape: BoxShape.circle,
                                  ),
                                  child: Icon(
                                    Icons.close,
                                    color: Colors.white,
                                    size: 10,
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],

                // Text input field
                Expanded(
                  child: Padding(
                    padding: EdgeInsets.symmetric(
                      horizontal: (!kIsWeb && _speechToTextEnabled) ? 8 : 20,
                      vertical: 12,
                    ),
                    child: TextField(
                      controller: _textController,
                      decoration: const InputDecoration(
                        hintText: 'Type your message...',
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.zero,
                      ),
                      onSubmitted: _isLoading ? null : _sendMessage,
                      enabled: !_isLoading,
                      maxLines: 1,
                      textCapitalization: TextCapitalization.sentences,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(width: 8),

        // Send button
        Material(
          color: _isLoading ? Colors.grey[300] : Colors.grey[800],
          borderRadius: BorderRadius.circular(20),
          child: InkWell(
            borderRadius: BorderRadius.circular(20),
            onTap: _isLoading ? null : () => _sendMessage(),
            child: const SizedBox(
              width: 40,
              height: 40,
              child: Icon(Icons.send, size: 20, color: Colors.white),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTypingIndicator() {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: Colors.blue[100],
            child: Icon(Icons.smart_toy, color: Colors.blue[700]),
          ),
          SizedBox(width: 12),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.grey[200],
              borderRadius: BorderRadius.circular(18),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                AnimatedBuilder(
                  animation: _typingAnimationController,
                  builder: (context, child) {
                    return Row(
                      children: List.generate(3, (index) {
                        final delay = index * 0.2;
                        final animationValue = (_typingAnimationController.value - delay).clamp(0.0, 1.0);
                        return Container(
                          margin: EdgeInsets.only(right: 4),
                          child: Transform.translate(
                            offset: Offset(0, -8 * (animationValue > 0.5 ? 1 - animationValue : animationValue) * 2),
                            child: SizedBox(
                              width: 8,
                              height: 8,
                              child: Container(
                                decoration: BoxDecoration(
                                  color: Colors.grey[600],
                                  shape: BoxShape.circle,
                                ),
                              ),
                            ),
                          ),
                        );
                      }),
                    );
                  },
                ),
                SizedBox(width: 8),
                Text(
                  'AI is thinking...',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    return Container(
      margin: EdgeInsets.only(bottom: 16),
      child: Row(
        mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!message.isUser) ...[
            CircleAvatar(
              backgroundColor: message.isError ? Colors.red[100] : Colors.blue[100],
              child: Icon(
                message.isError ? Icons.error : Icons.smart_toy,
                color: message.isError ? Colors.red[700] : Colors.blue[700],
              ),
            ),
            SizedBox(width: 12),
          ],
          
          Flexible(
            child: Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: message.isUser
                  ? Colors.grey[700]
                  : (message.isError ? Colors.red[50] : Colors.grey[200]),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Display message parts
                  if (message.parts.isNotEmpty) ...[
                    ...message.parts.map((part) => _buildMessagePart(part, message.isUser)),
                  ] else if (message.text.isNotEmpty) ...[
                    Text(
                      message.text,
                      style: TextStyle(
                        color: message.isUser ? Colors.white : Colors.black87,
                        fontSize: 16,
                      ),
                    ),
                  ],
                  
                  SizedBox(height: 4),
                  Text(
                    _formatTimestamp(message.timestamp),
                    style: TextStyle(
                      color: message.isUser ? Colors.white70 : Colors.grey[600],
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          if (message.isUser) ...[
            SizedBox(width: 12),
            CircleAvatar(
              backgroundColor: Colors.green[100],
              child: Icon(Icons.person, color: Colors.green[700]),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMessagePart(MessagePart part, bool isUser) {
    if (part is TextPart) {
      return Padding(
        padding: EdgeInsets.only(bottom: 8),
        child: Text(
          part.content,
          style: TextStyle(
            color: isUser ? Colors.white : Colors.black87,
            fontSize: 16,
          ),
        ),
      );
    } else if (part is ImagePart) {
      return Padding(
        padding: EdgeInsets.only(bottom: 8),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: _buildNetworkImage(part.uri, part.altText),
        ),
      );
    }
    return SizedBox.shrink();
  }

  Widget _buildNetworkImage(String imageUrl, String altText) {
  print('🖼️ Attempting to load image: $imageUrl'); // Add this debug line
  
  return Container(
    constraints: BoxConstraints(
      maxWidth: 300,
      maxHeight: 300,
    ),
    child: Image.network(
      imageUrl,
      width: double.infinity,
      fit: BoxFit.cover,
      loadingBuilder: (context, child, loadingProgress) {
        if (loadingProgress == null) {
          print('✅ Image loaded successfully: $imageUrl'); // Add this debug line
          return child;
        }
        return SizedBox(
          height: 200,
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                CircularProgressIndicator(
                  value: loadingProgress.expectedTotalBytes != null
                      ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                      : null,
                ),
                SizedBox(height: 8),
                Text(
                  'Loading image...',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        );
      },
      errorBuilder: (context, error, stackTrace) {
        print('❌ Image load error for $imageUrl: $error'); // Enhanced debug line
        
        return Container(
          height: 120,
          width: double.infinity,
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.grey[300]!),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.broken_image,
                color: Colors.grey[600],
                size: 32,
              ),
              SizedBox(height: 8),
              Text(
                altText,
                style: TextStyle(
                  color: Colors.grey[700],
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 4),
              Text(
                'Image not available',
                style: TextStyle(
                  color: Colors.grey[500],
                  fontSize: 12,
                ),
              ),
              SizedBox(height: 4),
              // Show filename for debugging
              Text(
                imageUrl.contains('/') ? imageUrl.split('/').last.split('?').first : imageUrl,
                style: TextStyle(
                  color: Colors.grey[400],
                  fontSize: 10,
                  fontFamily: 'monospace',
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        );
      },
    ),
  );
}

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);
    
    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h ago';
    } else {
      return '${timestamp.day}/${timestamp.month} ${timestamp.hour}:${timestamp.minute.toString().padLeft(2, '0')}';
    }
  }
}

// Data classes remain the same
class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final List<MessagePart> parts;
  final bool isError;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.parts = const [],
    this.isError = false,
  });
}

abstract class MessagePart {}

class TextPart extends MessagePart {
  final String content;
  TextPart({required this.content});
}

class ImagePart extends MessagePart {
  final String uri;
  final String altText;
  ImagePart({required this.uri, required this.altText});
}