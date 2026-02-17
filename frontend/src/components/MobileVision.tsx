import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Eye } from 'lucide-react';

interface MobileVisionProps {
    enabled: boolean;
    onReaction?: (text: string) => void;
}

const MobileVision: React.FC<MobileVisionProps> = ({ enabled, onReaction }) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    
    // Persistent Cooldown Storage (Survives Refresh)
    const getCooldowns = (): Record<string, number> => {
        try {
            const stored = localStorage.getItem('haruko_vision_cooldowns');
            return stored ? JSON.parse(stored) : {};
        } catch { return {}; }
    };

    const saveCooldowns = (cooldowns: Record<string, number>) => {
        localStorage.setItem('haruko_vision_cooldowns', JSON.stringify(cooldowns));
    };

    const lastReactionTimes = useRef<Record<string, number>>(getCooldowns());
    // const [debugInfo, setDebugInfo] = useState<string>(""); // Debugging UI

    // Variation für Begrüßungen (Zufallsprinzip)
    const getRandomGreeting = (name: string, isUnknown: boolean = false) => {
        const greetingsKnown = [
            `Hallo ${name}, schön dich zu sehen!`,
            `Willkommen zurück, ${name}.`,
            `Ah, ${name} ist da! Hallo!`,
            `Hey ${name}, ich hoffe du hast einen guten Tag.`,
            `Guten Tag ${name}.`
        ];
        const greetingsUnknown = [
            "Hallo! Ich glaube wir kennen uns noch nicht.",
            "Willkommen! Ich bin Haruko.",
            "Hallo, schön dich zu sehen, unbekannter Gast.",
            "Ein neues Gesicht! Hallo!",
            "Guten Tag."
        ];
        
        const list = isUnknown ? greetingsUnknown : greetingsKnown;
        return list[Math.floor(Math.random() * list.length)];
    };
    
    const [status, setStatus] = useState<string>("Inaktiv");
    const [lastDetection, setLastDetection] = useState<string | null>(null);
    const [stream, setStream] = useState<MediaStream | null>(null);

    useEffect(() => {
        if (enabled) {
            startCamera();
        } else {
            stopCamera();
        }
        return () => stopCamera();
    }, [enabled]);

    const startCamera = async () => {
        try {
            setStatus("Starte Kamera...");
            const s = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: "user", width: 640, height: 480 } 
            });
            setStream(s);
            if (videoRef.current) {
                videoRef.current.srcObject = s;
            }
            setStatus("Aktiv (Überwache...)");
        } catch (err) {
            console.error("Camera Error:", err);
            setStatus("Kamera-Fehler");
        }
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
        setStatus("Inaktiv");
    };

    // Analysis Loop
    useEffect(() => {
        if (!enabled || !stream) return;

        const interval = setInterval(async () => {
            if (videoRef.current && canvasRef.current) {
                const context = canvasRef.current.getContext('2d');
                if (context) {
                    // Draw video frame to canvas
                    context.drawImage(videoRef.current, 0, 0, 640, 480);
                    
                    // Convert to Blob/File
                    canvasRef.current.toBlob(async (blob) => {
                        if (blob) {
                            const formData = new FormData();
                            formData.append('file', blob, 'frame.jpg');

                            try {
                                const res = await axios.post('/api/vision/analyze', formData);
                                
                                if (res.data.status === 'success') {
                                    const names = res.data.detected;
                                    const action = res.data.action;
                                    // const person = res.data.person;
                                    
                                    // Debugging
                                    // setDebugInfo(JSON.stringify(res.data));

                                    if (names && names.length > 0) {
                                        const namesStr = names.join(", ");
                                        setLastDetection(namesStr);
                                        
                                        // Smart Cooldown Logic (15 Minutes per Person)
                                        const now = Date.now();
                                        const COOLDOWN = 15 * 60 * 1000; 

                                        if (onReaction) {
                                            // 1. Filter known people who are NOT on cooldown
                                            const knownPeople = names.filter((n: string) => n !== 'Unknown');
                                            
                                            // DEBUGGING (Removed for Production)
                                            // let debugMsg = "";

                                            const peopleToGreet = knownPeople.filter((name: string) => {
                                                const key = name.trim().toLowerCase(); // Normalize Key
                                                const lastTime = lastReactionTimes.current[key] || 0;
                                                const diff = now - lastTime;
                                                
                                                // debugMsg += `${name}: ${timeLeft.toFixed(0)}s Pause | `;

                                                if (diff > COOLDOWN) {
                                                    return true;
                                                } else {
                                                    return false;
                                                }
                                            });

                                            // setDebugInfo(debugMsg); // Update UI

                                            // 2. Greet valid people
                                            if (peopleToGreet.length > 0) {
                                                peopleToGreet.forEach((name: string) => {
                                                    const key = name.trim().toLowerCase();
                                                    const text = getRandomGreeting(name, false);
                                                    onReaction(text);
                                                    lastReactionTimes.current[key] = now;
                                                });
                                                saveCooldowns(lastReactionTimes.current);
                                            }
                                            
                                            // 3. Handle Unknowns (Guests)
                                            else if (action === 'alert') {
                                                 const key = 'unknown_guest';
                                                 const lastUnknownTime = lastReactionTimes.current[key] || 0;
                                                 if (now - lastUnknownTime > COOLDOWN) {
                                                     const text = getRandomGreeting("Gast", true);
                                                     onReaction(text);
                                                     lastReactionTimes.current[key] = now;
                                                     saveCooldowns(lastReactionTimes.current);
                                                 }
                                            }
                                        }

                                    } else {
                                        setLastDetection(null);
                                    }
                                }
                            } catch (e) {
                                console.error("Upload Error:", e);
                                setStatus("Verbindungsfehler (Upload)");
                            }
                        }
                    }, 'image/jpeg', 0.8);
                }
            }
        }, 10000); // Check every 10 seconds (Performance Optimization)

        return () => clearInterval(interval);
    }, [enabled, stream]);

    if (!enabled) return null;

    return (
        <div className="fixed bottom-4 right-4 bg-black/80 text-xs text-white p-2 rounded-lg border border-cyan-500/30 backdrop-blur-sm z-50 flex items-center gap-3">
            <div className="relative w-16 h-12 bg-gray-900 rounded overflow-hidden">
                <video 
                    ref={videoRef} 
                    autoPlay 
                    playsInline 
                    muted 
                    className="w-full h-full object-cover opacity-50"
                />
                <canvas ref={canvasRef} width="640" height="480" className="hidden" />
                <div className="absolute inset-0 flex items-center justify-center">
                    <Eye className="w-4 h-4 text-cyan-400 animate-pulse" />
                </div>
            </div>
            <div>
                <div className="font-bold text-cyan-400 flex items-center gap-1">
                    MOBILE VISION
                </div>
                <div>{status}</div>
                {lastDetection && (
                    <div className="text-green-400">Erkannt: {lastDetection}</div>
                )}
                {/* <div className="text-[10px] text-gray-400 mt-1 max-w-[150px] break-words">
                    {debugInfo}
                </div> */}
            </div>
        </div>
    );
};

export default MobileVision;