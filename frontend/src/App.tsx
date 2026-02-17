import { useState, useEffect, useRef } from 'react';
import { Send, Activity, Mic, MicOff, Home, MessageSquare, Settings, X, Camera, LayoutGrid, Eye, EyeOff, Ear, EarOff, ArrowLeft } from 'lucide-react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

import WaifuAvatar from './components/WaifuAvatar';
import SmartHomeDashboard from './components/SmartHomeDashboard';
import { CameraDashboard } from './components/CameraDashboard';
import MobileVision from './components/MobileVision';

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<{ role: string, content: string }[]>([]);
  const [status, setStatus] = useState('Standby');
  const [stats, setStats] = useState({ cpu: 0, ram: 0, gpu: 'N/A' });
  const [activeTab, setActiveTab] = useState<'chat' | 'home' | 'cameras'>('chat');
  const [avatarTheme, setAvatarTheme] = useState<{ timeOfDay: 'morning' | 'day' | 'evening' | 'night', weather: 'clear' | 'cloudy' | 'rain' | 'snow' | 'fog', temperature: number }>({ timeOfDay: 'day', weather: 'clear', temperature: 20 });
  const [isSpeaking, setIsSpeaking] = useState(false); // Track TTS status for lip-sync
  const [phygitalState, setPhygitalState] = useState<{state: string, temp: number, reaction: string | null}>({ state: 'neutral', temp: 0, reaction: null });
  const [currentAction, setCurrentAction] = useState<string | null>(null); // Animation Action State
 const [currentMood, setCurrentMood] = useState<string>('neutral'); // Persistent Mood State
  const [isMenuOpen, setIsMenuOpen] = useState(false); // Mobile Menu State
  const lastBroadcastId = useRef<string | null>(null); // Track last broadcast ID

  // TTS Voice Settings
  const [showSettings, setShowSettings] = useState(false);
  const [wakewordEnabled, setWakewordEnabled] = useState(false);
  const [mobileVisionEnabled, setMobileVisionEnabled] = useState(false);
  const [nimEnabled, setNimEnabled] = useState(false); // NVIDIA NIM Toggle
  const [location, setLocation] = useState('');
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (showSettings) {
        axios.get(`${API_URL}/settings/location`)
            .then(res => setLocation(res.data.city))
            .catch(err => console.error("Failed to fetch location", err));
        
        // Fetch NIM Status
        axios.get(`${API_URL}/settings/nim`)
            .then(res => setNimEnabled(res.data.enabled))
            .catch(err => console.error("Failed to fetch NIM status", err));
    }
  }, [showSettings]);

  const toggleNim = async () => {
    try {
        const newValue = !nimEnabled;
        // Optimistic UI Update
        setNimEnabled(newValue);
        await axios.post(`${API_URL}/settings/nim`, { enabled: newValue });
    } catch (err) {
        console.error("Failed to toggle NIM", err);
        setNimEnabled(!nimEnabled); // Revert on error
        alert("Fehler beim Speichern der NIM-Einstellung.");
    }
  };

  const saveLocation = async () => {
    try {
        await axios.post(`${API_URL}/settings/location`, { city: location });
        alert("Standort gespeichert!");
    } catch (err) {
        console.error("Failed to save location", err);
        alert("Fehler beim Speichern.");
    }
  };

  // TTS Helper Function (Server-Side for Consistency)
  const speakText = async (text: string) => {
      if (!text.trim()) return;

      try {
          // Cancel any active browser speech
          window.speechSynthesis.cancel();
          setIsSpeaking(true);

          // Use Server TTS (Edge-TTS) -> Same voice on ALL devices
          const response = await fetch('/tts', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ text })
          });

          if (!response.ok) throw new Error("Server TTS response not ok");

          const blob = await response.blob();
          const audioUrl = URL.createObjectURL(blob);
          const audio = new Audio(audioUrl);
          
          audio.onended = () => {
              setIsSpeaking(false);
              URL.revokeObjectURL(audioUrl);
          };
          
          audio.onerror = (e) => {
              console.error("Audio Playback Error", e);
              setIsSpeaking(false);
          };

          await audio.play();

      } catch (e) {
          console.error("Server TTS failed", e);
          setIsSpeaking(false);
      }
  };

  // Phygital Polling Logic (Reaktives Smart Home)
  useEffect(() => {
    const pollPhygital = async () => {
        try {
            const resp = await axios.get(`${API_URL}/phygital/state`);
            const { state, temp, reaction, broadcast } = resp.data;
            setPhygitalState({ state, temp, reaction });
            
            // Trigger Reaction TTS if available (Legacy/One-Time)
            if (reaction) {
                console.log("Phygital Reaction Triggered:", reaction);
                speakText(reaction);
            }

            // NEW: Broadcast Logic (Multi-Client)
            if (broadcast && broadcast.id && broadcast.text) {
                // Check if we already handled this broadcast
                if (broadcast.id !== lastBroadcastId.current) {
                    // Check timestamp age (ignore if older than 30s)
                    const now = Date.now() / 1000;
                    if (now - broadcast.timestamp < 30) {
                        console.log("Broadcast Received:", broadcast.text);
                        speakText(broadcast.text);
                    }
                    lastBroadcastId.current = broadcast.id;
                }
            }
            
            // Ambient Sync: Update Avatar Theme Temperature if sensor data is valid
            if (temp > 0) {
                 setAvatarTheme(prev => ({ ...prev, temperature: temp }));
            }
            
        } catch (e) { 
            // Silent fail on poll error
        }
    };
    
    // Initial Poll
    pollPhygital();
    const interval = setInterval(pollPhygital, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  // Wakeword / Continuous Listening Logic (Web Speech API)
  useEffect(() => {
    if (!wakewordEnabled) {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
            recognitionRef.current = null;
        }
        return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Dein Browser unterstützt keine Web Speech API (erforderlich für Wakeword). Bitte nutze Chrome oder Safari.");
        setWakewordEnabled(false);
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'de-DE';

    recognition.onresult = (event: any) => {
        const last = event.results.length - 1;
        const text = event.results[last][0].transcript.trim();
        console.log("Wakeword Listener hörte:", text);

        // Simple Wakeword Check
        if (text.toLowerCase().includes("haruko")) {
            // Feedback Sound (optional)
            // const audio = new Audio('/notification.mp3'); audio.play().catch(() => {});
            
            setStatus('Wakeword Detected!');
            setTimeout(() => setStatus('Processing...'), 1000);
            
            // Send command
            sendMessage(text);
        }
    };

    recognition.onend = () => {
        // Auto-restart if still enabled
        if (wakewordEnabled) {
            console.log("Restarting Wakeword Listener...");
            try {
                recognition.start();
            } catch (e) {
                console.error("Restart failed", e);
            }
        }
    };

    recognition.onerror = (event: any) => {
        console.warn("Wakeword Error:", event.error);
        if (event.error === 'not-allowed') {
            setWakewordEnabled(false);
            alert("Mikrofon-Zugriff verweigert.");
        }
    };

    try {
        recognition.start();
        recognitionRef.current = recognition;
        setStatus('Wakeword Active');
    } catch (e) {
        console.error("Start failed", e);
    }

    return () => {
        if (recognitionRef.current) recognitionRef.current.stop();
    };
  }, [wakewordEnabled]);


  // Voice selection logic removed in favor of Server-Side TTS

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Force relative path for Vite Proxy to handle HTTPS->HTTP
  const API_URL = '';
  // const API_URL = import.meta.env.VITE_API_URL || '';

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const resp = await axios.get(`${API_URL}/stats`);
        setStats(resp.data);
      } catch (err) {
        console.error("Failed to fetch stats", err);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const detectWeather = async () => {
      try {
        const getTimeOfDay = () => {
          const hour = new Date().getHours();
          if (hour < 6 || hour >= 22) return 'night'; // Sleep Mode: 22:00 - 06:00
          if (hour < 11) return 'morning';
          if (hour < 18) return 'day';
          return 'evening';
        };
        const timeOfDay = getTimeOfDay();
        
        // FORCE LOCATION: 06120 Halle (Saale)
        // User requested to ALWAYS use these coordinates
        const lat = 51.51;
        const lon = 11.92;

        /* Browser Geolocation Disabled to force Halle
        const fallback = { lat: 52.52, lon: 13.405 }; // Berlin
        const getPosition = (): Promise<{lat: number, lon: number}> => {
          return new Promise((resolve) => {
            if (!navigator.geolocation) return resolve(fallback);
            navigator.geolocation.getCurrentPosition(
              (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
              () => resolve(fallback),
              { timeout: 3000 }
            );
          });
        };
        const { lat, lon } = await getPosition();
        */

        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code`;
        const resp = await fetch(url);
        const data = await resp.json();
        const code = (data?.current?.weather_code ?? 0) as number;
        const temp = (data?.current?.temperature_2m ?? 20) as number;
        const mapCode = (c: number): 'clear' | 'cloudy' | 'rain' | 'snow' | 'fog' => {
          if ([0, 1].includes(c)) return 'clear';
          if ([2, 3].includes(c)) return 'cloudy';
          if ([51, 53, 55, 61, 63, 65, 80, 81, 82].includes(c)) return 'rain';
          if ([71, 73, 75, 85, 86].includes(c)) return 'snow';
          if ([45, 48].includes(c)) return 'fog';
          return 'cloudy';
        };
        setAvatarTheme({ timeOfDay, weather: mapCode(code), temperature: temp });
      } catch {
        setAvatarTheme({ timeOfDay: 'day', weather: 'clear', temperature: 20 });
      }
    };
    detectWeather();
    const t = setInterval(detectWeather, 10 * 60 * 1000);
    return () => clearInterval(t);
  }, []);

  const sendMessage = async (overrideMsg?: string) => {
    const textToSend = overrideMsg || input;
    if (!textToSend.trim()) return;

    // 1. Add User Message
    const userMsg = { role: 'user', content: textToSend };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    
    // Vision Check for Status Feedback
    const visionKeywords = ["sieh", "schau", "kamera", "webcam", "foto", "bildschirm", "screenshot", "was siehst du"];
    const isVision = visionKeywords.some(k => textToSend.toLowerCase().includes(k));
    
    setStatus(isVision ? 'ANALYZING VISUALS...' : 'Processing...');

    // 2. Add Placeholder Bot Message for Streaming
    setMessages(prev => [...prev, { role: 'bot', content: '' }]);

    try {
      // Use fetch for streaming
      const response = await fetch(`${API_URL}/chat_stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: textToSend,
          history: messages.map(m => ({
            role: m.role === 'bot' ? 'assistant' : m.role,
            content: m.content
          }))
        })
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let botResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        botResponse += chunk;
        
        // Detect and Strip Action Tags [ACTION: bow]
        const actionMatch = botResponse.match(/\[ACTION:\s*(\w+)\]/i);
        if (actionMatch) {
             const action = actionMatch[1].toLowerCase();
             console.log("Action Detected:", action);
             setCurrentAction(action);
             // Strip tag from text
             botResponse = botResponse.replace(actionMatch[0], "");
             
             // Reset action state after delay to allow re-triggering
             setTimeout(() => setCurrentAction(null), 5000);
        }

        // Detect and Strip Mood Tags [MOOD: happy]
        const moodMatch = botResponse.match(/\[MOOD:\s*(\w+)\]/i);
        if (moodMatch) {
             const mood = moodMatch[1].toLowerCase();
             console.log("Mood Detected:", mood);
             setCurrentMood(mood);
             // Strip tag from text
             botResponse = botResponse.replace(moodMatch[0], "");
        }

        // Prepare text for display - hide EXECUTE commands
        // We use a separate variable so we don't destructively modify the accumulator (botResponse) 
        // while the command is still being streamed/incomplete.
        let displayResponse = botResponse;
        
        // Hide complete EXECUTE lines
        displayResponse = displayResponse.replace(/EXECUTE:.*?(\n|$)/gi, "");
        
        // Hide partial EXECUTE at the end of string (streaming artifact)
        displayResponse = displayResponse.replace(/EXECUTE:.*$/gi, "");

        // Update the last message (bot) with accumulated text
        setMessages(prev => {
          const newHistory = [...prev];
          const lastMsg = newHistory[newHistory.length - 1];
          if (lastMsg && lastMsg.role === 'bot') {
            lastMsg.content = displayResponse;
          }
          return newHistory;
        });
      }
      
      setStatus('Online');
      
      // PARSE CLIENT COMMANDS (EXECUTE_CLIENT)
      let cleanResponse = botResponse;
      if (botResponse.includes("EXECUTE_CLIENT:")) {
          const parts = botResponse.split("EXECUTE_CLIENT:");
          cleanResponse = parts[0].trim();
          const commandStr = parts[1].trim();
          
          console.log("Client Command Received:", commandStr);
          
          if (commandStr.startsWith("open_url|")) {
              const url = commandStr.split("|")[1];
              if (url) {
                  window.open(url, '_blank');
              }
          } else if (commandStr.startsWith("scroll|")) {
              const direction = commandStr.split("|")[1] || "down";
              const amount = window.innerHeight * 0.8;
              if (direction === "down") {
                  window.scrollBy({ top: amount, behavior: 'smooth' });
              } else if (direction === "up") {
                  window.scrollBy({ top: -amount, behavior: 'smooth' });
              }
          } else if (commandStr.startsWith("reload")) {
              window.location.reload();
          } else if (commandStr.startsWith("alert|")) {
              alert(commandStr.split("|")[1]);
          }
      }

      // Final Cleanup: Strip EXECUTE commands from the final display message
      // This ensures they are removed even if they were part of the non-streaming final update
      cleanResponse = cleanResponse.replace(/EXECUTE:.*?(\n|$)/gi, "").trim();

      // Update UI to hide command
      setMessages(prev => {
          const newHistory = [...prev];
          const lastMsg = newHistory[newHistory.length - 1];
          if (lastMsg && lastMsg.role === 'bot') {
            lastMsg.content = cleanResponse;
          }
          return newHistory;
      });
      
      // Trigger TTS locally (Client Side) - This ensures sound on the requesting device
      if (cleanResponse.trim()) {
          speakText(cleanResponse);
      }

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown';
      console.error(err);
      setStatus('Error: ' + msg);
      // Update bot message to show error
      setMessages(prev => {
          const newHistory = [...prev];
          const lastMsg = newHistory[newHistory.length - 1];
          if (lastMsg && lastMsg.role === 'bot' && !lastMsg.content) {
             lastMsg.content = "Error: Connection failed.";
          }
          return newHistory;
        });
    }
  };

  const [isRecording, setIsRecording] = useState(false);
  const [recorder, setRecorder] = useState<MediaRecorder | null>(null);
  // const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>("");

  useEffect(() => {
    const getDevices = async () => {
        try {
            // Must ask for permission first to see labels
            await navigator.mediaDevices.getUserMedia({ audio: true });
            const devices = await navigator.mediaDevices.enumerateDevices();
            const mics = devices.filter(d => d.kind === 'audioinput');
            // setAudioDevices(mics);
            if (mics.length > 0) {
                // Try to find default or pick first
                const def = mics.find(m => m.deviceId === 'default');
                setSelectedDeviceId(def ? def.deviceId : mics[0].deviceId);
            }
        } catch (e) {
            console.error("Error fetching audio devices", e);
        }
    };
    getDevices();
  }, []);

  const startListening = async () => {
    if (isRecording) {
      recorder?.stop();
      setIsRecording(false);
      return;
    }

    try {
      const constraints = { 
          audio: selectedDeviceId ? { deviceId: { exact: selectedDeviceId } } : true 
      };
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'voice.webm');

        setStatus('Processing Voice...');
        try {
          const resp = await axios.post(`${API_URL}/process_audio`, formData);
          if (resp.data.text) {
            sendMessage(resp.data.text);
          } else {
            const errorMsg = resp.data.error || 'Unknown Error';
            console.error("Audio Process Error:", errorMsg);
            setStatus(`Error: ${errorMsg.substring(0, 20)}...`);
          }
        } catch (err) {
          console.error(err);
          setStatus('Upload Error');
        }
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setRecorder(mediaRecorder);
      setIsRecording(true);
      setStatus('Listening...');
    } catch (err) {
      console.error(err);
      setStatus('Mic Access Denied');
    }
  };

  return (
    <div className="relative w-full h-screen flex flex-col font-sans overflow-hidden bg-gray-900 text-white selection:bg-purple-500/30">
      
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-900 via-gray-900 to-black z-0 pointer-events-none" />

      {/* HEADER - DESKTOP ONLY (xl:flex) */}
      <div className="relative z-20 w-full p-4 hidden xl:flex justify-between items-center backdrop-blur-md bg-black/20 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center border border-purple-500/50">
             <Activity className="text-purple-400 animate-pulse" size={20} />
          </div>
          <div>
              <h1 className="text-xl font-bold tracking-wider text-white">HARUKO v2.5</h1>
              <div className="text-xs text-purple-300 opacity-60 flex gap-2">
                  <span>CPU: {stats.cpu}%</span>
                  <span>RAM: {stats.ram}%</span>
                  <span>GPU: {stats.gpu}</span>
              </div>
          </div>
        </div>

        {/* Settings Modal */}
        <AnimatePresence>
            {showSettings && (
                <motion.div 
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="absolute top-20 right-4 z-50 bg-gray-900 border border-white/20 p-4 rounded-xl shadow-2xl w-80 backdrop-blur-xl"
                >
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="font-bold text-white flex items-center gap-2"><Settings size={16}/> Einstellungen</h3>
                        <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-white"><X size={18}/></button>
                    </div>
                    
                    <div className="space-y-4">
                        {/* Wakeword Toggle */}
                        <div className="flex items-center justify-between bg-black/50 p-3 rounded-lg border border-white/10">
                            <div>
                                <label className="block text-sm font-bold text-white">Wakeword "Haruko"</label>
                                <p className="text-[10px] text-gray-400">Hört dauerhaft auf "Haruko..." (Benötigt Browser-Unterstützung)</p>
                            </div>
                            <button 
                                onClick={() => setWakewordEnabled(!wakewordEnabled)}
                                className={`w-12 h-6 rounded-full transition-colors relative ${wakewordEnabled ? 'bg-purple-600' : 'bg-gray-600'}`}
                            >
                                <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${wakewordEnabled ? 'translate-x-6' : 'translate-x-0'}`} />
                            </button>
                        </div>

                        {/* Mobile Vision Toggle */}
                        <div className="flex items-center justify-between bg-black/50 p-3 rounded-lg border border-white/10">
                            <div>
                                <label className="block text-sm font-bold text-white">Mobile Vision (FaceID)</label>
                                <p className="text-[10px] text-gray-400">Nutzt die Kamera dieses Geräts zur Personenerkennung.</p>
                            </div>
                            <button 
                                onClick={() => setMobileVisionEnabled(!mobileVisionEnabled)}
                                className={`w-12 h-6 rounded-full transition-colors relative ${mobileVisionEnabled ? 'bg-cyan-600' : 'bg-gray-600'}`}
                            >
                                <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${mobileVisionEnabled ? 'translate-x-6' : 'translate-x-0'}`} />
                            </button>
                        </div>

                        {/* NVIDIA NIM Toggle */}
                        <div className="flex items-center justify-between bg-black/50 p-3 rounded-lg border border-white/10">
                            <div>
                                <label className="block text-sm font-bold text-white flex items-center gap-2">
                                    NVIDIA NIM (Cloud AI)
                                    <span className="text-[10px] bg-green-500/20 text-green-400 px-1 rounded border border-green-500/30">FAST</span>
                                </label>
                                <p className="text-[10px] text-gray-400">Nutzt NVIDIA Cloud für schnellere Antworten & Vision.</p>
                            </div>
                            <button 
                                onClick={toggleNim}
                                className={`w-12 h-6 rounded-full transition-colors relative ${nimEnabled ? 'bg-green-600' : 'bg-gray-600'}`}
                            >
                                <div className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${nimEnabled ? 'translate-x-6' : 'translate-x-0'}`} />
                            </button>
                        </div>

                        {/* Location Settings */}
                        <div className="bg-black/50 p-3 rounded-lg border border-white/10 space-y-2">
                            <div>
                                <label className="block text-sm font-bold text-white">Standort (Wetter)</label>
                                <p className="text-[10px] text-gray-400">Für Wetterberichte und lokale Infos.</p>
                            </div>
                            <div className="flex gap-2">
                                <input 
                                    type="text" 
                                    value={location}
                                    onChange={(e) => setLocation(e.target.value)}
                                    placeholder="z.B. Berlin"
                                    className="flex-1 bg-gray-800 border border-white/10 rounded px-2 py-1 text-sm text-white focus:border-purple-500 outline-none"
                                />
                                <button 
                                    onClick={saveLocation}
                                    className="bg-purple-600 hover:bg-purple-500 text-white px-3 py-1 rounded text-xs font-bold transition-colors"
                                >
                                    Save
                                </button>
                            </div>
                        </div>

                        <div>
                            <p className="text-xs text-gray-400">
                                Haruko nutzt nun ihre eigene Neural-Stimme (Server-Side).
                                Keine Browser-Einstellungen mehr nötig.
                            </p>
                        </div>

                        {/* Credits */}
                        <div className="mt-4 pt-4 border-t border-white/10 text-center">
                            <p className="text-[10px] text-gray-500">
                                Developed & Designed by <br/>
                                <span className="text-purple-400 font-bold">Stephan Eck (Protheanreact)</span>
                            </p>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
        
        {/* DESKTOP NAVIGATION (Hidden on Mobile/Tablet) */}
        <div className="hidden xl:flex gap-2">
            <button 
                onClick={() => setActiveTab('chat')}
                className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all ${activeTab === 'chat' ? 'bg-purple-600 text-white' : 'text-gray-400 hover:bg-white/10'}`}
            >
                <MessageSquare size={18} /> Chat
            </button>
            <button 
                onClick={() => setActiveTab('home')}
                className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all ${activeTab === 'home' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-white/10'}`}
            >
                <Home size={18} /> Home
            </button>
            <button 
                onClick={() => setActiveTab('cameras')}
                className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all ${activeTab === 'cameras' ? 'bg-green-600 text-white' : 'text-gray-400 hover:bg-white/10'}`}
            >
                <Camera size={18} /> Kameras
            </button>
            <div className="w-px bg-white/10 mx-1" />
            <button 
                onClick={() => setShowSettings(!showSettings)}
                className={`p-2 rounded-xl transition-all ${showSettings ? 'bg-gray-700 text-white' : 'text-gray-400 hover:bg-white/10'}`}
            >
                <Settings size={18} />
            </button>
        </div>
      </div>

      {/* CONTENT AREA */}
      <div className="relative z-10 flex-1 overflow-hidden flex">
        
        {/* Mobile Vision Component (Hidden or Small Overlay) */}
        <MobileVision 
            enabled={mobileVisionEnabled} 
            onReaction={(text) => speakText(text)}
        />

        {/* AVATAR LAYER (Full Screen Background for Chat) */}
        <div className={`absolute inset-0 z-0 transition-all duration-700 ${activeTab === 'chat' ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}>
           <WaifuAvatar 
              speak={isSpeaking}
              theme={avatarTheme}
              phygitalMode={phygitalState.state}
              action={currentAction}
              mood={currentMood}
            />
           
           {/* Floating Status Badge */}
           <div className="absolute top-4 left-4 bg-black/50 backdrop-blur-md px-4 py-2 rounded-full border border-purple-500/30 text-xs font-mono text-purple-200 shadow-lg shadow-purple-900/20 z-20">
               STATUS: {status.toUpperCase()}
           </div>

            {/* CHAT OVERLAY - BOTTOM (Mobile Friendly) */}
            <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 via-black/60 to-transparent pt-20 flex justify-center z-30">
                <div className="w-full max-w-2xl flex flex-col gap-2">
                    
                    {/* Chat History (Limited View) */}
                    <div className="max-h-[30vh] overflow-y-auto space-y-2 scrollbar-hide px-2">
                         <AnimatePresence>
                            {messages.slice(-5).map((msg, i) => ( // Show only last 5 messages to keep focus on avatar
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    <div className={`max-w-[85%] px-4 py-2 rounded-2xl backdrop-blur-md text-sm ${
                                        msg.role === 'user' 
                                        ? 'bg-purple-600/60 text-white rounded-br-none' 
                                        : 'bg-black/60 text-blue-100 border border-white/10 rounded-bl-none'
                                    }`}>
                                        {msg.content}
                                    </div>
                                </motion.div>
                            ))}
                            <div ref={messagesEndRef} />
                        </AnimatePresence>
                    </div>

                    {/* Input Area with Mobile Menu */}
                    <div className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl p-2 flex gap-2 items-end relative z-50">
                        
                        {/* MOBILE APPS MENU TOGGLE (Visible on Mobile/Tablet) */}
                        <div className="relative xl:hidden">
                            <button
                                onClick={() => setIsMenuOpen(!isMenuOpen)}
                                className={`p-3 rounded-lg transition-all ${isMenuOpen ? 'bg-purple-600 text-white' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
                            >
                                <LayoutGrid size={20} />
                            </button>
                            
                            {/* BOTTOM MENU POPUP */}
                            <AnimatePresence>
                                {isMenuOpen && (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.9, y: 10 }}
                                        animate={{ opacity: 1, scale: 1, y: 0 }}
                                        exit={{ opacity: 0, scale: 0.9, y: 10 }}
                                        className="absolute bottom-14 left-0 w-64 bg-gray-900/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-2 flex flex-col gap-1"
                                    >
                                        <button onClick={() => { setActiveTab('chat'); setIsMenuOpen(false); }} className={`p-3 rounded-xl flex items-center gap-3 text-sm ${activeTab === 'chat' ? 'bg-purple-600 text-white' : 'text-gray-300 hover:bg-white/10'}`}>
                                            <MessageSquare size={16} /> Chat
                                        </button>
                                        <button onClick={() => { setActiveTab('home'); setIsMenuOpen(false); }} className={`p-3 rounded-xl flex items-center gap-3 text-sm ${activeTab === 'home' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-white/10'}`}>
                                            <Home size={16} /> Home
                                        </button>
                                        <button onClick={() => { setActiveTab('cameras'); setIsMenuOpen(false); }} className={`p-3 rounded-xl flex items-center gap-3 text-sm ${activeTab === 'cameras' ? 'bg-green-600 text-white' : 'text-gray-300 hover:bg-white/10'}`}>
                                            <Camera size={16} /> Kameras
                                        </button>
                                        <div className="h-px bg-white/10 my-1" />
                                        <button onClick={() => { setWakewordEnabled(!wakewordEnabled); }} className={`p-3 rounded-xl flex items-center gap-3 text-sm ${wakewordEnabled ? 'bg-red-500/20 text-red-300' : 'text-gray-300 hover:bg-white/10'}`}>
                                            {wakewordEnabled ? <Ear size={16} /> : <EarOff size={16} />} Wakeword {wakewordEnabled ? 'ON' : 'OFF'}
                                        </button>
                                        <button onClick={() => { setMobileVisionEnabled(!mobileVisionEnabled); }} className={`p-3 rounded-xl flex items-center gap-3 text-sm ${mobileVisionEnabled ? 'bg-blue-500/20 text-blue-300' : 'text-gray-300 hover:bg-white/10'}`}>
                                            {mobileVisionEnabled ? <Eye size={16} /> : <EyeOff size={16} />} Vision {mobileVisionEnabled ? 'ON' : 'OFF'}
                                        </button>
                                        <div className="h-px bg-white/10 my-1" />
                                        <button onClick={() => { setShowSettings(!showSettings); setIsMenuOpen(false); }} className="p-3 rounded-xl flex items-center gap-3 text-sm text-gray-300 hover:bg-white/10">
                                            <Settings size={16} /> Einstellungen
                                        </button>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        <button
                            onClick={startListening}
                            className={`p-3 rounded-lg transition-all ${
                                status === 'Listening...' 
                                ? 'bg-red-500/50 text-white animate-pulse' 
                                : 'text-gray-400 hover:text-white hover:bg-white/10'
                            }`}
                        >
                            {status === 'Listening...' ? <MicOff size={20} /> : <Mic size={20} />}
                        </button>
                        
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                            placeholder="Nachricht an Haruko..."
                            className="flex-1 bg-transparent border-none outline-none text-white py-3 px-2 placeholder-gray-500"
                        />
                        
                        <button
                            onClick={() => sendMessage()}
                            className="p-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg shadow-lg shadow-purple-900/20"
                        >
                            <Send size={20} />
                        </button>
                    </div>
                </div>
            </div>
        </div>

        {/* FULL SCREEN INTERFACE LAYER (Home & Cameras) */}
        {activeTab !== 'chat' && (
            <div className="relative z-10 w-full h-full bg-gray-900/95 overflow-hidden">
                {/* Floating Back Button (Mobile/Tablet Friendly) */}
                <button 
                    onClick={() => setActiveTab('chat')}
                    className="absolute bottom-6 left-6 z-50 p-4 bg-purple-600 hover:bg-purple-500 text-white rounded-full shadow-lg shadow-purple-900/50 transition-all hover:scale-110 flex items-center justify-center"
                    aria-label="Zurück zum Chat"
                >
                    <ArrowLeft size={24} />
                </button>

                <div className="h-full overflow-y-auto p-4 pb-24">
                    {activeTab === 'home' && (
                        <motion.div 
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="h-full"
                        >
                            <SmartHomeDashboard />
                        </motion.div>
                    )}

                    {activeTab === 'cameras' && <CameraDashboard apiUrl={API_URL} />}
                </div>
            </div>
        )}

      </div>
    </div>
  );
}

export default App;