# Universal Manual RAG Chat - Frontend

A Flutter-based frontend for the Universal Manual RAG Chat platform, providing an intuitive multimodal chat interface with speech-to-text, text-to-speech, and AI-powered responses.

[![Flutter](https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![Firebase](https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com)

## Features

- 🎯 **Multimodal Chat Interface** - Text and voice interactions with AI assistant
- 🔐 **Firebase Authentication** - Secure Google Sign-In integration
- 🎤 **Speech-to-Text** - Real-time voice input with Google Cloud Speech API
- 🔊 **Text-to-Speech** - Natural voice responses with Google Cloud TTS
- 📱 **Cross-Platform** - Runs on Web, iOS, and Android
- 🔒 **Secure Backend Integration** - Direct connection to Google Cloud Run backend
- 🎨 **Modern UI/UX** - Clean, responsive design with Material Design 3

## Quick Start

### Prerequisites

- **Flutter SDK** 3.16.0 or higher
- **Dart SDK** 3.2.0 or higher
- **Node.js** 22.x or higher (for Firebase Functions)
- **Firebase CLI** installed and configured
- **Google Cloud SDK** (optional, for advanced configuration)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/patiza604/universal-manual-rag-chat.git
   cd universal-manual-rag-chat/chatbot_frontend
   ```

2. **Install Flutter dependencies**
   ```bash
   flutter pub get
   ```

3. **Install Firebase Functions dependencies**
   ```bash
   cd functions
   npm install
   cd ..
   ```

4. **Configure Firebase** (if not already done)
   ```bash
   firebase login
   firebase use ai-chatbot-beb8d
   ```

### Development Setup

#### Local Development (Web)

```bash
# Run Flutter web app locally
flutter run -d web

# Or specify port
flutter run -d web --web-port=3000
```

The app will be available at `http://localhost:3000` (or specified port).

#### Mobile Development

```bash
# List available devices
flutter devices

# Run on connected device/emulator
flutter run

# Run on specific device
flutter run -d <device-id>
```

#### Firebase Functions Local Development

```bash
cd functions

# Start Firebase emulator suite
firebase emulators:start

# Or run specific emulators
firebase emulators:start --only functions,firestore,auth
```

### Building for Production

#### Web Build

```bash
# Build for web production
flutter build web

# Build with specific base href (if deploying to subdirectory)
flutter build web --base-href="/chat/"
```

Build output will be in `build/web/`.

#### Mobile Builds

**Android:**
```bash
# Build APK
flutter build apk

# Build App Bundle (recommended for Play Store)
flutter build appbundle
```

**iOS:**
```bash
# Build for iOS (requires Xcode on macOS)
flutter build ios

# Build archive for App Store
flutter build ipa
```

## Project Structure

```
chatbot_frontend/
├── lib/
│   ├── main.dart                 # App entry point
│   ├── screens/
│   │   ├── home_screen.dart      # Landing page
│   │   └── ai_chat_screen.dart   # Main chat interface
│   ├── services/
│   │   ├── auth_service.dart     # Firebase authentication
│   │   ├── ai_chat_service.dart  # Backend API communication
│   │   ├── speech_service.dart   # Speech-to-text functionality
│   │   └── tts_service.dart      # Text-to-speech functionality
│   ├── models/
│   │   └── chat_message.dart     # Data models
│   └── widgets/
│       └── message_bubble.dart   # Chat UI components
├── functions/
│   ├── index.js                  # Firebase Functions
│   └── package.json              # Node.js dependencies
├── web/
│   └── index.html                # Web app configuration
├── android/                      # Android-specific files
├── ios/                          # iOS-specific files
├── pubspec.yaml                  # Flutter dependencies
└── firebase.json                 # Firebase configuration
```

## Configuration

### Firebase Configuration

The app uses Firebase for authentication, database, and hosting. Configuration is automatically generated in `lib/firebase_options.dart`.

**Key Firebase services:**
- **Authentication** - Google Sign-In
- **Firestore** - Chat history storage
- **Cloud Storage** - File and image storage
- **Functions** - Server-side logic
- **Hosting** - Web app deployment

### Backend Integration

The frontend connects to the Google Cloud Run backend:

```dart
// In lib/services/ai_chat_service.dart
final String _backendBaseUrl = 'https://ai-agent-service-325296751367.us-central1.run.app';
```

### Environment-Specific Configuration

Create environment-specific configurations by modifying:

- `lib/firebase_options.dart` - Firebase project settings
- `lib/services/ai_chat_service.dart` - Backend URL configuration
- `functions/index.js` - Server-side environment variables

## Key Dependencies

### Core Flutter Dependencies

```yaml
dependencies:
  flutter:
    sdk: flutter
  firebase_core: ^4.1.0              # Firebase SDK
  cloud_firestore: ^6.0.1            # Database
  firebase_auth: ^6.0.2              # Authentication
  google_sign_in: ^6.1.5             # Google authentication
  http: ^1.4.0                       # HTTP requests
  audioplayers: ^6.5.0               # Audio playback
  record: ^6.0.0                     # Audio recording
  permission_handler: ^11.0.1        # Device permissions
```

### Speech Dependencies

```yaml
  speech_to_text:
    git:
      url: https://github.com/csdcorp/speech_to_text
      ref: improve_android_speech_settings   # Custom fork with improvements
```

### Development Dependencies

```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^5.0.0              # Linting rules
```

## Testing

### Unit Tests

```bash
# Run all tests
flutter test

# Run specific test file
flutter test test/widget_test.dart

# Run tests with coverage
flutter test --coverage
```

### Integration Tests

```bash
# Run integration tests
flutter test integration_test/
```

### Firebase Functions Tests

```bash
cd functions

# Run function tests
npm test

# Run with emulator
npm run test:emulator
```

## Deployment

### Web Deployment (Firebase Hosting)

```bash
# Build and deploy to Firebase Hosting
flutter build web
firebase deploy --only hosting

# Deploy specific Firebase services
firebase deploy --only functions
firebase deploy --only firestore:rules
```

### Mobile App Deployment

**Android (Google Play Store):**
1. Build app bundle: `flutter build appbundle`
2. Upload to Google Play Console
3. Follow Play Store publishing guidelines

**iOS (App Store):**
1. Build archive: `flutter build ipa`
2. Upload to App Store Connect via Xcode or Transporter
3. Follow App Store review guidelines

### Firebase Functions Deployment

```bash
cd functions

# Deploy all functions
firebase deploy --only functions

# Deploy specific function
firebase deploy --only functions:chatFunction
```

## Development Workflow

### Local Development

1. **Start backend locally** (optional):
   ```bash
   cd ../chatbot_backend
   python main.py
   ```

2. **Start Firebase emulators**:
   ```bash
   cd functions
   firebase emulators:start
   ```

3. **Run Flutter app**:
   ```bash
   flutter run -d web
   ```

### Code Style and Linting

```bash
# Analyze code
flutter analyze

# Format code
flutter format .

# Fix linting issues
dart fix --apply
```

### Debugging

**Flutter Inspector:**
- Available in VS Code and Android Studio
- Real-time widget tree inspection
- Performance profiling

**Firebase Debug View:**
- Monitor real-time database changes
- View authentication states
- Debug function executions

## Troubleshooting

### Common Issues

**Build Errors:**
```bash
# Clean build cache
flutter clean
flutter pub get
flutter build web
```

**Firebase Connection Issues:**
```bash
# Reinstall Firebase tools
npm uninstall -g firebase-tools
npm install -g firebase-tools
firebase login
```

**Speech Recognition Not Working:**
- Check microphone permissions
- Verify internet connection
- Test on different devices/browsers

**Authentication Failures:**
- Verify Firebase configuration
- Check Google Cloud Console settings
- Review OAuth consent screen setup

### Performance Optimization

**Web Performance:**
- Enable web renderer selection: `flutter run -d web --web-renderer html`
- Optimize images and assets
- Use `flutter build web --release` for production

**Mobile Performance:**
- Profile with `flutter run --profile`
- Optimize image sizes
- Use `const` constructors where possible

### Platform-Specific Issues

**Web:**
- CORS issues with backend - use image proxy endpoints
- Audio permissions - implement permission requests
- PWA features - configure `web/manifest.json`

**Mobile:**
- iOS permissions - update `ios/Runner/Info.plist`
- Android permissions - update `android/app/src/main/AndroidManifest.xml`
- Platform-specific plugins - check compatibility

## Contributing

Please read [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Guidelines

1. **Code Style** - Follow Flutter/Dart conventions
2. **Testing** - Write tests for new features
3. **Documentation** - Update README for significant changes
4. **Commits** - Use conventional commit messages

## Security

For security concerns, please review our [Security Policy](../SECURITY.md).

**Key Security Features:**
- Firebase Authentication with Google Sign-In
- Secure HTTPS communication with backend
- Input validation and sanitization
- Proper error handling without information leakage

## Support

- **Documentation**: See main [README.md](../README.md)
- **Issues**: [GitHub Issues](https://github.com/patiza604/universal-manual-rag-chat/issues)
- **Discussions**: [GitHub Discussions](https://github.com/patiza604/universal-manual-rag-chat/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Note**: This frontend is part of the Universal Manual RAG Chat platform. For complete setup instructions, please refer to the main [project documentation](../README.md).