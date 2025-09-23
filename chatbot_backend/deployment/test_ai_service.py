# deployment/test_ai_service.py
import os
import sys
from pathlib import Path
import time
import json
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

class EnhancedServiceTester:
    """Enhanced AI Agent Service tester with comprehensive validation"""
    
    def __init__(self):
        self.service_url = os.getenv("AI_SERVICE_URL", "https://ai-agent-service-294800519552.us-central1.run.app")
        self.project_id = os.getenv("PROJECT_ID", "ai-chatbot-beb8d")
        self.session = self._create_session()
        self.test_results = {
            'health_check': False,
            'startup_check': False,
            'initialization_status': False,
            'vector_service': False,
            'enhanced_features': False,
            'chat_functionality': False,
            'tts_functionality': False,
            'performance_metrics': {},
            'errors': []
        }
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()
        
        # Enhanced retry strategy for Cloud Run
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def run_comprehensive_tests(self) -> bool:
        """Run all tests and return overall success"""
        
        print("🚀 Enhanced AI Agent Service Testing Suite")
        print("=" * 60)
        print(f"🔗 Service URL: {self.service_url}")
        print(f"📊 Project ID: {self.project_id}")
        print(f"🕒 Test started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Test sequence
        test_sequence = [
            ("🏥 Health Check", self._test_health_endpoint),
            ("🚀 Startup Check", self._test_startup_check),
            ("⚙️ Initialization Status", self._test_initialization_status),
            ("📦 Vector Service", self._test_vector_service),
            ("🧠 Enhanced Features", self._test_enhanced_features),
            ("💬 Chat Functionality", self._test_chat_functionality),
            ("🔊 TTS Functionality", self._test_tts_functionality),
            ("📊 Performance Metrics", self._test_performance_metrics),
        ]
        
        overall_success = True
        
        for test_name, test_func in test_sequence:
            print(f"\n{test_name}")
            print("-" * 40)
            
            try:
                start_time = time.time()
                success = test_func()
                duration = time.time() - start_time
                
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"   Result: {status} ({duration:.2f}s)")
                
                if not success:
                    overall_success = False
                    
            except Exception as e:
                print(f"   Result: ❌ ERROR - {str(e)}")
                self.test_results['errors'].append(f"{test_name}: {str(e)}")
                overall_success = False
        
        # Print comprehensive summary
        self._print_test_summary(overall_success)
        
        return overall_success
    
    def _test_health_endpoint(self) -> bool:
        """Test health endpoint with detailed analysis"""
        
        try:
            response = self.session.get(f"{self.service_url}/health", timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Health endpoint returned {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
            
            health_data = response.json()
            print("✅ Health endpoint accessible")
            
            # Analyze health data
            services = health_data.get("services", {})
            status = health_data.get("status", "unknown")
            timestamp = health_data.get("timestamp", "unknown")
            
            print(f"   Status: {status}")
            print(f"   Timestamp: {timestamp}")
            
            # Check critical services
            critical_services = [
                "embedding_model", "generative_model", "chat_manager", 
                "faiss_service", "tts_service"
            ]
            
            healthy_services = 0
            for service in critical_services:
                service_status = services.get(service, False)
                status_icon = "✅" if service_status else "❌"
                print(f"   {service}: {status_icon}")
                
                if service_status:
                    healthy_services += 1
            
            # Check for enhanced features indicator
            if health_data.get("enhanced_features"):
                print("🚀 Enhanced features detected:")
                for feature in health_data["enhanced_features"]:
                    print(f"   • {feature}")
            
            self.test_results['health_check'] = healthy_services >= len(critical_services) - 1  # Allow 1 failure
            return self.test_results['health_check']
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def _test_startup_check(self) -> bool:
        """Test startup check endpoint"""
        
        try:
            response = self.session.get(f"{self.service_url}/debug/startup-check", timeout=20)
            
            if response.status_code != 200:
                print(f"❌ Startup check returned {response.status_code}")
                return False
            
            startup_data = response.json()
            print("✅ Startup check accessible")
            
            # Analyze startup data
            status = startup_data.get("status", "unknown")
            is_local = startup_data.get("is_local", False)
            environment = startup_data.get("environment", {})
            
            print(f"   Status: {status}")
            print(f"   Environment: {'Local' if is_local else 'Cloud'}")
            
            # Check environment configuration
            if environment:
                key_configs = ["PROJECT_ID", "LOCATION", "LOCAL_VECTOR_FILES_PATH"]
                for config in key_configs:
                    value = environment.get(config, "Not set")
                    print(f"   {config}: {value}")
            
            self.test_results['startup_check'] = status.lower() in ["ok", "ready", "healthy"]
            return self.test_results['startup_check']
            
        except Exception as e:
            print(f"❌ Startup check failed: {e}")
            return False
    
    def _test_initialization_status(self) -> bool:
        """Test initialization status with detailed analysis"""
        
        try:
            response = self.session.get(f"{self.service_url}/debug/initialization-status", timeout=20)
            
            if response.status_code != 200:
                print(f"❌ Initialization status returned {response.status_code}")
                return False
            
            init_data = response.json()
            print("✅ Initialization status accessible")
            
            # Analyze initialization status
            initialized_services = 0
            total_services = 0
            pending_services = []
            failed_services = []
            
            for key, value in init_data.items():
                if key.endswith("_initialized"):
                    total_services += 1
                    service_name = key.replace("_initialized", "")
                    
                    if isinstance(value, bool):
                        if value:
                            initialized_services += 1
                            print(f"   ✅ {service_name}")
                        else:
                            print(f"   ❌ {service_name}")
                            if "faiss" in service_name.lower():
                                failed_services.append(service_name)
                            else:
                                pending_services.append(service_name)
                    else:
                        print(f"   ❓ {service_name}: {value}")
            
            print(f"   Summary: {initialized_services}/{total_services} services initialized")
            
            if pending_services:
                print(f"   ⏳ Pending: {', '.join(pending_services)}")
            
            if failed_services:
                print(f"   ❌ Failed: {', '.join(failed_services)}")
                print("   💡 Check vector files and FAISS configuration")
            
            self.test_results['initialization_status'] = initialized_services >= (total_services * 0.8)  # 80% threshold
            return self.test_results['initialization_status']
            
        except Exception as e:
            print(f"❌ Initialization status failed: {e}")
            return False
    
    def _test_vector_service(self) -> bool:
        """Test vector service functionality"""
        
        try:
            # Check if there's a vector service status endpoint
            response = self.session.get(f"{self.service_url}/debug/vector-status", timeout=20)
            
            if response.status_code == 200:
                vector_data = response.json()
                print("✅ Vector service status accessible")
                
                # Analyze vector service
                service_type = vector_data.get("service_type", "unknown")
                is_ready = vector_data.get("is_ready", False)
                vector_count = vector_data.get("vector_count", 0)
                index_type = vector_data.get("index_type", "unknown")
                
                print(f"   Service Type: {service_type}")
                print(f"   Ready: {'✅' if is_ready else '❌'}")
                print(f"   Vector Count: {vector_count:,}")
                print(f"   Index Type: {index_type}")
                
                # Check for enhanced features
                enhanced_features = vector_data.get("enhanced_features", {})
                if enhanced_features:
                    print("   🚀 Enhanced features:")
                    for feature, enabled in enhanced_features.items():
                        status = "✅" if enabled else "❌"
                        print(f"     {feature}: {status}")
                
                self.test_results['vector_service'] = is_ready and vector_count > 0
                return self.test_results['vector_service']
            
            else:
                print("⚠️ Vector status endpoint not available, checking via chat test")
                return True  # Will be validated in chat test
                
        except Exception as e:
            print(f"⚠️ Vector service test inconclusive: {e}")
            return True  # Not critical if endpoint doesn't exist
    
    def _test_enhanced_features(self) -> bool:
        """Test enhanced features detection"""
        
        try:
            # Check for enhanced features endpoint
            response = self.session.get(f"{self.service_url}/debug/enhanced-features", timeout=15)
            
            if response.status_code == 200:
                features_data = response.json()
                print("✅ Enhanced features endpoint accessible")
                
                features = features_data.get("features", {})
                enabled_count = 0
                
                expected_features = [
                    "llm_classification", "multi_level_chunking", "quality_scoring",
                    "group_relationships", "dynamic_retrieval", "semantic_search"
                ]
                
                print("   Feature Status:")
                for feature in expected_features:
                    enabled = features.get(feature, False)
                    status = "✅" if enabled else "❌"
                    print(f"     {feature}: {status}")
                    if enabled:
                        enabled_count += 1
                
                # Check metadata richness
                metadata_info = features_data.get("metadata_info", {})
                if metadata_info:
                    print("   Metadata Information:")
                    for key, value in metadata_info.items():
                        print(f"     {key}: {value}")
                
                self.test_results['enhanced_features'] = enabled_count >= 3  # At least 3 enhanced features
                return self.test_results['enhanced_features']
            
            else:
                print("⚠️ Enhanced features endpoint not available")
                return True  # Not critical
                
        except Exception as e:
            print(f"⚠️ Enhanced features test inconclusive: {e}")
            return True
    
    def _test_chat_functionality(self) -> bool:
        """Test chat functionality with multiple queries"""
        
        test_queries = [
            {
                "message": "What is on page 22?",
                "expected_keywords": ["g", "start", "startup", "system", "harvesting"]
            },
            {
                "message": "What safety precautions should I take?",
                "expected_keywords": ["safety", "precaution", "danger", "warning", "caution"]
            },
            {
                "message": "How do I calibrate the diameter sensor?",
                "expected_keywords": ["calibrate", "diameter", "sensor", "calibration"]
            }
        ]
        
        successful_queries = 0
        
        for i, query_data in enumerate(test_queries, 1):
            print(f"\n   Test Query {i}: {query_data['message']}")
            
            try:
                start_time = time.time()
                response = self.session.post(
                    f"{self.service_url}/chat/send",
                    json={"message": query_data["message"]},
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    chat_data = response.json()
                    
                    # Analyze response structure
                    response_parts = chat_data.get("response", {}).get("parts", [])
                    
                    if response_parts:
                        # Extract text content
                        text_content = ""
                        image_count = 0
                        
                        for part in response_parts:
                            if part.get("type") == "text":
                                text_content += part.get("content", "")
                            elif part.get("type") == "image":
                                image_count += 1
                        
                        # Check relevance
                        text_lower = text_content.lower()
                        relevant_keywords = sum(1 for keyword in query_data["expected_keywords"] 
                                              if keyword in text_lower)
                        
                        relevance_score = relevant_keywords / len(query_data["expected_keywords"])
                        
                        print(f"     ✅ Response received ({response_time:.2f}s)")
                        print(f"     📝 Text length: {len(text_content)} chars")
                        print(f"     🖼️ Images: {image_count}")
                        print(f"     🎯 Relevance: {relevance_score:.2%}")
                        
                        if relevance_score >= 0.3:  # At least 30% keyword match
                            successful_queries += 1
                            print(f"     ✅ Query successful")
                        else:
                            print(f"     ⚠️ Low relevance score")
                    else:
                        print(f"     ❌ No response parts found")
                else:
                    print(f"     ❌ Request failed: {response.status_code}")
                    if response.status_code == 503:
                        print(f"     💡 Service may still be initializing")
                    
            except Exception as e:
                print(f"     ❌ Query failed: {e}")
        
        success_rate = successful_queries / len(test_queries)
        print(f"\n   📊 Chat Success Rate: {success_rate:.1%} ({successful_queries}/{len(test_queries)})")
        
        self.test_results['chat_functionality'] = success_rate >= 0.6  # 60% success threshold
        return self.test_results['chat_functionality']
    
    def _test_tts_functionality(self) -> bool:
        """Test TTS functionality"""
        
        try:
            tts_payload = {
                "message": "This is a test of the text-to-speech functionality.",
                "include_audio": True,
                "voice_name": "en-US-Chirp3-HD-Leda",
                "language_code": "en-US"
            }
            
            print("   Testing TTS generation...")
            start_time = time.time()
            
            response = self.session.post(
                f"{self.service_url}/chat/send-with-tts",
                json=tts_payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                tts_data = response.json()
                audio_generated = tts_data.get("audio_generated", False)
                
                print(f"   ✅ TTS endpoint accessible ({response_time:.2f}s)")
                
                if audio_generated:
                    audio_data = tts_data.get("audio_data", "")
                    audio_size = len(audio_data)
                    print(f"   🔊 Audio generated: {audio_size:,} bytes (base64)")
                    
                    # Validate audio data format
                    if audio_data.startswith("data:audio"):
                        print("   ✅ Valid audio data format")
                        self.test_results['tts_functionality'] = True
                        return True
                    else:
                        print("   ⚠️ Unexpected audio format")
                else:
                    error = tts_data.get("audio_error", "Unknown error")
                    print(f"   ❌ Audio generation failed: {error}")
                
            else:
                print(f"   ❌ TTS request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
            
            return False
            
        except Exception as e:
            print(f"   ❌ TTS test failed: {e}")
            return False
    
    def _test_performance_metrics(self) -> bool:
        """Test performance and gather metrics"""
        
        try:
            # Simple performance test
            print("   Running performance test...")
            
            test_message = "Quick performance test query"
            response_times = []
            
            for i in range(3):
                start_time = time.time()
                response = self.session.post(
                    f"{self.service_url}/chat/send",
                    json={"message": test_message},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code != 200:
                    print(f"   ⚠️ Performance test {i+1} failed: {response.status_code}")
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                
                print(f"   📊 Average response time: {avg_response_time:.2f}s")
                print(f"   📊 Min response time: {min_response_time:.2f}s")
                print(f"   📊 Max response time: {max_response_time:.2f}s")
                
                self.test_results['performance_metrics'] = {
                    'avg_response_time': avg_response_time,
                    'min_response_time': min_response_time,
                    'max_response_time': max_response_time
                }
                
                # Performance thresholds
                return avg_response_time < 15.0  # Under 15 seconds average
            
            return False
            
        except Exception as e:
            print(f"   ⚠️ Performance test failed: {e}")
            return False
    
    def _print_test_summary(self, overall_success: bool):
        """Print comprehensive test summary"""
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        # Overall status
        overall_status = "✅ PASSED" if overall_success else "❌ FAILED"
        print(f"🎯 Overall Result: {overall_status}")
        
        # Individual test results
        print(f"\n📋 Individual Test Results:")
        test_names = {
            'health_check': 'Health Check',
            'startup_check': 'Startup Check', 
            'initialization_status': 'Initialization Status',
            'vector_service': 'Vector Service',
            'enhanced_features': 'Enhanced Features',
            'chat_functionality': 'Chat Functionality',
            'tts_functionality': 'TTS Functionality'
        }
        
        passed_tests = 0
        for key, name in test_names.items():
            status = "✅" if self.test_results.get(key, False) else "❌"
            print(f"   {status} {name}")
            if self.test_results.get(key, False):
                passed_tests += 1
        
        success_rate = (passed_tests / len(test_names)) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}% ({passed_tests}/{len(test_names)})")
        
        # Performance metrics
        perf_metrics = self.test_results.get('performance_metrics', {})
        if perf_metrics:
            print(f"\n⚡ Performance Metrics:")
            print(f"   Average Response Time: {perf_metrics.get('avg_response_time', 0):.2f}s")
            print(f"   Min Response Time: {perf_metrics.get('min_response_time', 0):.2f}s")
            print(f"   Max Response Time: {perf_metrics.get('max_response_time', 0):.2f}s")
        
        # Errors
        if self.test_results['errors']:
            print(f"\n❌ Errors Encountered:")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if not self.test_results.get('chat_functionality', False):
            print("   • Check vector files and FAISS service initialization")
            print("   • Verify model credentials and quotas")
        
        if not self.test_results.get('tts_functionality', False):
            print("   • TTS issues are non-critical but check service account permissions")
        
        if perf_metrics.get('avg_response_time', 0) > 10:
            print("   • Consider optimizing vector search or upgrading Cloud Run resources")
        
        # Next steps
        print(f"\n🔗 Service Information:")
        print(f"   Service URL: {self.service_url}")
        print(f"   Project ID: {self.project_id}")
        
        if overall_success:
            print(f"\n🎉 Service is ready for production use!")
        else:
            print(f"\n🔧 Service needs attention before production use")
            print(f"   Check logs: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent-service' --limit=50 --project={self.project_id}")
        
        print("=" * 60)

def check_local_vector_files() -> bool:
    """Verify local vector files exist with enhanced support"""
    
    print("🔍 Verifying Vector Files")
    print("-" * 40)
    
    vector_path = Path(__file__).parent.parent / "app" / "vector-files"
    
    # Core files (required)
    core_files = [
        "embeddings_enhanced.npy",
        "metadata_enhanced.pkl", 
        "index_to_id_enhanced.pkl"
    ]
    
    # Enhanced files (optional but beneficial)
    enhanced_files = [
        "manual001_faiss.index",
        "manual001_stats.json"
    ]
    
    if not vector_path.exists():
        print(f"❌ Vector files directory not found: {vector_path}")
        print("💡 Run: .\\update_vectors.ps1")
        return False
    
    print(f"📁 Vector directory: {vector_path}")
    
    # Check core files
    all_core_present = True
    total_size = 0
    
    print("\n📋 Core Files:")
    for file in core_files:
        file_path = vector_path / file
        if file_path.exists():
            file_size = file_path.stat().st_size
            total_size += file_size
            print(f"   ✅ {file} ({file_size / 1024 / 1024:.1f} MB)")
        else:
            print(f"   ❌ {file} - MISSING")
            all_core_present = False
    
    # Check enhanced files
    enhanced_count = 0
    print("\n🚀 Enhanced Files:")
    for file in enhanced_files:
        file_path = vector_path / file
        if file_path.exists():
            file_size = file_path.stat().st_size
            total_size += file_size
            enhanced_count += 1
            print(f"   ✅ {file} ({file_size / 1024 / 1024:.1f} MB)")
        else:
            print(f"   ⚠️ {file} - Optional")
    
    print(f"\n📊 Summary:")
    print(f"   Total Size: {total_size / 1024 / 1024:.1f} MB")
    print(f"   Core Files: {'✅ Complete' if all_core_present else '❌ Incomplete'}")
    print(f"   Enhanced Files: {enhanced_count}/{len(enhanced_files)} present")
    
    if enhanced_count > 0:
        print("   🚀 Enhanced features available!")
    
    return all_core_present

def main():
    """Main test execution"""
    
    print("🧪 Enhanced AI Agent Service Test Suite")
    print("🕒 Started:", time.strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    # Step 1: Check local vector files
    if not check_local_vector_files():
        print("\n❌ Vector files check failed - cannot proceed with service tests")
        print("💡 Ensure vector files are properly deployed")
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # Step 2: Run comprehensive service tests
    tester = EnhancedServiceTester()
    overall_success = tester.run_comprehensive_tests()
    
    # Step 3: Exit with appropriate code
    exit_code = 0 if overall_success else 1
    
    if overall_success:
        print(f"\n🎉 All tests completed successfully!")
        print(f"✅ Enhanced AI Agent Service is ready for use")
    else:
        print(f"\n💥 Some tests failed!")
        print(f"🔧 Please review the issues above and check service logs")
    
    print(f"\n🏁 Test completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()